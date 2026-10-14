r"""
semantic.py — Visitor semántico para Compiscript.
Adaptado a la gramática grammars/compiscript/Compiscript.g4 actual.

Además de validar el programa, el analizador deja anotado el árbol para que
el generador de código intermedio no tenga que volver a inferir nada:

  node_types[ctx]    tipo inferido de cada expresión/nodo visitado
  node_scopes[ctx]   scope que abre cada bloque, función, clase o bucle
  node_symbols[ctx]  símbolo al que se resuelve un nodo (identificador,
                     declaración, llamada, acceso a miembro, new)
  warnings           avisos que no impiden generar código
"""
from antlr4 import *
# Importante: el parser se importa siempre por la ruta de paquete. Si se cargara
# también como módulo suelto ('CompiscriptParser'), Python lo trataría como otro
# módulo y los isinstance() contra sus contextos fallarían en silencio.
from compiscript.generated.CompiscriptVisitor import CompiscriptVisitor
from compiscript.generated.CompiscriptParser import CompiscriptParser
from compiscript.symbol_table import SymbolTable, Symbol, Type
from compiscript.errors import SemanticError, UndeclaredVariableError, RedeclarationError, TypeMismatchError, InvalidOperationError, ReturnOutsideFunctionError, BreakOutsideLoopError, ContinueOutsideLoopError, NotCallableError, ArgumentCountError, ReturnTypeMismatchError, UndeclaredClassError, AttributeNotFoundError, ThisOutsideClassError, ConstNotInitializedError, NonBooleanConditionError, DeadCodeError

def for_parts(ctx):
    """
    Separa la condición y la actualización de un for. Cualquiera de las dos
    puede faltar, así que no basta con mirar cuántas expresiones hay:
    se distingue por estar antes o después del segundo ';'.
    """
    cond = update = None
    seen_semicolon = False
    for child in list(ctx.getChildren())[3:-2]:
        if isinstance(child, CompiscriptParser.ExpressionContext):
            if seen_semicolon:
                update = child
            else:
                cond = child
        elif child.getText() == ';':
            seen_semicolon = True
    return cond, update


# Si es False, el código muerto se reporta como advertencia y no bloquea la
# generación de código. Por defecto es error, como en las pruebas existentes.
DEAD_CODE_IS_ERROR = True


class SemanticAnalyzer(CompiscriptVisitor):

    def __init__(self):
        self.table = SymbolTable()
        self.errors = []
        self.warnings = []
        self.node_types = {}
        self.node_scopes = {}
        self.node_symbols = {}

    def visit(self, tree):
        """Visita un nodo y guarda su tipo para el generador de código."""
        result = tree.accept(self)
        if isinstance(result, str) and not result.startswith('__'):
            self.node_types[tree] = result
        return result

    def error(self, err):
        self.errors.append(err)

    def _report_dead_code(self, stmt):
        severity = 'error' if DEAD_CODE_IS_ERROR else 'warning'
        err = DeadCodeError(self._line(stmt), self._col(stmt), severity)
        (self.errors if DEAD_CODE_IS_ERROR else self.warnings).append(err)

    def _check_call(self, name, params, args, line, col):
        """Valida cantidad y tipos de los argumentos de una llamada."""
        expected, got = len(params), len(args)
        if expected != got:
            self.error(ArgumentCountError(name, expected, got, line, col))
            return
        for (_, p_type), arg_type in zip(params, args):
            if not Type.is_compatible(p_type, arg_type):
                self.error(TypeMismatchError(p_type, arg_type, line, col))

    def _line(self, ctx):
        try:
            return ctx.start.line
        except:
            return None

    def _col(self, ctx):
        try:
            return ctx.start.column
        except:
            return None

    def visitProgram(self, ctx):
        return self.visitChildren(ctx)

    def visitVariableDeclaration(self, ctx):
        """
        variableDeclaration
          : ('let' | 'var') Identifier typeAnnotation? initializer? ';'
        """
        name = ctx.Identifier().getText()
        line, col = (self._line(ctx), self._col(ctx))
        if self.table.is_defined_local(name):
            self.error(RedeclarationError(name, line, col))
            return Type.UNKNOWN
        declared_type = None
        if ctx.typeAnnotation():
            declared_type = self._resolve_type(ctx.typeAnnotation())
        init_type = None
        if ctx.initializer():
            init_type = self.visit(ctx.initializer())
        final_type = declared_type or init_type or Type.ANY
        if declared_type and init_type:
            if init_type not in (Type.ANY, Type.UNKNOWN):
                if not Type.is_compatible(declared_type, init_type):
                    self.error(TypeMismatchError(declared_type, init_type, line, col))
        self.node_symbols[ctx] = self.table.define_variable(name, final_type, line=line)
        return final_type

    def visitConstantDeclaration(self, ctx):
        """
        constantDeclaration
          : 'const' Identifier typeAnnotation? '=' expression ';'
        """
        name = ctx.Identifier().getText()
        line, col = (self._line(ctx), self._col(ctx))
        if self.table.is_defined_local(name):
            self.error(RedeclarationError(name, line, col))
            return Type.UNKNOWN
        declared_type = None
        if ctx.typeAnnotation():
            declared_type = self._resolve_type(ctx.typeAnnotation())
        init_type = self.visit(ctx.expression())
        final_type = declared_type or init_type or Type.ANY
        if declared_type and init_type:
            if init_type not in (Type.ANY, Type.UNKNOWN):
                if not Type.is_compatible(declared_type, init_type):
                    self.error(TypeMismatchError(declared_type, init_type, line, col))
        self.node_symbols[ctx] = self.table.define_const(name, final_type, line=line)
        return final_type

    def visitInitializer(self, ctx):
        return self.visit(ctx.expression())

    def _check_property_assign(self, obj_type, member_name, value_type, line, col, node=None):
        """Valida `obj.miembro = valor` y retorna el tipo del miembro."""
        if obj_type in (Type.ANY, Type.UNKNOWN):
            return value_type
        if obj_type in (Type.INTEGER, Type.STRING, Type.BOOLEAN, Type.NULL, Type.VOID) or Type.is_array(obj_type):
            self.error(AttributeNotFoundError(str(obj_type), member_name, line, col))
            return Type.UNKNOWN
        member = self._lookup_class_member(obj_type, member_name)
        if not member:
            self.error(AttributeNotFoundError(obj_type, member_name, line, col))
            return Type.UNKNOWN
        if node is not None:
            self.node_symbols[node] = member
        if member.kind == 'const':
            self.error(SemanticError(f"No se puede reasignar la constante '{member_name}'", line, col))
        elif member.kind == 'function':
            self.error(SemanticError(f"No se puede asignar al método '{member_name}'", line, col))
        elif value_type != Type.UNKNOWN and not Type.is_compatible(member.type, value_type):
            self.error(TypeMismatchError(member.type, value_type, line, col))
        return member.type

    def visitAssignment(self, ctx):
        """
        assignment
          : Identifier '=' expression ';'
          | expression '.' Identifier '=' expression ';'
        """
        line, col = (self._line(ctx), self._col(ctx))
        if ctx.getChildCount() == 4:
            name = ctx.Identifier().getText()
            sym = self.table.lookup(name)
            if not sym:
                self.error(UndeclaredVariableError(name, line, col))
                self.visit(ctx.expression(0))
                return Type.UNKNOWN
            self.node_symbols[ctx] = sym
            value_type = self.visit(ctx.expression(0))
            if sym.kind == 'const':
                self.error(SemanticError(f"No se puede reasignar la constante '{name}'", line, col))
                return sym.type
            if value_type != Type.UNKNOWN:
                if not Type.is_compatible(sym.type, value_type):
                    self.error(TypeMismatchError(sym.type, value_type, line, col))
            return sym.type
        # asignación a propiedad: obj.miembro = valor
        expressions = ctx.expression()
        obj_type = self.visit(expressions[0])
        value_type = self.visit(expressions[1])
        return self._check_property_assign(obj_type, ctx.Identifier().getText(), value_type, line, col, ctx)

    def visitFunctionDeclaration(self, ctx):
        """
        functionDeclaration:
          'function' Identifier '(' parameters? ')'
          (':' type)? block;
        """
        name = ctx.Identifier().getText()
        line, col = (self._line(ctx), self._col(ctx))
        if self.table.is_defined_local(name):
            self.error(RedeclarationError(name, line, col))
            return Type.UNKNOWN
        params = []
        param_ctxs = []
        param_names = set()
        if ctx.parameters():
            for param in ctx.parameters().parameter():
                p_name = param.Identifier().getText()
                p_type = Type.ANY
                if param.type_():
                    p_type = self._resolve_type(param.type_())
                if p_name in param_names:
                    self.error(RedeclarationError(p_name, self._line(param), self._col(param)))
                param_names.add(p_name)
                params.append((p_name, p_type))
                param_ctxs.append(param)
        return_type = Type.VOID
        if ctx.type_():
            return_type = self._resolve_type(ctx.type_())
        # un método recibe `this` como primer parámetro implícito
        method_of = self.table.get_current_class() if self.table.current_scope.kind == 'class' else None
        sym = self.table.define_function(name, params, return_type, line=line)
        self.node_symbols[ctx] = sym
        scope = self.table.enter_scope(f'function:{name}', kind='function')
        self.node_scopes[ctx] = scope
        scope.function_symbol = sym
        scope.expected_return = return_type
        scope.found_return = False
        if method_of:
            self.table.define_param('this', method_of, line=line)
        for param, (p_name, p_type) in zip(param_ctxs, params):
            self.node_symbols[param] = self.table.define_param(p_name, p_type, line=self._line(param))
        self.visit(ctx.block())
        self.table.exit_scope()
        return return_type

    def _get_class_symbol(self, class_name):
        """Busca el símbolo global de una clase."""
        sym = self.table.global_scope.lookup_local(class_name)
        if sym and sym.kind == 'class':
            return sym
        return None

    def _get_class_scope(self, class_name):
        """Busca el scope creado para una clase."""
        target = f'class:{class_name}'
        for scope in self.table.all_scopes:
            if scope.name == target and scope.kind == 'class':
                return scope
        return None

    def _lookup_class_member(self, class_name, member_name):
        """Busca un atributo/método, incluyendo clases padre."""
        visited = set()
        while class_name and class_name not in visited:
            visited.add(class_name)
            class_scope = self._get_class_scope(class_name)
            if class_scope:
                member = class_scope.lookup_local(member_name)
                if member:
                    return member
            class_sym = self._get_class_symbol(class_name)
            class_name = getattr(class_sym, 'parent_class', None) if class_sym else None
        return None

    def visitClassDeclaration(self, ctx):
        """
        classDeclaration:
          'class' Identifier (':' Identifier)?
          '{' classMember* '}';
        """
        identifiers = ctx.Identifier()
        name = identifiers[0].getText()
        line, col = (self._line(ctx), self._col(ctx))
        if self.table.is_defined_local(name):
            self.error(RedeclarationError(name, line, col))
            return Type.UNKNOWN
        sym = self.table.define_class(name, line=line)
        self.node_symbols[ctx] = sym
        inherited_size = 0
        if len(identifiers) > 1:
            parent_name = identifiers[1].getText()
            parent_sym = self.table.lookup(parent_name)
            if not parent_sym or parent_sym.kind != 'class':
                self.error(UndeclaredClassError(parent_name, line, col))
            else:
                sym.parent_class = parent_name
                inherited_size = parent_sym.size   # los atributos heredados van primero
        scope = self.table.enter_scope(f'class:{name}', kind='class')
        self.node_scopes[ctx] = scope
        scope.class_symbol = sym
        scope.next_offset = inherited_size
        for member in ctx.classMember():
            self.visit(member)
        self.table.exit_scope()
        return name

    def visitClassMember(self, ctx):
        return self.visitChildren(ctx)

    def visitBlock(self, ctx):
        """
        block: '{' statement* '}';
        """
        self.node_scopes[ctx] = self.table.enter_scope('block', kind='block')
        dead_code = False
        for stmt in ctx.statement():
            if dead_code:
                self._report_dead_code(stmt)
                break
            result = self.visit(stmt)
            if result in ('__return__', '__break__', '__continue__'):
                dead_code = True
        self.table.exit_scope()

    def visitStatement(self, ctx):
        return self.visitChildren(ctx)

    def visitExpressionStatement(self, ctx):
        return self.visit(ctx.expression())

    def visitPrintStatement(self, ctx):
        self.visit(ctx.expression())
        return Type.VOID

    def visitReturnStatement(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        if not self.table.is_in_function():
            self.error(ReturnOutsideFunctionError(line, col))
            return '__return__'
        ret_type = Type.VOID
        if ctx.expression():
            ret_type = self.visit(ctx.expression())
        scope = self.table.current_scope
        while scope:
            if scope.kind == 'function':
                expected = getattr(scope, 'expected_return', Type.VOID)
                if expected != Type.VOID:
                    if not Type.is_compatible(expected, ret_type):
                        func_sym = getattr(scope, 'function_symbol', None)
                        fname = func_sym.name if func_sym else '?'
                        self.error(ReturnTypeMismatchError(fname, expected, ret_type, line, col))
                elif ret_type != Type.VOID:
                    func_sym = getattr(scope, 'function_symbol', None)
                    fname = func_sym.name if func_sym else '?'
                    self.error(ReturnTypeMismatchError(fname, Type.VOID, ret_type, line, col))
                scope.found_return = True
                break
            scope = scope.parent
        return '__return__'

    def visitBreakStatement(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        if not self.table.is_in_breakable():
            self.error(BreakOutsideLoopError(line, col))
        return '__break__'

    def visitContinueStatement(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        if not self.table.is_in_loop():
            self.error(ContinueOutsideLoopError(line, col))
        return '__continue__'

    def visitIfStatement(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        cond_type = self.visit(ctx.expression())
        if cond_type not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
            self.error(NonBooleanConditionError('if', cond_type, line, col))
        for block in ctx.block():
            self.visit(block)

    def visitWhileStatement(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        cond_type = self.visit(ctx.expression())
        if cond_type not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
            self.error(NonBooleanConditionError('while', cond_type, line, col))
        self.node_scopes[ctx] = self.table.enter_scope('while', kind='loop')
        self.visit(ctx.block())
        self.table.exit_scope()

    def visitDoWhileStatement(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        self.node_scopes[ctx] = self.table.enter_scope('do-while', kind='loop')
        self.visit(ctx.block())
        self.table.exit_scope()
        cond_type = self.visit(ctx.expression())
        if cond_type not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
            self.error(NonBooleanConditionError('do-while', cond_type, line, col))

    def visitForStatement(self, ctx):
        """
        forStatement:
          'for' '('
          (variableDeclaration | assignment | ';')
          expression? ';'
          expression?
          ')'
          block;
        """
        self.node_scopes[ctx] = self.table.enter_scope('for', kind='loop')
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        cond, update = for_parts(ctx)
        if cond is not None:
            condition_type = self.visit(cond)
            if condition_type not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
                self.error(NonBooleanConditionError('for', condition_type, self._line(cond), self._col(cond)))
        if update is not None:
            self.visit(update)
        self.visit(ctx.block())
        self.table.exit_scope()

    def visitForeachStatement(self, ctx):
        # la colección se evalúa en el scope de afuera; la variable es del bucle
        iter_type = self.visit(ctx.expression())
        element_type = Type.ANY
        if Type.is_array(iter_type):
            element_type = Type.element_type(iter_type)
        elif iter_type not in (Type.ANY, Type.UNKNOWN):
            self.error(TypeMismatchError('array', iter_type, self._line(ctx), self._col(ctx)))
        self.node_scopes[ctx] = self.table.enter_scope('foreach', kind='loop')
        var_name = ctx.Identifier().getText()
        self.node_symbols[ctx] = self.table.define_variable(var_name, element_type, line=self._line(ctx))
        self.visit(ctx.block())
        self.table.exit_scope()

    def visitTryCatchStatement(self, ctx):
        self.table.enter_scope('try', kind='block')
        self.visit(ctx.block(0))
        self.table.exit_scope()
        self.table.enter_scope('catch', kind='block')
        catch_name = ctx.Identifier().getText()
        self.table.define_variable(catch_name, Type.ANY)
        self.visit(ctx.block(1))
        self.table.exit_scope()

    def visitSwitchStatement(self, ctx):
        self.visit(ctx.expression())
        # 'switch' acepta break pero no continue (a menos que haya un bucle afuera)
        self.node_scopes[ctx] = self.table.enter_scope('switch', kind='switch')
        for case in ctx.switchCase():
            self.visit(case)
        if ctx.defaultCase():
            self.visit(ctx.defaultCase())
        self.table.exit_scope()

    def _visit_case_body(self, statements):
        dead_code = False
        for stmt in statements:
            if dead_code:
                self._report_dead_code(stmt)
                break
            result = self.visit(stmt)
            if result in ('__return__', '__break__', '__continue__'):
                dead_code = True

    def visitSwitchCase(self, ctx):
        self.visit(ctx.expression())
        self._visit_case_body(ctx.statement())
        return None

    def visitDefaultCase(self, ctx):
        self._visit_case_body(ctx.statement())
        return None

    def visitExpression(self, ctx):
        return self.visit(ctx.assignmentExpr())

    def _lvalue_kind(self, lhs_ctx):
        """Clasifica el lado izquierdo de una asignación: 'var' | 'index' | 'property' | None."""
        suffixes = lhs_ctx.suffixOp()
        if not suffixes:
            if isinstance(lhs_ctx.primaryAtom(), CompiscriptParser.IdentifierExprContext):
                return 'var'
            return None
        last = suffixes[-1]
        if isinstance(last, CompiscriptParser.IndexExprContext):
            return 'index'
        if isinstance(last, CompiscriptParser.PropertyAccessExprContext):
            return 'property'
        return None

    def visitAssignExpr(self, ctx):
        """
        lhs '=' assignmentExpr, donde lhs puede ser una variable (x),
        un elemento de lista (a[i]) o un atributo (obj.campo).
        """
        line, col = (self._line(ctx), self._col(ctx))
        lhs = ctx.lhs
        kind = self._lvalue_kind(lhs)
        target_type = self.visit(lhs)
        value_type = self.visit(ctx.assignmentExpr())

        if kind is None:
            self.error(SemanticError("El lado izquierdo de la asignación no es asignable", line, col))
            return Type.UNKNOWN
        if target_type == Type.UNKNOWN:
            return Type.UNKNOWN

        if kind == 'var':
            name = lhs.primaryAtom().getText()
            sym = self.node_symbols.get(lhs.primaryAtom())
            if sym is not None and sym.kind == 'const':
                self.error(SemanticError(f"No se puede reasignar la constante '{name}'", line, col))
            elif sym is not None and sym.kind in ('function', 'class'):
                self.error(SemanticError(f"'{name}' no es una variable asignable", line, col))
                return Type.UNKNOWN
        elif kind == 'property':
            member = self.node_symbols.get(lhs.suffixOp()[-1])
            member_name = lhs.suffixOp()[-1].Identifier().getText()
            if member is not None and member.kind == 'const':
                self.error(SemanticError(f"No se puede reasignar la constante '{member_name}'", line, col))
            elif member is not None and member.kind == 'function':
                self.error(SemanticError(f"No se puede asignar al método '{member_name}'", line, col))
                return Type.UNKNOWN

        if value_type != Type.UNKNOWN and not Type.is_compatible(target_type, value_type):
            self.error(TypeMismatchError(target_type, value_type, line, col))
        return target_type

    def visitPropertyAssignExpr(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        obj_type = self.visit(ctx.lhs)
        value_type = self.visit(ctx.assignmentExpr())
        return self._check_property_assign(obj_type, ctx.Identifier().getText(), value_type, line, col, ctx)

    def visitExprNoAssign(self, ctx):
        return self.visit(ctx.conditionalExpr())

    def visitTernaryExpr(self, ctx):
        condition_type = self.visit(ctx.logicalOrExpr())
        if not ctx.expression():
            return condition_type
        line, col = (self._line(ctx), self._col(ctx))
        if condition_type not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
            self.error(NonBooleanConditionError('?:', condition_type, line, col))
        expressions = ctx.expression()
        true_type = self.visit(expressions[0])
        false_type = self.visit(expressions[1])
        if Type.is_compatible(true_type, false_type):
            return true_type
        self.error(TypeMismatchError(true_type, false_type, line, col))
        return Type.ANY

    def visitLogicalOrExpr(self, ctx):
        operands = ctx.logicalAndExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        result = Type.BOOLEAN
        for operand in operands:
            t = self.visit(operand)
            if t not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
                self.error(InvalidOperationError('||', t, line=self._line(ctx), col=self._col(ctx)))
        return result

    def visitLogicalAndExpr(self, ctx):
        operands = ctx.equalityExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        for operand in operands:
            t = self.visit(operand)
            if t not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
                self.error(InvalidOperationError('&&', t, line=self._line(ctx), col=self._col(ctx)))
        return Type.BOOLEAN

    def visitEqualityExpr(self, ctx):
        operands = ctx.relationalExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        types = [self.visit(op) for op in operands]
        for i in range(len(types) - 1):
            if not Type.is_compatible(types[i], types[i + 1]):
                self.error(TypeMismatchError(types[i], types[i + 1], self._line(ctx), self._col(ctx)))
        return Type.BOOLEAN

    def visitRelationalExpr(self, ctx):
        operands = ctx.additiveExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        types = [self.visit(op) for op in operands]
        for i in range(len(types) - 1):
            t1 = types[i]
            t2 = types[i + 1]
            if t1 not in (Type.ANY, Type.UNKNOWN) and t2 not in (Type.ANY, Type.UNKNOWN):
                if not (Type.is_numeric(t1) and Type.is_numeric(t2)):
                    self.error(InvalidOperationError('relacional', t1, t2, self._line(ctx), self._col(ctx)))
        return Type.BOOLEAN

    def visitAdditiveExpr(self, ctx):
        operands = ctx.multiplicativeExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        current_type = self.visit(operands[0])
        children = list(ctx.getChildren())
        operand_index = 1
        for child in children:
            text = child.getText()
            if text not in ('+', '-'):
                continue
            next_type = self.visit(operands[operand_index])
            operand_index += 1
            if text == '+':
                if current_type == Type.STRING and next_type == Type.STRING:
                    current_type = Type.STRING
                    continue
                if Type.is_numeric(current_type) and Type.is_numeric(next_type):
                    current_type = Type.INTEGER
                    continue
                if current_type == Type.ANY or next_type == Type.ANY:
                    current_type = Type.ANY
                    continue
                self.error(InvalidOperationError('+', current_type, next_type, self._line(ctx), self._col(ctx)))
                current_type = Type.UNKNOWN
            elif current_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN) or next_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN):
                self.error(InvalidOperationError('-', current_type, next_type, self._line(ctx), self._col(ctx)))
                current_type = Type.UNKNOWN
            else:
                current_type = Type.INTEGER
        return current_type

    def visitMultiplicativeExpr(self, ctx):
        operands = ctx.unaryExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        current_type = self.visit(operands[0])
        children = list(ctx.getChildren())
        operand_index = 1
        for child in children:
            op = child.getText()
            if op not in ('*', '/', '%'):
                continue
            next_type = self.visit(operands[operand_index])
            operand_index += 1
            if current_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN) or next_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN):
                self.error(InvalidOperationError(op, current_type, next_type, self._line(ctx), self._col(ctx)))
                current_type = Type.UNKNOWN
            else:
                current_type = Type.INTEGER
        return current_type

    def visitUnaryExpr(self, ctx):
        if ctx.primaryExpr():
            return self.visit(ctx.primaryExpr())
        op = ctx.getChild(0).getText()
        value_type = self.visit(ctx.unaryExpr())
        line, col = (self._line(ctx), self._col(ctx))
        if op == '!':
            if value_type not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
                self.error(InvalidOperationError('!', value_type, line=line, col=col))
            return Type.BOOLEAN
        if op == '-':
            if value_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN):
                self.error(InvalidOperationError('-', value_type, line=line, col=col))
            return Type.INTEGER
        return value_type

    def visitPrimaryExpr(self, ctx):
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        if ctx.expression():
            return self.visit(ctx.expression())
        return Type.ANY

    def visitLiteralExpr(self, ctx):
        text = ctx.getText()
        if text == 'true':
            return Type.BOOLEAN
        if text == 'false':
            return Type.BOOLEAN
        if text == 'null':
            return Type.NULL
        if ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        if ctx.Literal():
            value = ctx.Literal().getText()
            if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                return Type.STRING
            try:
                int(value)
                return Type.INTEGER
            except ValueError:
                return Type.ANY
        return Type.ANY

    def visitLeftHandSide(self, ctx):
        """
        leftHandSide: primaryAtom (suffixOp)*
        Resuelve la cadena de sufijos (.miembro, (args), [indice]) de izquierda
        a derecha y anota el tipo resultante de cada sufijo.
        """
        current_type = self.visit(ctx.primaryAtom())
        pending_member = None   # miembro al que se aplicará la siguiente llamada
        for position, suffix in enumerate(ctx.suffixOp()):
            line, col = (self._line(suffix), self._col(suffix))

            if isinstance(suffix, CompiscriptParser.PropertyAccessExprContext):
                member_name = suffix.Identifier().getText()
                if current_type in (Type.ANY, Type.UNKNOWN, Type.INTEGER, Type.STRING, Type.BOOLEAN, Type.NULL, Type.VOID):
                    if current_type not in (Type.ANY, Type.UNKNOWN):
                        self.error(AttributeNotFoundError(str(current_type), member_name, line, col))
                    current_type = Type.ANY
                    pending_member = None
                else:
                    member = self._lookup_class_member(current_type, member_name)
                    if not member:
                        self.error(AttributeNotFoundError(current_type, member_name, line, col))
                        current_type = Type.UNKNOWN
                        pending_member = '__invalid_member__'
                    else:
                        self.node_symbols[suffix] = member
                        pending_member = member
                        if member.kind == 'function':
                            current_type = member.return_type or Type.ANY
                        else:
                            current_type = member.type

            elif isinstance(suffix, CompiscriptParser.CallExprContext):
                args = []
                if suffix.arguments():
                    for expr in suffix.arguments().expression():
                        args.append(self.visit(expr))
                if pending_member == '__invalid_member__':
                    current_type = Type.UNKNOWN
                elif pending_member is not None:
                    # llamada a un método: obj.metodo(...)
                    if pending_member.kind != 'function':
                        self.error(NotCallableError(pending_member.name, line, col))
                        current_type = Type.UNKNOWN
                    else:
                        self._check_call(pending_member.name, pending_member.params, args, line, col)
                        current_type = pending_member.return_type or Type.ANY
                elif position == 0:
                    # llamada directa a una función: f(...)
                    name = ctx.primaryAtom().getText()
                    if '(' in name:
                        name = name.split('(')[0]
                    sym = self.table.lookup(name)
                    if not sym:
                        current_type = Type.ANY
                    elif sym.kind != 'function':
                        self.error(NotCallableError(name, line, col))
                        current_type = Type.UNKNOWN
                    else:
                        self._check_call(name, sym.params, args, line, col)
                        self.node_symbols[suffix] = sym
                        current_type = sym.return_type or Type.ANY
                else:
                    # llamar el resultado de otra expresión (por ejemplo a[0](x)): no se conoce
                    current_type = Type.ANY
                pending_member = None

            elif isinstance(suffix, CompiscriptParser.IndexExprContext):
                index_type = self.visit(suffix.expression())
                if index_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN):
                    self.error(TypeMismatchError(Type.INTEGER, index_type, line, col))
                if Type.is_array(current_type):
                    current_type = Type.element_type(current_type)
                elif current_type in (Type.INTEGER, Type.BOOLEAN, Type.NULL, Type.VOID):
                    self.error(InvalidOperationError('[]', current_type, line=line, col=col))
                    current_type = Type.UNKNOWN
                else:
                    current_type = Type.ANY
                pending_member = None

            self.node_types[suffix] = current_type
        return current_type

    def visitIdentifierExpr(self, ctx):
        name = ctx.Identifier().getText()
        line, col = (self._line(ctx), self._col(ctx))
        sym = self.table.lookup(name)
        if not sym:
            self.error(UndeclaredVariableError(name, line, col))
            return Type.UNKNOWN
        self.node_symbols[ctx] = sym
        if sym.kind == 'function':
            return sym.return_type or Type.ANY
        if sym.kind == 'class':
            return sym.name
        return sym.type

    def visitNewExpr(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        class_name = ctx.Identifier().getText()
        class_sym = self.table.lookup(class_name)
        if not class_sym or class_sym.kind != 'class':
            self.error(UndeclaredClassError(class_name, line, col))
            if ctx.arguments():
                for expr in ctx.arguments().expression():
                    self.visit(expr)
            return Type.UNKNOWN
        self.node_symbols[ctx] = class_sym
        args = []
        if ctx.arguments():
            for expr in ctx.arguments().expression():
                args.append(self.visit(expr))
        constructor = self._lookup_class_member(class_name, 'constructor')
        if constructor and constructor.kind == 'function':
            self._check_call(f'{class_name}.constructor', constructor.params, args, line, col)
        elif args:
            self.error(ArgumentCountError(f'{class_name}.constructor', 0, len(args), line, col))
        return class_name

    def visitThisExpr(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        if not self.table.is_in_class():
            self.error(ThisOutsideClassError(line, col))
            return Type.UNKNOWN
        current_class = self.table.get_current_class()
        return current_class or Type.ANY

    def visitArguments(self, ctx):
        result = []
        for expr in ctx.expression():
            result.append(self.visit(expr))
        return result

    def visitArrayLiteral(self, ctx):
        expressions = ctx.expression()
        if not expressions:
            return 'array:any'
        element_types = [self.visit(expr) for expr in expressions]
        base_type = element_types[0]
        for current_type in element_types[1:]:
            if base_type not in (Type.ANY, Type.UNKNOWN) and current_type not in (Type.ANY, Type.UNKNOWN) and (not Type.is_compatible(base_type, current_type)):
                self.error(TypeMismatchError(base_type, current_type, self._line(ctx), self._col(ctx)))
        if base_type == Type.UNKNOWN:
            base_type = Type.ANY
        return f'array:{base_type}'

    def visitTypeAnnotation(self, ctx):
        return self._resolve_type(ctx)

    def visitType(self, ctx):
        return self._resolve_type(ctx)

    def visitBaseType(self, ctx):
        return self._resolve_type(ctx)

    def _resolve_type(self, type_ctx):
        """
        Convierte type/typeAnnotation/baseType
        al sistema Type de Compiscript.
        integer[] -> array:integer, integer[][] -> array:array:integer
        """
        text = type_ctx.getText().replace(':', '').strip()
        mapping = {'integer': Type.INTEGER, 'string': Type.STRING, 'boolean': Type.BOOLEAN, 'void': Type.VOID, 'null': Type.NULL}
        dims = 0
        while text.endswith('[]'):
            text = text[:-2]
            dims += 1
        resolved = mapping.get(text, text)
        for _ in range(dims):
            resolved = Type.array_of(resolved)
        return resolved

    def visitChildren(self, ctx):
        result = None
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if hasattr(child, 'accept'):
                result = child.accept(self)
        return result

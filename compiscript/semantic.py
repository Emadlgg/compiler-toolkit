"""
semantic.py — Visitor semántico para Compiscript.
Adaptado a la gramática Compiscript.g4 actual.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generated'))
from antlr4 import *
from CompiscriptVisitor import CompiscriptVisitor
from CompiscriptParser import CompiscriptParser
from compiscript.symbol_table import SymbolTable, Symbol, Type
from compiscript.errors import SemanticError, UndeclaredVariableError, RedeclarationError, TypeMismatchError, InvalidOperationError, ReturnOutsideFunctionError, BreakOutsideLoopError, ContinueOutsideLoopError, NotCallableError, ArgumentCountError, ReturnTypeMismatchError, UndeclaredClassError, AttributeNotFoundError, ThisOutsideClassError, ConstNotInitializedError, NonBooleanConditionError, DeadCodeError

class SemanticAnalyzer(CompiscriptVisitor):

    def __init__(self):
        self.table = SymbolTable()
        self.errors = []

    def error(self, err):
        self.errors.append(err)

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
        self.table.define_variable(name, final_type, line=line)
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
        self.table.define_const(name, final_type, line=line)
        return final_type

    def visitInitializer(self, ctx):
        return self.visit(ctx.expression())

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
                return Type.UNKNOWN
            value_type = self.visit(ctx.expression(0))
            if sym.kind == 'const':
                self.error(SemanticError(f"No se puede reasignar la constante '{name}'", line, col))
                return sym.type
            if value_type != Type.UNKNOWN:
                if not Type.is_compatible(sym.type, value_type):
                    self.error(TypeMismatchError(sym.type, value_type, line, col))
            return sym.type
        expressions = ctx.expression()
        if expressions:
            for expr in expressions:
                self.visit(expr)
        return Type.ANY

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
        return_type = Type.VOID
        if ctx.type_():
            return_type = self._resolve_type(ctx.type_())
        sym = self.table.define_function(name, params, return_type, line=line)
        scope = self.table.enter_scope(f'function:{name}', kind='function')
        scope.function_symbol = sym
        scope.expected_return = return_type
        scope.found_return = False
        for p_name, p_type in params:
            self.table.define_variable(p_name, p_type)
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
        if len(identifiers) > 1:
            parent_name = identifiers[1].getText()
            parent_sym = self.table.lookup(parent_name)
            if not parent_sym or parent_sym.kind != 'class':
                self.error(UndeclaredClassError(parent_name, line, col))
            else:
                sym.parent_class = parent_name
        self.table.enter_scope(f'class:{name}', kind='class')
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
        self.table.enter_scope('block', kind='block')
        dead_code = False
        for stmt in ctx.statement():
            if dead_code:
                self.error(DeadCodeError(self._line(stmt), self._col(stmt)))
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
        if not self.table.is_in_loop():
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
        self.table.enter_scope('while', kind='loop')
        self.visit(ctx.block())
        self.table.exit_scope()

    def visitDoWhileStatement(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        self.table.enter_scope('do-while', kind='loop')
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
        self.table.enter_scope('for', kind='loop')
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        expressions = ctx.expression()
        if expressions:
            condition_type = self.visit(expressions[0])
            if condition_type not in (Type.BOOLEAN, Type.ANY, Type.UNKNOWN):
                self.error(NonBooleanConditionError('for', condition_type, self._line(expressions[0]), self._col(expressions[0])))
            if len(expressions) > 1:
                self.visit(expressions[1])
        self.visit(ctx.block())
        self.table.exit_scope()

    def visitForeachStatement(self, ctx):
        self.table.enter_scope('foreach', kind='loop')
        var_name = ctx.Identifier().getText()
        self.table.define_variable(var_name, Type.ANY)
        self.visit(ctx.expression())
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
        self.table.enter_scope('switch', kind='loop')
        for case in ctx.switchCase():
            self.visit(case)
        if ctx.defaultCase():
            self.visit(ctx.defaultCase())
        self.table.exit_scope()

    def visitSwitchCase(self, ctx):
        self.visit(ctx.expression())
        dead_code = False
        for stmt in ctx.statement():
            if dead_code:
                self.error(DeadCodeError(self._line(stmt), self._col(stmt)))
                break
            result = self.visit(stmt)
            if result in ('__return__', '__break__', '__continue__'):
                dead_code = True
        return None

    def visitDefaultCase(self, ctx):
        dead_code = False
        for stmt in ctx.statement():
            if dead_code:
                self.error(DeadCodeError(self._line(stmt), self._col(stmt)))
                break
            result = self.visit(stmt)
            if result in ('__return__', '__break__', '__continue__'):
                dead_code = True
        return None

    def visitExpression(self, ctx):
        return self.visit(ctx.assignmentExpr())

    def visitAssignExpr(self, ctx):
        line, col = (self._line(ctx), self._col(ctx))
        lhs_text = ctx.lhs.getText()
        sym = self.table.lookup(lhs_text)
        if not sym:
            self.error(UndeclaredVariableError(lhs_text, line, col))
            self.visit(ctx.assignmentExpr())
            return Type.UNKNOWN
        value_type = self.visit(ctx.assignmentExpr())
        if sym.kind == 'const':
            self.error(SemanticError(f"No se puede reasignar la constante '{lhs_text}'", line, col))
        if value_type != Type.UNKNOWN:
            if not Type.is_compatible(sym.type, value_type):
                self.error(TypeMismatchError(sym.type, value_type, line, col))
        return sym.type

    def visitPropertyAssignExpr(self, ctx):
        self.visit(ctx.lhs)
        value_type = self.visit(ctx.assignmentExpr())
        return value_type

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
        current_type = self.visit(ctx.primaryAtom())
        pending_member = None
        for suffix in ctx.suffixOp():
            if isinstance(suffix, CompiscriptParser.PropertyAccessExprContext):
                member_name = suffix.Identifier().getText()
                if current_type in (Type.ANY, Type.UNKNOWN, Type.INTEGER, Type.STRING, Type.BOOLEAN, Type.NULL, Type.VOID):
                    if current_type not in (Type.ANY, Type.UNKNOWN):
                        self.error(AttributeNotFoundError(str(current_type), member_name, self._line(suffix), self._col(suffix)))
                    current_type = Type.ANY
                    pending_member = None
                    continue
                member = self._lookup_class_member(current_type, member_name)
                if not member:
                    self.error(AttributeNotFoundError(current_type, member_name, self._line(suffix), self._col(suffix)))
                    current_type = Type.UNKNOWN
                    pending_member = '__invalid_member__'
                    continue
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
                    pending_member = None
                    continue
                if pending_member is not None:
                    if pending_member.kind != 'function':
                        self.error(NotCallableError(pending_member.name, self._line(suffix), self._col(suffix)))
                        current_type = Type.UNKNOWN
                    else:
                        expected = len(pending_member.params)
                        got = len(args)
                        if expected != got:
                            self.error(ArgumentCountError(pending_member.name, expected, got, self._line(suffix), self._col(suffix)))
                        else:
                            for (_, p_type), arg_type in zip(pending_member.params, args):
                                if not Type.is_compatible(p_type, arg_type):
                                    self.error(TypeMismatchError(p_type, arg_type, self._line(suffix), self._col(suffix)))
                        current_type = pending_member.return_type or Type.ANY
                    pending_member = None
                else:
                    current_type = self._handle_call_suffix(ctx, suffix, current_type, precomputed_args=args)
            elif isinstance(suffix, CompiscriptParser.IndexExprContext):
                index_type = self.visit(suffix.expression())
                if index_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN):
                    self.error(TypeMismatchError(Type.INTEGER, index_type, self._line(suffix), self._col(suffix)))
                if isinstance(current_type, str) and current_type.startswith('array:'):
                    current_type = current_type.split(':', 1)[1]
                else:
                    current_type = Type.ANY
                pending_member = None
        return current_type

    def visitIdentifierExpr(self, ctx):
        name = ctx.Identifier().getText()
        line, col = (self._line(ctx), self._col(ctx))
        sym = self.table.lookup(name)
        if not sym:
            self.error(UndeclaredVariableError(name, line, col))
            return Type.UNKNOWN
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
        args = []
        if ctx.arguments():
            for expr in ctx.arguments().expression():
                args.append(self.visit(expr))
        constructor = self._lookup_class_member(class_name, 'constructor')
        if constructor and constructor.kind == 'function':
            expected = len(constructor.params)
            got = len(args)
            if expected != got:
                self.error(ArgumentCountError(f'{class_name}.constructor', expected, got, line, col))
            else:
                for (_, param_type), arg_type in zip(constructor.params, args):
                    if not Type.is_compatible(param_type, arg_type):
                        self.error(TypeMismatchError(param_type, arg_type, line, col))
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

    def visitCallExpr(self, ctx):
        """
        Este visitor normalmente es procesado desde
        visitLeftHandSide porque necesitamos conocer
        qué expresión se está llamando.
        """
        if ctx.arguments():
            for expr in ctx.arguments().expression():
                self.visit(expr)
        return Type.ANY

    def visitIndexExpr(self, ctx):
        index_type = self.visit(ctx.expression())
        if index_type not in (Type.INTEGER, Type.ANY, Type.UNKNOWN):
            self.error(TypeMismatchError(Type.INTEGER, index_type, self._line(ctx), self._col(ctx)))
        return Type.ANY

    def visitPropertyAccessExpr(self, ctx):
        return Type.ANY

    def _handle_call_suffix(self, lhs_ctx, call_ctx, current_type, precomputed_args=None):
        line, col = (self._line(call_ctx), self._col(call_ctx))
        primary = lhs_ctx.primaryAtom()
        name = primary.getText()
        if '(' in name:
            name = name.split('(')[0]
        sym = self.table.lookup(name)
        args = []
        if precomputed_args is not None:
            args = precomputed_args
        elif call_ctx.arguments():
            for expr in call_ctx.arguments().expression():
                args.append(self.visit(expr))
        if not sym:
            return Type.ANY
        if sym.kind != 'function':
            self.error(NotCallableError(name, line, col))
            return Type.UNKNOWN
        expected = len(sym.params)
        got = len(args)
        if expected != got:
            self.error(ArgumentCountError(name, expected, got, line, col))
        else:
            for (p_name, p_type), arg_type in zip(sym.params, args):
                if not Type.is_compatible(p_type, arg_type):
                    self.error(TypeMismatchError(p_type, arg_type, line, col))
        return sym.return_type or Type.ANY

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
        """
        text = type_ctx.getText().replace(':', '').strip()
        mapping = {'integer': Type.INTEGER, 'string': Type.STRING, 'boolean': Type.BOOLEAN, 'void': Type.VOID, 'null': Type.NULL}
        if text.endswith('[]'):
            return Type.ANY
        return mapping.get(text, text)

    def visitChildren(self, ctx):
        result = None
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if hasattr(child, 'accept'):
                result = child.accept(self)
        return result
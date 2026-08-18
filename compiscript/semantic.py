"""
semantic.py — Visitor semántico para Compiscript.
Recorre el árbol ANTLR y valida todas las reglas semánticas.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "generated"))

from antlr4 import *
from CompiscriptVisitor import CompiscriptVisitor
from CompiscriptParser  import CompiscriptParser

from compiscript.symbol_table import SymbolTable, Symbol, Type
from compiscript.errors import (
    UndeclaredVariableError, RedeclarationError, TypeMismatchError,
    InvalidOperationError, ReturnOutsideFunctionError, BreakOutsideLoopError,
    ContinueOutsideLoopError, NotCallableError, ArgumentCountError,
    ReturnTypeMismatchError, UndeclaredClassError, AttributeNotFoundError,
    ThisOutsideClassError, ConstNotInitializedError, NonBooleanConditionError,
    DeadCodeError
)


class SemanticAnalyzer(CompiscriptVisitor):

    def __init__(self):
        self.table  = SymbolTable()
        self.errors = []

    def error(self, err):
        self.errors.append(err)

    def _line(self, ctx):
        try:    return ctx.start.line
        except: return None

    def _col(self, ctx):
        try:    return ctx.start.column
        except: return None

    # ─────────────────────────────────────────────────────
    # Programa
    # ─────────────────────────────────────────────────────

    def visitProgram(self, ctx):
        return self.visitChildren(ctx)

    # ─────────────────────────────────────────────────────
    # Declaración de variables — let / const
    # ─────────────────────────────────────────────────────

    def visitVariableDeclaration(self, ctx):
        name     = ctx.IDENTIFIER().getText()
        is_const = ctx.getChild(0).getText() == "const"
        line, col = self._line(ctx), self._col(ctx)

        # Redeclaración
        if self.table.is_defined_local(name):
            self.error(RedeclarationError(name, line, col))
            return Type.UNKNOWN

        # Tipo declarado
        declared_type = None
        if ctx.typeAnnotation():
            declared_type = self._resolve_type(ctx.typeAnnotation())

        # Valor inicial
        init_type = None
        if ctx.initializer():
            init_type = self.visit(ctx.initializer())

        # Const debe inicializarse
        if is_const and not ctx.initializer():
            self.error(ConstNotInitializedError(name, line, col))

        # Verificar compatibilidad de tipos
        final_type = declared_type or init_type or Type.ANY
        if declared_type and init_type and init_type != Type.ANY:
            if not Type.is_compatible(declared_type, init_type):
                self.error(TypeMismatchError(declared_type, init_type, line, col))

        # Registrar en tabla
        if is_const:
            self.table.define_const(name, final_type, line=line)
        else:
            self.table.define_variable(name, final_type, line=line)

        return final_type

    def visitInitializer(self, ctx):
        return self.visit(ctx.expression())

    # ─────────────────────────────────────────────────────
    # Declaración de funciones
    # ─────────────────────────────────────────────────────

    def visitFunctionDeclaration(self, ctx):
        name      = ctx.IDENTIFIER().getText()
        line, col = self._line(ctx), self._col(ctx)

        # Redeclaración
        if self.table.is_defined_local(name):
            self.error(RedeclarationError(name, line, col))

        # Parámetros
        params      = []
        param_names = set()
        if ctx.parameters():
            for param in ctx.parameters().parameter():
                p_name = param.IDENTIFIER().getText()
                p_type = Type.ANY
                if param.typeAnnotation():
                    p_type = self._resolve_type(param.typeAnnotation())
                if p_name in param_names:
                    self.error(RedeclarationError(p_name, line, col))
                param_names.add(p_name)
                params.append((p_name, p_type))

        # Tipo de retorno
        return_type = Type.VOID
        if ctx.typeAnnotation():
            return_type = self._resolve_type(ctx.typeAnnotation())

        # Registrar función
        sym = self.table.define_function(name, params, return_type, line=line)

        # Nuevo scope para el cuerpo
        scope = self.table.enter_scope(f"function:{name}", kind="function")
        scope.function_symbol    = sym
        scope.expected_return    = return_type
        scope.found_return       = False

        # Agregar parámetros al scope
        for p_name, p_type in params:
            self.table.define_variable(p_name, p_type)

        # Visitar cuerpo
        self.visit(ctx.blockStatement())

        self.table.exit_scope()
        return return_type

    # ─────────────────────────────────────────────────────
    # Declaración de clases
    # ─────────────────────────────────────────────────────

    def visitClassDeclaration(self, ctx):
        name      = ctx.IDENTIFIER(0).getText()
        line, col = self._line(ctx), self._col(ctx)

        if self.table.is_defined_local(name):
            self.error(RedeclarationError(name, line, col))

        sym = self.table.define_class(name, line=line)

        # Herencia
        if ctx.IDENTIFIER(1):
            parent_name = ctx.IDENTIFIER(1).getText()
            parent_sym  = self.table.lookup(parent_name)
            if not parent_sym or parent_sym.kind != "class":
                self.error(UndeclaredClassError(parent_name, line, col))
            else:
                sym.parent_class = parent_name

        # Scope de la clase
        self.table.enter_scope(f"class:{name}", kind="class")

        # Visitar miembros
        if ctx.classBody():
            for member in ctx.classBody().classMember():
                self.visit(member)

        self.table.exit_scope()
        return name

    def visitClassMember(self, ctx):
        return self.visitChildren(ctx)

    # ─────────────────────────────────────────────────────
    # Bloque de sentencias
    # ─────────────────────────────────────────────────────

    def visitBlockStatement(self, ctx):
        self.table.enter_scope("block", kind="block")
        dead_code = False
        for stmt in ctx.statement():
            if dead_code:
                self.error(DeadCodeError(self._line(stmt), self._col(stmt)))
                break
            result = self.visit(stmt)
            if result == "__return__" or result == "__break__" or result == "__continue__":
                dead_code = True
        self.table.exit_scope()

    # ─────────────────────────────────────────────────────
    # Sentencias
    # ─────────────────────────────────────────────────────

    def visitStatement(self, ctx):
        return self.visitChildren(ctx)

    def visitReturnStatement(self, ctx):
        line, col = self._line(ctx), self._col(ctx)

        if not self.table.is_in_function():
            self.error(ReturnOutsideFunctionError(line, col))
            return "__return__"

        ret_type = Type.VOID
        if ctx.expression():
            ret_type = self.visit(ctx.expression())

        # Verificar tipo de retorno
        scope = self.table.current_scope
        while scope:
            if scope.kind == "function" and hasattr(scope, "expected_return"):
                expected = scope.expected_return
                if expected and expected != Type.VOID:
                    if not Type.is_compatible(expected, ret_type):
                        func_sym = scope.function_symbol
                        fname = func_sym.name if func_sym else "?"
                        self.error(ReturnTypeMismatchError(fname, expected, ret_type, line, col))
                scope.found_return = True
                break
            scope = scope.parent

        return "__return__"

    def visitBreakStatement(self, ctx):
        line, col = self._line(ctx), self._col(ctx)
        if not self.table.is_in_loop():
            self.error(BreakOutsideLoopError(line, col))
        return "__break__"

    def visitContinueStatement(self, ctx):
        line, col = self._line(ctx), self._col(ctx)
        if not self.table.is_in_loop():
            self.error(ContinueOutsideLoopError(line, col))
        return "__continue__"

    # ─────────────────────────────────────────────────────
    # Control de flujo
    # ─────────────────────────────────────────────────────

    def visitIfStatement(self, ctx):
        line, col  = self._line(ctx), self._col(ctx)
        cond_type  = self.visit(ctx.expression())

        if cond_type != Type.BOOLEAN and cond_type != Type.ANY:
            self.error(NonBooleanConditionError("if", cond_type, line, col))

        for stmt in ctx.statement():
            self.visit(stmt)

    def visitWhileStatement(self, ctx):
        line, col = self._line(ctx), self._col(ctx)
        cond_type = self.visit(ctx.expression())

        if cond_type != Type.BOOLEAN and cond_type != Type.ANY:
            self.error(NonBooleanConditionError("while", cond_type, line, col))

        self.table.enter_scope("while", kind="loop")
        self.visit(ctx.statement())
        self.table.exit_scope()

    def visitDoWhileStatement(self, ctx):
        line, col = self._line(ctx), self._col(ctx)

        self.table.enter_scope("do-while", kind="loop")
        self.visit(ctx.statement())
        self.table.exit_scope()

        cond_type = self.visit(ctx.expression())
        if cond_type != Type.BOOLEAN and cond_type != Type.ANY:
            self.error(NonBooleanConditionError("do-while", cond_type, line, col))

    def visitForStatement(self, ctx):
        line, col = self._line(ctx), self._col(ctx)
        self.table.enter_scope("for", kind="loop")

        children = list(ctx.getChildren())
        # visitar inicialización, condición y actualización
        self.visitChildren(ctx)

        self.table.exit_scope()

    def visitForeachStatement(self, ctx):
        self.table.enter_scope("foreach", kind="loop")
        var_name = ctx.IDENTIFIER(0).getText()
        self.table.define_variable(var_name, Type.ANY)
        self.visitChildren(ctx)
        self.table.exit_scope()

    def visitSwitchStatement(self, ctx):
        line, col = self._line(ctx), self._col(ctx)
        self.visit(ctx.expression())
        self.table.enter_scope("switch", kind="loop")  # loop para permitir break
        for case in ctx.caseClause():
            self.visit(case)
        if ctx.defaultClause():
            self.visit(ctx.defaultClause())
        self.table.exit_scope()

    def visitCaseClause(self, ctx):
        return self.visitChildren(ctx)

    def visitDefaultClause(self, ctx):
        return self.visitChildren(ctx)

    def visitTryCatch(self, ctx):
        self.table.enter_scope("try", kind="block")
        self.visit(ctx.blockStatement(0))
        self.table.exit_scope()

        if ctx.blockStatement(1):
            self.table.enter_scope("catch", kind="block")
            if ctx.IDENTIFIER():
                self.table.define_variable(ctx.IDENTIFIER().getText(), Type.ANY)
            self.visit(ctx.blockStatement(1))
            self.table.exit_scope()

    # ─────────────────────────────────────────────────────
    # Expresiones
    # ─────────────────────────────────────────────────────

    def visitExpression(self, ctx):
        return self.visitChildren(ctx)

    def visitAssignmentExpr(self, ctx):
        if ctx.getChildCount() == 3:
            # asignación: ID = expr
            name      = ctx.getChild(0).getText()
            line, col = self._line(ctx), self._col(ctx)
            sym = self.table.lookup(name)

            if not sym:
                self.error(UndeclaredVariableError(name, line, col))
                return Type.UNKNOWN

            val_type = self.visit(ctx.getChild(2))

            if sym.kind == "const":
                from compiscript.errors import SemanticError
                self.error(SemanticError(f"No se puede reasignar la constante '{name}'", line, col))

            if not Type.is_compatible(sym.type, val_type):
                self.error(TypeMismatchError(sym.type, val_type, line, col))

            return sym.type

        return self.visitChildren(ctx)

    def visitLogicalOrExpr(self, ctx):
        if ctx.getChildCount() == 3:
            t1 = self.visit(ctx.getChild(0))
            t2 = self.visit(ctx.getChild(2))
            line, col = self._line(ctx), self._col(ctx)
            if t1 not in (Type.BOOLEAN, Type.ANY) or t2 not in (Type.BOOLEAN, Type.ANY):
                self.error(InvalidOperationError("||", t1, t2, line, col))
            return Type.BOOLEAN
        return self.visitChildren(ctx)

    def visitLogicalAndExpr(self, ctx):
        if ctx.getChildCount() == 3:
            t1 = self.visit(ctx.getChild(0))
            t2 = self.visit(ctx.getChild(2))
            line, col = self._line(ctx), self._col(ctx)
            if t1 not in (Type.BOOLEAN, Type.ANY) or t2 not in (Type.BOOLEAN, Type.ANY):
                self.error(InvalidOperationError("&&", t1, t2, line, col))
            return Type.BOOLEAN
        return self.visitChildren(ctx)

    def visitEqualityExpr(self, ctx):
        if ctx.getChildCount() == 3:
            t1 = self.visit(ctx.getChild(0))
            t2 = self.visit(ctx.getChild(2))
            if not Type.is_compatible(t1, t2):
                self.error(TypeMismatchError(t1, t2, self._line(ctx), self._col(ctx)))
            return Type.BOOLEAN
        return self.visitChildren(ctx)

    def visitRelationalExpr(self, ctx):
        if ctx.getChildCount() == 3:
            t1 = self.visit(ctx.getChild(0))
            t2 = self.visit(ctx.getChild(2))
            op = ctx.getChild(1).getText()
            line, col = self._line(ctx), self._col(ctx)
            if not (Type.is_numeric(t1) or t1 == Type.ANY):
                self.error(InvalidOperationError(op, t1, t2, line, col))
            return Type.BOOLEAN
        return self.visitChildren(ctx)

    def visitAdditiveExpr(self, ctx):
        if ctx.getChildCount() == 3:
            t1  = self.visit(ctx.getChild(0))
            op  = ctx.getChild(1).getText()
            t2  = self.visit(ctx.getChild(2))
            line, col = self._line(ctx), self._col(ctx)

            # + permite string + string o integer + integer
            if op == "+":
                if t1 == Type.STRING and t2 == Type.STRING:
                    return Type.STRING
                if t1 == Type.ANY or t2 == Type.ANY:
                    return Type.ANY
                if not (Type.is_numeric(t1) and Type.is_numeric(t2)):
                    self.error(InvalidOperationError(op, t1, t2, line, col))
                return Type.INTEGER
            else:
                if t1 not in (Type.INTEGER, Type.ANY) or t2 not in (Type.INTEGER, Type.ANY):
                    self.error(InvalidOperationError(op, t1, t2, line, col))
                return Type.INTEGER

        return self.visitChildren(ctx)

    def visitMultiplicativeExpr(self, ctx):
        if ctx.getChildCount() == 3:
            t1  = self.visit(ctx.getChild(0))
            op  = ctx.getChild(1).getText()
            t2  = self.visit(ctx.getChild(2))
            line, col = self._line(ctx), self._col(ctx)
            if t1 not in (Type.INTEGER, Type.ANY) or t2 not in (Type.INTEGER, Type.ANY):
                self.error(InvalidOperationError(op, t1, t2, line, col))
            return Type.INTEGER
        return self.visitChildren(ctx)

    def visitUnaryExpr(self, ctx):
        if ctx.getChildCount() == 2:
            op        = ctx.getChild(0).getText()
            t         = self.visit(ctx.getChild(1))
            line, col = self._line(ctx), self._col(ctx)
            if op == "!" and t not in (Type.BOOLEAN, Type.ANY):
                self.error(InvalidOperationError("!", t, line=line, col=col))
                return Type.BOOLEAN
            if op == "-" and t not in (Type.INTEGER, Type.ANY):
                self.error(InvalidOperationError("-", t, line=line, col=col))
                return Type.INTEGER
            return t
        return self.visitChildren(ctx)

    # ─────────────────────────────────────────────────────
    # Primarios: literals, variables, llamadas, this, new
    # ─────────────────────────────────────────────────────

    def visitPrimaryExpr(self, ctx):
        text = ctx.getText()

        # Literales
        if ctx.INTEGER_LITERAL():  return Type.INTEGER
        if ctx.FLOAT_LITERAL():    return Type.INTEGER  # tratamos float como number
        if ctx.STRING_LITERAL():   return Type.STRING
        if ctx.BOOLEAN_LITERAL():  return Type.BOOLEAN
        if text == "null":         return Type.NULL

        # this
        if text == "this":
            line, col = self._line(ctx), self._col(ctx)
            if not self.table.is_in_class():
                self.error(ThisOutsideClassError(line, col))
            return Type.ANY

        # Identificador
        if ctx.IDENTIFIER():
            name      = ctx.IDENTIFIER().getText()
            line, col = self._line(ctx), self._col(ctx)
            sym = self.table.lookup(name)
            if not sym:
                self.error(UndeclaredVariableError(name, line, col))
                return Type.UNKNOWN
            return sym.type

        # Expresión entre paréntesis
        if ctx.expression():
            return self.visit(ctx.expression())

        return Type.ANY

    def visitCallExpr(self, ctx):
        """Llamada a función: ID(args)"""
        line, col = self._line(ctx), self._col(ctx)
        callee    = self.visit(ctx.getChild(0))
        name      = ctx.getChild(0).getText().split("(")[0]

        sym = self.table.lookup(name)
        if sym and sym.kind not in ("function",):
            self.error(NotCallableError(name, line, col))
            return Type.UNKNOWN

        # Validar argumentos
        args = []
        if ctx.argumentList():
            for arg in ctx.argumentList().expression():
                args.append(self.visit(arg))

        if sym and sym.kind == "function":
            expected = len(sym.params)
            got      = len(args)
            if expected != got:
                self.error(ArgumentCountError(name, expected, got, line, col))
            else:
                for i, ((p_name, p_type), arg_type) in enumerate(zip(sym.params, args)):
                    if not Type.is_compatible(p_type, arg_type):
                        self.error(TypeMismatchError(p_type, arg_type, line, col))

            return sym.return_type or Type.ANY

        return Type.ANY

    def visitNewExpr(self, ctx):
        """new ClassName(args)"""
        line, col  = self._line(ctx), self._col(ctx)
        class_name = ctx.IDENTIFIER().getText()
        sym = self.table.lookup(class_name)
        if not sym or sym.kind != "class":
            self.error(UndeclaredClassError(class_name, line, col))
            return Type.UNKNOWN
        return class_name

    def visitMemberAccess(self, ctx):
        """obj.attr o obj.method()"""
        return Type.ANY

    def visitArrayAccess(self, ctx):
        """arr[index]"""
        return Type.ANY

    def visitArrayLiteral(self, ctx):
        """[1, 2, 3]"""
        types = []
        if ctx.expressionList():
            for expr in ctx.expressionList().expression():
                types.append(self.visit(expr))
        return Type.ANY

    # ─────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────

    def _resolve_type(self, type_ctx):
        """Convierte el texto del tipo a un tipo del sistema."""
        text = type_ctx.getText().replace(":", "").strip()
        mapping = {
            "integer": Type.INTEGER,
            "string":  Type.STRING,
            "boolean": Type.BOOLEAN,
            "void":    Type.VOID,
            "null":    Type.NULL,
        }
        if text.endswith("[]"):
            return Type.ANY  # arrays simplificados
        return mapping.get(text, text)  # clases custom retornan su nombre

    def visitChildren(self, ctx):
        result = None
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if hasattr(child, "accept"):
                result = child.accept(self)
        return result
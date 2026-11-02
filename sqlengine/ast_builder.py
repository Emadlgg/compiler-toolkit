"""
ast_builder.py — Convierte el árbol sintáctico del parser en el AST.

    result = parse(texto)
    if result.ok:
        script = build_ast(result)      # Script con una sentencia por cada sentencia del texto
"""

from sqlengine import ast
from sqlengine.ast import Name
from sqlengine.generated.SqlParser import SqlParser
from sqlengine.generated.SqlParserVisitor import SqlParserVisitor
from sqlengine.treeview import render_text


def build_ast(result):
    """AST de un script ya analizado. Solo se puede construir si no hubo errores."""
    if not result.ok:
        raise ValueError("no se puede construir el AST: el texto tiene errores léxicos o sintácticos")
    return AstBuilder().visit(result.tree)


def format_ast(node, positions=False):
    """El AST como texto con sangría."""
    return render_text(ast.to_tree(node, positions))


def _pos(ctx):
    return {"line": ctx.start.line, "column": ctx.start.column}


def _name(ctx):
    """Un nombre con su posición en el texto."""
    return Name(ctx.getText(), ctx.start.line, ctx.start.column)


def _unquote(text):
    """'O''Brien' -> O'Brien"""
    return text[1:-1].replace("''", "'")


class AstBuilder(SqlParserVisitor):

    # ── Programa y sentencias ─────────────────────────────

    def visitScript(self, ctx):
        return ast.Script([self.visit(s) for s in ctx.statement()], **_pos(ctx))

    def visitStatement(self, ctx):
        return self.visit(ctx.getChild(0))

    # ── Definición de datos ───────────────────────────────

    def visitCreateTable(self, ctx):
        return ast.CreateTable(_name(ctx.tableName()), [self.visit(c) for c in ctx.columnDef()], **_pos(ctx))

    def visitColumnDef(self, ctx):
        flags = {c.getText().upper() for c in ctx.columnConstraint()}      # getText junta los tokens: PRIMARYKEY, NOTNULL
        return ast.ColumnDef(
            _name(ctx.columnName()), self.visit(ctx.dataType()),
            primary_key="PRIMARYKEY" in flags, not_null="NOTNULL" in flags, unique="UNIQUE" in flags,
            **_pos(ctx))

    def visitDataType(self, ctx):
        name = ctx.getChild(0).getText().upper()
        length = int(ctx.INTEGER_LITERAL().getText()) if ctx.INTEGER_LITERAL() else None
        return ast.DataType(name, length, **_pos(ctx))

    def visitDropTable(self, ctx):
        return ast.DropTable(_name(ctx.tableName()), **_pos(ctx))

    def visitCreateIndex(self, ctx):
        return ast.CreateIndex(_name(ctx.indexName()), _name(ctx.tableName()), _name(ctx.columnName()), **_pos(ctx))

    def visitDropIndex(self, ctx):
        return ast.DropIndex(_name(ctx.indexName()), **_pos(ctx))

    def visitCreateDatabase(self, ctx):
        return ast.CreateDatabase(_name(ctx.databaseName()), **_pos(ctx))

    def visitUseDatabase(self, ctx):
        return ast.UseDatabase(_name(ctx.databaseName()), **_pos(ctx))

    def visitShowDatabases(self, ctx):
        return ast.ShowDatabases(**_pos(ctx))

    def visitShowTables(self, ctx):
        return ast.ShowTables(**_pos(ctx))

    # ── Manipulación de datos ─────────────────────────────

    def visitInsertStmt(self, ctx):
        columns = [_name(c) for c in ctx.columnName()]
        return ast.Insert(_name(ctx.tableName()), columns or None, [self.visit(r) for r in ctx.valueRow()], **_pos(ctx))

    def visitValueRow(self, ctx):
        return ast.Row([self.visit(e) for e in ctx.expr()], **_pos(ctx))

    def visitUpdateStmt(self, ctx):
        where = self.visit(ctx.expr()) if ctx.expr() else None
        return ast.Update(_name(ctx.tableName()), [self.visit(a) for a in ctx.assignment()], where, **_pos(ctx))

    def visitAssignment(self, ctx):
        return ast.Assignment(_name(ctx.columnName()), self.visit(ctx.expr()), **_pos(ctx))

    def visitDeleteStmt(self, ctx):
        where = self.visit(ctx.expr()) if ctx.expr() else None
        return ast.Delete(_name(ctx.tableName()), where, **_pos(ctx))

    # ── Consultas ─────────────────────────────────────────

    def visitSelectStmt(self, ctx):
        return ast.Select(
            items=[self.visit(i) for i in ctx.selectItem()],
            from_table=self.visit(ctx.tableRef()),
            joins=[self.visit(j) for j in ctx.joinClause()],
            where=self.visit(ctx.where) if ctx.where else None,
            group_by=[self.visit(e) for e in ctx.groupBy],
            having=self.visit(ctx.having) if ctx.having else None,
            order_by=[self.visit(o) for o in ctx.orderItem()],
            **_pos(ctx))

    def visitSelectAll(self, ctx):
        return ast.Star(None, **_pos(ctx))

    def visitSelectAllFrom(self, ctx):
        return ast.Star(_name(ctx.tableName()), **_pos(ctx))

    def visitSelectExpr(self, ctx):
        alias = _name(ctx.alias()) if ctx.alias() else None
        return ast.SelectExpr(self.visit(ctx.expr()), alias, **_pos(ctx))

    def visitTableRef(self, ctx):
        alias = _name(ctx.alias()) if ctx.alias() else None
        return ast.TableRef(_name(ctx.tableName()), alias, **_pos(ctx))

    def visitJoinClause(self, ctx):
        return ast.Join(self.visit(ctx.tableRef()), self.visit(ctx.expr()), **_pos(ctx))

    def visitOrderItem(self, ctx):
        return ast.OrderItem(self.visit(ctx.expr()), ctx.DESC() is not None, **_pos(ctx))

    # ── Expresiones ───────────────────────────────────────

    def visitExpr(self, ctx):
        return self.visit(ctx.orExpr())

    def _chain(self, ctx, operands, ops):
        """Encadena los operandos hacia la izquierda: a - b - c es (a - b) - c."""
        node = self.visit(operands[0])
        for i in range(1, len(operands)):
            node = ast.BinaryOp(ops[i - 1], node, self.visit(operands[i]), **_pos(ctx))
        return node

    @staticmethod
    def _operators(ctx):
        """Los operadores de una cadena `a op b op c`, que son los hijos en posición impar."""
        return [ctx.getChild(i).getText().upper() for i in range(1, ctx.getChildCount(), 2)]

    def visitOrExpr(self, ctx):
        return self._chain(ctx, ctx.andExpr(), self._operators(ctx))

    def visitAndExpr(self, ctx):
        return self._chain(ctx, ctx.notExpr(), self._operators(ctx))

    def visitNotExpr(self, ctx):
        if ctx.NOT() is None:
            return self.visit(ctx.predicate())
        operand = self.visit(ctx.notExpr())
        if isinstance(operand, ast.Exists):                 # NOT EXISTS (...) es un solo nodo
            operand.negated = not operand.negated
            operand.line, operand.column = ctx.start.line, ctx.start.column
            return operand
        return ast.UnaryOp("NOT", operand, **_pos(ctx))

    def visitComparisonPred(self, ctx):
        op = ctx.op.getText()
        return ast.BinaryOp("<>" if op == "!=" else op, self.visit(ctx.left), self.visit(ctx.right), **_pos(ctx))

    def visitInPred(self, ctx):
        expr = self.visit(ctx.additive())
        negated = ctx.NOT() is not None
        values = ctx.inList()
        if values.selectStmt():
            return ast.InSubquery(expr, self.visit(values.selectStmt()), negated, **_pos(ctx))
        return ast.InList(expr, [self.visit(e) for e in values.expr()], negated, **_pos(ctx))

    def visitIsNullPred(self, ctx):
        return ast.IsNull(self.visit(ctx.additive()), ctx.NOT() is not None, **_pos(ctx))

    def visitExistsPred(self, ctx):
        return ast.Exists(self.visit(ctx.selectStmt()), False, **_pos(ctx))

    def visitPlainPred(self, ctx):
        return self.visit(ctx.additive())

    def visitAdditive(self, ctx):
        return self._chain(ctx, ctx.multiplicative(), self._operators(ctx))

    def visitMultiplicative(self, ctx):
        return self._chain(ctx, ctx.unary(), self._operators(ctx))

    def visitUnary(self, ctx):
        if ctx.primary() is not None:
            return self.visit(ctx.primary())
        operand = self.visit(ctx.unary())
        if ctx.getChild(0).getText() == "+":
            return operand
        if isinstance(operand, ast.Literal) and operand.type in ("INT", "FLOAT"):     # -5 es un literal
            return ast.Literal(operand.type, -operand.value, **_pos(ctx))
        return ast.UnaryOp("-", operand, **_pos(ctx))

    def visitLiteralPrimary(self, ctx):
        return self.visit(ctx.literal())

    def visitAggregatePrimary(self, ctx):
        return self.visit(ctx.aggregate())

    def visitColumnPrimary(self, ctx):
        return self.visit(ctx.columnRef())

    def visitScalarSubquery(self, ctx):
        return ast.Subquery(self.visit(ctx.selectStmt()), **_pos(ctx))

    def visitParenPrimary(self, ctx):
        return self.visit(ctx.expr())

    def visitCountStar(self, ctx):
        return ast.Aggregate("COUNT", None, **_pos(ctx))

    def visitAggregateCall(self, ctx):
        return ast.Aggregate(ctx.func.text.upper(), self.visit(ctx.expr()), **_pos(ctx))

    def visitColumnRef(self, ctx):
        table = _name(ctx.tableName()) if ctx.tableName() else None
        return ast.ColumnRef(_name(ctx.columnName()), table, **_pos(ctx))

    def visitLiteral(self, ctx):
        first = ctx.getChild(0).symbol
        text = first.text
        if ctx.getChildCount() == 2:                                   # DATE 'AAAA-MM-DD'
            return ast.Literal("DATE", _unquote(ctx.getChild(1).getText()), **_pos(ctx))
        if first.type == SqlParser.INTEGER_LITERAL:
            return ast.Literal("INT", int(text), **_pos(ctx))
        if first.type == SqlParser.FLOAT_LITERAL:
            return ast.Literal("FLOAT", float(text), **_pos(ctx))
        if first.type == SqlParser.STRING_LITERAL:
            return ast.Literal("VARCHAR", _unquote(text), **_pos(ctx))
        if first.type == SqlParser.NULL:
            return ast.Literal("NULL", None, **_pos(ctx))
        return ast.Literal("BOOLEAN", first.type == SqlParser.TRUE, **_pos(ctx))

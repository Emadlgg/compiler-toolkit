# Generated from SqlParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .SqlParser import SqlParser
else:
    from SqlParser import SqlParser

# This class defines a complete generic visitor for a parse tree produced by SqlParser.

class SqlParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SqlParser#script.
    def visitScript(self, ctx:SqlParser.ScriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#statement.
    def visitStatement(self, ctx:SqlParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#createDatabase.
    def visitCreateDatabase(self, ctx:SqlParser.CreateDatabaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#useDatabase.
    def visitUseDatabase(self, ctx:SqlParser.UseDatabaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#showDatabases.
    def visitShowDatabases(self, ctx:SqlParser.ShowDatabasesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#showTables.
    def visitShowTables(self, ctx:SqlParser.ShowTablesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#databaseName.
    def visitDatabaseName(self, ctx:SqlParser.DatabaseNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#createTable.
    def visitCreateTable(self, ctx:SqlParser.CreateTableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#columnDef.
    def visitColumnDef(self, ctx:SqlParser.ColumnDefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#columnConstraint.
    def visitColumnConstraint(self, ctx:SqlParser.ColumnConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#dataType.
    def visitDataType(self, ctx:SqlParser.DataTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#dropTable.
    def visitDropTable(self, ctx:SqlParser.DropTableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#createIndex.
    def visitCreateIndex(self, ctx:SqlParser.CreateIndexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#dropIndex.
    def visitDropIndex(self, ctx:SqlParser.DropIndexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#insertStmt.
    def visitInsertStmt(self, ctx:SqlParser.InsertStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#valueRow.
    def visitValueRow(self, ctx:SqlParser.ValueRowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#updateStmt.
    def visitUpdateStmt(self, ctx:SqlParser.UpdateStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#assignment.
    def visitAssignment(self, ctx:SqlParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#deleteStmt.
    def visitDeleteStmt(self, ctx:SqlParser.DeleteStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#selectStmt.
    def visitSelectStmt(self, ctx:SqlParser.SelectStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#selectAll.
    def visitSelectAll(self, ctx:SqlParser.SelectAllContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#selectAllFrom.
    def visitSelectAllFrom(self, ctx:SqlParser.SelectAllFromContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#selectExpr.
    def visitSelectExpr(self, ctx:SqlParser.SelectExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#tableRef.
    def visitTableRef(self, ctx:SqlParser.TableRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#joinClause.
    def visitJoinClause(self, ctx:SqlParser.JoinClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#orderItem.
    def visitOrderItem(self, ctx:SqlParser.OrderItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#expr.
    def visitExpr(self, ctx:SqlParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#orExpr.
    def visitOrExpr(self, ctx:SqlParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#andExpr.
    def visitAndExpr(self, ctx:SqlParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#notExpr.
    def visitNotExpr(self, ctx:SqlParser.NotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#comparisonPred.
    def visitComparisonPred(self, ctx:SqlParser.ComparisonPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#inPred.
    def visitInPred(self, ctx:SqlParser.InPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#isNullPred.
    def visitIsNullPred(self, ctx:SqlParser.IsNullPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#existsPred.
    def visitExistsPred(self, ctx:SqlParser.ExistsPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#plainPred.
    def visitPlainPred(self, ctx:SqlParser.PlainPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#inList.
    def visitInList(self, ctx:SqlParser.InListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#compOp.
    def visitCompOp(self, ctx:SqlParser.CompOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#additive.
    def visitAdditive(self, ctx:SqlParser.AdditiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#multiplicative.
    def visitMultiplicative(self, ctx:SqlParser.MultiplicativeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#unary.
    def visitUnary(self, ctx:SqlParser.UnaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#literalPrimary.
    def visitLiteralPrimary(self, ctx:SqlParser.LiteralPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#aggregatePrimary.
    def visitAggregatePrimary(self, ctx:SqlParser.AggregatePrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#columnPrimary.
    def visitColumnPrimary(self, ctx:SqlParser.ColumnPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#scalarSubquery.
    def visitScalarSubquery(self, ctx:SqlParser.ScalarSubqueryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#parenPrimary.
    def visitParenPrimary(self, ctx:SqlParser.ParenPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#countStar.
    def visitCountStar(self, ctx:SqlParser.CountStarContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#aggregateCall.
    def visitAggregateCall(self, ctx:SqlParser.AggregateCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#columnRef.
    def visitColumnRef(self, ctx:SqlParser.ColumnRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#literal.
    def visitLiteral(self, ctx:SqlParser.LiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#tableName.
    def visitTableName(self, ctx:SqlParser.TableNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#columnName.
    def visitColumnName(self, ctx:SqlParser.ColumnNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#indexName.
    def visitIndexName(self, ctx:SqlParser.IndexNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SqlParser#alias.
    def visitAlias(self, ctx:SqlParser.AliasContext):
        return self.visitChildren(ctx)



del SqlParser
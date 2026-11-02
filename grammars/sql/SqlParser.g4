parser grammar SqlParser;

options { tokenVocab = SqlLexer; }

// ── Programa ──────────────────────────────────────────────
// Un script es una lista de sentencias separadas por ';'. Se aceptan ';' de más
// y que la última sentencia no lleve ';'.
script
    : statement? (SEMI statement?)* EOF
    ;

statement
    : createTable
    | dropTable
    | createIndex
    | dropIndex
    | insertStmt
    | updateStmt
    | deleteStmt
    | selectStmt
    | createDatabase
    | useDatabase
    | showDatabases
    | showTables
    ;

createDatabase : CREATE DATABASE databaseName ;
useDatabase : USE databaseName ;
showDatabases : SHOW DATABASES ;
showTables : SHOW TABLES ;
databaseName : IDENTIFIER ;

// ── Definición de datos ───────────────────────────────────
createTable
    : CREATE TABLE tableName LPAREN columnDef (COMMA columnDef)* RPAREN
    ;

columnDef
    : columnName dataType columnConstraint*
    ;

columnConstraint
    : PRIMARY KEY
    | NOT NULL
    | UNIQUE
    ;

dataType
    : INT
    | FLOAT
    | BOOLEAN
    | DATE
    | VARCHAR LPAREN INTEGER_LITERAL RPAREN
    ;

dropTable
    : DROP TABLE tableName
    ;

createIndex
    : CREATE INDEX indexName ON tableName LPAREN columnName RPAREN
    ;

dropIndex
    : DROP INDEX indexName
    ;

// ── Manipulación de datos ─────────────────────────────────
insertStmt
    : INSERT INTO tableName (LPAREN columnName (COMMA columnName)* RPAREN)?
      VALUES valueRow (COMMA valueRow)*
    ;

valueRow
    : LPAREN expr (COMMA expr)* RPAREN
    ;

updateStmt
    : UPDATE tableName SET assignment (COMMA assignment)* (WHERE expr)?
    ;

assignment
    : columnName EQ expr
    ;

deleteStmt
    : DELETE FROM tableName (WHERE expr)?
    ;

// ── Consultas ─────────────────────────────────────────────
// `selectStmt` es una consulta completa; también se usa dentro de WHERE como subconsulta.
selectStmt
    : SELECT selectItem (COMMA selectItem)*
      FROM tableRef joinClause*
      (WHERE where=expr)?
      (GROUP BY groupBy+=expr (COMMA groupBy+=expr)*)?
      (HAVING having=expr)?
      (ORDER BY orderItem (COMMA orderItem)*)?
    ;

selectItem
    : STAR                       # selectAll
    | tableName DOT STAR         # selectAllFrom
    | expr (AS? alias)?          # selectExpr
    ;

tableRef
    : tableName (AS? alias)?
    ;

joinClause
    : INNER? JOIN tableRef ON expr
    ;

orderItem
    : expr (ASC | DESC)?
    ;

// ── Expresiones (de menor a mayor precedencia) ────────────
expr
    : orExpr
    ;

orExpr
    : andExpr (OR andExpr)*
    ;

andExpr
    : notExpr (AND notExpr)*
    ;

notExpr
    : NOT notExpr
    | predicate
    ;

predicate
    : left=additive op=compOp right=additive         # comparisonPred
    | additive NOT? IN LPAREN inList RPAREN          # inPred
    | additive IS NOT? NULL                          # isNullPred
    | EXISTS LPAREN selectStmt RPAREN                # existsPred
    | additive                                       # plainPred
    ;

inList
    : selectStmt
    | expr (COMMA expr)*
    ;

compOp
    : EQ | NEQ | LT | LE | GT | GE
    ;

additive
    : multiplicative ((PLUS | MINUS) multiplicative)*
    ;

multiplicative
    : unary ((STAR | SLASH) unary)*
    ;

unary
    : (MINUS | PLUS) unary
    | primary
    ;

primary
    : literal                       # literalPrimary
    | aggregate                     # aggregatePrimary
    | columnRef                     # columnPrimary
    | LPAREN selectStmt RPAREN      # scalarSubquery
    | LPAREN expr RPAREN            # parenPrimary
    ;

aggregate
    : COUNT LPAREN STAR RPAREN                                  # countStar
    | func=(COUNT | SUM | AVG | MIN | MAX) LPAREN expr RPAREN   # aggregateCall
    ;

columnRef
    : (tableName DOT)? columnName
    ;

literal
    : INTEGER_LITERAL
    | FLOAT_LITERAL
    | STRING_LITERAL
    | TRUE
    | FALSE
    | NULL
    | DATE STRING_LITERAL
    ;

// ── Nombres ───────────────────────────────────────────────
tableName  : IDENTIFIER ;
columnName : IDENTIFIER ;
indexName  : IDENTIFIER ;
alias      : IDENTIFIER ;

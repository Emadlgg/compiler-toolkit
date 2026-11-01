lexer grammar SqlLexer;

// SQL no distingue mayúsculas de minúsculas en las palabras clave: select = SELECT.
options { caseInsensitive = true; }

// ── Palabras clave ────────────────────────────────────────
CREATE  : 'CREATE';
TABLE   : 'TABLE';
DROP    : 'DROP';
INDEX   : 'INDEX';
ON      : 'ON';
INSERT  : 'INSERT';
INTO    : 'INTO';
VALUES  : 'VALUES';
UPDATE  : 'UPDATE';
SET     : 'SET';
DELETE  : 'DELETE';
SELECT  : 'SELECT';
FROM    : 'FROM';
WHERE   : 'WHERE';
AND     : 'AND';
OR      : 'OR';
NOT     : 'NOT';
ORDER   : 'ORDER';
BY      : 'BY';
ASC     : 'ASC';
DESC    : 'DESC';
INNER   : 'INNER';
JOIN    : 'JOIN';
GROUP   : 'GROUP';
HAVING  : 'HAVING';
IN      : 'IN';
EXISTS  : 'EXISTS';
AS      : 'AS';
IS      : 'IS';
NULL    : 'NULL';
TRUE    : 'TRUE';
FALSE   : 'FALSE';
PRIMARY : 'PRIMARY';
KEY     : 'KEY';
UNIQUE  : 'UNIQUE';

// ── Funciones de agregación ───────────────────────────────
COUNT   : 'COUNT';
SUM     : 'SUM';
AVG     : 'AVG';
MIN     : 'MIN';
MAX     : 'MAX';

// ── Tipos de datos ────────────────────────────────────────
INT     : 'INT';
FLOAT   : 'FLOAT';
VARCHAR : 'VARCHAR';
BOOLEAN : 'BOOLEAN';
DATE    : 'DATE';

// ── Operadores y puntuación ───────────────────────────────
EQ      : '=';
NEQ     : '<>' | '!=';
LE      : '<=';
GE      : '>=';
LT      : '<';
GT      : '>';
PLUS    : '+';
MINUS   : '-';
STAR    : '*';
SLASH   : '/';
LPAREN  : '(';
RPAREN  : ')';
COMMA   : ',';
SEMI    : ';';
DOT     : '.';

// ── Literales e identificadores ───────────────────────────
FLOAT_LITERAL   : [0-9]+ '.' [0-9]+ ;
INTEGER_LITERAL : [0-9]+ ;
STRING_LITERAL  : '\'' ( ~'\'' | '\'\'' )* '\'' ;      // 'texto', con '' para una comilla
IDENTIFIER      : [\p{L}_] [\p{L}\p{N}_]* ;             // acepta letras con acento y ñ

// ── Se ignoran ────────────────────────────────────────────
WS            : [ \t\r\n]+ -> skip ;
LINE_COMMENT  : '--' ~[\r\n]* -> skip ;
BLOCK_COMMENT : '/*' .*? '*/' -> skip ;

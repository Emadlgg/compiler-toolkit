"""
ast_cases.py — Pruebas del AST con el resultado esperado escrito a mano.

Cada caso es un texto SQL y el árbol que debe producir. Los nodos se comparan por estructura:
la posición (línea y columna) no cuenta, salvo en los casos de ubicación, que la revisan aparte.
"""

from sqlengine import ast as A
from sqlengine.frontend import parse
from sqlengine.ast_builder import build_ast


def build(sql):
    result = parse(sql)
    assert result.ok, f"el texto no analiza: {[str(e) for e in result.errors]}"
    return build_ast(result)


def first(sql):
    return build(sql).statements[0]


# ── Atajos para escribir lo esperado ──────────────────────

def col(name, table=None): return A.ColumnRef(name, table)
def num(v): return A.Literal("INT", v)
def text(v): return A.Literal("VARCHAR", v)
def op(o, l, r): return A.BinaryOp(o, l, r)
def tref(name, alias=None): return A.TableRef(name, alias)
def item(expr, alias=None): return A.SelectExpr(expr, alias)


def sel(items, frm, joins=(), where=None, group=(), having=None, order=()):
    return A.Select(list(items), frm, list(joins), where, list(group), having, list(order))


def where_of(sql):
    return first(sql).where


def expr_of(sql_expr):
    """La expresión de `SELECT <expr> FROM t`."""
    return first(f"SELECT {sql_expr} FROM t;").items[0].expr


# ── Casos ─────────────────────────────────────────────────

def check_precedence():
    assert where_of("SELECT a FROM t WHERE x OR y AND z;") == op("OR", col("x"), op("AND", col("y"), col("z")))
    assert where_of("SELECT a FROM t WHERE x AND y OR z;") == op("OR", op("AND", col("x"), col("y")), col("z"))
    assert where_of("SELECT a FROM t WHERE (x OR y) AND z;") == op("AND", op("OR", col("x"), col("y")), col("z"))
    assert where_of("SELECT a FROM t WHERE NOT x = 1 AND y;") == op("AND", A.UnaryOp("NOT", op("=", col("x"), num(1))), col("y"))


def check_arithmetic():
    assert expr_of("2 + 3 * 4") == op("+", num(2), op("*", num(3), num(4)))
    assert expr_of("(2 + 3) * 4") == op("*", op("+", num(2), num(3)), num(4))
    assert expr_of("1 - 2 - 3") == op("-", op("-", num(1), num(2)), num(3))
    assert expr_of("8 / 4 / 2") == op("/", op("/", num(8), num(4)), num(2))
    assert expr_of("a * b + c / d") == op("+", op("*", col("a"), col("b")), op("/", col("c"), col("d")))


def check_comparison_operators():
    for written, canonical in [("=", "="), ("<>", "<>"), ("!=", "<>"), ("<", "<"), ("<=", "<="), (">", ">"), (">=", ">=")]:
        assert where_of(f"SELECT a FROM t WHERE a {written} 1;") == op(canonical, col("a"), num(1)), written


def check_unary():
    assert expr_of("-5") == A.Literal("INT", -5)
    assert expr_of("-2.5") == A.Literal("FLOAT", -2.5)
    assert expr_of("+5") == A.Literal("INT", 5)
    assert expr_of("- -5") == A.Literal("INT", 5)
    assert expr_of("-x") == A.UnaryOp("-", col("x"))
    assert expr_of("-(1 + 2)") == A.UnaryOp("-", op("+", num(1), num(2)))
    assert expr_of("1 - -2") == op("-", num(1), A.Literal("INT", -2))


def check_literals():
    assert expr_of("'hola'") == text("hola")
    assert expr_of("'O''Brien'") == text("O'Brien")
    assert expr_of("''") == text("")
    assert expr_of("2.5") == A.Literal("FLOAT", 2.5)
    assert expr_of("TRUE") == A.Literal("BOOLEAN", True)
    assert expr_of("false") == A.Literal("BOOLEAN", False)
    assert expr_of("NULL") == A.Literal("NULL", None)
    assert expr_of("DATE '2005-01-02'") == A.Literal("DATE", "2005-01-02")
    assert expr_of("'2005-01-02'") == text("2005-01-02")        # sin DATE sigue siendo texto


def check_exists_and_not():
    q = sel([item(num(1))], tref("x"))
    assert where_of("SELECT a FROM t WHERE EXISTS (SELECT 1 FROM x);") == A.Exists(q, False)
    assert where_of("SELECT a FROM t WHERE NOT EXISTS (SELECT 1 FROM x);") == A.Exists(q, True)
    assert where_of("SELECT a FROM t WHERE NOT NOT EXISTS (SELECT 1 FROM x);") == A.Exists(q, False)


def check_in_variants():
    assert where_of("SELECT a FROM t WHERE x IN (1, 2);") == A.InList(col("x"), [num(1), num(2)], False)
    assert where_of("SELECT a FROM t WHERE x NOT IN (1);") == A.InList(col("x"), [num(1)], True)
    sub = sel([item(col("id"))], tref("u"))
    assert where_of("SELECT a FROM t WHERE x IN (SELECT id FROM u);") == A.InSubquery(col("x"), sub, False)
    assert where_of("SELECT a FROM t WHERE x NOT IN (SELECT id FROM u);") == A.InSubquery(col("x"), sub, True)


def check_is_null():
    assert where_of("SELECT a FROM t WHERE x IS NULL;") == A.IsNull(col("x"), False)
    assert where_of("SELECT a FROM t WHERE x IS NOT NULL;") == A.IsNull(col("x"), True)


def check_aggregates():
    assert expr_of("COUNT(*)") == A.Aggregate("COUNT", None)
    assert expr_of("count(id)") == A.Aggregate("COUNT", col("id"))
    assert expr_of("Sum(a * 2)") == A.Aggregate("SUM", op("*", col("a"), num(2)))
    for fn in ("AVG", "MIN", "MAX"):
        assert expr_of(f"{fn}(x)") == A.Aggregate(fn, col("x"))


def check_scalar_subquery():
    inner = sel([item(A.Aggregate("AVG", col("edad")))], tref("t"))
    assert where_of("SELECT a FROM t WHERE edad > (SELECT AVG(edad) FROM t);") == op(">", col("edad"), A.Subquery(inner))


def check_select_items_and_aliases():
    s = first("SELECT a AS x, b y, t.*, *, u.c FROM t AS u;")
    assert s.items == [item(col("a"), "x"), item(col("b"), "y"), A.Star("t"), A.Star(None), item(col("c", "u"))]
    assert s.from_table == tref("t", "u")
    assert s.from_table.effective_name == "u"
    assert tref("t").effective_name == "t"


def check_joins():
    s = first("SELECT * FROM a INNER JOIN b ON a.id = b.aid JOIN c AS cc ON cc.x = b.x;")
    assert s.joins == [
        A.Join(tref("b"), op("=", col("id", "a"), col("aid", "b"))),
        A.Join(tref("c", "cc"), op("=", col("x", "cc"), col("x", "b"))),
    ]


def check_group_having_order():
    s = first("SELECT a, COUNT(*) FROM t GROUP BY a, b HAVING COUNT(*) > 1 ORDER BY a, b DESC, c ASC;")
    assert s.group_by == [col("a"), col("b")]
    assert s.having == op(">", A.Aggregate("COUNT", None), num(1))
    assert s.order_by == [A.OrderItem(col("a"), False), A.OrderItem(col("b"), True), A.OrderItem(col("c"), False)]
    bare = first("SELECT a FROM t;")
    assert (bare.where, bare.group_by, bare.having, bare.order_by, bare.joins) == (None, [], None, [], [])


def check_insert():
    s = first("INSERT INTO t (a, b) VALUES (1, 'x'), (2, 'y');")
    assert s == A.Insert("t", ["a", "b"], [A.Row([num(1), text("x")]), A.Row([num(2), text("y")])])
    assert first("INSERT INTO t VALUES (1);").columns is None
    assert first("INSERT INTO t VALUES (-1, 1 + 2);").rows[0].values == [A.Literal("INT", -1), op("+", num(1), num(2))]


def check_update_delete():
    u = first("UPDATE t SET a = a + 1, b = 'z' WHERE id = 3;")
    assert u == A.Update("t", [A.Assignment("a", op("+", col("a"), num(1))), A.Assignment("b", text("z"))], op("=", col("id"), num(3)))
    assert first("UPDATE t SET a = 1;").where is None
    assert first("DELETE FROM t WHERE a < 5;") == A.Delete("t", op("<", col("a"), num(5)))
    assert first("DELETE FROM t;").where is None


def check_create_table():
    s = first("CREATE TABLE t (id INT PRIMARY KEY, nombre VARCHAR(50) NOT NULL UNIQUE, nota FLOAT, ok BOOLEAN, f DATE);")
    assert s.name == "t"
    assert s.columns == [
        A.ColumnDef("id", A.DataType("INT"), primary_key=True),
        A.ColumnDef("nombre", A.DataType("VARCHAR", 50), not_null=True, unique=True),
        A.ColumnDef("nota", A.DataType("FLOAT")),
        A.ColumnDef("ok", A.DataType("BOOLEAN")),
        A.ColumnDef("f", A.DataType("DATE")),
    ]
    assert str(s.columns[1].type) == "VARCHAR(50)"


def check_index_and_drop():
    assert first("CREATE INDEX idx ON t (c);") == A.CreateIndex("idx", "t", "c")
    assert first("DROP INDEX idx;") == A.DropIndex("idx")
    assert first("DROP TABLE t;") == A.DropTable("t")


def check_names_keep_case():
    s = first("SELECT Nombre FROM Estudiantes E WHERE E.Edad > 1;")
    assert s.items[0].expr == col("Nombre")
    assert s.from_table == tref("Estudiantes", "E")


def check_script_statements():
    script = build("SELECT 1 FROM t;; DROP TABLE t; INSERT INTO t VALUES (1)")
    assert [type(s).__name__ for s in script.statements] == ["Select", "DropTable", "Insert"]
    assert build("").statements == []
    assert build(";;;").statements == []


def check_positions():
    s = first("SELECT a\nFROM t\nWHERE b > 1;")
    assert (s.line, s.column) == (1, 0)
    assert (s.from_table.line, s.from_table.column) == (2, 5)
    assert (s.where.line, s.where.column) == (3, 6)                        # empieza en `b`
    assert (s.where.right.line, s.where.right.column) == (3, 10)           # el 1
    assert (s.items[0].expr.line, s.items[0].expr.column) == (1, 7)
    neg = first("SELECT 1 FROM t WHERE x = -5;").where.right
    assert (neg.line, neg.column) == (1, 26)                               # el literal negativo empieza en el '-'
    sql = "SELECT 1 FROM t WHERE a IN (SELECT b FROM u);"
    nested = first(sql).where.query
    assert (nested.line, nested.column) == (1, sql.index("SELECT b"))     # la subconsulta empieza en su propio SELECT


def check_structure_ignores_position():
    a = first("SELECT a FROM t WHERE x = 1;")
    b = first("\n\n   SELECT a   FROM t\n   WHERE x   =   1 ;")
    assert a == b and (a.line, a.column) != (b.line, b.column)


def check_refuses_broken_input():
    try:
        build_ast(parse("SELECT FROM t;"))
    except ValueError:
        return
    raise AssertionError("debía negarse a construir el AST de un texto con errores")


CASES = [
    ("precedencia de AND, OR y NOT", check_precedence),
    ("aritmética: precedencia, paréntesis y asociatividad", check_arithmetic),
    ("operadores de comparación (!= se guarda como <>)", check_comparison_operators),
    ("unarios: -5 es literal, +5 es 5, -x es operación", check_unary),
    ("literales: comillas dobles, DATE, booleanos, NULL", check_literals),
    ("EXISTS, NOT EXISTS y NOT NOT EXISTS", check_exists_and_not),
    ("IN y NOT IN con lista y con subconsulta", check_in_variants),
    ("IS NULL e IS NOT NULL", check_is_null),
    ("funciones de agregación", check_aggregates),
    ("subconsulta escalar", check_scalar_subquery),
    ("elementos del SELECT y alias", check_select_items_and_aliases),
    ("INNER JOIN en cadena", check_joins),
    ("GROUP BY, HAVING y ORDER BY", check_group_having_order),
    ("INSERT con y sin columnas, varias filas", check_insert),
    ("UPDATE y DELETE con y sin WHERE", check_update_delete),
    ("CREATE TABLE con tipos y restricciones", check_create_table),
    ("CREATE INDEX, DROP INDEX y DROP TABLE", check_index_and_drop),
    ("los nombres conservan sus mayúsculas", check_names_keep_case),
    ("script con varias sentencias y vacíos", check_script_statements),
    ("ubicación (línea y columna) de los nodos", check_positions),
    ("comparar nodos ignora la ubicación", check_structure_ignores_position),
    ("no construye el AST si hay errores", check_refuses_broken_input),
]

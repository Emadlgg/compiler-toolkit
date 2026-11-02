"""
ast.py — Árbol de sintaxis abstracta (AST) de SQL.

El árbol sintáctico del parser refleja la gramática, con todas sus capas de precedencia y la
puntuación. El AST guarda solo lo que importa para analizar y ejecutar una sentencia.

    Script
      Select
        items:      SelectExpr(ColumnRef nombre)
        from:       TableRef estudiantes
        where:      BinaryOp >=(ColumnRef edad, Literal INT 18)

Cada nodo guarda `line` y `column` (0-based, igual que los errores): donde empieza en el texto.
Esa ubicación no cuenta al comparar nodos, así que dos árboles iguales en estructura son iguales.

Decisiones del AST:
  * Los paréntesis no generan nodo: solo agrupan.
  * `!=` se guarda como `<>`.
  * `-5` y `-2.5` se guardan como literales negativos; `+x` es simplemente x.
  * `NOT EXISTS (...)` es un Exists con negated=True.
  * Los nombres se guardan tal como se escribieron; comparar sin distinguir mayúsculas
    es tarea del análisis semántico.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from sqlengine.treeview import TreeItem


class Name(str):
    """
    Un nombre (de tabla, columna, índice o alias) que recuerda dónde está escrito.
    Se comporta como un `str` normal; `line` y `column` permiten que los errores señalen
    el nombre exacto y no solo el comienzo de la sentencia.
    """

    def __new__(cls, text, line=0, column=0):
        obj = super().__new__(cls, text)
        obj.line = line
        obj.column = column
        return obj


@dataclass
class Node:
    line: int = field(default=0, kw_only=True, compare=False, repr=False)
    column: int = field(default=0, kw_only=True, compare=False, repr=False)
    # Lo llena el análisis semántico en las expresiones: INT, FLOAT, VARCHAR, BOOLEAN, DATE o NULL
    sql_type: Optional[str] = field(default=None, kw_only=True, compare=False, repr=False)

    # Cómo se muestra: un texto y los hijos, agrupados opcionalmente bajo un título ("where:", ...)
    def label(self):
        return type(self).__name__

    def parts(self):
        """Lista de (título o None, [hijos]). Un título agrupa a sus hijos bajo una línea propia."""
        return []


def _present(*pairs):
    """Descarta los grupos vacíos para que no aparezcan títulos sin nada debajo."""
    return [(title, kids) for title, kids in pairs if kids]


# ── Definición de datos ───────────────────────────────────

@dataclass
class DataType(Node):
    name: str                       # INT, FLOAT, BOOLEAN, DATE o VARCHAR
    length: Optional[int] = None    # solo VARCHAR

    def __str__(self):
        return f"{self.name}({self.length})" if self.length is not None else self.name


@dataclass
class ColumnDef(Node):
    name: str
    type: DataType
    primary_key: bool = False
    not_null: bool = False
    unique: bool = False

    def label(self):
        flags = [t for t, on in (("PRIMARY KEY", self.primary_key), ("NOT NULL", self.not_null), ("UNIQUE", self.unique)) if on]
        return " ".join(["ColumnDef", self.name, str(self.type)] + flags)


@dataclass
class CreateTable(Node):
    name: str
    columns: List[ColumnDef]

    def label(self):
        return f"CreateTable {self.name}"

    def parts(self):
        return [(None, self.columns)]


@dataclass
class DropTable(Node):
    name: str

    def label(self):
        return f"DropTable {self.name}"


@dataclass
class CreateIndex(Node):
    name: str
    table: str
    column_name: str

    def label(self):
        return f"CreateIndex {self.name} ON {self.table}({self.column_name})"


@dataclass
class DropIndex(Node):
    name: str

    def label(self):
        return f"DropIndex {self.name}"


@dataclass
class CreateDatabase(Node):
    name: str
    def label(self):
        return f"CreateDatabase {self.name}"

@dataclass
class UseDatabase(Node):
    name: str
    def label(self):
        return f"UseDatabase {self.name}"

@dataclass
class ShowDatabases(Node):
    pass

@dataclass
class ShowTables(Node):
    pass

# ── Manipulación de datos ─────────────────────────────────

@dataclass
class Row(Node):
    values: List[Node]

    def parts(self):
        return [(None, self.values)]


@dataclass
class Insert(Node):
    table: str
    columns: Optional[List[str]]    # None si no se indicaron
    rows: List[Row]
    schema: Any = field(default=None, kw_only=True, compare=False, repr=False)             # Table del catálogo
    target_indexes: Any = field(default=None, kw_only=True, compare=False, repr=False)     # posición de cada columna destino en la tabla

    def label(self):
        cols = f" ({', '.join(self.columns)})" if self.columns else ""
        return f"Insert {self.table}{cols}"

    def parts(self):
        return [(None, self.rows)]


@dataclass
class Assignment(Node):
    column_name: str
    value: Node

    def label(self):
        return f"Assign {self.column_name}"

    def parts(self):
        return [(None, [self.value])]


@dataclass
class Update(Node):
    table: str
    assignments: List[Assignment]
    where: Optional[Node] = None
    schema: Any = field(default=None, kw_only=True, compare=False, repr=False)

    def label(self):
        return f"Update {self.table}"

    def parts(self):
        return _present((None, self.assignments), ("where:", [self.where] if self.where else []))


@dataclass
class Delete(Node):
    table: str
    where: Optional[Node] = None
    schema: Any = field(default=None, kw_only=True, compare=False, repr=False)

    def label(self):
        return f"Delete {self.table}"

    def parts(self):
        return _present(("where:", [self.where] if self.where else []))


# ── Consultas ─────────────────────────────────────────────

@dataclass
class TableRef(Node):
    name: str
    alias: Optional[str] = None

    def label(self):
        return f"TableRef {self.name}" + (f" AS {self.alias}" if self.alias else "")

    @property
    def effective_name(self):
        """Con qué nombre se refiere el resto de la consulta a esta tabla."""
        return self.alias or self.name


@dataclass
class Join(Node):
    table: TableRef
    on: Node

    def label(self):
        return "Join INNER"

    def parts(self):
        return [(None, [self.table]), ("on:", [self.on])]


@dataclass
class Star(Node):
    table: Optional[str] = None     # `t.*` o `*`

    def label(self):
        return f"Star {self.table}.*" if self.table else "Star *"


@dataclass
class SelectExpr(Node):
    expr: Node
    alias: Optional[str] = None

    def label(self):
        return "SelectExpr" + (f" AS {self.alias}" if self.alias else "")

    def parts(self):
        return [(None, [self.expr])]


@dataclass
class OrderItem(Node):
    expr: Node
    descending: bool = False

    def label(self):
        return f"OrderItem {'DESC' if self.descending else 'ASC'}"

    def parts(self):
        return [(None, [self.expr])]


@dataclass
class Select(Node):
    items: List[Node]               # Star y SelectExpr
    from_table: TableRef
    joins: List[Join]
    where: Optional[Node]
    group_by: List[Node]
    having: Optional[Node]
    order_by: List[OrderItem]
    sources: Any = field(default=None, kw_only=True, compare=False, repr=False)    # tablas de FROM y JOIN, ya resueltas
    output: Any = field(default=None, kw_only=True, compare=False, repr=False)     # columnas del resultado: [(nombre, tipo)]

    def parts(self):
        return _present(
            ("items:", self.items),
            ("from:", [self.from_table]),
            ("joins:", self.joins),
            ("where:", [self.where] if self.where else []),
            ("group by:", self.group_by),
            ("having:", [self.having] if self.having else []),
            ("order by:", self.order_by),
        )


@dataclass
class Script(Node):
    statements: List[Node]

    def parts(self):
        return [(None, self.statements)]


# ── Expresiones ───────────────────────────────────────────

@dataclass
class Literal(Node):
    type: str       # INT, FLOAT, VARCHAR, BOOLEAN, DATE o NULL
    value: Any      # int, float, str, bool o None; una fecha se guarda como el texto 'YYYY-MM-DD'

    def label(self):
        if self.type == "NULL":
            return "Literal NULL"
        if self.type in ("VARCHAR", "DATE"):
            return f"Literal {self.type} '{str(self.value).replace(chr(39), chr(39) * 2)}'"     # como se escribe en SQL: ''
        if self.type == "BOOLEAN":
            return f"Literal BOOLEAN {'TRUE' if self.value else 'FALSE'}"
        return f"Literal {self.type} {self.value}"


@dataclass
class ColumnRef(Node):
    name: str
    table: Optional[str] = None
    binding: Any = field(default=None, kw_only=True, compare=False, repr=False)    # a qué columna se resolvió

    def label(self):
        return f"ColumnRef {self.table}.{self.name}" if self.table else f"ColumnRef {self.name}"


@dataclass
class UnaryOp(Node):
    op: str         # '-' o 'NOT'
    operand: Node

    def label(self):
        return f"UnaryOp {self.op}"

    def parts(self):
        return [(None, [self.operand])]


@dataclass
class BinaryOp(Node):
    op: str         # + - * /   = <> < <= > >=   AND OR
    left: Node
    right: Node

    ARITHMETIC = ("+", "-", "*", "/")
    COMPARISON = ("=", "<>", "<", "<=", ">", ">=")
    LOGICAL = ("AND", "OR")

    def label(self):
        return f"BinaryOp {self.op}"

    def parts(self):
        return [(None, [self.left, self.right])]


@dataclass
class IsNull(Node):
    expr: Node
    negated: bool = False

    def label(self):
        return "IsNotNull" if self.negated else "IsNull"

    def parts(self):
        return [(None, [self.expr])]


@dataclass
class InList(Node):
    expr: Node
    values: List[Node]
    negated: bool = False

    def label(self):
        return "NotIn" if self.negated else "In"

    def parts(self):
        return [(None, [self.expr]), ("values:", self.values)]


@dataclass
class InSubquery(Node):
    expr: Node
    query: "Select"
    negated: bool = False

    def label(self):
        return "NotInSubquery" if self.negated else "InSubquery"

    def parts(self):
        return [(None, [self.expr]), ("query:", [self.query])]


@dataclass
class Exists(Node):
    query: "Select"
    negated: bool = False

    def label(self):
        return "NotExists" if self.negated else "Exists"

    def parts(self):
        return [(None, [self.query])]


@dataclass
class Subquery(Node):
    """Subconsulta escalar usada como valor: `edad > (SELECT AVG(edad) FROM t)`."""
    query: "Select"

    def parts(self):
        return [(None, [self.query])]


@dataclass
class Aggregate(Node):
    func: str                       # COUNT, SUM, AVG, MIN o MAX
    arg: Optional[Node] = None      # None significa COUNT(*)

    def label(self):
        return f"Aggregate {self.func}(*)" if self.arg is None else f"Aggregate {self.func}"

    def parts(self):
        return [(None, [self.arg])] if self.arg is not None else []


# ── Vista ─────────────────────────────────────────────────

def to_tree(node, positions=False):
    """El AST como TreeItem, para mostrarlo como texto o dibujarlo."""

    def text(n):
        return n.label() + (f"  [{n.line}:{n.column}]" if positions else "")

    def build(n):
        children = []
        for title, kids in n.parts():
            built = [build(k) for k in kids]
            if title is None:
                children.extend(built)
            else:
                children.append(TreeItem(title, "role", built))
        return TreeItem(text(n), "node" if children else "leaf", children)

    return build(node)

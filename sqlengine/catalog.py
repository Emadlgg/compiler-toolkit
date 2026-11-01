"""
catalog.py — El esquema de la base de datos: tablas, columnas e índices.

El catálogo es lo que consulta el análisis semántico. Vive en el archivo `metadata.txt` de la
carpeta de la base de datos (ver metadata.py). Los nombres no distinguen mayúsculas, pero se
guardan como se escribieron.
"""

import copy
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlengine import ast
from sqlengine import types as T


@dataclass
class Column:
    name: str
    type: str                       # INT, FLOAT, VARCHAR, BOOLEAN o DATE
    length: Optional[int] = None    # solo VARCHAR
    primary_key: bool = False
    not_null: bool = False
    unique: bool = False

    @property
    def nullable(self):
        return not (self.not_null or self.primary_key)

    @property
    def must_be_unique(self):
        return self.unique or self.primary_key

    @property
    def type_text(self):
        return T.describe(self.type, self.length)


@dataclass
class Index:
    name: str
    table: str
    column: str


@dataclass
class Table:
    name: str
    columns: List[Column]
    indexes: List[Index] = field(default_factory=list)

    def find_column(self, name) -> Optional[Tuple[int, Column]]:
        """(posición, columna) o None. No distingue mayúsculas."""
        wanted = name.lower()
        for i, column in enumerate(self.columns):
            if column.name.lower() == wanted:
                return i, column
        return None

    @property
    def column_names(self):
        return [c.name for c in self.columns]


class Catalog:
    def __init__(self):
        self._tables = {}           # nombre en minúsculas -> Table, en orden de creación

    # ── consultas ─────────────────────────────────────────

    @property
    def tables(self):
        return list(self._tables.values())

    def has_table(self, name):
        return name.lower() in self._tables

    def table(self, name) -> Optional[Table]:
        return self._tables.get(name.lower())

    def find_index(self, name) -> Optional[Index]:
        """Los nombres de índice son únicos en toda la base de datos."""
        wanted = name.lower()
        for table in self._tables.values():
            for index in table.indexes:
                if index.name.lower() == wanted:
                    return index
        return None

    def index_on(self, table_name, column_name) -> Optional[Index]:
        table = self.table(table_name)
        if table is None:
            return None
        for index in table.indexes:
            if index.column.lower() == column_name.lower():
                return index
        return None

    # ── cambios ───────────────────────────────────────────

    def add_table(self, table):
        self._tables[table.name.lower()] = table

    def drop_table(self, name):
        self._tables.pop(name.lower(), None)        # sus índices se van con ella

    def add_index(self, index):
        self._tables[index.table.lower()].indexes.append(index)

    def drop_index(self, name):
        wanted = name.lower()
        for table in self._tables.values():
            table.indexes = [i for i in table.indexes if i.name.lower() != wanted]

    def copy(self):
        return copy.deepcopy(self)

    def __eq__(self, other):
        return isinstance(other, Catalog) and self.tables == other.tables


def table_from_create(stmt):
    """La tabla que define un CREATE TABLE ya analizado."""
    columns = [
        Column(str(c.name), c.type.name, c.type.length, c.primary_key, c.not_null, c.unique)
        for c in stmt.columns
    ]
    return Table(str(stmt.name), columns)


def apply_ddl(catalog, stmt):
    """Aplica al catálogo el efecto de una sentencia de definición (las demás no lo cambian)."""
    if isinstance(stmt, ast.CreateTable):
        catalog.add_table(table_from_create(stmt))
    elif isinstance(stmt, ast.DropTable):
        catalog.drop_table(stmt.name)
    elif isinstance(stmt, ast.CreateIndex):
        catalog.add_index(Index(str(stmt.name), str(stmt.table), str(stmt.column_name)))
    elif isinstance(stmt, ast.DropIndex):
        catalog.drop_index(stmt.name)

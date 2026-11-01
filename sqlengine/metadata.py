"""
metadata.py — Lee y escribe el esquema en `metadata.txt`.

Formato (texto legible, se puede editar a mano):

    table estudiantes
      column id INT PRIMARY KEY
      column nombre VARCHAR(50) NOT NULL
      column edad INT
      index idx_estudiantes_edad edad

    table cursos
      column id INT
      ...

  * `table NOMBRE` abre una tabla; sus columnas e índices van debajo, con sangría.
  * `column NOMBRE TIPO [PRIMARY KEY] [NOT NULL] [UNIQUE]`
  * `index NOMBRE COLUMNA`: un índice sobre una columna de la tabla. Los nombres de índice son únicos.
  * Las líneas en blanco y las que empiezan con # se ignoran.
"""

import os
import re

from sqlengine.catalog import Catalog, Column, Index, Table
from sqlengine import types as T

FILE_NAME = "metadata.txt"
_NAME = re.compile(r"^[^\W\d]\w*$")
_TYPE = re.compile(r"^(INT|FLOAT|BOOLEAN|DATE|VARCHAR\((\d+)\))$", re.IGNORECASE)
HEADER = "# metadata.txt: esquema de la base de datos (lo escribe el intérprete; también se puede editar a mano)"


class MetadataError(Exception):
    def __init__(self, message, line=None):
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self):
        return f"[Línea {self.line}] {self.message}" if self.line else self.message


def parse_metadata(text):
    """Convierte el texto de metadata.txt en un Catalog. Lanza MetadataError con la línea del problema."""
    catalog = Catalog()
    table = None
    table_line = None
    seen_indexes = set()

    def close_table():
        if table is not None:
            if not table.columns:
                raise MetadataError(f"La tabla '{table.name}' no tiene columnas", table_line)
            catalog.add_table(table)

    for number, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        words = line.split()
        indented = line[0] in " \t"
        keyword = words[0].lower()

        if not indented:
            if keyword != "table" or len(words) != 2:
                raise MetadataError(f"Se esperaba 'table NOMBRE' y se encontró: {line.strip()}", number)
            name = words[1]
            if not _NAME.match(name):
                raise MetadataError(f"Nombre de tabla no válido: '{name}'", number)
            close_table()
            if catalog.has_table(name):
                raise MetadataError(f"La tabla '{name}' está repetida", number)
            table, table_line = Table(name, []), number
            continue

        if table is None:
            raise MetadataError("Hay una columna o un índice antes de la primera 'table'", number)

        if keyword == "column":
            table.columns.append(_parse_column(words[1:], table, number))
        elif keyword == "index":
            if len(words) != 3:
                raise MetadataError("Se esperaba 'index NOMBRE COLUMNA'", number)
            name, column = words[1], words[2]
            if not _NAME.match(name):
                raise MetadataError(f"Nombre de índice no válido: '{name}'", number)
            if name.lower() in seen_indexes:
                raise MetadataError(f"El índice '{name}' está repetido", number)
            if table.find_column(column) is None:
                raise MetadataError(f"El índice '{name}' usa la columna '{column}', que no existe en '{table.name}'", number)
            seen_indexes.add(name.lower())
            table.indexes.append(Index(name, table.name, table.columns[table.find_column(column)[0]].name))
        else:
            raise MetadataError(f"Se esperaba 'column' o 'index' y se encontró '{words[0]}'", number)

    close_table()
    return catalog


def _parse_column(words, table, number):
    if len(words) < 2:
        raise MetadataError("Se esperaba 'column NOMBRE TIPO'", number)
    name, type_text = words[0], words[1]
    if not _NAME.match(name):
        raise MetadataError(f"Nombre de columna no válido: '{name}'", number)
    if table.find_column(name):
        raise MetadataError(f"La columna '{name}' está repetida en la tabla '{table.name}'", number)
    m = _TYPE.match(type_text)
    if m is None:
        raise MetadataError(f"Tipo no válido: '{type_text}' (INT, FLOAT, VARCHAR(n), BOOLEAN o DATE)", number)
    length = int(m.group(2)) if m.group(2) else None
    if length is not None and length < 1:
        raise MetadataError("VARCHAR necesita un largo mayor que cero", number)
    column = Column(name, type_text.split("(")[0].upper(), length)

    rest = " ".join(w.upper() for w in words[2:])
    for phrase, attribute in (("PRIMARY KEY", "primary_key"), ("NOT NULL", "not_null"), ("UNIQUE", "unique")):
        if phrase in rest:
            setattr(column, attribute, True)
            rest = rest.replace(phrase, "", 1)
    if rest.strip():
        raise MetadataError(f"Restricción no reconocida: '{rest.strip()}' (PRIMARY KEY, NOT NULL o UNIQUE)", number)
    if column.primary_key and any(c.primary_key for c in table.columns):
        raise MetadataError(f"La tabla '{table.name}' tiene más de una columna PRIMARY KEY", number)
    return column


def format_metadata(catalog):
    """El texto de metadata.txt para un catálogo (parse_metadata(format_metadata(c)) == c)."""
    out = [HEADER]
    for table in catalog.tables:
        out.append("")
        out.append(f"table {table.name}")
        for c in table.columns:
            flags = [t for t, on in (("PRIMARY KEY", c.primary_key), ("NOT NULL", c.not_null), ("UNIQUE", c.unique)) if on]
            out.append("  " + " ".join(["column", c.name, c.type_text] + flags))
        for index in table.indexes:
            out.append(f"  index {index.name} {index.column}")
    return "\n".join(out) + "\n"


def load_catalog(directory):
    """El catálogo de una carpeta de base de datos; vacío si todavía no tiene metadata.txt."""
    path = os.path.join(directory, FILE_NAME)
    if not os.path.exists(path):
        return Catalog()
    with open(path, encoding="utf-8") as f:
        return parse_metadata(f.read())


def save_catalog(catalog, directory):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, FILE_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(format_metadata(catalog))

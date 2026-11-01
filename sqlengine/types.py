"""
types.py — Tipos de SQL y sus reglas: promoción numérica, comparabilidad y fechas.

Los tipos de las expresiones son nombres simples (INT, FLOAT, VARCHAR, BOOLEAN, DATE). Dos más
sirven al análisis: NULL (el tipo del literal NULL, compatible con todo) y UNKNOWN (una expresión
que ya tuvo un error: se usa para no repetir errores en cascada).
"""

import datetime
import re

INT, FLOAT, VARCHAR, BOOLEAN, DATE = "INT", "FLOAT", "VARCHAR", "BOOLEAN", "DATE"
NULL, UNKNOWN = "NULL", "UNKNOWN"

NUMERIC = (INT, FLOAT)
DATA_TYPES = (INT, FLOAT, VARCHAR, BOOLEAN, DATE)     # los que puede tener una columna


def is_numeric(t):
    return t in NUMERIC


def promote(a, b):
    """El tipo de una operación aritmética: FLOAT si alguno lo es, si no INT."""
    return FLOAT if FLOAT in (a, b) else INT


def comparable(a, b, op="="):
    """¿Se pueden comparar un valor de tipo `a` con otro de tipo `b` usando `op`?"""
    if UNKNOWN in (a, b) or NULL in (a, b):
        return True
    if is_numeric(a) and is_numeric(b):
        return True
    if a == b:
        return op in ("=", "<>") if a == BOOLEAN else True      # un booleano solo se compara por igualdad
    return False


def assignable(target, source):
    """¿Se puede guardar un valor de tipo `source` en una columna de tipo `target`?"""
    if source in (UNKNOWN, NULL):
        return True
    if target == FLOAT:
        return source in NUMERIC                 # un entero se convierte a decimal
    return target == source                      # un decimal no se guarda en una columna INT


_DATE_FORMAT = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def parse_date(text):
    """Una fecha AAAA-MM-DD válida, o None. Se rechazan formatos que date.fromisoformat sí acepta."""
    m = _DATE_FORMAT.match(text)
    if m is None:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:                           # por ejemplo 2024-02-30
        return None


def describe(type_name, length=None):
    """El tipo como se escribe en SQL: VARCHAR(50), INT..."""
    return f"{type_name}({length})" if length is not None else type_name

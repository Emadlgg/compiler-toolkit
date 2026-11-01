"""errors.py — Errores del intérprete SQL, con tipo y ubicación."""

LEXICAL = "léxico"
SYNTAX = "sintáctico"
SEMANTIC = "semántico"


class SqlError:
    """Un error con su fase (léxico, sintáctico o semántico) y su ubicación."""

    def __init__(self, kind, message, line=None, column=None):
        self.kind = kind
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        where = f"[Línea {self.line}:{self.column}] " if self.line else ""
        return f"{where}Error {self.kind}: {self.message}"

    def __repr__(self):
        return f"SqlError({self.kind!r}, {self.message!r}, {self.line}, {self.column})"

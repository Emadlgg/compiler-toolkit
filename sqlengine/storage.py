"""Persistencia CSV de fase 1; sin DBMS externo."""
import csv
import os
from sqlengine.metadata import load_catalog, save_catalog
from sqlengine.catalog import table_from_create
from sqlengine import types as T

class StorageError(ValueError):
    pass

class FileStorage:
    def __init__(self, directory):
        self.directory = os.path.abspath(directory)
        self.catalog = load_catalog(self.directory)

    def _path(self, name):
        return os.path.join(self.directory, name + '.csv')

    def create_table(self, stmt):
        if self.catalog.has_table(stmt.name):
            raise StorageError(f"La tabla '{stmt.name}' ya existe")
        table = table_from_create(stmt)
        os.makedirs(self.directory, exist_ok=True)
        path = self._path(table.name)
        if os.path.exists(path):
            raise StorageError(f"Ya existe el archivo {path}")
        with open(path, 'x', encoding='utf-8', newline='') as f:
            csv.writer(f).writerow(table.column_names)
        self.catalog.add_table(table)
        try:
            save_catalog(self.catalog, self.directory)
        except Exception:
            self.catalog.drop_table(table.name)
            os.remove(path)
            raise

    def drop_table(self, name):
        table = self.catalog.table(name)
        if table is None:
            raise StorageError(f"La tabla '{name}' no existe")
        path = self._path(table.name)
        if not os.path.isfile(path):
            raise StorageError(f"Falta el archivo de la tabla '{name}'")
        # Guardar el catálogo antes de borrar los datos; revertir ante un fallo.
        old = self.catalog.copy()
        self.catalog.drop_table(name)
        try:
            save_catalog(self.catalog, self.directory)
            os.remove(path)
        except Exception:
            self.catalog = old
            save_catalog(old, self.directory)
            raise

    def rows(self, name):
        table = self.catalog.table(name)
        if table is None:
            raise StorageError(f"La tabla '{name}' no existe")
        try:
            with open(self._path(table.name), encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
                if header != table.column_names:
                    raise StorageError(f"Cabecera CSV incompatible en '{table.name}'")
                rows = list(reader)
        except (OSError, StopIteration) as e:
            raise StorageError(f"No se pudo leer '{table.name}': {e}") from e
        if any(len(row) != len(table.columns) for row in rows):
            raise StorageError(f"CSV dañado en '{table.name}'")
        return rows

    def insert(self, stmt):
        from sqlengine.evaluator import encode
        table = self.catalog.table(stmt.table)
        if table is None:
            raise StorageError(f"La tabla '{stmt.table}' no existe")
        existing = self.rows(table.name)
        targets = ([table.find_column(n)[0] for n in stmt.columns] if stmt.columns else list(range(len(table.columns))))
        pending = []
        for row in stmt.rows:
            if len(row.values) != len(targets):
                raise StorageError('Cantidad incorrecta de valores INSERT')
            values = [None] * len(table.columns)
            for pos, expr in zip(targets, row.values):
                values[pos] = encode(self._literal(expr, table.columns[pos]), table.columns[pos])
            for pos, col in enumerate(table.columns):
                if values[pos] is None and not col.nullable:
                    raise StorageError(f"La columna '{col.name}' no admite NULL")
            pending.append(values)
        for pos, col in enumerate(table.columns):
            if col.must_be_unique:
                seen = {r[pos] for r in existing if r[pos] != ''}
                for row in pending:
                    val = row[pos]
                    if val != '':
                        if val in seen:
                            raise StorageError(f"Valor duplicado para '{col.name}': {val}")
                        seen.add(val)
        # Validar todas las filas antes de escribir alguna.
        with open(self._path(table.name), 'a', encoding='utf-8', newline='') as f:
            csv.writer(f).writerows([['' if v is None else v for v in row] for row in pending])
        return len(pending)

    @staticmethod
    def _literal(expr, col):
        from sqlengine.ast import Literal
        if not isinstance(expr, Literal):
            raise StorageError('Fase 1: INSERT admite únicamente valores literales')
        val = expr.value
        if val is None:
            return None
        if not T.assignable(col.type, expr.type):
            raise StorageError(f"Tipo incompatible en '{col.name}': {expr.type} para {col.type}")
        if col.type == 'VARCHAR':
            if len(val) > col.length:
                raise StorageError(f"'{col.name}' supera VARCHAR({col.length})")
            return val
        if col.type == 'DATE':
            if T.parse_date(str(val)) is None:
                raise StorageError(f"Fecha inválida en '{col.name}'")
            return val
        if col.type == 'BOOLEAN':
            return val
        if col.type == 'FLOAT':
            return float(val)
        return val

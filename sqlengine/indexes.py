"""Indices persistentes JSON: valor de columna -> posiciones de fila CSV."""
import json
import os
import tempfile
from sqlengine.catalog import Index
from sqlengine.metadata import save_catalog
from sqlengine.storage import StorageError

class IndexManager:
    def __init__(self, storage):
        self.storage = storage
        self.folder = os.path.join(storage.directory, 'indexes')

    def _path(self, name):
        return os.path.join(self.folder, name.lower() + '.json')

    def rebuild(self, index):
        table = self.storage.catalog.table(index.table)
        found = table.find_column(index.column)
        if found is None:
            raise StorageError(f'Columna indexada inexistente: {index.column}')
        position = found[0]
        mapping = {}
        for row_id, record in enumerate(self.storage.rows(table.name)):
            mapping.setdefault(record[position], []).append(row_id)
        os.makedirs(self.folder, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=self.folder, prefix='.idx_', suffix='.json')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump({'table': table.name, 'column': index.column, 'values': mapping}, stream, ensure_ascii=False)
            os.replace(temp, self._path(index.name))
        finally:
            if os.path.exists(temp):
                os.remove(temp)

    def refresh_table(self, table_name):
        table = self.storage.catalog.table(table_name)
        if table:
            for index in table.indexes:
                self.rebuild(index)

    def create(self, stmt):
        catalog = self.storage.catalog
        if catalog.find_index(stmt.name):
            raise StorageError(f'Indice duplicado: {stmt.name}')
        table = catalog.table(stmt.table)
        if table is None or table.find_column(stmt.column_name) is None:
            raise StorageError(f'Tabla o columna inexistente: {stmt.table}.{stmt.column_name}')
        if catalog.index_on(table.name, stmt.column_name):
            raise StorageError(f'Ya existe un indice para {table.name}.{stmt.column_name}')
        index = Index(str(stmt.name), table.name, str(stmt.column_name))
        catalog.add_index(index)
        try:
            self.rebuild(index)
            save_catalog(catalog, self.storage.directory)
        except Exception:
            catalog.drop_index(index.name)
            if os.path.exists(self._path(index.name)):
                os.remove(self._path(index.name))
            raise

    def drop(self, name):
        catalog = self.storage.catalog
        if catalog.find_index(name) is None:
            raise StorageError(f'Indice inexistente: {name}')
        catalog.drop_index(name)
        save_catalog(catalog, self.storage.directory)
        if os.path.exists(self._path(name)):
            os.remove(self._path(name))

    def lookup(self, table_name, column_name, value):
        index = self.storage.catalog.index_on(table_name, column_name)
        if index is None:
            return None
        table = self.storage.catalog.table(table_name)
        column = table.find_column(column_name)[1]
        from sqlengine.evaluator import encode
        key = encode(value, column)
        path = self._path(index.name)
        if not os.path.exists(path):
            self.rebuild(index)
        try:
            with open(path, encoding='utf-8') as stream:
                data = json.load(stream)
            if data['table'].lower() != table.name.lower() or data['column'].lower() != column.name.lower():
                raise StorageError(f'Indice inconsistente: {index.name}')
            return data['values'].get(key, [])
        except (ValueError, KeyError, OSError) as error:
            raise StorageError(f'Indice dañado: {index.name}: {error}') from error

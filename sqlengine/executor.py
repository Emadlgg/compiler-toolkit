"""Punto de entrada: análisis, validación y ejecución SQL sobre archivos."""
from sqlengine import ast
from sqlengine.frontend import parse
from sqlengine.ast_builder import build_ast
from sqlengine.semantic import analyze_script
from sqlengine.storage import FileStorage, StorageError
from sqlengine.query_engine import QueryEngine
from sqlengine.indexes import IndexManager


def execute(sql, directory):
    parsed = parse(sql)
    if not parsed.ok:
        raise StorageError('\n'.join(map(str, parsed.errors)))
    script = build_ast(parsed)
    store = FileStorage(directory)
    supported = (ast.CreateTable, ast.DropTable, ast.CreateIndex, ast.DropIndex,
                 ast.Insert, ast.Select, ast.Update, ast.Delete)
    if any(not isinstance(stmt, supported) for stmt in script.statements):
        raise StorageError('Sentencia no soportada por el ejecutor')
    checked = analyze_script(script, store.catalog)
    if checked.errors:
        raise StorageError('\n'.join(map(str, checked.errors)))
    engine = QueryEngine(store)
    indexes = IndexManager(store)
    outputs = []
    for stmt in script.statements:
        if isinstance(stmt, ast.CreateTable):
            store.create_table(stmt)
            outputs.append(f'Tabla creada: {stmt.name}')
        elif isinstance(stmt, ast.DropTable):
            table = store.catalog.table(stmt.name)
            names = [index.name for index in table.indexes]
            store.drop_table(stmt.name)
            import os
            for name in names:
                path = indexes._path(name)
                if os.path.exists(path):
                    os.remove(path)
            outputs.append(f'Tabla eliminada: {stmt.name}')
        elif isinstance(stmt, ast.CreateIndex):
            indexes.create(stmt)
            outputs.append(f'Indice creado: {stmt.name}')
        elif isinstance(stmt, ast.DropIndex):
            indexes.drop(stmt.name)
            outputs.append(f'Indice eliminado: {stmt.name}')
        elif isinstance(stmt, ast.Insert):
            count = store.insert(stmt)
            indexes.refresh_table(stmt.table)
            outputs.append(f'{count} fila(s) insertada(s) en {stmt.table}')
        elif isinstance(stmt, ast.Select):
            outputs.append(engine.select(stmt))
        elif isinstance(stmt, ast.Update):
            count = engine.update(stmt)
            indexes.refresh_table(stmt.table)
            outputs.append(f'{count} fila(s) actualizada(s) en {stmt.table}')
        elif isinstance(stmt, ast.Delete):
            count = engine.delete(stmt)
            indexes.refresh_table(stmt.table)
            outputs.append(f'{count} fila(s) eliminada(s) de {stmt.table}')
    return outputs

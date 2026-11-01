"""Ejecutor de CREATE TABLE, DROP TABLE e INSERT (fase 1)."""
from sqlengine import ast
from sqlengine.frontend import parse
from sqlengine.ast_builder import build_ast
from sqlengine.semantic import analyze_script
from sqlengine.storage import FileStorage, StorageError


def execute(sql, directory):
    parsed = parse(sql)
    if not parsed.ok:
        raise StorageError('\n'.join(map(str, parsed.errors)))
    script = build_ast(parsed)
    store = FileStorage(directory)
    # Validación semántica completa ANTES de ejecutar el script.
    checked = analyze_script(script, store.catalog)
    if checked.errors:
        raise StorageError('\n'.join(map(str, checked.errors)))
    supported = (ast.CreateTable, ast.DropTable, ast.Insert)
    if any(not isinstance(s, supported) for s in script.statements):
        raise StorageError('Fase 1 solo ejecuta CREATE TABLE, DROP TABLE e INSERT')
    messages = []
    for stmt in script.statements:
        if isinstance(stmt, ast.CreateTable):
            store.create_table(stmt)
            messages.append(f'Tabla creada: {stmt.name}')
        elif isinstance(stmt, ast.DropTable):
            store.drop_table(stmt.name)
            messages.append(f'Tabla eliminada: {stmt.name}')
        elif isinstance(stmt, ast.Insert):
            count = store.insert(stmt)
            messages.append(f'{count} fila(s) insertada(s) en {stmt.table}')
    return messages

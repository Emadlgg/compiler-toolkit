"""Punto de entrada: análisis, validación y ejecución SQL sobre archivos."""
from sqlengine import ast
from sqlengine.frontend import parse
from sqlengine.ast_builder import build_ast
from sqlengine.semantic import analyze_script
from sqlengine.storage import FileStorage, StorageError
from sqlengine.query_engine import QueryEngine
from sqlengine.indexes import IndexManager


def _execute_sql_batch(sql, directory):
    parsed = parse(sql)
    if not parsed.ok:
        raise StorageError('\n'.join(map(str, parsed.errors)))
    return _execute_sql_batch_ast(build_ast(parsed), directory)


def execute_with_context(sql, directory):
    """Procesa todos los comandos con el lexer, parser y AST de ANTLR."""
    from sqlengine.database_commands import workspace, perform
    parsed = parse(sql)
    if not parsed.ok:
        raise StorageError('\n'.join(map(str, parsed.errors)))
    script = build_ast(parsed)
    root, current = workspace(directory)
    outputs, pending = [], []
    database_nodes = (ast.CreateDatabase, ast.UseDatabase, ast.ShowDatabases, ast.ShowTables)

    def flush():
        if pending:
            outputs.extend(_execute_sql_batch_ast(ast.Script(list(pending)), str(current)))
            pending.clear()

    for stmt in script.statements:
        if isinstance(stmt, database_nodes):
            flush()
            if isinstance(stmt, ast.CreateDatabase):
                command, argument = 'CREATE DATABASE', str(stmt.name)
            elif isinstance(stmt, ast.UseDatabase):
                command, argument = 'USE', str(stmt.name)
            elif isinstance(stmt, ast.ShowDatabases):
                command, argument = 'SHOW DATABASES', ''
            else:
                command, argument = 'SHOW TABLES', ''
            output, current = perform(command, argument, root, current)
            outputs.append(output)
        else:
            pending.append(stmt)
    flush()
    return outputs, str(current)


def _execute_sql_batch_ast(script, directory):
    """Ejecuta nodos AST ya analizados sin volver a procesar el texto."""
    store = FileStorage(directory)
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


def execute(sql, directory):
    """API compatible con ejecutar_sql.py y las pruebas existentes."""
    outputs, _ = execute_with_context(sql, directory)
    return outputs

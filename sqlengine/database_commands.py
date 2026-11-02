"""Administracion de bases de datos por directorios (sin DBMS externo)."""
import os
import re
from pathlib import Path
from sqlengine.storage import StorageError
from sqlengine.metadata import load_catalog

NAME = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')
COMMAND = re.compile(r'\s*(CREATE\s+DATABASE|USE|SHOW\s+DATABASES|SHOW\s+TABLES)\b(.*?)\s*\Z', re.I | re.S)
MARKER = '.compilerlab_db'


def split_statements(source):
    """Divide por ; sin romper cadenas SQL ni comentarios."""
    result, start, i, state = [], 0, 0, 'normal'
    while i < len(source):
        c = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ''
        if state == 'normal':
            if c == "'": state = 'string'
            elif c == '-' and nxt == '-': state = 'line'; i += 1
            elif c == '/' and nxt == '*': state = 'block'; i += 1
            elif c == ';':
                result.append(source[start:i]); start = i + 1
        elif state == 'string':
            if c == "'" and nxt == "'": i += 1
            elif c == "'": state = 'normal'
        elif state == 'line':
            if c in '\r\n': state = 'normal'
        elif state == 'block':
            if c == '*' and nxt == '/': state = 'normal'; i += 1
        i += 1
    if state in ('string', 'block'):
        raise StorageError('Cadena o comentario SQL sin cerrar')
    result.append(source[start:])
    return [s for s in result if strip_comments(s).strip()]


def strip_comments(source):
    return re.sub(r'/\*.*?\*/|--[^\r\n]*', ' ', source, flags=re.S)


def database_command(statement):
    clean = strip_comments(statement).strip()
    match = COMMAND.fullmatch(clean)
    if not match:
        return None
    command = ' '.join(match.group(1).upper().split())
    arg = match.group(2).strip()
    if command in ('SHOW DATABASES', 'SHOW TABLES'):
        if arg:
            raise StorageError(f'{command} no recibe argumentos')
    elif not NAME.fullmatch(arg):
        raise StorageError(f'Nombre de base de datos no valido: {arg!r}')
    return command, arg


def workspace(directory):
    """Si se selecciono una base creada con USE, conservar su carpeta padre."""
    current = Path(directory).resolve()
    if (current / MARKER).is_file():
        return current.parent, current
    return current, current


def perform(command, argument, root, current):
    root = Path(root).resolve()
    current = Path(current).resolve()
    if command == 'CREATE DATABASE':
        root.mkdir(parents=True, exist_ok=True)
        target = root / argument
        if target.exists():
            raise StorageError(f"La base de datos '{argument}' ya existe")
        target.mkdir()
        (target / MARKER).write_text('Compiler Lab database\n', encoding='utf-8')
        return f'Base de datos creada: {argument}', current
    if command == 'USE':
        target = root / argument
        if not target.is_dir() or not ((target / MARKER).is_file() or (target / 'metadata.txt').is_file()):
            raise StorageError(f"La base de datos '{argument}' no existe en {root}")
        return f'Base de datos seleccionada: {argument}', target
    if command == 'SHOW DATABASES':
        names = sorted(p.name for p in root.iterdir() if p.is_dir() and
                       ((p / MARKER).is_file() or (p / 'metadata.txt').is_file())) if root.is_dir() else []
        return (['database'], [[n] for n in names]), current
    if command == 'SHOW TABLES':
        names = [table.name for table in load_catalog(str(current)).tables]
        return (['table'], [[n] for n in names]), current
    raise StorageError(f'Comando desconocido: {command}')

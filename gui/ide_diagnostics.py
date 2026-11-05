"""Small, GUI-independent helpers for Compiscript diagnostics."""
from pathlib import Path


def source_matches_path(editor_source, path):
    """Whether editor content is the source currently stored at path."""
    try:
        return Path(path).resolve().read_text(encoding='utf-8').rstrip('\n') == editor_source.rstrip('\n')
    except (OSError, ValueError):
        return False


def format_problem_detail(phase, line, column, message, path=None):
    """Readable, copyable diagnostic with its full message and location."""
    parts = [str(phase)]
    if path:
        parts.append('Archivo: ' + str(path))
    if line is not None and str(line) not in ('', '—'):
        parts.append(f'Línea: {line}    Columna: {column}')
    parts.extend(('', str(message)))
    return '\n'.join(parts)

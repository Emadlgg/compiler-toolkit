"""Fuente Compiscript del editor, con resolución de módulos relativa al archivo."""
from pathlib import Path
from compiscript.modules import resolve_project


def save_and_resolve(path, text):
    """Guarda la edición actual y devuelve la fuente unificada para ANTLR.

    El archivo principal debe existir en disco para resolver imports relativos.
    Los errores de módulos se propagan al llamador para mostrarlos en el IDE.
    """
    path = Path(path).resolve()
    if path.suffix.lower() != '.cps':
        raise ValueError('El archivo principal debe tener extensión .cps')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip('\n') + '\n', encoding='utf-8')
    return resolve_project(path)

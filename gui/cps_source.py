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


def save_and_resolve_with_map(path, text):
    """Like save_and_resolve, also return original source locations."""
    from compiscript.modules.resolver import resolve_project_with_map
    path = Path(path).resolve()
    if path.suffix.lower() != '.cps':
        raise ValueError('El archivo principal debe tener extensión .cps')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip('\n') + '\n', encoding='utf-8')
    return resolve_project_with_map(path)


def make_analyzer(path):
    """SemanticAnalyzer listo para el archivo `path`, con las clases/funciones de
    las bibliotecas .cplobj que importa (igual que hace el CLI).

    Devuelve (analyzer, error). Si hay un problema con las bibliotecas, error trae
    el mensaje para mostrarlo en el IDE.
    """
    from compiscript.semantic import SemanticAnalyzer
    from compiscript.modules.compiled_import_plan import build_import_plan
    from compiscript.modules.compiled_imports import CompiledImportError
    from compiscript.modules.semantic_bridge import install_plan_symbols
    analyzer = SemanticAnalyzer()
    try:
        plan = build_import_plan(Path(path).resolve())
        entry = Path(path).resolve()
        install_plan_symbols(analyzer, plan, entry)
    except (CompiledImportError, OSError, ValueError) as exc:
        return None, f'Error de bibliotecas compiladas: {exc}'
    return analyzer, None


def library_output_path(path):
    """Ruta por omisión del .cplobj: <carpeta>/build/<NombreArchivo>.cplobj"""
    path = Path(path).resolve()
    return path.parent / 'build' / (path.stem + '.cplobj')

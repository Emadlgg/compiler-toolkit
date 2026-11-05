"""Safe, UI-independent discovery of Compiscript project files."""
from pathlib import Path


def list_project_files(root, max_files=500):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f'Carpeta inexistente: {root}')
    found = []
    for path in root.rglob('*.cps'):
        if any(part in {'.git', '__pycache__', 'build', '.venv', 'venv'} for part in path.relative_to(root).parts):
            continue
        if not path.is_file():
            continue
        found.append(path)
        if len(found) > max_files:
            raise ValueError(f'El proyecto supera el límite de {max_files} archivos .cps')
    return sorted(found, key=lambda p: str(p.relative_to(root)).lower())

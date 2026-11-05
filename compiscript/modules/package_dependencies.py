"""Verified, deterministic dependency graph for compiled .cplobj packages.

Dependencies are relative package paths with SHA-256 pins. This is a link-time
facility; it does not yet compile a source module that imports external classes.
"""
import hashlib
import json
from pathlib import Path
import zipfile

from .compiled_imports import CompiledImportError, load_compiled_dependency


def dependency_entries(package):
    package = Path(package)
    try:
        with zipfile.ZipFile(package) as archive:
            manifest = json.loads(archive.read('manifest.json'))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        raise CompiledImportError(f'Manifiesto invalido: {package}: {exc}') from exc
    entries = manifest.get('dependencies', [])
    if not isinstance(entries, list):
        raise CompiledImportError('Lista de dependencias invalida')
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'path', 'sha256'}:
            raise CompiledImportError('Entrada de dependencia invalida')
        name, digest = entry['path'], entry['sha256']
        if (not isinstance(name, str) or not name or '\\' in name or '\x00' in name
                or Path(name).is_absolute() or not name.endswith('.cplobj')
                or any(part in ('..', '.') for part in name.split('/'))):
            raise CompiledImportError(f'Ruta de dependencia insegura: {name}')
        if (name in seen or not isinstance(digest, str) or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise CompiledImportError(f'Dependencia duplicada o hash invalido: {name}')
        seen.add(name)
    return entries


def resolve_package_graph(roots):
    """Return verified dependencies first, roots last, each package once."""
    resolved, active, result = set(), [], []

    def visit(path):
        path = Path(path).resolve()
        if path in active:
            raise CompiledImportError('Dependencia circular: ' + ' -> '.join(p.name for p in active + [path]))
        if path in resolved:
            return
        active.append(path)
        dep = load_compiled_dependency(path)
        for entry in dependency_entries(path):
            target = (path.parent / entry['path']).resolve()
            if not target.is_file():
                raise CompiledImportError(f'Dependencia inexistente: {target}')
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if digest != entry['sha256']:
                raise CompiledImportError(f'Integridad de dependencia incorrecta: {target}')
            visit(target)
        active.pop()
        resolved.add(path)
        result.append(dep)

    for root in roots:
        visit(root)
    return result

"""Plan verified compiled-library imports without compiling interface bodies.

This stage deliberately does not inject interface.cps into the TAC generator:
those bodies are declarations, not executable implementations.
"""
from dataclasses import dataclass
from pathlib import Path
import re

from .compiled_imports import CompiledImportError, load_compiled_dependency
from .resolver import IMPORT, IMPORT_ITEM, _strip_comments_preserve_strings, _global_declarations


@dataclass(frozen=True)
class ImportedSymbol:
    local_name: str
    exported_name: str
    library: Path
    abi: dict


@dataclass
class CompiledImportPlan:
    entry: Path
    libraries: list
    symbols: dict

    def extract_objects(self, directory):
        """Write verified MIPS objects for the later linker stage."""
        from .compiled_package import extract_object
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        outputs = []
        for index, dep in enumerate(self.libraries):
            output = directory / f'compiled_{index}.mobj'
            extract_object(dep.path, output)
            outputs.append(output)
        return outputs


def build_import_plan(entry):
    """Resolve named .cplobj imports, including aliases, with deterministic order.

    Source .cps dependencies are walked too. Duplicate names and missing
    exports fail early. This is a pre-link validation stage, not a compiler.
    """
    entry = Path(entry).resolve()
    active = []
    visited = set()
    libraries = {}
    bindings = {}
    global_names = {}

    def walk(path):
        path = path.resolve()
        if path in active:
            raise CompiledImportError('Dependencia circular: ' + ' -> '.join(p.name for p in active + [path]))
        if path in visited:
            return
        if path.suffix.lower() == '.cplobj':
            libraries[path] = load_compiled_dependency(path)
            visited.add(path)
            return
        if path.suffix.lower() != '.cps':
            raise CompiledImportError(f'Extension de modulo no soportada: {path}')
        try:
            source = path.read_text(encoding='utf-8-sig')
        except OSError as exc:
            raise CompiledImportError(f'No se pudo leer {path}: {exc}') from exc
        clean = _strip_comments_preserve_strings(source)
        own_names = set(_global_declarations(source))
        for name in own_names:
            if name in global_names and global_names[name] != path:
                raise CompiledImportError(f'Simbolo global duplicado: {name}')
            global_names[name] = path
        active.append(path)
        for match in IMPORT.finditer(clean):
            relative = match.group(2)
            if not relative.startswith(('./', '../')):
                raise CompiledImportError(f'Importacion no relativa: {relative}')
            target = path.parent / relative
            if not target.suffix:
                target = target.with_suffix('.cps')
            target = target.resolve()
            parts = [part.strip() for part in match.group(1).split(',')]
            if not parts or any(not IMPORT_ITEM.fullmatch(part) for part in parts):
                raise CompiledImportError(f'Importacion invalida: {match.group(0).strip()}')
            walk(target)
            if target.suffix.lower() == '.cplobj':
                dep = libraries[target]
                for part in parts:
                    exported, alias = IMPORT_ITEM.fullmatch(part).groups()
                    local = alias or exported
                    if exported not in dep.metadata['exports']:
                        raise CompiledImportError(f'Simbolo no exportado: {exported} ({target.name})')
                    key = (path, local)
                    if key in bindings or local in own_names:
                        raise CompiledImportError(f'Nombre importado duplicado: {local} ({path.name})')
                    bindings[key] = ImportedSymbol(local, exported, target, dep.metadata['exports'][exported])
        active.pop()
        visited.add(path)

    walk(entry)
    if libraries:
        from .package_dependencies import resolve_package_graph
        ordered = resolve_package_graph(libraries)
    else:
        ordered = []
    return CompiledImportPlan(entry, ordered, bindings)

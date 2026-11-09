"""Safe preparation of compiled-library imports for the existing source resolver.

The semantic interface is compiled as declarations only; executable stubs must
never be silently treated as a compiled library implementation.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import re
import tempfile

from .compiled_package import read_package, read_interface_metadata
from .interface_metadata import InterfaceError, validate_metadata
from .mips_linker import _read_full


class CompiledImportError(ValueError):
    pass


@dataclass(frozen=True)
class CompiledDependency:
    path: Path
    interface: str
    object_bytes: bytes
    metadata: dict
    exports: frozenset


def load_compiled_dependency(path):
    """Validate the full package, ABI and exported MIPS labels before use."""
    path = Path(path).resolve()
    if not path.is_file():
        raise CompiledImportError(
            f'No se encontro la biblioteca compilada "{path.name}" en: {path}. '
            f'Genera el archivo con BUILD LIB (o --build-library) sobre el .cps que la define; '
            f'la ruta del import es relativa a la carpeta del archivo que importa.')
    try:
        interface, object_bytes, exports = read_package(path)
        metadata = read_interface_metadata(path)
        if metadata is None:
            raise CompiledImportError(f'Biblioteca sin interfaz ABI: {path.name}')
        validate_metadata(metadata)
        abi_labels = set()
        for name, entry in metadata['exports'].items():
            if entry['kind'] == 'class':
                abi_labels.update(method['label'] for method in entry['methods'].values())
            elif entry['kind'] == 'function':
                abi_labels.add(entry['label'])
            else:
                raise CompiledImportError(f'Exportacion de datos aun no soportada: {name}')
        if not abi_labels <= exports:
            raise CompiledImportError('Faltan etiquetas de metodos/funciones en el objeto MIPS')
        # Forbid interface source that would execute top-level statements.
        # A full parser-based interface validator is planned for the next step.
        if not re.search(r'\b(?:class|function)\s+[A-Za-z_]\w*', interface):
            raise CompiledImportError('La interfaz no contiene declaraciones')
        return CompiledDependency(path, interface, object_bytes, metadata, frozenset(exports))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        if isinstance(exc, CompiledImportError):
            raise
        raise CompiledImportError(f'Biblioteca compilada invalida {path.name}: {exc}') from exc


def collect_compiled_dependencies(entry):
    """Discover direct and transitive .cplobj imports from .cps files.

    This does not link or compile anything, and does not assume that a stub
    implementation is executable. Cycles in source dependencies are rejected.
    """
    from .resolver import IMPORT, _strip_comments_preserve_strings, IMPORT_ITEM
    seen_source = set()
    compiled = {}
    def walk(path):
        path = Path(path).resolve()
        if path.suffix == '.cplobj':
            compiled[path] = load_compiled_dependency(path)
            return
        if path in seen_source:
            return
        seen_source.add(path)
        source = path.read_text(encoding='utf-8-sig')
        clean = _strip_comments_preserve_strings(source)
        for match in IMPORT.finditer(clean):
            target = match.group(2)
            if not target.startswith(('./', '../')):
                raise CompiledImportError(f'Importacion no relativa: {target}')
            target_path = (path.parent / target)
            if not target_path.suffix:
                target_path = target_path.with_suffix('.cps')
            walk(target_path)
            if target_path.suffix == '.cplobj':
                dep = compiled[target_path.resolve()]
                for raw in match.group(1).split(','):
                    item = IMPORT_ITEM.fullmatch(raw.strip())
                    if not item or item.group(1) not in dep.metadata['exports']:
                        raise CompiledImportError(f'Simbolo no exportado por {target_path.name}: {raw.strip()}')
    walk(entry)
    return list(compiled.values())

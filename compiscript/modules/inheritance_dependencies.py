"""Validate cross-package class inheritance without trusting unverified ABI.

This is a pre-compilation guard; it does not claim to lower external parent
methods into MIPS or replace the source compiler's semantic checks.
"""
from pathlib import Path

from .compiled_imports import CompiledImportError, load_compiled_dependency
from .package_dependencies import resolve_package_graph


def validate_external_inheritance(metadata, dependencies):
    """Return verified external parent ABI entries used by exported classes.

    Dependencies must be actual .cplobj paths. All are integrity-checked,
    including transitive packages. Ambiguous class names fail closed.
    """
    from .interface_metadata import validate_metadata
    validate_metadata(metadata)
    roots = [Path(p).resolve() for p in dependencies]
    packages = resolve_package_graph(roots) if roots else []
    external = {}
    for package in packages:
        for name, item in package.metadata['exports'].items():
            if item['kind'] != 'class':
                continue
            if name in external and external[name][0] != package.path:
                raise CompiledImportError(f'Clase externa ambigua: {name}')
            external[name] = (package.path, item)
    local = metadata['exports']
    for name, item in local.items():
        if item['kind'] != 'class':
            continue
        visited = {name}
        parent = item.get('parent')
        current_size = item['size']
        while parent:
            if parent in visited:
                raise CompiledImportError(f'Herencia circular: {name}')
            visited.add(parent)
            if parent in local:
                ancestor = local[parent]
            elif parent in external:
                ancestor = external[parent][1]
            else:
                raise CompiledImportError(f'Clase padre no disponible: {name} -> {parent}')
            if ancestor['kind'] != 'class':
                raise CompiledImportError(f'Padre no es una clase: {parent}')
            if current_size < ancestor['size']:
                raise CompiledImportError(f'Layout incompatible: {name} -> {parent}')
            inherited = {field['offset'] for field in ancestor['fields'].values()}
            if parent == item.get('parent'):
                for field_name, field in item['fields'].items():
                    if field['offset'] in inherited:
                        raise CompiledImportError(
                            f'Atributo solapado: {name}.{field_name} con {parent}')
            current_size = ancestor['size']
            parent = ancestor.get('parent')
    return external

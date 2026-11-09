"""Prepare verified external ABI symbols for a Compiscript semantic analyzer.

This bridge is intentionally not a linker. It must be called before analyzing
source declarations; object-code linkage and external-call lowering are separate.
"""
from collections import defaultdict
from pathlib import Path

from .external_symbols import install_external_symbols, ExternalSymbolError
from .compiled_imports import CompiledImportError


def install_plan_symbols(analyzer, plan, source_path=None):
    """Install imported compiled symbols into an empty semantic analyzer.

    Only bindings imported by the entry source are installed. Imports found in
    transitive source modules must be handled when their owning source is
    analyzed; silently placing them in the entry scope would leak names.
    Returns local-name -> Symbol. Rejects duplicate MIPS labels across packages.
    """
    if analyzer.table.global_scope.children:
        raise CompiledImportError('La tabla semantica ya contiene ambitos: instalar antes de analizar')
    # El resolvedor concatena todos los modulos .cps en un unico ambito global,
    # asi que los simbolos importados desde cualquier modulo .cps del proyecto se
    # instalan una sola vez. Un mismo nombre solo puede apuntar a un unico simbolo.
    grouped = defaultdict(dict)
    owner_of = {}
    for (owner, local), imported in plan.symbols.items():
        previous = owner_of.get(local)
        if previous is not None:
            if previous != (imported.library, imported.exported_name):
                raise CompiledImportError(f'Alias externo duplicado: {local}')
            continue
        owner_of[local] = (imported.library, imported.exported_name)
        grouped[imported.library][local] = imported.exported_name

    # Prevalidate all names and labels so a collision cannot partially mutate
    # the table. Names already defined by builtins are also rejected.
    names = set()
    labels = set(analyzer.table._labels)
    for dep in plan.libraries:
        aliases = grouped.get(dep.path, {})
        for local, exported in aliases.items():
            if local in names or analyzer.table.global_scope.lookup_local(local):
                raise CompiledImportError(f'Nombre externo duplicado: {local}')
            names.add(local)
            item = dep.metadata['exports'][exported]
            methods = item['methods'].values() if item['kind'] == 'class' else [item] if item['kind'] == 'function' else []
            for method in methods:
                label = method['label']
                if label in labels:
                    raise CompiledImportError(f'Etiqueta externa duplicada: {label}')
                labels.add(label)

    installed = {}
    for dep in plan.libraries:
        aliases = grouped.get(dep.path, {})
        if aliases:
            try:
                installed.update(install_external_symbols(analyzer.table, dep.metadata, aliases))
            except (ExternalSymbolError, ValueError) as exc:
                raise CompiledImportError(str(exc)) from exc
    _install_ancestors(analyzer, plan, installed)
    return installed


def _install_ancestors(analyzer, plan, installed):
    """Una clase importada puede heredar de otra que vive en una dependencia: se instala
    tambien (con su propio nombre) para que sus miembros heredados se resuelvan aunque el
    programa no la haya importado de forma explicita."""
    classes = {}
    for dep in plan.libraries:
        for name, item in dep.metadata['exports'].items():
            if item['kind'] == 'class':
                classes.setdefault(name, dep)
    pending = list(installed.values())
    while pending:
        parent = getattr(pending.pop(), 'parent_class', None)
        dep = classes.get(parent)
        if not parent or dep is None or analyzer.table.global_scope.lookup_local(parent) is not None:
            continue
        try:
            added = install_external_symbols(analyzer.table, dep.metadata, {parent: parent})
        except (ExternalSymbolError, ValueError):
            continue
        installed.update(added)
        pending.extend(added.values())

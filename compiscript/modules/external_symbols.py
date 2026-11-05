"""Install verified compiled-library ABI symbols into an existing symbol table.

This module only registers declarations. It does not emit TAC, compile bodies,
or link object code. Call it before semantic analysis of the consuming source.
"""
from compiscript.symbol_table import Scope, Symbol, FRAME_HEADER
from .interface_metadata import validate_metadata


class ExternalSymbolError(ValueError):
    pass


def install_external_symbols(table, metadata, aliases=None):
    """Register exported ABI declarations, preserving their external layouts.

    aliases maps local names to exported names. A collision is an error; no
    partial installation is performed for obvious naming/label conflicts.
    Returns a dict of local name -> external Symbol.
    """
    validate_metadata(metadata)
    exports = metadata['exports']
    aliases = dict(aliases) if aliases is not None else {name: name for name in exports}
    if len(set(aliases)) != len(aliases):
        raise ExternalSymbolError('Nombres importados duplicados')
    if len(set(aliases.values())) != len(aliases):
        raise ExternalSymbolError('No se puede importar un simbolo dos veces con nombres diferentes')
    for local, exported in aliases.items():
        if not isinstance(local, str) or not local.isidentifier() or exported not in exports:
            raise ExternalSymbolError(f'Importacion externa invalida: {local} -> {exported}')
        if table.global_scope.lookup_local(local) is not None:
            raise ExternalSymbolError(f'Simbolo global duplicado: {local}')
    labels = set(table._labels)
    for exported in aliases.values():
        item = exports[exported]
        members = item['methods'].values() if item['kind'] == 'class' else [item] if item['kind'] == 'function' else []
        for method in members:
            if method['label'] in labels:
                raise ExternalSymbolError(f'Etiqueta MIPS duplicada: {method["label"]}')
            labels.add(method['label'])

    result = {}
    for local, exported in aliases.items():
        item = exports[exported]
        kind = item['kind']
        if kind == 'class':
            cls = Symbol(local, 'class', type_=local)
            cls.storage = 'class'
            cls.attributes, cls.methods = {}, {}
            cls.parent_class = item.get('parent')
            cls.size = item['size']
            cls.external = True
            cls.external_name = exported
            table.global_scope.define(cls)
            scope = Scope(f'class:{local}', parent=table.global_scope, kind='class')
            scope.class_symbol = cls
            scope.next_offset = cls.size
            table.all_scopes.append(scope)
            for name, field in item['fields'].items():
                sym = Symbol(name, 'variable', type_=field['type'], class_name=local)
                sym.storage, sym.offset, sym.external = 'field', field['offset'], True
                scope.define(sym)
                cls.attributes[name] = sym
            for name, method in item['methods'].items():
                sym = _callable(name, method)
                sym.storage, sym.class_name = 'method', local
                scope.define(sym)
                cls.methods[name] = sym
        elif kind == 'function':
            cls = _callable(local, item)
            cls.storage = 'function'
            table.global_scope.define(cls)
        else:
            raise ExternalSymbolError(f'Exportacion externa aun no soportada: {exported} ({kind})')
        cls.external = True
        cls.external_name = exported
        result[local] = cls
    table._labels.update(labels)
    return result


def _callable(name, item):
    sym = Symbol(name, 'function', params=[tuple(p) for p in item['params']], return_type=item['return_type'])
    sym.label = item['label']
    sym.frame_size = item['frame_size']
    sym.external = True
    return sym

"""Serializable semantic ABI for compiled Compiscript libraries.

This is metadata only: it does not turn stub declarations into executable code.
"""

ABI_VERSION = 'compiscript-interface-abi-v1'


class InterfaceError(ValueError):
    pass


def _method(symbol):
    return {
        'label': symbol.label,
        'params': [[name, typ] for name, typ in symbol.params],
        'return_type': symbol.return_type,
        'frame_size': symbol.frame_size,
    }


def from_symbol_table(table, exports):
    """Capture the analyzed interface's public ABI, including inherited layouts."""
    exports = sorted(set(exports))
    result = {'format': ABI_VERSION, 'exports': {}}
    for name in exports:
        sym = table.global_scope.lookup_local(name)
        if sym is None or sym.storage == 'builtin':
            raise InterfaceError(f'Simbolo exportado inexistente: {name}')
        if sym.kind == 'class':
            result['exports'][name] = {
                'kind': 'class', 'parent': getattr(sym, 'parent_class', None),
                'size': sym.size,
                'fields': {key: {'type': field.type, 'offset': field.offset}
                           for key, field in sorted(sym.attributes.items())},
                'methods': {key: _method(method)
                            for key, method in sorted(sym.methods.items())},
            }
        elif sym.kind == 'function':
            result['exports'][name] = {'kind': 'function', **_method(sym)}
        elif sym.kind in ('variable', 'const'):
            result['exports'][name] = {
                'kind': sym.kind, 'type': sym.type, 'offset': sym.offset,
            }
        else:
            raise InterfaceError(f'Tipo de exportacion no soportado: {name}')
    validate_metadata(result)
    return result


def validate_metadata(metadata):
    if not isinstance(metadata, dict) or metadata.get('format') != ABI_VERSION:
        raise InterfaceError('Version de interfaz ABI no soportada')
    exports = metadata.get('exports')
    if not isinstance(exports, dict):
        raise InterfaceError('Exportaciones ABI invalidas')
    for name, item in exports.items():
        if not isinstance(name, str) or not isinstance(item, dict):
            raise InterfaceError('Simbolo ABI invalido')
        kind = item.get('kind')
        if kind == 'class':
            if not isinstance(item.get('size'), int) or item['size'] < 0 or item['size'] % 4:
                raise InterfaceError(f'Tamano de clase invalido: {name}')
            if not isinstance(item.get('fields'), dict) or not isinstance(item.get('methods'), dict):
                raise InterfaceError(f'Miembros de clase invalidos: {name}')
            for field in item['fields'].values():
                if (not isinstance(field, dict) or not isinstance(field.get('offset'), int)
                        or field['offset'] < 0 or field['offset'] % 4
                        or field['offset'] + 4 > item['size'] or not isinstance(field.get('type'), str)):
                    raise InterfaceError(f'Offset de atributo invalido: {name}')
            for method in item['methods'].values():
                _validate_callable(method)
        elif kind == 'function':
            _validate_callable(item)
        elif kind in ('variable', 'const'):
            if not isinstance(item.get('type'), str) or not isinstance(item.get('offset'), int) or item['offset'] < 0:
                raise InterfaceError(f'Variable ABI invalida: {name}')
        else:
            raise InterfaceError(f'Clase de simbolo ABI desconocida: {name}')
    return metadata


def _validate_callable(item):
    if (not isinstance(item.get('label'), str) or not item['label']
            or not isinstance(item.get('return_type'), str)
            or not isinstance(item.get('frame_size'), int) or item['frame_size'] < 16
            or not isinstance(item.get('params'), list)):
        raise InterfaceError('Firma ABI de funcion invalida')
    for param in item['params']:
        if not isinstance(param, list) or len(param) != 2 or not all(isinstance(x, str) for x in param):
            raise InterfaceError('Parametro ABI invalido')

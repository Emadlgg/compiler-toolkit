"""Compiled library container, v1: typed interface plus precompiled MIPS object.

The interface is intentionally separate from the object code. Consumers must
still type-check against the interface; they must NOT compile its stub bodies.
This module does not yet integrate that distinction into the CPS compiler.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

FORMAT = 'compiscript-compiled-package-v1'


class CompiledPackageError(ValueError):
    pass


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _validate_interface(source):
    if not source.strip():
        raise CompiledPackageError('La interfaz no puede estar vacia')
    if '\x00' in source:
        raise CompiledPackageError('Interfaz invalida')


def create_package(interface_path, object_path, output_path, *, metadata=None, dependencies=None):
    """Package a separate interface and a validated .mobj file.

    Does not claim to compile the .cps source. This separation is necessary to
    prevent recompiling function bodies when a consumer imports a library.
    """
    from .mips_linker import _read_full
    interface = Path(interface_path).read_text(encoding='utf-8-sig')
    _validate_interface(interface)
    _data, _text, exports = _read_full(object_path)
    interface_bytes = interface.encode('utf-8')
    object_bytes = Path(object_path).read_bytes()
    if metadata is not None:
        from .interface_metadata import validate_metadata, InterfaceError
        validate_metadata(metadata)
        from .class_package_builder import _exported_labels
        if not set(_exported_labels(metadata)).issubset(set(exports)):
            raise CompiledPackageError('Las etiquetas ABI deben estar exportadas por MIPS')
    manifest = {
        'format': FORMAT,
        'exports': sorted(exports),
        'interface_sha256': _digest(interface_bytes),
        'object_sha256': _digest(object_bytes),
    }
    if dependencies:
        from .package_dependencies import dependency_entries
        entries = []
        for dependency in dependencies:
            dependency = Path(dependency).resolve()
            relative = dependency.relative_to(Path(output_path).resolve().parent).as_posix()
            entries.append({'path': relative, 'sha256': _digest(dependency.read_bytes())})
        manifest['dependencies'] = entries
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if metadata is not None:
        metadata_bytes = json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode('utf-8')
        manifest['metadata_sha256'] = _digest(metadata_bytes)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', json.dumps(manifest, sort_keys=True))
        archive.writestr('interface.cps', interface_bytes)
        archive.writestr('object.mobj', object_bytes)
        if metadata is not None:
            archive.writestr('interface.json', metadata_bytes)
    return target


def read_package(path):
    """Return (interface, object_bytes, exports), validating all payloads."""
    from .mips_linker import _validate_text, _validate_v2, FORMAT as V1, FORMAT_V2
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            expected = ['interface.cps', 'manifest.json', 'object.mobj']
            if sorted(names) not in (expected, sorted(expected + ['interface.json'])):
                raise CompiledPackageError('Archivos faltantes o duplicados')
            manifest = json.loads(archive.read('manifest.json'))
            interface_bytes = archive.read('interface.cps')
            object_bytes = archive.read('object.mobj')
            metadata_bytes = archive.read('interface.json') if 'interface.json' in names else None
    except (OSError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise CompiledPackageError(f'Paquete ilegible: {exc}') from exc
    if (metadata_bytes is None) != ('metadata_sha256' not in manifest):
        raise CompiledPackageError('Metadatos ABI incompletos')
    if metadata_bytes is not None:
        if _digest(metadata_bytes) != manifest['metadata_sha256']:
            raise CompiledPackageError('Integridad de metadatos ABI incorrecta')
        from .interface_metadata import validate_metadata
        try:
            metadata = json.loads(metadata_bytes)
            validate_metadata(metadata)
            from .class_package_builder import _exported_labels
            if not set(_exported_labels(metadata)).issubset(set(manifest['exports'])):
                raise CompiledPackageError('Exportaciones ABI inconsistentes')
        except (ValueError, TypeError) as exc:
            raise CompiledPackageError(f'Metadatos ABI invalidos: {exc}') from exc
    if manifest.get('format') != FORMAT:
        raise CompiledPackageError('Formato de paquete no soportado')
    if _digest(interface_bytes) != manifest.get('interface_sha256') or _digest(object_bytes) != manifest.get('object_sha256'):
        raise CompiledPackageError('Integridad de paquete incorrecta')
    try:
        interface = interface_bytes.decode('utf-8')
        obj = json.loads(object_bytes.decode('utf-8-sig'))
        exports = obj['exports']
        if obj['format'] == V1:
            _validate_text(obj['text'])
            digest = obj['text']
        elif obj['format'] == FORMAT_V2:
            _validate_v2(obj['data'], obj['text'])
            digest = json.dumps({'data': obj['data'], 'text': obj['text']}, sort_keys=True, ensure_ascii=False)
        else:
            raise CompiledPackageError('Formato MIPS no soportado')
        if _digest(digest.encode('utf-8')) != obj['sha256']:
            raise CompiledPackageError('Integridad MIPS incorrecta')
        if sorted(exports) != manifest['exports']:
            raise CompiledPackageError('Exportaciones inconsistentes')
        _validate_interface(interface)
    except (UnicodeError, KeyError, TypeError, ValueError) as exc:
        raise CompiledPackageError(f'Contenido de paquete invalido: {exc}') from exc
    return interface, object_bytes, set(exports)


def extract_object(package_path, output_path):
    _, obj, _ = read_package(package_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(obj)
    return target


def main():
    parser = argparse.ArgumentParser(description='Paquetes Compiscript de interfaz y MIPS precompilado')
    sub = parser.add_subparsers(dest='action', required=True)
    pack = sub.add_parser('pack')
    pack.add_argument('interface')
    pack.add_argument('object')
    pack.add_argument('-o', '--output', required=True)
    pack.add_argument('--dependency', action='append', default=[], help='Paquete .cplobj requerido (repetible)')
    unpack = sub.add_parser('extract-object')
    unpack.add_argument('package')
    unpack.add_argument('-o', '--output', required=True)
    args = parser.parse_args()
    try:
        path = (create_package(args.interface, args.object, args.output, dependencies=args.dependency)
                if args.action == 'pack' else extract_object(args.package, args.output))
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'Archivo guardado en: {path}')


if __name__ == '__main__':
    main()


def read_interface_metadata(path):
    """Read verified semantic ABI, if present (legacy packages return None)."""
    read_package(path)
    with zipfile.ZipFile(path) as archive:
        if 'interface.json' not in archive.namelist():
            return None
        return json.loads(archive.read('interface.json'))

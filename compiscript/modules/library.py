"""Portable Compiscript library bundles (.cplib), format version 1.

This format packages source declarations and export metadata; it is NOT a
precompiled MIPS object file. Consumers still run semantic analysis and TAC.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

FORMAT = 'compiscript-library-v1'


class LibraryError(ValueError):
    pass


def build_library(source_path, output_path):
    from .resolver import _load, _global_declarations
    source_path = Path(source_path).resolve()
    if source_path.suffix.lower() != '.cps':
        raise LibraryError('La biblioteca debe originarse de un archivo .cps')
    module = _load(source_path)
    if module.imports:
        raise LibraryError('v1 solo admite bibliotecas sin importaciones')
    declarations = set(_global_declarations(module.source))
    if not module.exports <= declarations:
        raise LibraryError('Exportacion sin declaracion global')
    source = module.source.encode('utf-8')
    manifest = {
        'format': FORMAT,
        'exports': sorted(module.exports),
        'sha256': hashlib.sha256(source).hexdigest(),
        'source_name': source_path.name,
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, sort_keys=True))
        archive.writestr('module.cps', source)
    return output_path


def read_library(path):
    path = Path(path)
    try:
        with zipfile.ZipFile(path) as archive:
            if sorted(archive.namelist()) != ['manifest.json', 'module.cps']:
                raise LibraryError(f'Contenido de biblioteca no valido: {path}')
            manifest = json.loads(archive.read('manifest.json'))
            raw = archive.read('module.cps')
    except (OSError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise LibraryError(f'Biblioteca ilegible: {path}: {exc}') from exc
    if manifest.get('format') != FORMAT:
        raise LibraryError(f'Version de biblioteca no soportada: {path}')
    if hashlib.sha256(raw).hexdigest() != manifest.get('sha256'):
        raise LibraryError(f'Integridad de biblioteca incorrecta: {path}')
    exports = manifest.get('exports')
    if not isinstance(exports, list) or not all(isinstance(x, str) for x in exports):
        raise LibraryError(f'Exportaciones invalidas: {path}')
    try:
        source = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise LibraryError(f'Codigo de biblioteca no es UTF-8: {path}') from exc
    return source, set(exports)


def main():
    parser = argparse.ArgumentParser(description='Crear biblioteca Compiscript portable (.cplib)')
    parser.add_argument('source', help='Archivo .cps sin dependencias')
    parser.add_argument('-o', '--output', required=True, help='Archivo .cplib')
    args = parser.parse_args()
    try:
        output = build_library(args.source, args.output)
    except (LibraryError, OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'Biblioteca guardada en: {output}')


if __name__ == '__main__':
    main()

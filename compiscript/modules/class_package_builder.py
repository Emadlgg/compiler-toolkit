"""Build a verified .cplobj from an already compiled Compiscript MIPS file.

This is an explicit packaging stage, not a source-to-object compiler.  The
caller supplies the ABI produced by the semantic analyzer and an interface.
Unsupported relocations are rejected by library_object_builder.
"""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .compiled_package import create_package
from .interface_metadata import validate_metadata
from .library_object_builder import build_library_object, LibraryBuildError


class ClassPackageBuildError(ValueError):
    pass


def _exported_labels(metadata):
    validate_metadata(metadata)
    labels = []
    exports = metadata['exports']
    for name, item in exports.items():
        if item['kind'] == 'class':
            if item.get('parent'):
                parent = item['parent']
                if parent not in exports or exports[parent]['kind'] != 'class':
                    raise ClassPackageBuildError(
                        f'Herencia externa no soportada aun en empaquetado: {name} -> {parent}')
                if item['size'] < exports[parent]['size']:
                    raise ClassPackageBuildError(
                        f'Layout de herencia invalido: {name} tiene menos espacio que {parent}')
                seen = {name}
                ancestor = parent
                while ancestor:
                    if ancestor in seen:
                        raise ClassPackageBuildError(f'Herencia circular: {name}')
                    seen.add(ancestor)
                    if ancestor not in exports or exports[ancestor]['kind'] != 'class':
                        raise ClassPackageBuildError(f'Ancestro no exportado: {ancestor}')
                    ancestor = exports[ancestor].get('parent')
            labels.extend(method['label'] for method in item['methods'].values())
        elif item['kind'] == 'function':
            labels.append(item['label'])
        else:
            raise ClassPackageBuildError(
                f'Exportacion con datos globales no soportada: {name}')
    # Reject layouts that reuse an inherited field slot. A package can
    # otherwise link successfully and silently corrupt the parent object.
    for name, item in exports.items():
        if item['kind'] != 'class':
            continue
        occupied = {}
        ancestor = item.get('parent')
        while ancestor:
            parent = exports[ancestor]
            for field_name, field in parent['fields'].items():
                occupied.setdefault(field['offset'], f'{ancestor}.{field_name}')
            ancestor = parent.get('parent')
        for field_name, field in item['fields'].items():
            offset = field['offset']
            if offset in occupied:
                raise ClassPackageBuildError(
                    f'Layout de herencia con solapamiento: {name}.{field_name} '
                    f'comparte offset {offset} con {occupied[offset]}')
    if not labels or len(labels) != len(set(labels)):
        raise ClassPackageBuildError('Se requieren etiquetas de rutinas unicas')
    return labels


def build_class_package(assembly, interface, metadata_path, output):
    """Package compiled routines with ABI metadata; fail closed on unsafe input."""
    metadata = json.loads(Path(metadata_path).read_text(encoding='utf-8-sig'))
    labels = _exported_labels(metadata)
    with TemporaryDirectory(prefix='cps-lib-') as directory:
        obj = Path(directory) / 'library.mobj'
        try:
            build_library_object(assembly, labels, obj)
            return create_package(interface, obj, output, metadata=metadata)
        except (ValueError, OSError) as exc:
            raise ClassPackageBuildError(str(exc)) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description='Empaquetar MIPS Compiscript con ABI en .cplobj')
    parser.add_argument('assembly', help='MIPS generado desde Compiscript')
    parser.add_argument('--interface', required=True, help='Interfaz CPS')
    parser.add_argument('--metadata', required=True, help='ABI JSON del analizador semantico')
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args(argv)
    try:
        result = build_class_package(args.assembly, args.interface, args.metadata, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'Biblioteca guardada en: {result}')


if __name__ == '__main__':
    main()

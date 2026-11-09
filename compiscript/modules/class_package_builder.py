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


def _exported_labels(metadata, allow_external_parents=False):
    """allow_external_parents: el paquete declara dependencias; el padre puede vivir
    en otra biblioteca (se verifica aparte con validate_external_inheritance)."""
    validate_metadata(metadata)
    labels = []
    exports = metadata['exports']
    for name, item in exports.items():
        if item['kind'] == 'class':
            if item.get('parent'):
                parent = item['parent']
                if parent not in exports and allow_external_parents:
                    labels.extend(method['label'] for method in item['methods'].values())
                    continue
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
                    if ancestor not in exports and allow_external_parents:
                        break
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
        while ancestor and ancestor in exports:
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


def dependency_labels(packages):
    """Etiquetas MIPS exportadas por una lista de paquetes verificados."""
    labels = set()
    for package in packages:
        for item in package.metadata['exports'].values():
            if item['kind'] == 'class':
                labels.update(method['label'] for method in item['methods'].values())
            elif item['kind'] == 'function':
                labels.add(item['label'])
    return labels


def build_class_package(assembly, interface, metadata_path, output, dependencies=None):
    """Package compiled routines with ABI metadata; fail closed on unsafe input.

    dependencies: paquetes .cplobj de los que depende la biblioteca (por ejemplo, el
    paquete de la clase padre). Se verifican con hash, se guardan en el manifiesto y
    sus rutinas pueden ser referenciadas desde el objeto MIPS.
    """
    metadata = json.loads(Path(metadata_path).read_text(encoding='utf-8-sig'))
    deps = [Path(d).resolve() for d in (dependencies or [])]
    labels = _exported_labels(metadata, allow_external_parents=bool(deps))
    external_labels = set()
    if deps:
        from .inheritance_dependencies import validate_external_inheritance
        from .package_dependencies import resolve_package_graph
        validate_external_inheritance(metadata, deps)
        external_labels = dependency_labels(resolve_package_graph(deps))
        if external_labels & set(labels):
            raise ClassPackageBuildError('Etiqueta duplicada entre la biblioteca y sus dependencias: '
                                         + ', '.join(sorted(external_labels & set(labels))))
        base = Path(output).resolve().parent
        for dep in deps:
            try:
                dep.relative_to(base)
            except ValueError:
                raise ClassPackageBuildError(
                    f'La biblioteca debe guardarse en la misma carpeta (o una superior) que sus '
                    f'dependencias: {dep.name} esta en {dep.parent}') from None
    with TemporaryDirectory(prefix='cps-lib-') as directory:
        obj = Path(directory) / 'library.mobj'
        try:
            build_library_object(assembly, labels, obj, external_labels=external_labels)
            return create_package(interface, obj, output, metadata=metadata, dependencies=deps or None)
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

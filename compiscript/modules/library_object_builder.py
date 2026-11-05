"""Extract reusable MIPS routines and relocatable data from Compiscript output.

The source-library builder already rejects user global variables.  This module
removes the generated program's unused global-area placeholder, retains the
library's static constants, and lets the v2 object linker namespace private
labels.  It fails closed on $gp accesses and unsupported references.
"""
from pathlib import Path
import re
from .mips_linker import build_object, LinkError, _split_sections, _symbols, _references, _validate_v2

_LABEL = re.compile(r'^\s*([A-Za-z_][A-Za-z_0-9]*):')
_GLOBAL = re.compile(r'^\s*_globals:\s*\.space\s+(\d+)\s*(?:#.*)?$')
_GP = re.compile(r'(?<!\w)\$gp(?!\w)')


class LibraryBuildError(ValueError):
    pass


def _extract(assembly, exported_labels):
    source = Path(assembly).read_text(encoding='utf-8-sig')
    try:
        data, code = _split_sections(source)
    except LinkError as exc:
        raise LibraryBuildError(str(exc)) from exc

    # The backend always emits _globals even for a module without globals.
    # The source-library builder rejects actual global declarations.  Never
    # preserve this label: each executable already owns its own global area.
    data_lines = []
    for line in data.splitlines():
        match = _GLOBAL.fullmatch(line.strip())
        if match:
            if match:
                if int(match.group(1)) != 4:
                    raise LibraryBuildError(
                        'Biblioteca con datos globales: requiere relocacion de $gp'
                    )
                continue
        if re.match(r'^\s*_globals\s*:', line):
            raise LibraryBuildError('Definicion global no soportada')
        data_lines.append(line)
    data = '\n'.join(data_lines).strip()

    blocks, current, lines = [], None, []
    for line in code.splitlines():
        match = _LABEL.match(line)
        if match and not line.startswith((' ', '\t')):
            if current is not None:
                blocks.append((current, lines))
            current, lines = match.group(1), [line]
        elif current is not None:
            lines.append(line)
        elif line.strip() and not line.lstrip().startswith('#'):
            if line.strip() not in ('la $gp, _globals', 'j main'):
                raise LibraryBuildError('Codigo fuera de funciones')
    if current is not None:
        blocks.append((current, lines))
    labels = {name for name, _ in blocks}
    exports = set(exported_labels)
    if not exports or not exports <= labels or 'main' in exports:
        raise LibraryBuildError('Exportaciones invalidas o inexistentes')
    if 'main' not in labels:
        raise LibraryBuildError('Se esperaba un programa Compiscript con main')
    first_export = next((idx for idx, (name, _) in enumerate(blocks) if name in exports), None)
    if first_export is None:
        raise LibraryBuildError('No hay rutinas exportables')
    text = '\n'.join(line for _, group in blocks[first_export:] for line in group)
    if not text.strip():
        raise LibraryBuildError('No hay rutinas exportables')
    if re.search(r'(?<![\w])_globals(?![\w])', text) or _GP.search(text):
        raise LibraryBuildError('Referencia a datos globales no relocable')
    try:
        known = _validate_v2(data, text)
    except LinkError as exc:
        raise LibraryBuildError(str(exc)) from exc
    for reference in list(_references(data, True)) + list(_references(text)):
        if reference not in known:
            raise LibraryBuildError(f'Referencia externa no resuelta: {reference}')
    return data, text


def extract_routines(assembly, exported_labels):
    """Backward-compatible text-only extractor; refuses data-bearing objects."""
    data, text = _extract(assembly, exported_labels)
    if data:
        raise LibraryBuildError('La extraccion de solo rutinas no admite datos; use build_library_object')
    return text


def build_library_object(assembly, exported_labels, output):
    """Write a v1 object for text-only modules, or v2 with relocatable data."""
    data, text = _extract(assembly, exported_labels)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    intermediate = output.with_suffix('.library-tmp.asm')
    try:
        content = ('.data\n' + data + '\n.text\n' + text) if data else text
        intermediate.write_text(content, encoding='utf-8')
        return build_object(intermediate, exported_labels, output)
    finally:
        intermediate.unlink(missing_ok=True)

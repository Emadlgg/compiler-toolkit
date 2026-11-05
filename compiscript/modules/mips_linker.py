"""Enlazador estatico MIPS para objetos .mobj v1 y v2.

v2 permite secciones .data/.text y referencias a simbolos entre objetos.
No es un enlazador ELF: solo admite el subconjunto de directivas listado.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

FORMAT = 'compiscript-mips-object-v1'
FORMAT_V2 = 'compiscript-mips-object-v2'
SYMBOL = re.compile(r'^[A-Za-z_][A-Za-z_0-9]*$')
LABEL = re.compile(r'^\s*([A-Za-z_][A-Za-z_0-9]*):\s*(.*)$')
REF_OPS = {'j', 'jal', 'beq', 'bne', 'blt', 'ble', 'bgt', 'bge',
           'beqz', 'bnez', 'bltz', 'bgez', 'blez', 'bgtz', 'la'}
DIRECTIVES = {'.word', '.byte', '.half', '.space', '.ascii', '.asciiz', '.align'}


class LinkError(ValueError):
    pass


def _symbols(text):
    return [m.group(1) for line in text.splitlines()
            if (m := LABEL.match(line.split('#', 1)[0]))]


def _split_sections(text):
    data, code = [], []
    section = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped in ('.data', '.text'):
            section = stripped
            continue
        if stripped.startswith('.globl '):
            continue
        if section is None:
            if stripped and not stripped.startswith('#'):
                raise LinkError('Instruccion fuera de .data/.text')
            continue
        (data if section == '.data' else code).append(raw)
    if section is None:
        raise LinkError('Objeto sin secciones .data/.text')
    return '\n'.join(data), '\n'.join(code)


def _validate_text(text):
    if not isinstance(text, str) or not text.strip():
        raise LinkError('Objeto sin instrucciones')
    for line in text.splitlines():
        code = line.split('#', 1)[0].strip()
        if code.startswith('.') or code.startswith('_globals:'):
            raise LinkError('Los objetos v1 no permiten directivas ni datos')
    names = _symbols(text)
    if len(names) != len(set(names)):
        raise LinkError('Etiquetas duplicadas en el objeto')
    return set(names)


def _validate_v2(data, text):
    if not isinstance(data, str) or not isinstance(text, str) or not text.strip():
        raise LinkError('Se requiere una seccion .text no vacia')
    names = _symbols(data) + _symbols(text)
    if len(names) != len(set(names)):
        raise LinkError('Etiquetas duplicadas en el objeto')
    for line in data.splitlines():
        code = line.split('#', 1)[0].strip()
        match = LABEL.match(code)
        if match:
            code = match.group(2).strip()
        if code and not any(code == d or code.startswith(d + ' ') for d in DIRECTIVES):
            raise LinkError(f'Directiva de datos no soportada: {code}')
    for line in text.splitlines():
        code = line.split('#', 1)[0].strip()
        match = LABEL.match(code)
        if match:
            code = match.group(2).strip()
        if code.startswith('.'):
            raise LinkError(f'Directiva no soportada en .text: {code}')
    return set(names)


def build_object(assembly, exports, output):
    source = Path(assembly).read_text(encoding='utf-8-sig')
    exports = sorted(set(exports))
    if not exports or any(not SYMBOL.fullmatch(e) for e in exports):
        raise LinkError('Se requiere al menos una exportacion valida')
    if re.search(r'^\s*\.(?:text|data)\s*$', source, re.MULTILINE):
        data, text = _split_sections(source)
        defined = _validate_v2(data, text)
        payload = {'format': FORMAT_V2, 'exports': exports, 'data': data, 'text': text}
        digest = json.dumps({'data': data, 'text': text}, sort_keys=True, ensure_ascii=False)
    else:
        defined = _validate_text(source)
        payload = {'format': FORMAT, 'exports': exports, 'text': source}
        digest = source
    if not set(exports) <= defined:
        raise LinkError('La exportacion no existe en el ensamblador')
    payload['sha256'] = hashlib.sha256(digest.encode('utf-8')).hexdigest()
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding='utf-8')
    return target


def _read_full(path):
    try:
        obj = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise LinkError(f'Objeto ilegible: {path}: {exc}') from exc
    if not isinstance(obj, dict) or obj.get('format') not in (FORMAT, FORMAT_V2):
        raise LinkError('Formato de objeto no soportado')
    exports = obj.get('exports')
    if not isinstance(exports, list) or not exports or not all(isinstance(x, str) and SYMBOL.fullmatch(x) for x in exports) or len(set(exports)) != len(exports):
        raise LinkError('Exportaciones invalidas')
    if obj['format'] == FORMAT:
        data, text = '', obj.get('text')
        defined = _validate_text(text)
        digest = text
    else:
        data, text = obj.get('data'), obj.get('text')
        defined = _validate_v2(data, text)
        digest = json.dumps({'data': data, 'text': text}, sort_keys=True, ensure_ascii=False)
    if hashlib.sha256(digest.encode('utf-8')).hexdigest() != obj.get('sha256'):
        raise LinkError('Hash de objeto incorrecto')
    if not set(exports) <= defined:
        raise LinkError('Exportaciones no definidas')
    return data, text, set(exports)


def read_object(path):
    """API compatible con v1: retorna texto y simbolos exportados."""
    data, text, exports = _read_full(path)
    return ('.data\n' + data + '\n.text\n' + text if data else text), exports


def _replace_references(line, mapping, known):
    """Reescribe operandos simbolicos sin alterar strings ni comentarios."""
    head, marker, comment = line.partition('#')
    # Preserve quoted string contents in data directives.
    chunks = re.split(r'("(?:\\.|[^"\\])*")', head)
    for idx in range(0, len(chunks), 2):
        part = chunks[idx]
        for old, new in mapping.items():
            part = re.sub(r'(?<![\w$])' + re.escape(old) + r'(?!\w)', new, part)
        chunks[idx] = part
    return ''.join(chunks) + (marker + comment if marker else '')


def _references(section, is_data=False):
    for raw in section.splitlines():
        code = raw.split('#', 1)[0].strip()
        label = LABEL.match(code)
        if label:
            code = label.group(2).strip()
        if not code:
            continue
        parts = code.split(None, 1)
        op = parts[0]
        operands = parts[1] if len(parts) > 1 else ''
        if op in REF_OPS and operands:
            candidate = operands.split(',')[-1].strip()
            if SYMBOL.fullmatch(candidate) and not candidate.startswith('$'):
                yield candidate
        elif is_data and op in ('.word', '.half', '.byte'):
            for item in operands.split(','):
                candidate = item.strip()
                if SYMBOL.fullmatch(candidate):
                    yield candidate


def link(program, objects, output):
    source = Path(program).read_text(encoding='utf-8-sig')
    if '.text' not in source or '.data' not in source:
        raise LinkError('El programa principal requiere .data y .text')
    main_data, main_text = _split_sections(source)
    main_labels = set(_symbols(main_data) + _symbols(main_text))
    compiled = [_read_full(path) for path in objects]
    exports = set()
    for _, _, names in compiled:
        collision = names & (exports | main_labels)
        if collision:
            raise LinkError('Simbolo exportado duplicado: ' + ', '.join(sorted(collision)))
        exports.update(names)
    data_chunks, text_chunks = [main_data], [main_text]
    for idx, (data, text, public) in enumerate(compiled):
        local = set(_symbols(data) + _symbols(text))
        mapping = {name: f'_obj{idx}_{name}' for name in local - public}
        available = local | exports | main_labels
        for reference in list(_references(data, True)) + list(_references(text)):
            if reference not in available:
                raise LinkError(f'Referencia externa sin resolver: {reference}')
        data_chunks.append('\n'.join(_replace_references(line, mapping, available) for line in data.splitlines()))
        converted = []
        for line in text.splitlines():
            rewritten = _replace_references(line, mapping, available)
            # Keep the v1 branch formatting expected by existing integrations.
            if data == '' and re.match(r'^\s*j\s+', rewritten) and rewritten != line:
                rewritten = re.sub(r'^(\s*j)\s+', r'\1  ', rewritten)
            converted.append(rewritten)
        text_chunks.append('\n'.join(converted))
    result = '.data\n' + '\n'.join(data_chunks) + '\n.text\n.globl main\n' + '\n'.join(text_chunks) + '\n'
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result, encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description='Empaquetar y enlazar rutinas MIPS (.mobj)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('pack')
    p.add_argument('assembly')
    p.add_argument('--export', action='append', required=True)
    p.add_argument('-o', '--output', required=True)
    p = sub.add_parser('link')
    p.add_argument('program')
    p.add_argument('objects', nargs='+')
    p.add_argument('-o', '--output', required=True)
    args = parser.parse_args()
    try:
        result = build_object(args.assembly, args.export, args.output) if args.command == 'pack' else link(args.program, args.objects, args.output)
    except (LinkError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'Archivo guardado en: {result}')


if __name__ == '__main__':
    main()

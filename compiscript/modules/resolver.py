"""Resuelve imports/export de archivos .cps antes del parser existente.

Importaciones nombradas y alias, con espacio global compartido.
Las declaraciones se combinan en orden de dependencias para aprovechar
la tabla de simbolos y el backend existentes. No es un enlazador binario.
"""
from dataclasses import dataclass
from pathlib import Path
import re


class ModuleError(ValueError):
    pass


IMPORT = re.compile(
    r'^\s*import\s*\{\s*([^{};]*)\s*\}\s*from\s*["\']([^"\'\r\n]+)["\']\s*;\s*$',
    re.MULTILINE,
)
EXPORT = re.compile(r'^(\s*)export\s+(class|function|const|let|var)\s+([A-Za-z_][A-Za-z_0-9]*)\b', re.MULTILINE)
DECL = re.compile(r'^\s*(?:class|function|const|let|var)\s+([A-Za-z_][A-Za-z_0-9]*)\b', re.MULTILINE)
IDENT = re.compile(r'^[A-Za-z_][A-Za-z_0-9]*$')
IMPORT_ITEM = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*)(?:\s+as\s+([A-Za-z_][A-Za-z_0-9]*))?$')


@dataclass
class Module:
    path: Path
    source: str
    exports: set
    imports: list
    aliases: dict


def _strip_comments_preserve_strings(source):
    """Elimina comentarios para detectar directivas sin confundir strings."""
    pattern = re.compile(r'("(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/)', re.MULTILINE)
    return pattern.sub(lambda m: m.group() if m.group().startswith('"') else re.sub(r'[^\n]', ' ', m.group()), source)


def _load(path):
    if path.suffix.lower() == '.cplib':
        from .library import read_library, LibraryError
        try:
            source, exports = read_library(path)
        except LibraryError as exc:
            raise ModuleError(str(exc)) from exc
        if re.search(r'^\s*(?:import|export)\b', _strip_comments_preserve_strings(source), re.MULTILINE):
            raise ModuleError(f'Biblioteca contiene directivas inesperadas: {path}')
        return Module(path, source, exports, [], {})
    try:
        original = path.read_text(encoding='utf-8-sig')
    except OSError as exc:
        raise ModuleError(f'No se pudo leer modulo {path}: {exc}') from exc
    clean = _strip_comments_preserve_strings(original)
    imports = []
    aliases = {}
    for match in IMPORT.finditer(clean):
        items = [part.strip() for part in match.group(1).split(',')]
        parsed = []
        if not items or any(not IMPORT_ITEM.fullmatch(part) for part in items):
            raise ModuleError(f'Importacion invalida en {path}: {match.group(0).strip()}')
        for item in items:
            symbol, alias = IMPORT_ITEM.fullmatch(item).groups()
            local = alias or symbol
            if local in aliases:
                raise ModuleError(f"Nombre importado duplicado '{local}' en {path.name}")
            aliases[local] = (symbol, match.group(2))
            parsed.append((symbol, local))
        imports.append((parsed, match.group(2)))
    exports = set(EXPORT.findall(clean))
    exported_names = {name for _, _, name in exports}
    # Evitar interpretar directivas no soportadas como codigo valido.
    stripped = IMPORT.sub(lambda m: '\n' * m.group().count('\n'), original)
    stripped = EXPORT.sub(lambda m: m.group(1) + m.group(2) + ' ' + m.group(3), stripped)
    if re.search(r'^\s*(?:import|export)\b', _strip_comments_preserve_strings(stripped), re.MULTILINE):
        raise ModuleError(f'Sintaxis import/export no soportada en {path}; usar import {{ Nombre }} from "./archivo";')
    return Module(path, stripped, exported_names, imports, aliases)


def _replace_aliases(source, aliases):
    """Replace alias identifiers, never strings/comments or member names after '.'."""
    if not aliases:
        return source
    token = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/|[A-Za-z_][A-Za-z_0-9]*')
    def rewrite(match):
        word = match.group()
        if word not in aliases:
            return word
        prefix = source[:match.start()].rstrip()
        if prefix.endswith('.'):
            return word
        return aliases[word]
    return token.sub(rewrite, source)


def _global_declarations(source):
    """Encuentra declaraciones a nivel de modulo, no metodos de clases.

    El resolvedor actual concatena fuentes: solo los simbolos del ambito
    global deben considerarse colisiones entre archivos.
    """
    clean = _strip_comments_preserve_strings(source)
    # Las llaves dentro de literales no alteran la profundidad de bloques.
    clean = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: ' ' * len(m.group()), clean)
    depth = 0
    for line in clean.splitlines():
        if depth == 0:
            match = DECL.match(line)
            if match:
                yield match.group(1)
        depth += line.count('{') - line.count('}')


def resolve_project(entry, *, with_source_map=False):
    """Retorna fuente compilable unificada, validando rutas y exportaciones.

    Limitacion: todos los simbolos globales comparten espacio de nombres.
    """
    root = Path(entry).resolve()
    active = []
    visited = {}
    order = []
    declared = {}

    def visit(path):
        path = path.resolve()
        if path in active:
            chain = ' -> '.join(p.name for p in active + [path])
            raise ModuleError(f'Dependencia circular: {chain}')
        if path in visited:
            return visited[path]
        if path.suffix.lower() not in ('.cps', '.cplib'):
            raise ModuleError(f'Solo se permiten modulos .cps o .cplib: {path}')
        module = _load(path)
        active.append(path)
        for names, relative in module.imports:
            if not relative.startswith('./') and not relative.startswith('../'):
                raise ModuleError(f'Importacion debe usar ruta relativa: {relative} ({path.name})')
            target = path.parent / relative
            if not target.suffix:
                target = target.with_suffix('.cps')
            if target.suffix.lower() == '.cplobj':
                # Verified and installed separately by the compiled import plan.
                continue
            dependency = visit(target)
            for name, local in names:
                if name not in dependency.exports:
                    raise ModuleError(f"'{name}' no esta exportado por {dependency.path.name} (importado desde {path.name})")
        # Existing compiler uses a single global symbol table. Alias names
        # are rewritten to their exported declarations before ANTLR runs.
        substitutions = {local: original for local, (original, relative) in module.aliases.items()
                         if local != original and not relative.lower().endswith('.cplobj')}
        own_globals = set(_global_declarations(module.source))
        collisions = own_globals.intersection(substitutions)
        if collisions:
            raise ModuleError(f"Alias en conflicto con declaracion global: {', '.join(sorted(collisions))} ({path.name})")
        module.source = _replace_aliases(module.source, substitutions)
        active.pop()
        visited[path] = module
        order.append(module)
        return module

    visit(root)
    for module in order:
        # El parser original tiene un unico ambito global. Detectar colisiones
        # tempranamente en lugar de generar etiquetas ambiguas.
        for name in _global_declarations(module.source):
            if name in declared:
                raise ModuleError(f"Simbolo global duplicado '{name}': {declared[name].name} y {module.path.name}")
            declared[name] = module.path
    chunks = [f'// modulo: {m.path.name}\n{m.source}' for m in order]
    combined = '\n'.join(chunks)
    if not with_source_map:
        return combined
    # Source map indexed by 1-based combined line. None means a generated header.
    # Use character offsets to preserve the exact old concatenation behavior.
    spans = []
    offset = 0
    for module, chunk in zip(order, chunks):
        header = f'// modulo: {module.path.name}\n'
        spans.append((offset, offset + len(header), module.path, None))
        pos = offset + len(header)
        for line_no, line in enumerate(module.source.splitlines(keepends=True), 1):
            spans.append((pos, pos + len(line), module.path, line_no))
            pos += len(line)
        offset += len(chunk) + 1
    line_map = {}
    position = 0
    for number, line in enumerate(combined.splitlines(keepends=True), 1):
        for start, end, path, original_line in spans:
            if start <= position < end:
                line_map[number] = (path, original_line)
                break
        position += len(line)
    return combined, line_map


def resolve_project_with_map(entry):
    """Returns (combined source, {combined line: (original Path, original line)})."""
    return resolve_project(entry, with_source_map=True)

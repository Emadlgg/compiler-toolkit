"""Resuelve imports/export de archivos .cps antes del parser existente.

Primera etapa: importaciones nombradas, sin alias, de clases y funciones.
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


@dataclass
class Module:
    path: Path
    source: str
    exports: set
    imports: list


def _strip_comments_preserve_strings(source):
    """Elimina comentarios para detectar directivas sin confundir strings."""
    pattern = re.compile(r'("(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/)', re.MULTILINE)
    return pattern.sub(lambda m: m.group() if m.group().startswith('"') else re.sub(r'[^\n]', ' ', m.group()), source)


def _load(path):
    try:
        original = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise ModuleError(f'No se pudo leer modulo {path}: {exc}') from exc
    clean = _strip_comments_preserve_strings(original)
    imports = []
    for match in IMPORT.finditer(clean):
        names = [name.strip() for name in match.group(1).split(',')]
        if not names or any(not IDENT.fullmatch(name) for name in names):
            raise ModuleError(f'Importacion invalida en {path}: {match.group(0).strip()}')
        imports.append((names, match.group(2)))
    exports = set(EXPORT.findall(clean))
    exported_names = {name for _, _, name in exports}
    # Evitar interpretar directivas no soportadas como codigo valido.
    stripped = IMPORT.sub(lambda m: '\n' * m.group().count('\n'), original)
    stripped = EXPORT.sub(lambda m: m.group(1) + m.group(2) + ' ' + m.group(3), stripped)
    if re.search(r'^\s*(?:import|export)\b', _strip_comments_preserve_strings(stripped), re.MULTILINE):
        raise ModuleError(f'Sintaxis import/export no soportada en {path}; usar import {{ Nombre }} from "./archivo";')
    return Module(path, stripped, exported_names, imports)


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


def resolve_project(entry):
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
        if path.suffix.lower() != '.cps':
            raise ModuleError(f'Solo se permiten modulos .cps: {path}')
        module = _load(path)
        active.append(path)
        for names, relative in module.imports:
            if not relative.startswith('./') and not relative.startswith('../'):
                raise ModuleError(f'Importacion debe usar ruta relativa: {relative} ({path.name})')
            target = path.parent / relative
            if not target.suffix:
                target = target.with_suffix('.cps')
            dependency = visit(target)
            for name in names:
                if name not in dependency.exports:
                    raise ModuleError(f"'{name}' no esta exportado por {dependency.path.name} (importado desde {path.name})")
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
    return '\n'.join(f'// modulo: {m.path.name}\n{m.source}' for m in order)

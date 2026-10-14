"""
activation_record.py — Registros de activación y layouts de memoria.

Arma, a partir de la tabla de símbolos y de los temporales que usó cada
función, el reporte de cómo queda organizada la memoria:

  * datos globales (offsets de las variables globales)
  * registro de activación de cada función
  * layout de cada clase (atributos y sus offsets)

Registro de activación (direcciones bajas a altas):

  fp+0    valor de retorno
  fp+4    dirección de retorno
  fp+8    enlace de control  (fp del llamador)
  fp+12   enlace de acceso   (fp del ámbito léxico que define la función)
  fp+16   parámetros (en un método, `this` va primero)
          variables locales
          temporales
"""

from compiscript.symbol_table import WORD, FRAME_HEADER

HEADER = [
    (0, "valor de retorno"),
    (4, "dirección de retorno"),
    (8, "enlace de control"),
    (12, "enlace de acceso"),
]


class ActivationRecord:
    def __init__(self, label, depth):
        self.label = label
        self.depth = depth
        self.slots = []          # [(offset, rol, [nombres])]
        self.symbols_end = FRAME_HEADER
        self.temps = 0

    @property
    def size(self):
        return self.symbols_end + self.temps * WORD

    @classmethod
    def from_scope(cls, label, scope, temps):
        """Registro de una función a partir de su scope y la cantidad de temporales usados."""
        rec = cls(label, scope.depth)
        by_offset = {}

        def collect(s):
            for sym in s.symbols.values():
                if sym.kind in ("variable", "const", "parameter") and sym.storage in ("local", "param"):
                    by_offset.setdefault(sym.offset, []).append(sym)
            for child in s.children:
                if child.kind not in ("function", "class"):
                    collect(child)

        collect(scope)
        for offset in sorted(by_offset):
            syms = by_offset[offset]
            role = "parámetro" if all(s.kind == "parameter" for s in syms) else "local"
            names = []
            for s in syms:
                if s.name not in names:
                    names.append(s.name)
            rec.slots.append((offset, role, names))
        rec.symbols_end = max(scope.frame_size, FRAME_HEADER)
        rec.temps = temps
        return rec

    @classmethod
    def synthetic(cls, label, depth, params, temps):
        """Registro de una función generada por el compilador (por ejemplo la que inicializa atributos)."""
        rec = cls(label, depth)
        for i, name in enumerate(params):
            rec.slots.append((FRAME_HEADER + i * WORD, "parámetro", [name]))
        rec.symbols_end = FRAME_HEADER + len(params) * WORD
        rec.temps = temps
        return rec

    def format(self):
        lines = [f"{self.label}  (nivel {self.depth}, {self.size} bytes)"]
        for offset, role in HEADER:
            lines.append(f"  fp+{offset:<4} {role}")
        for offset, role, names in self.slots:
            shared = "  (comparten espacio)" if len(names) > 1 else ""
            lines.append(f"  fp+{offset:<4} {role} {', '.join(names)}{shared}")
        for i in range(self.temps):
            lines.append(f"  fp+{self.symbols_end + i * WORD:<4} temporal t{i}")
        return "\n".join(lines)


def global_area(table):
    """Líneas del área de datos globales."""
    syms = []

    def collect(scope):
        for sym in scope.symbols.values():
            if sym.kind in ("variable", "const") and sym.storage == "global":
                syms.append(sym)
        for child in scope.children:
            if child.kind not in ("function", "class"):
                collect(child)

    collect(table.global_scope)
    lines = [f"Datos globales  ({table.global_size()} bytes)"]
    for sym in sorted(syms, key=lambda s: s.offset):
        lines.append(f"  global+{sym.offset:<4} {sym.name}")
    if not syms:
        lines.append("  (sin variables globales)")
    return "\n".join(lines)


def class_layouts(table):
    """Líneas con el layout de cada clase, incluyendo los atributos heredados."""
    classes = {}
    for scope in table.all_scopes:
        if scope.kind == "class" and scope.class_symbol is not None:
            classes[scope.class_symbol.name] = scope.class_symbol

    blocks = []
    for name, sym in classes.items():
        chain = []
        cur = sym
        while cur is not None:
            chain.append(cur)
            cur = classes.get(cur.parent_class) if cur.parent_class else None
        fields = []
        for c in reversed(chain):
            for attr in c.attributes.values():
                fields.append((attr.offset, attr.name, c.name))
        header = f"Clase {name}  (objeto de {sym.size} bytes)"
        if sym.parent_class:
            header += f"  hereda de {sym.parent_class}"
        lines = [header]
        for offset, field, origin in sorted(fields):
            where = "" if origin == name else f"  (de {origin})"
            lines.append(f"  obj+{offset:<4} {field}{where}")
        if not fields:
            lines.append("  (sin atributos)")
        for m in sym.methods.values():
            lines.append(f"  método {m.name} -> {m.label}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def full_report(table, records):
    """Reporte completo de memoria: globales, clases y un registro por función."""
    parts = [global_area(table)]
    layouts = class_layouts(table)
    if layouts:
        parts.append(layouts)
    for rec in records:
        parts.append("Registro de activación: " + rec.format())
    return "\n\n".join(parts)

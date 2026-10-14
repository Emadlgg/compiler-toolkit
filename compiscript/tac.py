"""
tac.py — Código de tres direcciones (TAC) de Compiscript.

Operandos
---------
  tN        temporal (vive en el registro de activación de la función)
  5, "a"    constantes: enteros, cadenas, true, false, null
  x         variable global, o local/parámetro de la función actual
  x@k       variable de una función que contiene a la actual, k niveles léxicos
            más arriba (se llega siguiendo k enlaces de acceso)

Instrucciones
-------------
  x = y                 copia
  x = y op z            binaria: + - * / %  == != < <= > >=  y  concat
  x = -y   x = !y       unaria
  L:                    etiqueta
  goto L                salto incondicional
  if x goto L           salta si x es verdadero
  ifFalse x goto L      salta si x es falso
  if x op y goto L      salto condicional con comparación
  param x               empuja un argumento
  call f, n             llamada con n argumentos (los últimos n 'param')
  x = call f, n         llamada con valor de retorno
  return [x]            retorna (con valor opcional)
  x = a[i]              lectura de lista (i es índice de elemento)
  a[i] = x              escritura de lista
  x = o.campo           lectura de atributo (desplazamiento en el comentario)
  o.campo = x           escritura de atributo
  x = new C, n          crea un objeto de n bytes
  x = newarray n        crea una lista de n elementos
  x = len a             cantidad de elementos de una lista
  enter n               reserva el registro de activación (n bytes)
  halt                  fin del programa

La sintaxis completa y ejemplos de traducción están en docs/CI.md.
"""

import re


# ── Operandos ─────────────────────────────────────────────

class Temp:
    def __init__(self, n):
        self.n = n

    def __str__(self):
        return f"t{self.n}"

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Temp) and other.n == self.n

    def __hash__(self):
        return hash(("t", self.n))


class Const:
    def __init__(self, value):
        self.value = value       # int | bool | str | None

    def __str__(self):
        v = self.value
        if v is None:
            return "null"
        if v is True:
            return "true"
        if v is False:
            return "false"
        if isinstance(v, str):
            return '"' + v + '"'
        return str(v)

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Const) and type(other.value) is type(self.value) and other.value == self.value

    def __hash__(self):
        return hash(("c", repr(self.value)))


class Var:
    """Variable con nombre. `sym` es el símbolo de la tabla (offset, storage)."""

    def __init__(self, name, sym=None, hops=0):
        self.name = name
        self.sym = sym
        self.hops = hops

    def __str__(self):
        return f"{self.name}@{self.hops}" if self.hops else self.name

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Var) and other.name == self.name and other.hops == self.hops and other.sym is self.sym

    def __hash__(self):
        return hash(("v", self.name, self.hops))


# ── Instrucciones ─────────────────────────────────────────

class Instr:
    dest = None
    comment = ""

    def operands(self):
        return []


class Copy(Instr):
    def __init__(self, dest, src):
        self.dest, self.src = dest, src

    def __str__(self):
        return f"{self.dest} = {self.src}"


class Binary(Instr):
    def __init__(self, dest, op, left, right):
        self.dest, self.op, self.left, self.right = dest, op, left, right

    def __str__(self):
        if self.op == "concat":
            return f"{self.dest} = concat {self.left}, {self.right}"
        return f"{self.dest} = {self.left} {self.op} {self.right}"


class Unary(Instr):
    def __init__(self, dest, op, src):
        self.dest, self.op, self.src = dest, op, src

    def __str__(self):
        return f"{self.dest} = {self.op}{self.src}"


class Label(Instr):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}:"


class Goto(Instr):
    def __init__(self, label):
        self.label = label

    def __str__(self):
        return f"goto {self.label}"


class IfGoto(Instr):
    def __init__(self, cond, label, negate=False):
        self.cond, self.label, self.negate = cond, label, negate

    def __str__(self):
        word = "ifFalse" if self.negate else "if"
        return f"{word} {self.cond} goto {self.label}"


class IfRel(Instr):
    def __init__(self, left, op, right, label):
        self.left, self.op, self.right, self.label = left, op, right, label

    def __str__(self):
        return f"if {self.left} {self.op} {self.right} goto {self.label}"


class Param(Instr):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"param {self.value}"


class Call(Instr):
    def __init__(self, dest, target, nargs, link=None):
        self.dest, self.target, self.nargs, self.link = dest, target, nargs, link

    def __str__(self):
        prefix = f"{self.dest} = " if self.dest is not None else ""
        suffix = f", link={self.link}" if self.link is not None else ""
        return f"{prefix}call {self.target}, {self.nargs}{suffix}"


class Return(Instr):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return "return" if self.value is None else f"return {self.value}"


class LoadIndex(Instr):
    def __init__(self, dest, base, index):
        self.dest, self.base, self.index = dest, base, index

    def __str__(self):
        return f"{self.dest} = {self.base}[{self.index}]"


class StoreIndex(Instr):
    def __init__(self, base, index, src):
        self.base, self.index, self.src = base, index, src

    def __str__(self):
        return f"{self.base}[{self.index}] = {self.src}"


class LoadField(Instr):
    def __init__(self, dest, obj, field, offset):
        self.dest, self.obj, self.field, self.offset = dest, obj, field, offset
        self.comment = f"offset +{offset}"

    def __str__(self):
        return f"{self.dest} = {self.obj}.{self.field}"


class StoreField(Instr):
    def __init__(self, obj, field, offset, src):
        self.obj, self.field, self.offset, self.src = obj, field, offset, src
        self.comment = f"offset +{offset}"

    def __str__(self):
        return f"{self.obj}.{self.field} = {self.src}"


class New(Instr):
    def __init__(self, dest, cls, size):
        self.dest, self.cls, self.size = dest, cls, size

    def __str__(self):
        return f"{self.dest} = new {self.cls}, {self.size}"


class NewArray(Instr):
    def __init__(self, dest, count):
        self.dest, self.count = dest, count

    def __str__(self):
        return f"{self.dest} = newarray {self.count}"


class Len(Instr):
    def __init__(self, dest, array):
        self.dest, self.array = dest, array

    def __str__(self):
        return f"{self.dest} = len {self.array}"


class FuncBegin(Instr):
    def __init__(self, label, depth=0):
        self.label, self.depth, self.size = label, depth, 0

    def __str__(self):
        return f"func {self.label}:"

    @property
    def comment(self):
        return f"nivel {self.depth}, registro de {self.size} bytes"


class Enter(Instr):
    def __init__(self, size=0):
        self.size = size

    def __str__(self):
        return f"enter {self.size}"


class Halt(Instr):
    def __str__(self):
        return "halt"


# Instrucciones cuyo destino se puede redirigir (ver CodeGenerator.assign_to)
RETARGETABLE = (Binary, Unary, LoadIndex, LoadField, Len, Call, NewArray)


# ── Salida ────────────────────────────────────────────────

_COMMENT_COLUMN = 38


def format_instr(instr):
    """Una instrucción con su sangría y su comentario."""
    text = str(instr)
    if isinstance(instr, FuncBegin):
        line = text
    elif isinstance(instr, Label):
        line = "  " + text
    else:
        line = "    " + text
    if instr.comment:
        line = f"{line:<{_COMMENT_COLUMN}} ; {instr.comment}"
    return line


def format_program(instructions):
    """Programa completo; deja una línea en blanco entre funciones."""
    lines = []
    for instr in instructions:
        if isinstance(instr, FuncBegin) and lines:
            lines.append("")
        lines.append(format_instr(instr))
    return "\n".join(lines)


_RESERVED = re.compile(r"^(t\d+|L\d+)$")
_KEYWORDS = {"concat", "goto", "ifFalse", "param", "call", "newarray", "len", "enter", "halt", "func", "link"}


def safe_name(name):
    """
    Evita que una variable del usuario se confunda con un temporal, una
    etiqueta o el nombre de una instrucción (`concat = concat a, b` es válido
    pero ilegible).
    """
    return name + "_v" if _RESERVED.match(name) or name in _KEYWORDS else name

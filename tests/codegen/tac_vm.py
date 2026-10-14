"""
tac_vm.py — Intérprete mínimo de TAC, solo para la batería de pruebas.

Ejecuta las instrucciones que produce el generador y devuelve lo que el
programa imprime. Sirve para comprobar que el código intermedio hace lo que
debe, no solo que "se ve bien". Respeta la organización de memoria real:

  * las variables globales viven en un área de datos, en su offset
  * cada llamada crea un registro de activación con sus parámetros desde fp+16
    y un enlace de acceso (el que indica `call f, n, link=k`)
  * x@k sigue k enlaces de acceso antes de leer el offset de x
  * los temporales son locales a cada registro de activación
"""

from compiscript.tac import (
    Temp, Const, Var,
    Copy, Binary, Unary, Label, Goto, IfGoto, IfRel, Param, Call, Return,
    LoadIndex, StoreIndex, LoadField, StoreField, New, NewArray, Len,
    FuncBegin, Enter, Halt,
)
from compiscript.symbol_table import FRAME_HEADER, WORD


class VMError(Exception):
    pass


class Frame:
    def __init__(self, static_link):
        self.mem = {}
        self.temps = {}
        self.static_link = static_link


class Obj:
    def __init__(self, cls):
        self.cls = cls
        self.fields = {}


def show(value):
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def truncating_div(a, b):
    if b == 0:
        raise VMError("división entre cero")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


BINARY = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": truncating_div,
    "%": lambda a, b: a - truncating_div(a, b) * b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "concat": lambda a, b: a + b,
}


class TacVM:
    def __init__(self, instructions, max_steps=500_000):
        self.funcs = {}
        self.entry = None
        current = None
        for instr in instructions:
            if isinstance(instr, FuncBegin):
                current = (instr.label, [], {})
                self.funcs[instr.label] = current
                self.entry = self.entry or instr.label
            current[1].append(instr)
            if isinstance(instr, Label):
                current[2][instr.name] = len(current[1]) - 1
        self.globals = {}
        self.params = []
        self.output = []
        self.steps = 0
        self.max_steps = max_steps

    def run(self):
        self.call(self.entry, [], None)
        return self.output

    # ── memoria ───────────────────────────────────────────

    def _locate(self, frame, var):
        if var.sym is not None and var.sym.storage == "global":
            return self.globals, var.sym.offset
        target = frame
        for _ in range(var.hops):
            if target.static_link is None:
                raise VMError(f"{var}: no hay enlace de acceso")
            target = target.static_link
        offset = FRAME_HEADER if var.sym is None else var.sym.offset     # `this` es el primer parámetro
        return target.mem, offset

    def read(self, frame, op):
        if isinstance(op, Const):
            return op.value
        if isinstance(op, Temp):
            if op.n not in frame.temps:
                raise VMError(f"se lee {op} antes de asignarlo")
            return frame.temps[op.n]
        memory, offset = self._locate(frame, op)
        return memory.get(offset, 0)

    def write(self, frame, op, value):
        if isinstance(op, Temp):
            frame.temps[op.n] = value
            return
        if isinstance(op, Var):
            memory, offset = self._locate(frame, op)
            memory[offset] = value
            return
        raise VMError(f"destino inválido: {op}")

    # ── ejecución ─────────────────────────────────────────

    def call(self, label, args, static_link):
        if label not in self.funcs:
            raise VMError(f"función inexistente: {label}")
        _, code, labels = self.funcs[label]
        frame = Frame(static_link)
        for i, value in enumerate(args):
            frame.mem[FRAME_HEADER + i * WORD] = value
        pc = 0
        while pc < len(code):
            instr = code[pc]
            pc += 1
            self.steps += 1
            if self.steps > self.max_steps:
                raise VMError("se superó el límite de pasos (¿bucle infinito?)")
            kind = type(instr)
            if kind in (FuncBegin, Enter, Label):
                continue
            if kind is Copy:
                self.write(frame, instr.dest, self.read(frame, instr.src))
            elif kind is Binary:
                self.write(frame, instr.dest, BINARY[instr.op](self.read(frame, instr.left), self.read(frame, instr.right)))
            elif kind is Unary:
                value = self.read(frame, instr.src)
                self.write(frame, instr.dest, -value if instr.op == "-" else (not value))
            elif kind is Goto:
                pc = labels[instr.label]
            elif kind is IfGoto:
                if bool(self.read(frame, instr.cond)) != instr.negate:
                    pc = labels[instr.label]
            elif kind is IfRel:
                if BINARY[instr.op](self.read(frame, instr.left), self.read(frame, instr.right)):
                    pc = labels[instr.label]
            elif kind is Param:
                self.params.append(self.read(frame, instr.value))
            elif kind is Call:
                n = instr.nargs
                args = self.params[len(self.params) - n:] if n else []
                del self.params[len(self.params) - n:]
                if instr.target == "print":
                    self.output.append(show(args[0]))
                    result = None
                else:
                    link = None
                    if instr.link is not None:
                        link = frame
                        for _ in range(instr.link):
                            link = link.static_link
                    result = self.call(instr.target, args, link)
                if instr.dest is not None:
                    self.write(frame, instr.dest, result)
            elif kind is Return:
                return None if instr.value is None else self.read(frame, instr.value)
            elif kind is Halt:
                return None
            elif kind is LoadIndex:
                self.write(frame, instr.dest, self._array(frame, instr.base)[self._index(frame, instr)])
            elif kind is StoreIndex:
                self._array(frame, instr.base)[self._index(frame, instr)] = self.read(frame, instr.src)
            elif kind is LoadField:
                self.write(frame, instr.dest, self._object(frame, instr.obj).fields.get(instr.offset, 0))
            elif kind is StoreField:
                self._object(frame, instr.obj).fields[instr.offset] = self.read(frame, instr.src)
            elif kind is New:
                self.write(frame, instr.dest, Obj(instr.cls))
            elif kind is NewArray:
                self.write(frame, instr.dest, [0] * self.read(frame, instr.count))
            elif kind is Len:
                self.write(frame, instr.dest, len(self._array(frame, instr.array)))
            else:
                raise VMError(f"instrucción desconocida: {instr}")
        return None

    def _array(self, frame, op):
        value = self.read(frame, op)
        if not isinstance(value, list):
            raise VMError(f"{op} no es una lista")
        return value

    def _index(self, frame, instr):
        i = self.read(frame, instr.index)
        if not isinstance(i, int) or i < 0:
            raise VMError(f"índice inválido: {i}")
        return i

    def _object(self, frame, op):
        value = self.read(frame, op)
        if not isinstance(value, Obj):
            raise VMError(f"{op} no es un objeto")
        return value

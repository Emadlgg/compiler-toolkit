"""Asignador determinista de registros MIPS.

Dos conjuntos, un mismo algoritmo getReg():
  * $t0-$t7 (por defecto): scratch dentro de una instruccion TAC. Los valores
    temporales se guardan en su slot de pila al terminar la instruccion.
  * $s0-$s7 (SAVED_REGISTERS): variables locales y parametros "calientes" que
    viven en registro durante toda la funcion (el llamado los guarda y los
    restaura, porque son registros preservados).
Si no quedan registros libres se expulsa uno (callback `spill`) hacia la pila.
"""

TEMP_REGISTERS = tuple(f'$t{i}' for i in range(8))
SAVED_REGISTERS = tuple(f'$s{i}' for i in range(8))


class RegisterAllocationError(RuntimeError):
    pass


class RegisterAllocator:
    REGISTERS = TEMP_REGISTERS

    def __init__(self, spill=None, registers=None):
        self.registers = tuple(registers) if registers else self.REGISTERS
        self.used = set()
        self.owners = {}
        self.dirty = set()
        self.spill = spill
        self._next_victim = 0

    def getReg(self, owner=None, dirty=False):
        if owner is not None:
            for reg, value in self.owners.items():
                if value == owner:
                    if dirty:
                        self.dirty.add(reg)
                    return reg
        for reg in self.registers:
            if reg not in self.used:
                return self._claim(reg, owner, dirty)
        if self.spill is None:
            raise RegisterAllocationError('Sin registros: falta callback de spill')
        reg = self.registers[self._next_victim]
        self._next_victim = (self._next_victim + 1) % len(self.registers)
        if reg in self.dirty:
            if reg not in self.owners:
                raise RegisterAllocationError('Registro sucio sin propietario')
            self.spill(self.owners[reg], reg)
        return self._claim(reg, owner, dirty)

    def _claim(self, reg, owner, dirty):
        self.used.add(reg)
        self.owners.pop(reg, None)
        self.dirty.discard(reg)
        if owner is not None:
            self.owners[reg] = owner
        if dirty:
            self.dirty.add(reg)
        return reg

    def release(self, *registers):
        for reg in registers:
            self.used.discard(reg)
            self.owners.pop(reg, None)
            self.dirty.discard(reg)

    def flush(self):
        if self.dirty and self.spill is None:
            raise RegisterAllocationError('No se pueden guardar registros sin callback')
        for reg in self.registers:
            if reg in self.dirty:
                self.spill(self.owners[reg], reg)
                self.dirty.remove(reg)

    def clear(self):
        self.used.clear()
        self.owners.clear()
        self.dirty.clear()
        self._next_victim = 0

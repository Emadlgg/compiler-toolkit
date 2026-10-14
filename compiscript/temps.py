"""
temps.py — Asignación y reciclaje de variables temporales.

Cada función tiene su propio pool: los temporales viven en su registro de
activación, así que dos funciones pueden usar t0 sin conflicto.

Algoritmo
---------
  new()   entrega el temporal libre de menor índice; si no hay ninguno
          libre, crea uno nuevo.
  free(t) devuelve un temporal al pool apenas su valor fue consumido.

El generador libera los operandos de una instrucción antes de pedir el
temporal de su resultado, de modo que el resultado puede reutilizar el de
un operando (por ejemplo `t0 = t0 + t1`). `count` es la cantidad máxima de
temporales distintos que se necesitaron y es lo que se suma al tamaño del
registro de activación.
"""

from compiscript.tac import Temp


class TempPool:
    def __init__(self):
        self._free = []        # índices libres
        self._in_use = set()
        self.count = 0         # índices creados en total (máximo simultáneo)

    def new(self):
        if self._free:
            n = min(self._free)
            self._free.remove(n)
        else:
            n = self.count
            self.count += 1
        self._in_use.add(n)
        return Temp(n)

    def free(self, operand):
        """Libera `operand` si es un temporal; con cualquier otro operando no hace nada."""
        if not isinstance(operand, Temp):
            return
        if operand.n in self._in_use:
            self._in_use.remove(operand.n)
            self._free.append(operand.n)

    def in_use(self):
        return sorted(self._in_use)

"""Emisor sencillo de secciones de ensamblador."""

class MIPSEmitter:
    def __init__(self):
        self.data = []
        self.text = []

    def emit(self, *lines):
        self.text.extend(lines)

    def render(self):
        return '\n'.join(['.data', *self.data, '', '.text', '.globl main', *self.text, ''])

"""Los registros $s (preservados) se usan, se guardan y se restauran correctamente."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from compiscript.mips.registers import RegisterAllocator, SAVED_REGISTERS

ROOT = Path(__file__).resolve().parent.parent.parent
CASE = ROOT / 'tests' / 'mips' / 'cases' / 'ok' / '09_registros_s.cps'


def compile_case():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / 'p.asm'
        subprocess.run([sys.executable, str(ROOT / 'compiscript.py'), str(CASE), '--mips',
                        '--output', str(out)], cwd=ROOT, check=True, capture_output=True)
        return out.read_text(encoding='utf-8')


def block(asm, label):
    start = asm.index(f'\n{label}:') + 1
    end = asm.find('\n\n', start)
    return asm[start:end if end > 0 else None]


class TestSavedRegisters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asm = compile_case()

    def test_loop_variables_live_in_s_registers(self):
        body = block(self.asm, 'suma')
        self.assertIn('sw $s0, -4($fp)', body)      # guarda el $s del llamador
        self.assertIn('lw $s0, -4($fp)', body)      # y lo restaura antes de volver
        self.assertRegex(body, r'move \$s\d, \$t\d')  # escrituras a variables en registro

    def test_at_most_eight_saved_registers(self):
        body = block(self.asm, 'diez')
        used = {r for r in SAVED_REGISTERS if r in body}
        self.assertEqual(len(used), 8)              # 12 variables, solo 8 caben

    def test_captured_variable_stays_in_memory(self):
        # 'total' la modifica la funcion anidada por enlace estatico ($t9 = fp del
        # dueño): si estuviera en un $s, la anidada no la veria. La salida correcta
        # (10) la comprueba la bateria e2e; aqui se verifica el acceso por memoria.
        self.assertRegex(self.asm, r'lw \$t9, 12\(\$t9\)\n  lw \$t\d, \d+\(\$t9\)')
        self.assertRegex(self.asm, r'sw \$t\d, \d+\(\$t9\)')

    def test_allocator_with_saved_pool(self):
        alloc = RegisterAllocator(registers=SAVED_REGISTERS)
        regs = [alloc.getReg(owner=i) for i in range(8)]
        self.assertEqual(regs, list(SAVED_REGISTERS))
        self.assertEqual(alloc.getReg(owner=3), '$s3')  # mismo propietario, mismo registro


if __name__ == '__main__':
    unittest.main()

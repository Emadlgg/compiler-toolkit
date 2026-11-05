"""Incremento 10: pruebas integrales CLI -> TAC -> MIPS -> MARS.

No altera el compilador. Si MARS no esta disponible, solo se omiten
las comprobaciones que necesitan ejecutar ensamblador.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from compiscript.mars import find_mars, java_available

ROOT = Path(__file__).resolve().parents[2]
CLASSES = ROOT / 'tests' / 'classes' / 'fixtures' / 'main.cps'


def run_command(args, timeout=45):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    return subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                          text=True, encoding='utf-8', errors='replace', timeout=timeout)


def compile_cps(source, output):
    return run_command([sys.executable, str(ROOT / 'compiscript.py'),
                        str(source), '--mips', '--output', str(output)])


def mars_jar():
    return find_mars() if java_available() else None


class TestIncrement10(unittest.TestCase):
    def test_advanced_classes_generate_assembly(self):
        with tempfile.TemporaryDirectory() as temp:
            asm = Path(temp) / 'advanced.asm'
            result = compile_cps(CLASSES, asm)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(asm.is_file())
            text = asm.read_text(encoding='utf-8')
            self.assertIn('.text', text)
            self.assertIn('jal ', text)

    def test_advanced_classes_execute_in_mars(self):
        jar = mars_jar()
        if jar is None:
            self.skipTest('Configura MARS_JAR o coloca tools/Mars.jar')
        with tempfile.TemporaryDirectory() as temp:
            asm = Path(temp) / 'advanced.asm'
            compiled = compile_cps(CLASSES, asm)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            executed = run_command(['java', '-jar', str(jar), 'nc', str(asm)])
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            self.assertEqual(executed.stdout.replace("\n", ""), '101001320012920011')

    def test_missing_import_does_not_create_assembly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'main.cps'
            source.write_text('import { Inexistente } from "./faltante";\nprint(1);\n', encoding='utf-8')
            asm = root / 'missing.asm'
            result = compile_cps(source, asm)
            self.assertFalse(asm.exists(), result.stdout + result.stderr)
            self.assertTrue(result.returncode != 0 or 'error' in
                            (result.stdout + result.stderr).lower())

    def test_invalid_member_does_not_create_assembly(self):
        with tempfile.TemporaryDirectory() as temp:
            asm = Path(temp) / 'invalid.asm'
            source = ROOT / 'tests' / 'classes' / 'fixtures' / 'invalid_member.cps'
            result = compile_cps(source, asm)
            self.assertFalse(asm.exists(), result.stdout + result.stderr)
            self.assertTrue(result.returncode != 0 or 'error' in
                            (result.stdout + result.stderr).lower())

    def test_runtime_division_by_zero(self):
        jar = mars_jar()
        if jar is None:
            self.skipTest('Configura MARS_JAR o coloca tools/Mars.jar')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'division.cps'
            source.write_text('let divisor: integer = 0;\nprint(10 / divisor);\n', encoding='utf-8')
            asm = root / 'division.asm'
            compiled = compile_cps(source, asm)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            executed = run_command(['java', '-jar', str(jar), 'nc', str(asm)])
            self.assertIn('Division by zero', executed.stdout + executed.stderr)


if __name__ == '__main__':
    unittest.main()

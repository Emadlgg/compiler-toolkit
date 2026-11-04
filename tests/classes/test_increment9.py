"""Pruebas de clases entre modulos: analisis, TAC, MIPS y ejecucion opcional.

MARS_JAR puede apuntar a tools/Mars.jar. Sin MARS se omite SOLO la
prueba de ejecucion; la compilacion se verifica igualmente.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compiscript.modules import resolve_project

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / 'fixtures'
EXPECTED = '101001320012920011'


def compile_file(source, output=None):
    cmd = [sys.executable, str(ROOT / 'compiscript.py'), str(source)]
    if output is not None:
        cmd += ['--mips', '--output', str(output)]
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', env=env, timeout=45)


class TestAdvancedClasses(unittest.TestCase):
    def test_resolution_and_deduplication(self):
        source = resolve_project(FIXTURES / 'main.cps')
        self.assertEqual(source.count('class Base {'), 1)
        self.assertEqual(source.count('class Derivada : Base'), 1)
        self.assertEqual(source.count('class Nieta : Derivada'), 1)
        self.assertLess(source.index('class Base {'), source.index('class Derivada : Base'))
        self.assertLess(source.index('class Derivada : Base'), source.index('class Nieta : Derivada'))

    def test_compile_advanced_classes(self):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / 'clases.asm'
            result = compile_file(FIXTURES / 'main.cps', asm)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(asm.is_file(), result.stdout + result.stderr)
            code = asm.read_text(encoding='utf-8')
            self.assertIn('.text', code)
            self.assertIn('jal ', code)
            self.assertIn('syscall', code)

    def test_invalid_member_rejected(self):
        result = compile_file(FIXTURES / 'invalid_member.cps')
        output = result.stdout + result.stderr
        self.assertTrue('error' in output.lower() or result.returncode != 0, output)

    def test_invalid_constructor_rejected(self):
        result = compile_file(FIXTURES / 'invalid_constructor.cps')
        output = result.stdout + result.stderr
        self.assertTrue('error' in output.lower() or result.returncode != 0, output)

    def test_mars_advanced_classes(self):
        jar = os.environ.get('MARS_JAR')
        if not jar:
            local = ROOT / 'tools' / 'Mars.jar'
            jar = str(local) if local.is_file() else None
        if not jar or not Path(jar).is_file():
            self.skipTest('Configurar MARS_JAR o tools/Mars.jar para validar ejecucion')
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / 'clases.asm'
            result = compile_file(FIXTURES / 'main.cps', asm)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(asm.exists(), result.stdout + result.stderr)
            mars = subprocess.run(['java', '-jar', jar, 'nc', str(asm)], cwd=ROOT,
                                  capture_output=True, text=True, encoding='utf-8',
                                  errors='replace', timeout=45)
            self.assertEqual(mars.returncode, 0, mars.stdout + mars.stderr)
            self.assertEqual(mars.stdout.strip(), EXPECTED, mars.stdout + mars.stderr)


if __name__ == '__main__':
    unittest.main()

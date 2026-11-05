"""End-to-end tests for reusable compiled Compiscript classes (20E).

These tests deliberately compile the producer once, remove its source, then
compile and execute the consumer. They are integration tests, not mocks.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'compiscript.py'
MARS_LOCAL = ROOT / 'tools' / 'Mars.jar'

CLASS_SOURCE = '''export class Contador {
    let valor: integer;

    function constructor(inicial: integer) {
        this.valor = inicial;
    }

    function sumar(cantidad: integer): integer {
        this.valor = this.valor + cantidad;
        return this.valor;
    }

    function obtener(): integer {
        return this.valor;
    }
}
'''


def run_command(*args):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    return subprocess.run([str(a) for a in args], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding='utf-8', errors='replace', timeout=40)


class TestCompiledClassesE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cps-compiled-e2e-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'Contador.cps'
        self.package = self.base / 'Contador.cplobj'
        self.source.write_text(CLASS_SOURCE, encoding='utf-8')

    def build_library(self):
        result = run_command(sys.executable, CLI, self.source, '--build-library',
                             '--output', self.package)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.package.is_file(), 'No se genero el paquete .cplobj')
        return result

    def compile_consumer(self, code):
        source = self.base / 'main.cps'
        output = self.base / 'program.asm'
        source.write_text(code, encoding='utf-8')
        result = run_command(sys.executable, CLI, source, '--mips', '--output', output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(output.is_file(), 'No se genero el ensamblador')
        return output

    def execute(self, asm, expected):
        jar = Path(os.environ.get('MARS_JAR', str(MARS_LOCAL)))
        if not jar.is_file():
            self.skipTest('MARS no disponible: configure MARS_JAR o tools/Mars.jar')
        result = run_command('java', '-jar', jar, 'nc', asm)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.replace("\n", ""), expected)

    def test_package_compiles_without_consumer(self):
        self.build_library()

    def test_constructor_method_parameter_and_return_without_source(self):
        self.build_library()
        self.source.unlink()
        asm = self.compile_consumer('''import { Contador } from "./Contador.cplobj";
let c = new Contador(7);
print(c.sumar(5));
print(c.obtener());
''')
        self.execute(asm, '1212')

    def test_two_independent_instances(self):
        self.build_library()
        self.source.unlink()
        asm = self.compile_consumer('''import { Contador } from "./Contador.cplobj";
let a = new Contador(3);
let b = new Contador(20);
print(a.sumar(2));
print(b.sumar(4));
print(a.obtener());
''')
        self.execute(asm, '5245')

    def test_import_alias_and_method_call(self):
        self.build_library()
        self.source.unlink()
        asm = self.compile_consumer('''import { Contador as Cuenta } from "./Contador.cplobj";
let c = new Cuenta(9);
print(c.sumar(1));
''')
        self.execute(asm, '10')


if __name__ == '__main__':
    unittest.main()

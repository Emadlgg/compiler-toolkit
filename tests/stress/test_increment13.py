"""Pruebas de extremo a extremo para Compiscript -> MIPS -> MARS.

No altera el compilador. Cada caso usa un directorio temporal independiente.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from compiscript.mars import find_mars, java_available

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'compiscript.py'


def command(args, timeout=40):
    env = os.environ.copy()
    env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    return subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                          text=True, encoding='utf-8', errors='replace', timeout=timeout)


def mars():
    return find_mars() if java_available() else None


class TestIncrement13(unittest.TestCase):
    def compile_case(self, source, expected_success=True):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name)
        cps = path / 'main.cps'
        asm = path / 'main.asm'
        cps.write_text(source, encoding='utf-8')
        result = command([sys.executable, str(CLI), str(cps), '--mips', '--output', str(asm)])
        output = result.stdout + result.stderr
        if expected_success:
            self.assertEqual(result.returncode, 0, output)
            self.assertTrue(asm.is_file(), output)
        else:
            self.assertFalse(asm.exists(), output)
            self.assertTrue(result.returncode != 0 or 'error' in output.lower(), output)
        return asm, output

    def run_case(self, source, expected):
        jar = mars()
        if jar is None:
            self.skipTest('MARS no disponible: configura MARS_JAR o tools/Mars.jar')
        asm, _ = self.compile_case(source)
        result = command(['java', '-jar', str(jar), 'nc', str(asm)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.replace("\n", ""), expected)

    def test_recursive_factorial(self):
        self.run_case('''function factorial(n: integer): integer {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);
}
print(factorial(6));
''', '720')

    def test_loop_and_array_mutation(self):
        self.run_case('''let a: integer[] = [2, 4, 6];
let i: integer = 0;
let total: integer = 0;
while (i < 3) {
    total = total + a[i];
    i = i + 1;
}
a[1] = 10;
print(total);
print(a[1]);
''', '1210')

    def test_string_concat(self):
        self.run_case('''let a: string = "Hola";
let b: string = " mundo";
print(a + b);
''', 'Hola mundo')

    def test_null_field_access_reports_runtime_error(self):
        jar = mars()
        if jar is None:
            self.skipTest('MARS no disponible')
        asm, _ = self.compile_case('''class Caja { let valor: integer; }
let caja: Caja = null;
print(caja.valor);
''')
        result = command(['java', '-jar', str(jar), 'nc', str(asm)])
        self.assertIn('Null reference', result.stdout + result.stderr)

    def test_out_of_bounds_reports_runtime_error(self):
        jar = mars()
        if jar is None:
            self.skipTest('MARS no disponible')
        asm, _ = self.compile_case('''let a: integer[] = [1, 2];
print(a[2]);
''')
        result = command(['java', '-jar', str(jar), 'nc', str(asm)])
        self.assertIn('Array index out of bounds', result.stdout + result.stderr)

    def test_negative_array_size_reports_runtime_error(self):
        """Exercise the MIPS backend directly: source grammar has no new integer[n]."""
        jar = mars()
        if jar is None:
            self.skipTest('MARS no disponible')

        from compiscript.activation_record import ActivationRecord
        from compiscript.mips.generator import MIPSGenerator
        from compiscript.tac import Const, Enter, FuncBegin, Halt, NewArray, Temp

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        asm = Path(temp.name) / 'negative_array.asm'

        record = ActivationRecord.synthetic('main', 0, [], 1)
        instructions = [
            FuncBegin('main', 0),
            Enter(record.size),
            NewArray(Temp(0), Const(-1)),
            Halt(),
        ]
        asm.write_text(MIPSGenerator(instructions, [record]).generate(), encoding='utf-8')

        result = command(['java', '-jar', str(jar), 'nc', str(asm)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Invalid array size', result.stdout + result.stderr)

    def test_missing_import_rejected(self):
        self.compile_case('import { X } from "./missing";\nprint(1);\n', False)

    def test_syntax_error_rejected(self):
        self.compile_case('let x: integer = ;\n', False)


if __name__ == '__main__':
    unittest.main()

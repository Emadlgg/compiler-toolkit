"""End-to-end checks for dynamic Compiscript arrays (ANTLR 4.13.2 required)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestDynamicArrays(unittest.TestCase):
    def compile(self, source):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            src = folder / 'main.cps'
            asm = folder / 'main.asm'
            src.write_text(source, encoding='utf-8')
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            proc = subprocess.run(
                [sys.executable, str(ROOT / 'compiscript.py'), str(src),
                 '--mips', '--output', str(asm)],
                cwd=ROOT, env=env, capture_output=True,
                text=True, encoding='utf-8', errors='replace',
            )
            return proc, asm.read_text(encoding='utf-8') if asm.exists() else None

    def test_dynamic_integer_array(self):
        proc, asm = self.compile('''let n: integer = 3;
let a: integer[] = new integer[n];
a[0] = 7;
a[2] = 8;
print(a[0] + a[2]);
''')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIsNotNone(asm)
        self.assertIn('syscall', asm)

    def test_dynamic_boolean_array(self):
        proc, asm = self.compile('''let flags: boolean[] = new boolean[2];
flags[0] = true;
print(flags[0]);
''')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIsNotNone(asm)

    def test_noninteger_size_rejected(self):
        proc, asm = self.compile('''let a: integer[] = new integer[true];''')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIsNone(asm)

    def test_negative_size_compiles_for_runtime_check(self):
        proc, asm = self.compile('''let n: integer = -1;
let a: integer[] = new integer[n];''')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('_mips_size_error', asm)


if __name__ == '__main__':
    unittest.main()

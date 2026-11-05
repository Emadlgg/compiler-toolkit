"""CLI preflight: compiled packages must never be mistaken for source modules."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from compiscript.modules.compiled_package import create_package
from compiscript.modules.interface_metadata import ABI_VERSION
from compiscript.modules.mips_linker import build_object

ROOT = Path(__file__).resolve().parents[2]


class TestCompiledImportCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        (self.dir / 'api.asm').write_text('hello:\n  jr $ra\n', encoding='utf-8')
        build_object(self.dir / 'api.asm', ['hello'], self.dir / 'api.mobj')
        (self.dir / 'api.cps').write_text('function hello(): void {}\n', encoding='utf-8')
        metadata = {'format': ABI_VERSION, 'exports': {'hello': {
            'kind': 'function', 'label': 'hello', 'params': [],
            'return_type': 'void', 'frame_size': 16}}}
        create_package(self.dir / 'api.cps', self.dir / 'api.mobj',
                       self.dir / 'api.cplobj', metadata=metadata)

    def run_cli(self, source):
        (self.dir / 'main.cps').write_text(source, encoding='utf-8')
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        return subprocess.run([sys.executable, str(ROOT / 'compiscript.py'),
                               str(self.dir / 'main.cps'), '--check-compiled-imports'],
                              capture_output=True, text=True, encoding='utf-8',
                              errors='replace', env=env)

    def test_valid_library(self):
        proc = self.run_cli('import { hello as greet } from "./api.cplobj";\n')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('Bibliotecas compiladas verificadas: 1', proc.stdout)
        self.assertIn('no compila ni enlaza', proc.stdout)

    def test_missing_export(self):
        proc = self.run_cli('import { absent } from "./api.cplobj";\n')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('no exportado', proc.stdout)

    def test_missing_package(self):
        proc = self.run_cli('import { hello } from "./missing.cplobj";\n')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('Error de bibliotecas', proc.stdout)


if __name__ == '__main__':
    unittest.main()

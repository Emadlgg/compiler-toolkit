import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess

from gui.cps_source import save_and_resolve
from gui.mips_runner import compile_and_run


class TestIncrement8(unittest.TestCase):
    def test_editor_import_and_current_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Animal.cps').write_text('export class Animal {}', encoding='utf-8')
            main = root / 'main.cps'
            merged = save_and_resolve(main, 'import { Animal } from "./Animal";\nlet a = new Animal();')
            self.assertIn('class Animal', merged)
            self.assertIn('let a = new Animal()', merged)
            self.assertNotIn('import {', merged)
            self.assertIn('import { Animal }', main.read_text(encoding='utf-8'))

    def test_missing_module_reports_error(self):
        from compiscript.modules import ModuleError
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ModuleError):
                save_and_resolve(Path(tmp) / 'main.cps', 'import { X } from "./missing";')

    def test_compiler_subprocess_uses_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'main.cps'
            source.write_text('print(42);', encoding='utf-8')
            output = root / 'main.asm'
            def fake_run(args, **kwargs):
                self.assertEqual(kwargs['env']['PYTHONIOENCODING'], 'utf-8')
                self.assertEqual(kwargs['env']['PYTHONUTF8'], '1')
                output.write_text('.text\nmain:', encoding='utf-8')
                return CompletedProcess(args, 0, 'OK', '')
            with patch('gui.mips_runner.subprocess.run', side_effect=fake_run):
                result = compile_and_run(source, output)
            self.assertTrue(result.ok)


if __name__ == '__main__':
    unittest.main()

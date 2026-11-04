import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess
from gui.mips_runner import compile_and_run


class TestMIPSRunner(unittest.TestCase):
    def test_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            result = compile_and_run(Path(temp) / 'missing.cps', Path(temp) / 'out.asm')
            self.assertFalse(result.ok)

    def test_build(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'main.cps'
            source.write_text('print(42);', encoding='utf-8')
            output = Path(temp) / 'build' / 'main.asm'
            def fake_run(args, **kwargs):
                output.write_text('.text\nmain:', encoding='utf-8')
                return CompletedProcess(args, 0, 'MIPS guardado', '')
            with patch('gui.mips_runner.subprocess.run', side_effect=fake_run):
                result = compile_and_run(source, output)
            self.assertTrue(result.ok)
            self.assertIn('.text', result.asm)

    def test_failed_compile_does_not_reuse_old_asm(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'main.cps'
            source.write_text('bad', encoding='utf-8')
            output = Path(temp) / 'main.asm'
            output.write_text('OLD', encoding='utf-8')
            with patch('gui.mips_runner.subprocess.run', return_value=CompletedProcess([], 1, 'syntax error', '')):
                result = compile_and_run(source, output)
            self.assertFalse(result.ok)
            self.assertIsNone(result.asm)
            self.assertFalse(output.exists())

    def test_mars_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'main.cps'
            source.write_text('print(42);', encoding='utf-8')
            output = Path(temp) / 'main.asm'
            def fake_run(args, **kwargs):
                output.write_text('.text', encoding='utf-8')
                return CompletedProcess(args, 0, '', '')
            with patch('gui.mips_runner.subprocess.run', side_effect=fake_run):
                result = compile_and_run(source, output, run=True, mars_jar=str(Path(temp) / 'none.jar'))
            self.assertFalse(result.ok)
            self.assertTrue(result.executed)
            self.assertIsNotNone(result.asm)

if __name__ == '__main__':
    unittest.main()

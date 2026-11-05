import tempfile
import unittest
from pathlib import Path
from gui.ide_diagnostics import format_problem_detail, source_matches_path


class TestIDEIncrement121(unittest.TestCase):
    def test_long_message_not_truncated(self):
        msg = 'No se pudo leer el modulo: ' + 'carpeta/' * 100
        result = format_problem_detail('SINTACTICO', 12, 5, msg, Path('clases/Perro.cps'))
        self.assertIn(msg, result)
        self.assertIn('Perro.cps', result)
        self.assertIn('12', result)

    def test_editor_path_consistency(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'main.cps'
            path.write_text('print(42);\n', encoding='utf-8')
            self.assertTrue(source_matches_path('print(42);', path))
            self.assertFalse(source_matches_path('print(7);', path))
            self.assertFalse(source_matches_path('print(42);', Path(temp) / 'missing.cps'))


if __name__ == '__main__':
    unittest.main()

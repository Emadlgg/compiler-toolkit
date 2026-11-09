"""TEST MIPS: la salida de tests/mips/run_tests.py debe poder leerla la pestana Pruebas CPS."""
import ast, re, subprocess, sys, textwrap, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / 'gui' / 'app.py').read_text(encoding='utf-8')


def _gui_parser():
    """Extrae _parse_cps_tests de gui/app.py sin importar Tkinter."""
    tree = ast.parse(APP)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_parse_cps_tests':
            node.decorator_list = []
            module = ast.Module(body=[node], type_ignores=[])
            namespace = {'re': re}
            exec(compile(ast.fix_missing_locations(module), 'app.py', 'exec'), namespace)
            return namespace['_parse_cps_tests']
    raise AssertionError('No se encontro _parse_cps_tests en gui/app.py')


class TestMipsTestsButton(unittest.TestCase):
    def test_button_is_wired(self):
        self.assertIn("self._sidebar_actions['TEST MIPS']", APP)
        self.assertIn("'TEST CPS', 'TEST MIPS'", APP)
        self.assertIn('def _run_mips_tests', APP)
        self.assertIn("'mips' if getattr(self, '_tests_mode', 'tac') == 'mips' else 'codegen'", APP)

    def test_gui_parses_runner_output(self):
        from compiscript.mars import find_mars, java_available
        if find_mars() is None or not java_available():
            self.skipTest('Java o Mars.jar no disponibles')
        out = subprocess.run([sys.executable, str(ROOT / 'tests' / 'mips' / 'run_tests.py'), '-v'], cwd=ROOT,
                             capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300).stdout
        groups, total = _gui_parser()(out)
        self.assertIsNotNone(total, out)
        self.assertEqual(total[0], total[1], out)
        self.assertEqual([g for g, _ in groups], ['Casos exitosos', 'Casos fallidos'])
        names = [t['name'] for _, tests in groups for t in tests]
        self.assertEqual(int(total[1]), len(names))
        self.assertTrue(all(n.startswith(('codegen/', 'mips/cases/')) for n in names), names)
        self.assertTrue(all(t['ok'] for _, tests in groups for t in tests))

    def test_gui_parser_reads_failures(self):
        sample = textwrap.dedent('''\
            Casos exitosos
              ok     codegen/ok/01_a.cps
              FALLA  mips/cases/ok/02_b.cps
                esperado: '1'
                obtenido: '2'
            Casos fallidos
              ok     mips/cases/error/01_c.cps

            2/3 pruebas correctas
        ''')
        groups, total = _gui_parser()(sample)
        self.assertEqual(total, ('2', '3'))
        failing = [t for _, tests in groups for t in tests if not t['ok']]
        self.assertEqual(len(failing), 1)
        self.assertTrue(failing[0]['problems'])


if __name__ == '__main__':
    unittest.main()

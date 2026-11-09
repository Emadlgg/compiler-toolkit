"""Mensajes claros de bibliotecas y herencia entre clases exportadas."""
import subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARS = ROOT / 'tools' / 'Mars.jar'

FAMILIA = '''export class Animal {
    let edad: integer;
    function constructor() { this.edad = 5; }
    function obtener(): integer { return this.edad; }
}
export class Perro : Animal {
    let bono: integer;
    function constructor() { this.edad = 5; this.bono = 2; }
    function total(): integer { return this.obtener() + this.bono; }
}
'''


def cli(*args, cwd):
    r = subprocess.run([sys.executable, str(ROOT / 'compiscript.py'), *map(str, args)], cwd=cwd,
                       capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env={'PYTHONIOENCODING': 'utf-8', 'PATH': __import__('os').environ.get('PATH', '')})
    return r.returncode, r.stdout + r.stderr


class TestLibraryMessages(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_cplobj_gives_clear_message(self):
        (self.dir / 'main.cps').write_text('import { A } from "./build/NoExiste.cplobj";\nlet a = new A();\n', encoding='utf-8')
        _, out = cli('main.cps', '--mips', '--output', 'build/m.asm', cwd=self.dir)
        self.assertIn('No se encontro la biblioteca compilada "NoExiste.cplobj"', out)
        self.assertIn('BUILD LIB', out)

    def test_library_with_imports_explains_workaround(self):
        (self.dir / 'Animal.cps').write_text('export class Animal { function constructor() { } }\n', encoding='utf-8')
        (self.dir / 'Perro.cps').write_text('import { Animal } from "./Animal";\n'
                                            'export class Perro : Animal { function constructor() { } }\n', encoding='utf-8')
        code, out = cli('Perro.cps', '--build-library', '--output', 'build/Perro.cplobj', cwd=self.dir)
        self.assertNotEqual(code, 0)
        self.assertIn('mismo archivo', out)

    def test_parent_and_child_in_one_library(self):
        (self.dir / 'Familia.cps').write_text(FAMILIA, encoding='utf-8')
        code, out = cli('Familia.cps', '--build-library', '--output', 'build/Familia.cplobj', cwd=self.dir)
        self.assertEqual(code, 0, out)
        (self.dir / 'main.cps').write_text('import { Animal, Perro } from "./build/Familia.cplobj";\n'
                                           'let p = new Perro();\nprint(p.total());\nprint(p.obtener());\n', encoding='utf-8')
        code, out = cli('main.cps', '--mips', '--output', 'build/m.asm', cwd=self.dir)
        self.assertEqual(code, 0, out)
        if MARS.is_file():
            r = subprocess.run(['java', '-jar', str(MARS), 'nc', str(self.dir / 'build' / 'm.asm')],
                               capture_output=True, text=True, timeout=60)
            lines = [l for l in r.stdout.splitlines() if l.strip()]
            self.assertEqual(lines[-2:], ['7', '5'])


if __name__ == '__main__':
    unittest.main()

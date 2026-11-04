import tempfile
import unittest
from pathlib import Path

from compiscript.modules import ModuleError, resolve_project


class TestModules(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding='utf-8')
        return path

    def test_import_and_inheritance(self):
        self.write('clases/Animal.cps', 'export class Animal { nombre: string; }')
        self.write('clases/Perro.cps', 'import { Animal } from "./Animal";\nexport class Perro : Animal {}')
        main = self.write('main.cps', 'import { Perro } from "./clases/Perro";\nlet mascota = new Perro();')
        source = resolve_project(main)
        self.assertLess(source.index('class Animal'), source.index('class Perro'))
        self.assertLess(source.index('class Perro'), source.index('let mascota'))
        self.assertNotIn('export class', source)

    def test_missing_export(self):
        self.write('lib.cps', 'class Privada {}')
        main = self.write('main.cps', 'import { Privada } from "./lib";')
        with self.assertRaisesRegex(ModuleError, 'no esta exportado'):
            resolve_project(main)

    def test_missing_file(self):
        main = self.write('main.cps', 'import { Nada } from "./no_existe";')
        with self.assertRaisesRegex(ModuleError, 'No se pudo leer'):
            resolve_project(main)

    def test_cycle(self):
        a = self.write('a.cps', 'import { B } from "./b";\nexport class A {}')
        self.write('b.cps', 'import { A } from "./a";\nexport class B {}')
        with self.assertRaisesRegex(ModuleError, 'Dependencia circular'):
            resolve_project(a)

    def test_deduplicated_dependency(self):
        self.write('base.cps', 'export class Base {}')
        self.write('a.cps', 'import { Base } from "./base";\nexport class A : Base {}')
        self.write('b.cps', 'import { Base } from "./base";\nexport class B : Base {}')
        main = self.write('main.cps', 'import { A } from "./a";\nimport { B } from "./b";')
        self.assertEqual(resolve_project(main).count('class Base'), 1)

    def test_duplicate_global(self):
        self.write('a.cps', 'export class X {}')
        self.write('b.cps', 'export class X {}')
        main = self.write('main.cps', 'import { X } from "./a";\nimport { X } from "./b";')
        with self.assertRaisesRegex(ModuleError, 'duplicado'):
            resolve_project(main)


if __name__ == '__main__':
    unittest.main()

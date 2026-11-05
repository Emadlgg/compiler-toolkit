import tempfile
import unittest
from pathlib import Path
from compiscript.modules import resolve_project, ModuleError


class TestImportAliases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, text, encoding='utf-8'):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding=encoding)
        return p

    def test_class_alias_and_inheritance(self):
        self.write('Animal.cps', 'export class Animal {}')
        main = self.write('main.cps', 'import { Animal as SerVivo } from "./Animal";\nclass Perro : SerVivo {}\nlet a = new SerVivo();')
        combined = resolve_project(main)
        self.assertIn('class Perro : Animal', combined)
        self.assertIn('new Animal()', combined)
        self.assertNotIn('SerVivo', combined)

    def test_alias_does_not_rewrite_strings_or_comments_or_properties(self):
        self.write('lib.cps', 'export function saludo() {}')
        main = self.write('main.cps', 'import { saludo as hola } from "./lib";\n// hola\nprint("hola");\nobj.hola();\nhola();')
        combined = resolve_project(main)
        self.assertIn('// hola', combined)
        self.assertIn('"hola"', combined)
        self.assertIn('obj.hola()', combined)
        self.assertIn('saludo();', combined)

    def test_alias_collision(self):
        self.write('lib.cps', 'export class Animal {}')
        main = self.write('main.cps', 'import { Animal as Perro } from "./lib";\nclass Perro {}')
        with self.assertRaisesRegex(ModuleError, 'Alias en conflicto'):
            resolve_project(main)

    def test_missing_export_with_alias(self):
        self.write('lib.cps', 'class Animal {}')
        main = self.write('main.cps', 'import { Animal as SerVivo } from "./lib";')
        with self.assertRaisesRegex(ModuleError, 'no esta exportado'):
            resolve_project(main)

    def test_bom_in_imported_file(self):
        self.write('lib.cps', 'export class Animal {}', 'utf-8-sig')
        main = self.write('main.cps', 'import { Animal as SerVivo } from "./lib";\nnew SerVivo();', 'utf-8-sig')
        combined = resolve_project(main)
        self.assertNotIn('\ufeff', combined)
        self.assertIn('new Animal()', combined)


if __name__ == '__main__':
    unittest.main()

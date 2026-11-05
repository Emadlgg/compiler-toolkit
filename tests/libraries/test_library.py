import tempfile
import unittest
from pathlib import Path
from compiscript.modules.library import build_library, read_library, LibraryError
from compiscript.modules.resolver import resolve_project, ModuleError


class TestLibrary(unittest.TestCase):
    def test_pack_and_import_without_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'Animal.cps'
            source.write_text('export class Animal { let edad: integer; }\n', encoding='utf-8')
            lib = build_library(source, root / 'Animal.cplib')
            source.unlink()
            (root / 'main.cps').write_text('import { Animal } from "./Animal.cplib";\nlet a = new Animal();\n', encoding='utf-8')
            combined = resolve_project(root / 'main.cps')
            self.assertIn('class Animal', combined)
            self.assertIn('new Animal()', combined)
            self.assertEqual(read_library(lib)[1], {'Animal'})

    def test_missing_export(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'A.cps').write_text('export class A {}\n', encoding='utf-8')
            build_library(root / 'A.cps', root / 'A.cplib')
            (root / 'main.cps').write_text('import { B } from "./A.cplib";\n', encoding='utf-8')
            with self.assertRaises(ModuleError):
                resolve_project(root / 'main.cps')

    def test_tampered_library(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'A.cps').write_text('export class A {}\n', encoding='utf-8')
            lib = build_library(root / 'A.cps', root / 'A.cplib')
            import zipfile
            with zipfile.ZipFile(lib, 'a') as archive:
                archive.writestr('module.cps', 'class B {}')
            with self.assertRaises(LibraryError):
                read_library(lib)

    def test_dependencies_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'A.cps').write_text('import { B } from "./B";\nexport class A {}\n', encoding='utf-8')
            with self.assertRaises(LibraryError):
                build_library(root / 'A.cps', root / 'A.cplib')


if __name__ == '__main__':
    unittest.main()

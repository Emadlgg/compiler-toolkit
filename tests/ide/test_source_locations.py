import tempfile
import unittest
from pathlib import Path
from compiscript.modules.resolver import resolve_project, resolve_project_with_map


class TestSourceLocations(unittest.TestCase):
    def test_imported_line_maps_to_original_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Animal.cps').write_text('export class Animal {\n    let edad: integer;\n}\n', encoding='utf-8')
            (root / 'main.cps').write_text('import { Animal } from "./Animal";\nlet a = new Animal();\n', encoding='utf-8')
            source, mapping = resolve_project_with_map(root / 'main.cps')
            self.assertEqual(source, resolve_project(root / 'main.cps'))
            line = next(i for i, text in enumerate(source.splitlines(), 1) if 'let edad:' in text)
            self.assertEqual(mapping[line], ((root / 'Animal.cps').resolve(), 2))
            main_line = next(i for i, text in enumerate(source.splitlines(), 1) if 'let a =' in text)
            self.assertEqual(mapping[main_line], ((root / 'main.cps').resolve(), 2))

    def test_repeated_dependency_keeps_single_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'A.cps').write_text('export class A {}\n', encoding='utf-8')
            (root / 'B.cps').write_text('import { A } from "./A";\nexport class B {}\n', encoding='utf-8')
            (root / 'main.cps').write_text('import { A } from "./A";\nimport { B } from "./B";\n', encoding='utf-8')
            source, mapping = resolve_project_with_map(root / 'main.cps')
            self.assertEqual(source.count('class A {}'), 1)
            self.assertTrue(mapping)


if __name__ == '__main__':
    unittest.main()

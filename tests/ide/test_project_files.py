import tempfile
import unittest
from pathlib import Path
from gui.project_files import list_project_files


class TestProjectFiles(unittest.TestCase):
    def test_nested_files_and_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'clases').mkdir()
            (root / 'main.cps').write_text('print(1);', encoding='utf-8')
            (root / 'clases' / 'Animal.cps').write_text('class Animal {}', encoding='utf-8')
            self.assertEqual([p.relative_to(root).as_posix() for p in list_project_files(root)],
                             ['clases/Animal.cps', 'main.cps'])

    def test_build_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'build').mkdir()
            (root / 'build' / 'unused.cps').write_text('', encoding='utf-8')
            self.assertEqual(list_project_files(root), [])

    def test_missing_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                list_project_files(Path(temp) / 'missing')

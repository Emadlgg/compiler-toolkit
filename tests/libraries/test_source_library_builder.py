"""CLI and input guards for the source-to-library compiler."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compiscript.modules.source_library_builder import build_source_library, SourceLibraryError


class TestSourceLibraryBuilder(unittest.TestCase):
    def test_requires_cps(self):
        with self.assertRaisesRegex(SourceLibraryError, r'\.cps'):
            build_source_library('sample.txt', 'out.cplobj')

    def test_rejects_missing_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'sample.cps'
            source.write_text('class Animal {}', encoding='utf-8')
            with self.assertRaisesRegex(SourceLibraryError, 'exportadas'):
                build_source_library(source, Path(directory) / 'out.cplobj')

    def test_rejects_source_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'sample.cps'
            source.write_text('import { Animal } from "./Animal";\nexport class Perro {}', encoding='utf-8')
            with self.assertRaisesRegex(SourceLibraryError, 'imports'):
                build_source_library(source, Path(directory) / 'out.cplobj')

    def test_cli_validation(self):
        import importlib.util
        root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location('cps_cli_lib_test', root / 'compiscript.py')
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        self.assertTrue(cli.validate_arguments(['--build-library', '--output', 'lib.cplobj']))
        self.assertFalse(cli.validate_arguments(['--build-library']))
        self.assertFalse(cli.validate_arguments(['--build-library', '--mips', '--output', 'x']))


if __name__ == '__main__':
    unittest.main()

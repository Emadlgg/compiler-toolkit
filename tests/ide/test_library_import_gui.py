"""Importar clases desde otro documento: ruta que usa el IDE (sin Tkinter)."""
import shutil, tempfile, unittest
from pathlib import Path
from antlr4 import CommonTokenStream, InputStream
from compiscript.generated.CompiscriptLexer import CompiscriptLexer
from compiscript.generated.CompiscriptParser import CompiscriptParser
from gui.cps_source import make_analyzer, library_output_path, save_and_resolve_with_map
from gui.mips_runner import build_library

ANIMAL = 'export class Animal {\n  let edad: integer;\n  function constructor() { this.edad = 5; }\n}\n'
MAIN = 'import { Animal } from "./build/Animal.cplobj";\nlet a = new Animal();\nprint(a.edad);\n'


class TestLibraryImportGui(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / 'Animal.cps').write_text(ANIMAL, encoding='utf-8')
        (self.dir / 'main.cps').write_text(MAIN, encoding='utf-8')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _errors(self):
        main = self.dir / 'main.cps'
        source, _ = save_and_resolve_with_map(main, MAIN)
        tree = CompiscriptParser(CommonTokenStream(CompiscriptLexer(InputStream(source)))).program()
        analyzer, error = make_analyzer(main)
        if error:
            return [error]
        analyzer.visit(tree)
        return analyzer.errors

    def test_build_then_import(self):
        out = library_output_path(self.dir / 'Animal.cps')
        ok, log = build_library(self.dir / 'Animal.cps', out)
        self.assertTrue(ok, log)
        self.assertEqual(self._errors(), [])

    def test_missing_library_reports_error(self):
        self.assertTrue(self._errors())


if __name__ == '__main__':
    unittest.main()

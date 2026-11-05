import tempfile
import unittest
from pathlib import Path

from compiscript.modules.compiled_import_plan import build_import_plan
from compiscript.modules.compiled_imports import CompiledImportError
from compiscript.modules.compiled_package import create_package
from compiscript.modules.interface_metadata import ABI_VERSION
from compiscript.modules.mips_linker import build_object, _read_full


class TestCompiledImportPlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'lib.asm').write_text('hello:\n  jr $ra\n', encoding='utf-8')
        build_object(self.root/'lib.asm', ['hello'], self.root/'lib.mobj')
        (self.root/'api.cps').write_text('function hello(): void {}\n', encoding='utf-8')
        meta = {'format': ABI_VERSION, 'exports': {'hello': {
            'kind': 'function', 'label': 'hello', 'params': [],
            'return_type': 'void', 'frame_size': 16}}}
        create_package(self.root/'api.cps', self.root/'lib.mobj', self.root/'lib.cplobj', metadata=meta)

    def source(self, value):
        (self.root/'main.cps').write_text(value, encoding='utf-8')
        return self.root/'main.cps'

    def test_alias_and_extract(self):
        entry = self.source('import { hello as greet } from "./lib.cplobj";\ngreet();\n')
        plan = build_import_plan(entry)
        self.assertEqual(len(plan.libraries), 1)
        self.assertEqual(plan.symbols[(entry.resolve(), 'greet')].exported_name, 'hello')
        files = plan.extract_objects(self.root/'objects')
        self.assertEqual(len(files), 1)
        self.assertEqual(_read_full(files[0])[2], {'hello'})

    def test_deduplicates_library(self):
        (self.root/'other.cps').write_text('import { hello } from "./lib.cplobj";\n', encoding='utf-8')
        entry = self.source('import { hello } from "./lib.cplobj";\nimport { hello as h } from "./other.cps";\n')
        self.assertEqual(len(build_import_plan(entry).libraries), 1)

    def test_missing_export_rejected(self):
        with self.assertRaisesRegex(CompiledImportError, 'no exportado'):
            build_import_plan(self.source('import { missing } from "./lib.cplobj";'))

    def test_duplicate_alias_rejected(self):
        with self.assertRaisesRegex(CompiledImportError, 'duplicado'):
            build_import_plan(self.source('import { hello as x } from "./lib.cplobj";\nimport { hello as x } from "./lib.cplobj";'))

    def test_missing_source_rejected(self):
        with self.assertRaises(CompiledImportError):
            build_import_plan(self.source('import { x } from "./absent.cps";'))


if __name__ == '__main__':
    unittest.main()

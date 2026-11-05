import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compiscript.modules.compiled_package import create_package
from compiscript.modules.compiled_import_plan import build_import_plan
from compiscript.modules.compiled_imports import CompiledImportError
from compiscript.modules.interface_metadata import ABI_VERSION
from compiscript.modules.mips_linker import build_object
from compiscript.modules.package_dependencies import resolve_package_graph


class TestPackageDependencies(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def package(self, name, dependencies=()):
        label = name.lower()
        interface = self.root / (name + '.cps')
        asm = self.root / (name + '.asm')
        obj = self.root / (name + '.mobj')
        package = self.root / (name + '.cplobj')
        interface.write_text(f'function {label}(): void {{}}', encoding='utf-8')
        asm.write_text(f'{label}:\n  jr $ra\n', encoding='utf-8')
        build_object(asm, [label], obj)
        metadata = {'format': ABI_VERSION, 'exports': {label: {
            'kind': 'function', 'label': label, 'params': [],
            'return_type': 'void', 'frame_size': 16}}}
        create_package(interface, obj, package, metadata=metadata, dependencies=dependencies)
        return package

    def test_transitive_dependency_and_deduplication(self):
        base = self.package('Base')
        middle = self.package('Middle', [base])
        top = self.package('Top', [middle])
        entry = self.root / 'main.cps'
        entry.write_text('import { top } from "./Top.cplobj";\n'
                         'import { base } from "./Base.cplobj";\n', encoding='utf-8')
        plan = build_import_plan(entry)
        self.assertEqual([d.path.name for d in plan.libraries],
                         ['Base.cplobj', 'Middle.cplobj', 'Top.cplobj'])
        self.assertEqual(len(plan.extract_objects(self.root / 'objects')), 3)

    def test_missing_dependency_rejected(self):
        base = self.package('Base')
        top = self.package('Top', [base])
        base.unlink()
        with self.assertRaisesRegex(CompiledImportError, 'inexistente'):
            resolve_package_graph([top])

    def test_modified_dependency_rejected(self):
        base = self.package('Base')
        top = self.package('Top', [base])
        base.write_bytes(base.read_bytes() + b'x')
        with self.assertRaisesRegex(CompiledImportError, 'Integridad'):
            resolve_package_graph([top])

    def test_cycle_rejected(self):
        a = self.package('A')
        b = self.package('B')
        from compiscript.modules import package_dependencies as module
        original = module.dependency_entries
        def fake(path):
            if Path(path).name == 'A.cplobj':
                return [{'path': 'B.cplobj', 'sha256': __import__('hashlib').sha256(b.read_bytes()).hexdigest()}]
            if Path(path).name == 'B.cplobj':
                return [{'path': 'A.cplobj', 'sha256': __import__('hashlib').sha256(a.read_bytes()).hexdigest()}]
            return original(path)
        with patch.object(module, 'dependency_entries', side_effect=fake):
            with self.assertRaisesRegex(CompiledImportError, 'circular'):
                resolve_package_graph([a])


if __name__ == '__main__':
    unittest.main()

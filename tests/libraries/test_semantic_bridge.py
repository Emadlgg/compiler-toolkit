import unittest
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from compiscript.symbol_table import SymbolTable
from compiscript.modules.semantic_bridge import install_plan_symbols
from compiscript.modules.compiled_imports import CompiledImportError
from compiscript.modules.compiled_import_plan import ImportedSymbol
from compiscript.modules.interface_metadata import ABI_VERSION


class TestSemanticBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.entry = Path(self.tmp.name) / 'main.cps'
        self.lib = (Path(self.tmp.name) / 'lib.cplobj').resolve()
        self.metadata = {'format': ABI_VERSION, 'exports': {
            'Animal': {'kind': 'class', 'parent': None, 'size': 4,
                       'fields': {'edad': {'type': 'integer', 'offset': 0}},
                       'methods': {'constructor': {'label': 'Animal_constructor',
                                    'params': [], 'return_type': 'void', 'frame_size': 20}}}
        }}

    def plan(self, bindings):
        dep = SimpleNamespace(path=self.lib, metadata=self.metadata)
        return SimpleNamespace(entry=self.entry, libraries=[dep], symbols={
            (self.entry.resolve(), local): ImportedSymbol(local, exported, self.lib, self.metadata['exports'][exported])
            for local, exported in bindings.items()})

    def test_installs_alias_and_preserves_abi(self):
        analyzer = SimpleNamespace(table=SymbolTable())
        installed = install_plan_symbols(analyzer, self.plan({'SerVivo': 'Animal'}))
        self.assertEqual(installed['SerVivo'].size, 4)
        self.assertEqual(installed['SerVivo'].attributes['edad'].offset, 0)
        self.assertEqual(installed['SerVivo'].methods['constructor'].label, 'Animal_constructor')

    def test_duplicate_name_rejected(self):
        analyzer = SimpleNamespace(table=SymbolTable())
        install_plan_symbols(analyzer, self.plan({'SerVivo': 'Animal'}))
        with self.assertRaises(CompiledImportError):
            install_plan_symbols(analyzer, self.plan({'SerVivo': 'Animal'}))

    def test_other_source_import_not_leaked(self):
        analyzer = SimpleNamespace(table=SymbolTable())
        plan = self.plan({'SerVivo': 'Animal'})
        imported = plan.symbols.pop((self.entry.resolve(), 'SerVivo'))
        plan.symbols[(self.entry.parent / 'other.cps', 'SerVivo')] = imported
        self.assertEqual(install_plan_symbols(analyzer, plan), {})


if __name__ == '__main__':
    unittest.main()

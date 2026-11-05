import unittest
from compiscript.symbol_table import SymbolTable
from compiscript.modules.external_symbols import install_external_symbols, ExternalSymbolError
from compiscript.modules.interface_metadata import ABI_VERSION


class TestExternalSymbols(unittest.TestCase):
    def setUp(self):
        self.metadata = {'format': ABI_VERSION, 'exports': {
            'Animal': {'kind': 'class', 'parent': None, 'size': 8,
                       'fields': {'edad': {'type': 'integer', 'offset': 0}},
                       'methods': {'getEdad': {'label': 'Animal_getEdad', 'params': [],
                                              'return_type': 'integer', 'frame_size': 20}}},
            'suma': {'kind': 'function', 'label': 'lib_suma', 'params': [['a', 'integer'], ['b', 'integer']],
                     'return_type': 'integer', 'frame_size': 24}}}

    def test_class_layout_and_alias(self):
        table = SymbolTable()
        installed = install_external_symbols(table, self.metadata, {'SerVivo': 'Animal'})
        cls = installed['SerVivo']
        self.assertTrue(cls.external)
        self.assertEqual(cls.size, 8)
        self.assertEqual(cls.attributes['edad'].offset, 0)
        self.assertEqual(cls.methods['getEdad'].label, 'Animal_getEdad')
        self.assertEqual(cls.methods['getEdad'].frame_size, 20)
        self.assertEqual(next(s for s in table.all_scopes if s.name == 'class:SerVivo').lookup_local('edad').type, 'integer')

    def test_function_signature(self):
        table = SymbolTable()
        sym = install_external_symbols(table, self.metadata, {'sumar': 'suma'})['sumar']
        self.assertEqual(sym.params, [('a', 'integer'), ('b', 'integer')])
        self.assertEqual(sym.label, 'lib_suma')

    def test_collision_does_not_mutate_table(self):
        table = SymbolTable()
        with self.assertRaises(ExternalSymbolError):
            install_external_symbols(table, self.metadata, {'print': 'suma', 'Animal': 'Animal'})
        self.assertIsNone(table.global_scope.lookup_local('Animal'))

    def test_duplicate_label_rejected(self):
        table = SymbolTable()
        table._labels.add('Animal_getEdad')
        with self.assertRaises(ExternalSymbolError):
            install_external_symbols(table, self.metadata, {'Animal': 'Animal'})

    def test_unknown_export_rejected(self):
        with self.assertRaises(ExternalSymbolError):
            install_external_symbols(SymbolTable(), self.metadata, {'Otro': 'Inexistente'})


if __name__ == '__main__':
    unittest.main()

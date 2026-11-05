import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from compiscript.symbol_table import SymbolTable
from compiscript.modules.interface_metadata import from_symbol_table, InterfaceError
from compiscript.modules.compiled_package import (
    create_package, read_interface_metadata, CompiledPackageError,
)
from compiscript.modules.mips_linker import build_object


class TestInterfaceMetadata(unittest.TestCase):
    def test_layout_and_method_signature(self):
        table = SymbolTable()
        cls = table.define_class('Animal')
        table.enter_scope('class:Animal', kind='class').class_symbol = cls
        table.define_variable('edad', 'integer')
        method = table.define_function('getEdad', [], 'integer')
        table.enter_scope('function:getEdad', kind='function').function_symbol = method
        table.exit_scope()
        table.exit_scope()
        metadata = from_symbol_table(table, {'Animal'})
        item = metadata['exports']['Animal']
        self.assertEqual(item['size'], 4)
        self.assertEqual(item['fields']['edad'], {'type': 'integer', 'offset': 0})
        self.assertEqual(item['methods']['getEdad']['label'], method.label)

    def test_unknown_export_rejected(self):
        with self.assertRaises(InterfaceError):
            from_symbol_table(SymbolTable(), {'Inexistente'})

    def test_package_metadata_roundtrip_and_tamper(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'api.cps').write_text('function suma(): integer { return 0; }', encoding='utf-8')
            (root / 'code.asm').write_text('suma:\n  jr $ra\n', encoding='utf-8')
            build_object(root / 'code.asm', ['suma'], root / 'code.mobj')
            table = SymbolTable()
            fn = table.define_function('suma', [], 'integer')
            table.enter_scope('function:suma', kind='function').function_symbol = fn
            table.exit_scope()
            metadata = from_symbol_table(table, {'suma'})
            create_package(root / 'api.cps', root / 'code.mobj', root / 'lib.cplobj', metadata=metadata)
            self.assertEqual(read_interface_metadata(root / 'lib.cplobj'), metadata)
            with zipfile.ZipFile(root / 'lib.cplobj') as archive:
                contents = {n: archive.read(n) for n in archive.namelist()}
            contents['interface.json'] = b'{}'
            with zipfile.ZipFile(root / 'broken.cplobj', 'w') as archive:
                for name, data in contents.items():
                    archive.writestr(name, data)
            with self.assertRaises(CompiledPackageError):
                read_interface_metadata(root / 'broken.cplobj')


if __name__ == '__main__':
    unittest.main()

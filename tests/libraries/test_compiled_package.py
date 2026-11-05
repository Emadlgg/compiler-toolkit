import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from compiscript.modules.compiled_package import (
    CompiledPackageError, create_package, read_package, extract_object,
)
from compiscript.modules.mips_linker import build_object


class TestCompiledPackage(unittest.TestCase):
    def test_round_trip_and_extract(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / 'interface.cps').write_text('function suma(a: integer, b: integer): integer { return 0; }', encoding='utf-8')
            (root / 'suma.asm').write_text('suma:\n  addu $v0, $a0, $a1\n  jr $ra\n', encoding='utf-8')
            build_object(root / 'suma.asm', ['suma'], root / 'suma.mobj')
            create_package(root / 'interface.cps', root / 'suma.mobj', root / 'lib.cplobj')
            interface, obj, exports = read_package(root / 'lib.cplobj')
            self.assertIn('function suma', interface)
            self.assertEqual(exports, {'suma'})
            extract_object(root / 'lib.cplobj', root / 'extracted.mobj')
            self.assertEqual(obj, (root / 'extracted.mobj').read_bytes())

    def test_tamper_rejected(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / 'interface.cps').write_text('function suma(): integer { return 0; }', encoding='utf-8')
            (root / 'suma.asm').write_text('suma:\n  jr $ra\n', encoding='utf-8')
            build_object(root / 'suma.asm', ['suma'], root / 'suma.mobj')
            create_package(root / 'interface.cps', root / 'suma.mobj', root / 'lib.cplobj')
            with zipfile.ZipFile(root / 'lib.cplobj') as src:
                contents = {name: src.read(name) for name in src.namelist()}
            contents['interface.cps'] = b'altered'
            with zipfile.ZipFile(root / 'broken.cplobj', 'w') as out:
                for name, data in contents.items():
                    out.writestr(name, data)
            with self.assertRaises(CompiledPackageError):
                read_package(root / 'broken.cplobj')

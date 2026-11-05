import json
import tempfile
import unittest
from pathlib import Path
from compiscript.modules.library_object_builder import build_library_object, LibraryBuildError
from compiscript.modules.mips_linker import link


class TestLibraryDataRelocation(unittest.TestCase):
    def test_string_data_is_preserved_and_namespaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asm = root / 'lib.asm'
            asm.write_text('.data\n_globals: .space 4\n_str_0: .asciiz "hola"\n'
                           '.text\n.globl main\n  la $gp, _globals\n  j main\n'
                           'main:\n  li $v0, 10\n  syscall\n'
                           'Animal_constructor:\n  la $a0, _str_0\n  li $v0, 4\n  syscall\n  jr $ra\n')
            obj = root / 'Animal.mobj'
            build_library_object(asm, ['Animal_constructor'], obj)
            payload = json.loads(obj.read_text())
            self.assertEqual(payload['format'], 'compiscript-mips-object-v2')
            self.assertIn('_str_0:', payload['data'])
            self.assertNotIn('_globals:', payload['data'])
            main = root / 'main.asm'
            main.write_text('.data\n_globals: .space 4\n.text\nmain:\n  jal Animal_constructor\n  li $v0, 10\n  syscall\n')
            out = root / 'linked.asm'
            link(main, [obj], out)
            merged = out.read_text()
            self.assertIn('_obj0__str_0:', merged)
            self.assertIn('la $a0, _obj0__str_0', merged)

    def test_global_pointer_access_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / 'lib.asm'
            asm.write_text('.data\n_globals: .space 4\n.text\n  la $gp, _globals\n  j main\n'
                           'main:\n  li $v0, 10\n  syscall\n'
                           'f:\n  lw $t0, 0($gp)\n  jr $ra\n')
            with self.assertRaisesRegex(LibraryBuildError, 'globales'):
                build_library_object(asm, ['f'], Path(tmp) / 'f.mobj')

    def test_nonempty_global_area_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            asm = Path(tmp) / 'lib.asm'
            asm.write_text('.data\n_globals: .space 8\n.text\n  la $gp, _globals\n  j main\n'
                           'main:\n  li $v0, 10\n  syscall\n'
                           'f:\n  jr $ra\n')
            with self.assertRaisesRegex(LibraryBuildError, 'global'):
                build_library_object(asm, ['f'], Path(tmp) / 'f.mobj')

if __name__ == '__main__':
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from compiscript.modules.library_object_builder import extract_routines, build_library_object, LibraryBuildError
from compiscript.modules.mips_linker import read_object


class TestLibraryObjectBuilder(unittest.TestCase):
    def test_extract_and_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'full.asm'
            src.write_text('.data\n.text\n.globl main\nmain:\n  li $v0, 10\n  syscall\nFoo_bar:\n  li $v0, 7\n  jr $ra\n', encoding='utf-8')
            result = Path(tmp) / 'Foo.mobj'
            build_library_object(src, ['Foo_bar'], result)
            text, exports = read_object(result)
            self.assertIn('Foo_bar:', text)
            self.assertNotIn('main:', text)
            self.assertEqual(exports, {'Foo_bar'})

    def test_rejects_globals(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'full.asm'
            src.write_text('.data\n_globals: .space 8\n.text\nmain:\n  syscall\nFoo_bar:\n  jr $ra\n', encoding='utf-8')
            with self.assertRaisesRegex(LibraryBuildError, 'datos'):
                extract_routines(src, ['Foo_bar'])

    def test_rejects_missing_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'full.asm'
            src.write_text('.data\n.text\nmain:\n  syscall\nFoo_bar:\n  jal missing\n  jr $ra\n', encoding='utf-8')
            with self.assertRaisesRegex(LibraryBuildError, 'missing'):
                extract_routines(src, ['Foo_bar'])

if __name__ == '__main__':
    unittest.main()

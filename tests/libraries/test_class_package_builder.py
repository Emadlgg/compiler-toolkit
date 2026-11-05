import json
import tempfile
import unittest
from pathlib import Path

from compiscript.modules.class_package_builder import (
    build_class_package, ClassPackageBuildError)
from compiscript.modules.compiled_package import read_interface_metadata, read_package
from compiscript.modules.interface_metadata import ABI_VERSION


class TestClassPackageBuilder(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.asm = self.root / 'compiled.asm'
        self.interface = self.root / 'interface.cps'
        self.meta = self.root / 'abi.json'
        self.output = self.root / 'Animal.cplobj'
        self.asm.write_text('.data\n_globals: .space 4\n.text\n'
                            '  la $gp, _globals\n  j main\n'
                            'main:\n  li $v0, 10\n  syscall\n'
                            'Animal_constructor:\n  move $fp, $sp\n'
                            '  sw $ra, 4($fp)\n  lw $ra, 4($fp)\n'
                            '  lw $t9, 8($fp)\n  addiu $sp, $sp, 20\n'
                            '  move $fp, $t9\n  jr $ra\n', encoding='utf-8')
        self.interface.write_text('class Animal {}', encoding='utf-8')
        self.metadata = {'format': ABI_VERSION, 'exports': {
            'Animal': {'kind': 'class', 'parent': None, 'size': 4,
                       'fields': {}, 'methods': {
                           'constructor': {'label': 'Animal_constructor',
                                           'params': [], 'return_type': 'void',
                                           'frame_size': 20}}}}}
        self.meta.write_text(json.dumps(self.metadata), encoding='utf-8')

    def test_package_has_real_abi_and_compiled_object(self):
        build_class_package(self.asm, self.interface, self.meta, self.output)
        source, obj, exports = read_package(self.output)
        self.assertIn('Animal', source)
        self.assertIn('Animal_constructor', exports)
        self.assertEqual(read_interface_metadata(self.output), self.metadata)
        self.assertNotIn(b'main:', obj)

    def test_rejects_unavailable_method(self):
        self.metadata['exports']['Animal']['methods']['constructor']['label'] = 'missing'
        self.meta.write_text(json.dumps(self.metadata), encoding='utf-8')
        with self.assertRaises(ClassPackageBuildError):
            build_class_package(self.asm, self.interface, self.meta, self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_globals_and_unsafe_references(self):
        self.asm.write_text(self.asm.read_text().replace('_globals: .space 4',
                           '_globals: .space 8'), encoding='utf-8')
        with self.assertRaises(ClassPackageBuildError):
            build_class_package(self.asm, self.interface, self.meta, self.output)

    def test_rejects_inheritance_until_relocation_supported(self):
        self.metadata['exports']['Animal']['parent'] = 'Base'
        self.meta.write_text(json.dumps(self.metadata), encoding='utf-8')
        with self.assertRaisesRegex(ClassPackageBuildError, 'Herencia'):
            build_class_package(self.asm, self.interface, self.meta, self.output)


if __name__ == '__main__':
    unittest.main()

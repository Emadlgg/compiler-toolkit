"""Regression tests for v2 data/text objects and CLI integration."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from compiscript.modules.mips_linker import build_object, link, LinkError


class TestObjectV2(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main = self.root / 'main.asm'
        self.main.write_text('.data\n.text\nmain:\n  jal greet\n  li $v0, 10\n  syscall\n', encoding='utf-8')
        self.asm = self.root / 'lib.asm'
        self.obj = self.root / 'lib.mobj'
        self.asm.write_text('.data\nmessage: .asciiz "hola"\n.text\ngreet:\n  la $a0, message\n  li $v0, 4\n  syscall\n  jr $ra\n', encoding='utf-8')

    def test_data_and_text_are_linked(self):
        build_object(self.asm, ['greet'], self.obj)
        content = link(self.main, [self.obj], self.root / 'result.asm').read_text(encoding='utf-8')
        self.assertIn('_obj0_message: .asciiz "hola"', content)
        self.assertIn('la $a0, _obj0_message', content)
        self.assertIn('greet:', content)

    def test_v2_integrity(self):
        build_object(self.asm, ['greet'], self.obj)
        payload = json.loads(self.obj.read_text(encoding='utf-8'))
        payload['data'] += '\ncorrupt: .word 2'
        self.obj.write_text(json.dumps(payload), encoding='utf-8')
        with self.assertRaisesRegex(LinkError, 'Hash'):
            link(self.main, [self.obj], self.root / 'result.asm')

    def test_data_reference_to_other_library(self):
        self.asm.write_text('.data\nptr: .word other\n.text\ngreet:\n  jr $ra\n', encoding='utf-8')
        build_object(self.asm, ['greet'], self.obj)
        other = self.root / 'other.asm'
        other.write_text('other:\n  jr $ra\n', encoding='utf-8')
        other_obj = self.root / 'other.mobj'
        build_object(other, ['other'], other_obj)
        content = link(self.main, [self.obj, other_obj], self.root / 'result.asm').read_text()
        self.assertIn('.word other', content)

    def test_unresolved_data_symbol(self):
        self.asm.write_text('.data\nptr: .word missing\n.text\ngreet:\n  jr $ra\n', encoding='utf-8')
        build_object(self.asm, ['greet'], self.obj)
        with self.assertRaisesRegex(LinkError, 'sin resolver'):
            link(self.main, [self.obj], self.root / 'result.asm')


if __name__ == '__main__':
    unittest.main()

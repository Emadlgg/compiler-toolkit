import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from compiscript.modules.mips_linker import build_object, link, read_object, LinkError

class TestMIPSObjectLinker(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.program = self.root / 'main.asm'
        self.program.write_text('.data\n.text\n.globl main\nmain:\n  jal suma\n  li $v0, 10\n  syscall\n')
        self.routine = self.root / 'sum.asm'
        self.routine.write_text('suma:\n  li $v0, 5\n  jr $ra\n')
        self.obj = self.root / 'sum.mobj'

    def test_pack_and_link(self):
        build_object(self.routine, ['suma'], self.obj)
        result = link(self.program, [self.obj], self.root / 'linked.asm').read_text()
        self.assertIn('jal suma', result)
        self.assertIn('suma:\n  li $v0, 5', result)

    def test_tamper_rejected(self):
        build_object(self.routine, ['suma'], self.obj)
        obj = json.loads(self.obj.read_text())
        obj['text'] += '\n  syscall'
        self.obj.write_text(json.dumps(obj))
        with self.assertRaisesRegex(LinkError, 'Hash'):
            read_object(self.obj)

    def test_duplicate_export_rejected(self):
        build_object(self.routine, ['suma'], self.obj)
        with self.assertRaisesRegex(LinkError, 'duplicado'):
            link(self.program, [self.obj, self.obj], self.root / 'linked.asm')

    def test_unresolved_symbol_rejected(self):
        self.routine.write_text('suma:\n  jal missing\n  jr $ra\n')
        build_object(self.routine, ['suma'], self.obj)
        with self.assertRaisesRegex(LinkError, 'sin resolver'):
            link(self.program, [self.obj], self.root / 'linked.asm')

    def test_private_labels_namespaced(self):
        self.routine.write_text('suma:\n  j loop\nloop:\n  li $v0, 5\n  jr $ra\n')
        build_object(self.routine, ['suma'], self.obj)
        result = link(self.program, [self.obj], self.root / 'linked.asm').read_text()
        self.assertIn('_obj0_loop:', result)
        self.assertIn('j  _obj0_loop', result)

if __name__ == '__main__':
    unittest.main()

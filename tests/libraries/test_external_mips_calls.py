"""External MIPS calls must have a verified ABI and must not mask unknown calls."""
import unittest

from compiscript.activation_record import ActivationRecord
from compiscript.mips import MIPSGenerator, MIPSError
from compiscript.tac import Call, Const, Enter, FuncBegin, Halt, Param


class TestExternalMIPSCalls(unittest.TestCase):
    def setUp(self):
        self.main = ActivationRecord.synthetic('main', 0, [], 0)
        self.external = ActivationRecord.synthetic('Animal_constructor', 1, ['this'], 0)
        self.code = [FuncBegin('main'), Enter(self.main.size),
                     Param(Const(100)), Call(None, 'Animal_constructor', 1), Halt()]

    def test_external_constructor_uses_abi_frame(self):
        asm = MIPSGenerator(self.code, [self.main, self.external],
                            external_labels={'Animal_constructor'}).generate()
        self.assertIn('jal Animal_constructor', asm)
        self.assertIn('sw $t0, 16($sp)', asm)
        self.assertNotIn('Animal_constructor:', asm)

    def test_external_without_declaration_rejected(self):
        with self.assertRaisesRegex(MIPSError, 'Función desconocida'):
            MIPSGenerator(self.code, [self.main, self.external]).generate()

    def test_external_without_frame_rejected(self):
        with self.assertRaisesRegex(MIPSError, 'Registro de activacion externo ausente'):
            MIPSGenerator(self.code, [self.main], external_labels={'Animal_constructor'})

    def test_duplicate_local_and_external_rejected(self):
        code = self.code + [FuncBegin('Animal_constructor'), Enter(self.external.size), Halt()]
        with self.assertRaisesRegex(MIPSError, 'tambien definida localmente'):
            MIPSGenerator(code, [self.main, self.external], external_labels={'Animal_constructor'})


if __name__ == '__main__':
    unittest.main()

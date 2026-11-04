"""Pruebas unitarias sin ANTLR para el primer incremento MIPS."""
import unittest
from compiscript.tac import *
from compiscript.activation_record import ActivationRecord
from compiscript.mips import MIPSGenerator, MIPSError


class TestMIPS(unittest.TestCase):
    def test_arithmetic(self):
        rec = ActivationRecord.synthetic('main', 0, [], 1)
        code = [FuncBegin('main'), Enter(rec.size), Binary(Temp(0), '+', Const(5), Const(3)), Halt()]
        asm = MIPSGenerator(code, [rec]).generate()
        self.assertIn('addu $t2, $t0, $t1', asm)
        self.assertIn('sw $t2, 16($fp)', asm)
        self.assertIn('li $v0, 10', asm)

    def test_function_call(self):
        main = ActivationRecord.synthetic('main', 0, [], 1)
        func = ActivationRecord.synthetic('doble', 1, ['n'], 0)
        class Sym:
            offset = 16
            storage = 'param'
        code = [FuncBegin('main'), Enter(main.size), Param(Const(4)), Call(Temp(0), 'doble', 1), Halt(),
                FuncBegin('doble', 1), Enter(func.size), Return(Var('n', Sym()))]
        asm = MIPSGenerator(code, [main, func]).generate()
        self.assertIn('jal doble', asm)
        self.assertIn('sw $fp, 8($sp)', asm)
        self.assertIn('lw $ra, 4($fp)', asm)

    def test_unsupported_is_error(self):
        rec = ActivationRecord.synthetic('main', 0, [], 1)
        code = [FuncBegin('main'), Enter(rec.size), Binary(Temp(0), '**', Const(3), Const(2)), Halt()]
        with self.assertRaisesRegex(MIPSError, 'Operador binario'):
            MIPSGenerator(code, [rec]).generate()


if __name__ == '__main__':
    unittest.main()

class TestIncrement2(unittest.TestCase):
    def test_allocator_spill_and_reuse(self):
        from compiscript.mips.registers import RegisterAllocator
        spilled = []
        alloc = RegisterAllocator(lambda owner, reg: spilled.append((owner, reg)))
        regs = [alloc.getReg(f't{i}', dirty=True) for i in range(8)]
        self.assertEqual(len(set(regs)), 8)
        self.assertEqual(alloc.getReg('t8', dirty=True), '$t0')
        self.assertEqual(spilled, [('t0', '$t0')])
        alloc.flush()
        self.assertEqual(len(spilled), 9)
        alloc.release('$t0')
        self.assertEqual(alloc.getReg(), '$t0')

    def test_recursive_call_has_independent_frames(self):
        main = ActivationRecord.synthetic('main', 0, [], 1)
        fact = ActivationRecord.synthetic('fact', 1, ['n'], 3)
        class Sym:
            offset = 16
            storage = 'param'
        n = Var('n', Sym())
        code = [FuncBegin('main'), Enter(main.size), Param(Const(5)),
                Call(Temp(0), 'fact', 1), Halt(),
                FuncBegin('fact', 1), Enter(fact.size),
                IfRel(n, '<=', Const(1), 'base'),
                Binary(Temp(0), '-', n, Const(1)),
                Param(Temp(0)), Call(Temp(1), 'fact', 1),
                Binary(Temp(2), '*', n, Temp(1)), Return(Temp(2)),
                Label('base'), Return(Const(1))]
        asm = MIPSGenerator(code, [main, fact]).generate()
        self.assertEqual(asm.count('jal fact'), 2)
        self.assertIn('sw $fp, 8($sp)', asm)
        self.assertIn('lw $t9, 8($fp)', asm)
        self.assertIn('move $fp, $t9', asm)
        self.assertIn('jr $ra', asm)
        self.assertIn('sw $t0, 16($sp)', asm)

    def test_static_link_hops(self):
        main = ActivationRecord.synthetic('main', 0, [], 0)
        outer = ActivationRecord.synthetic('outer', 1, [], 0)
        inner = ActivationRecord.synthetic('inner', 2, [], 0)
        code = [FuncBegin('main'), Enter(main.size), Call(None, 'outer', 0), Halt(),
                FuncBegin('outer', 1), Enter(outer.size), Call(None, 'inner', 0, link=0), Return(),
                FuncBegin('inner', 2), Enter(inner.size), Call(None, 'outer', 0, link=1), Return()]
        asm = MIPSGenerator(code, [main, outer, inner]).generate()
        self.assertIn('sw $t9, 12($sp)', asm)
        self.assertIn('lw $t9, 12($t9)', asm)

    def test_frame_validation(self):
        from compiscript.mips.frames import FrameManager
        with self.assertRaises(ValueError):
            FrameManager.validate_call(16, 1)
        self.assertEqual(FrameManager.reserve(40000), ['  li $t8, 40000', '  subu $sp, $sp, $t8'])
        self.assertEqual(FrameManager.restore(40000), ['  li $t8, 40000', '  addu $sp, $fp, $t8'])


class TestIncrement3(unittest.TestCase):
    def make_asm(self, body, temps=8):
        rec = ActivationRecord.synthetic('main', 0, [], temps)
        return MIPSGenerator([FuncBegin('main'), Enter(rec.size), *body, Halt()], [rec]).generate()

    def test_array_allocation_access_and_length(self):
        asm = self.make_asm([
            NewArray(Temp(0), Const(3)),
            StoreIndex(Temp(0), Const(1), Const(42)),
            LoadIndex(Temp(1), Temp(0), Const(1)),
            Len(Temp(2), Temp(0)),
        ])
        self.assertIn('li $v0, 9', asm)
        self.assertIn('sw $t4, 0($t3)', asm)
        self.assertIn('bge $t1, $t2, _mips_bounds_error', asm)
        self.assertIn('lw $t3, 0($t0)', asm)
        self.assertIn('_mips_bounds_error:', asm)

    def test_object_fields_and_zero_init(self):
        asm = self.make_asm([
            New(Temp(0), 'Persona', 12),
            StoreField(Temp(0), 'edad', 8, Const(21)),
            LoadField(Temp(1), Temp(0), 'edad', 8),
        ])
        self.assertIn('li $t0, 12', asm)
        self.assertIn('sw $zero, 0($t0)', asm)
        self.assertIn('li $t1, 8', asm)
        self.assertIn('_mips_null_error:', asm)

    def test_dynamic_count_and_null_checks(self):
        asm = self.make_asm([NewArray(Temp(0), Const(0)), Len(Temp(1), Temp(0))])
        self.assertIn('bltz $t0, _mips_size_error', asm)
        self.assertIn('beq $t0, $zero, _mips_null_error', asm)
        self.assertIn('_mips_size_error:', asm)

    def test_invalid_field_offset(self):
        with self.assertRaisesRegex(MIPSError, 'Offset de atributo invalido'):
            self.make_asm([LoadField(Temp(1), Temp(0), 'x', -4)])

class TestIncrement4(unittest.TestCase):
    def asm(self, body, temps=5):
        rec = ActivationRecord.synthetic('main', 0, [], temps)
        return MIPSGenerator([FuncBegin('main'), Enter(rec.size), *body, Halt()], [rec]).generate()

    def test_print_string_variable_and_concat(self):
        asm = self.asm([
            Binary(Temp(0), 'concat', Const('Hola '), Const('mundo')),
            Copy(Temp(1), Temp(0)), Param(Temp(1)), Call(None, 'print', 1),
        ])
        self.assertIn('jal _mips_concat', asm)
        self.assertIn('_mips_concat_copy_b:', asm)
        self.assertIn('sb $t3, 0($t5)', asm)
        self.assertIn('li $v0, 4\n  syscall', asm)

    def test_print_boolean_and_integer(self):
        asm = self.asm([
            Param(Const(True)), Call(None, 'print', 1),
            Param(Const(42)), Call(None, 'print', 1),
        ])
        self.assertIn('jal _mips_print_bool', asm)
        self.assertIn('_mips_true: .asciiz "true"', asm)
        self.assertIn('li $v0, 1\n  syscall', asm)

    def test_print_type_hint_from_codegen(self):
        call = Call(None, 'print', 1)
        call.print_type = 'string'
        asm = self.asm([Param(Temp(0)), call])
        self.assertIn('li $v0, 4\n  syscall', asm)

    def test_unsupported_print_type_fails(self):
        call = Call(None, 'print', 1)
        call.print_type = 'array:integer'
        with self.assertRaisesRegex(MIPSError, 'print no soporta'):
            self.asm([Param(Const(0)), call])

"""Prueba real de MIPS opcional: requiere MARS_JAR apuntando a Mars.jar."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiscript.activation_record import ActivationRecord
from compiscript.mips import MIPSGenerator
from compiscript.tac import (Binary, Call, Const, Enter, FuncBegin, Halt,
                             IfRel, Label, NewArray, Param, Return, StoreIndex,
                             LoadIndex, Temp, Var)


def smoke_program():
    main = ActivationRecord.synthetic('main', 0, [], 4)
    double = ActivationRecord.synthetic('doble', 1, ['x'], 1)

    class ParamSymbol:
        offset = 16
        storage = 'param'

    code = [
        FuncBegin('main'), Enter(main.size),
        NewArray(Temp(0), Const(2)),
        StoreIndex(Temp(0), Const(0), Const(21)),
        LoadIndex(Temp(1), Temp(0), Const(0)),
        Param(Temp(1)), Call(Temp(2), 'doble', 1),
        Param(Temp(2)), Call(None, 'print', 1), Halt(),
        FuncBegin('doble', 1), Enter(double.size),
        Binary(Temp(0), '+', Var('x', ParamSymbol()), Var('x', ParamSymbol())),
        Return(Temp(0)),
    ]
    return MIPSGenerator(code, [main, double]).generate()


class TestMARSSmoke(unittest.TestCase):
    def test_generated_assembly(self):
        asm = smoke_program()
        self.assertIn('jal doble', asm)
        self.assertIn('li $v0, 9', asm)
        self.assertIn('.globl main', asm)

    @unittest.skipUnless(os.environ.get('MARS_JAR'), 'Definir MARS_JAR para ejecutar en MARS')
    def test_execute_mars(self):
        jar = Path(os.environ['MARS_JAR'])
        if not jar.is_file():
            self.fail(f'MARS_JAR no existe: {jar}')
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'smoke.asm'
            source.write_text(smoke_program(), encoding='utf-8')
            result = subprocess.run(
                ['java', '-jar', str(jar.resolve()), 'nc', 'sm', str(source)],
                capture_output=True, text=True, timeout=25,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), '42', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

"""Primer backend MIPS: enteros, booleanos, saltos, variables y funciones.

Las instrucciones no implementadas generan MIPSError; nunca se ignoran.
"""
from compiscript import tac
from compiscript.symbol_table import Type
from .emitter import MIPSEmitter
from .frames import FrameManager
from .registers import RegisterAllocator


class MIPSError(Exception):
    pass


class MIPSGenerator:
    def __init__(self, instructions, records, symbol_table=None):
        self.instructions = instructions
        self.records = {r.label: r for r in records}
        self.table = symbol_table
        self.emitter = MIPSEmitter()
        self.regs = RegisterAllocator()
        self.current = None
        self.pending = []
        self.strings = {}
        self.labels = {i.label: i for i in instructions if isinstance(i, tac.FuncBegin)}
        self.value_types = {}
        self.needs_concat = False
        self.needs_print_bool = False

    def emit(self, *lines):
        self.emitter.emit(*lines)

    def _size(self, label):
        if label not in self.records:
            raise MIPSError(f'No hay registro de activación para {label}')
        return FrameManager.frame_size(self.records[label].size)

    def _slot(self, op):
        if isinstance(op, tac.Temp):
            rec = self.records[self.current]
            return rec.symbols_end + op.n * 4, '$fp'
        if isinstance(op, tac.Var):
            # Los inicializadores sinteticos usan Var('this', None, hops).
            # El contrato de llamadas coloca this como primer argumento (fp+16).
            # Para metodos normales preferimos el simbolo real del analizador.
            if op.name == 'this' and op.sym is None:
                if op.hops:
                    self.emit('  move $t9, $fp')
                    for _ in range(op.hops):
                        self.emit('  lw $t9, 12($t9)')
                    return 16, '$t9'
                return 16, '$fp'
            if op.sym is None or op.sym.offset is None:
                raise MIPSError(f'Variable sin offset: {op}')
            if op.sym.storage == 'global':
                return op.sym.offset, '$gp'
            if op.sym.storage not in ('local', 'param'):
                raise MIPSError(f'Storage no soportado: {op.sym.storage}')
            if op.hops:
                self.emit('  move $t9, $fp')
                for _ in range(op.hops):
                    self.emit('  lw $t9, 12($t9)')
                return op.sym.offset, '$t9'
            return op.sym.offset, '$fp'
        raise MIPSError(f'No es una ubicación: {op}')

    def _load(self, op, reg):
        if isinstance(op, tac.Const):
            v = op.value
            if isinstance(v, str):
                if v not in self.strings:
                    name = f'_str_{len(self.strings)}'
                    self.strings[v] = name
                    encoded = v.encode('utf-8') + b'\0'
                    self.emitter.data.append(f'{name}: .byte ' + ', '.join(map(str, encoded)))
                self.emit(f'  la {reg}, {self.strings[v]}')
            elif v is None:
                self.emit(f'  move {reg}, $zero')
            else:
                self.emit(f'  li {reg}, {int(v)}')
        else:
            offset, base = self._slot(op)
            self.emit(f'  lw {reg}, {offset}({base})')

    def _store(self, op, reg):
        offset, base = self._slot(op)
        self.emit(f'  sw {reg}, {offset}({base})')

    def _type_of(self, op):
        if isinstance(op, tac.Const):
            return (Type.STRING if isinstance(op.value, str) else
                    Type.BOOLEAN if isinstance(op.value, bool) else
                    Type.NULL if op.value is None else Type.INTEGER)
        if isinstance(op, tac.Var) and op.sym is not None:
            return op.sym.type
        return self.value_types.get((self.current, str(op)), Type.ANY)

    def _set_type(self, op, typ):
        if op is not None:
            self.value_types[(self.current, str(op))] = typ

    def _binary(self, instr):
        if instr.op == 'concat':
            self._load(instr.left, '$a0')
            self._load(instr.right, '$a1')
            # The helper receives two NUL-terminated string pointers.
            self.emit('  jal _mips_concat')
            self._store(instr.dest, '$v0')
            self._set_type(instr.dest, Type.STRING)
            self.needs_concat = True
            return
        a, b, c = (self.regs.getReg() for _ in range(3))
        self._load(instr.left, a)
        self._load(instr.right, b)
        op = instr.op
        simple = {'+':'addu','-':'subu','*':'mul','&':'and','|':'or',
                  '==':'seq','!=':'sne','<':'slt','<=':'sle','>':'sgt','>=':'sge'}
        if op in simple:
            self.emit(f'  {simple[op]} {c}, {a}, {b}')
        elif op in ('/', '%'):
            self.emit(f'  beq {b}, $zero, _mips_div_zero', f'  div {a}, {b}',
                      f'  {"mflo" if op == "/" else "mfhi"} {c}')
            self.needs_div_zero = True
        else:
            raise MIPSError(f'Operador binario no implementado: {op}')
        self._store(instr.dest, c)
        self._set_type(instr.dest, Type.BOOLEAN if op in ("==", "!=", "<", "<=", ">", ">=") else Type.INTEGER)
        self.regs.release(a, b, c)

    def _call(self, instr):
        if len(self.pending) < instr.nargs:
            raise MIPSError(f'Faltan parámetros para {instr.target}')
        args = self.pending[-instr.nargs:] if instr.nargs else []
        if instr.nargs:
            del self.pending[-instr.nargs:]
        if instr.target == 'print':
            if len(args) != 1:
                raise MIPSError('print requiere un argumento')
            self._load(args[0], '$a0')
            typ = getattr(instr, 'print_type', None) or self._type_of(args[0])
            if typ == Type.STRING:
                self.emit('  li $v0, 4', '  syscall')
            elif typ == Type.BOOLEAN:
                self.emit('  jal _mips_print_bool')
                self.needs_print_bool = True
            elif typ in (Type.INTEGER, Type.ANY):
                self.emit('  li $v0, 1', '  syscall')
            else:
                raise MIPSError(f'print no soporta el tipo {typ}')
            return
        if instr.target not in self.labels:
            raise MIPSError(f'Función desconocida: {instr.target}')
        size = self._size(instr.target)
        try:
            FrameManager.validate_call(size, len(args))
        except ValueError as exc:
            raise MIPSError(f'{instr.target}: {exc}') from exc
        # Evaluar parámetros ANTES de cambiar $sp/$fp. Los registros del
        # llamador se guardan en sus slots tras cada instrucción.
        self.emit(*FrameManager.reserve(size), '  sw $fp, 8($sp)')
        if instr.link is not None and (not isinstance(instr.link, int) or instr.link < 0):
            raise MIPSError(f'Enlace estatico invalido: {instr.link}')
        if instr.link is None:
            self.emit('  sw $zero, 12($sp)')
        else:
            self.emit('  move $t9, $fp')
            for _ in range(instr.link):
                self.emit('  lw $t9, 12($t9)')
            self.emit('  sw $t9, 12($sp)')
        # Los operandos de parámetros se leen respecto al marco llamador,
        # que sigue disponible mediante $fp.
        for index, arg in enumerate(args):
            self._load(arg, '$t0')
            self.emit(f'  sw $t0, {16 + index * 4}($sp)')
        self.emit(f'  jal {instr.target}')
        if instr.dest is not None:
            self._store(instr.dest, '$v0')

    def _check_ref(self, reg):
        self.emit(f'  beq {reg}, $zero, _mips_null_error')
        self.needs_null_error = True

    def _heap_alloc(self, byte_reg, dest_reg):
        # MARS syscall 9 (sbrk); preserve requested size in a0.
        self.emit(f'  move $a0, {byte_reg}', '  li $v0, 9', '  syscall',
                  f'  move {dest_reg}, $v0')

    def _array_address(self, base, index):
        self._load(base, '$t0')
        self._check_ref('$t0')
        self._load(index, '$t1')
        self.emit('  bltz $t1, _mips_bounds_error',
                  '  lw $t2, 0($t0)',
                  '  bge $t1, $t2, _mips_bounds_error',
                  '  sll $t1, $t1, 2',
                  '  addu $t0, $t0, $t1',
                  '  addiu $t0, $t0, 4')
        self.needs_bounds_error = True

    def _memory_instruction(self, i):
        if isinstance(i, tac.New):
            if not isinstance(i.size, int) or i.size < 0:
                raise MIPSError(f'Tamano de objeto invalido: {i.size}')
            # Even an empty object gets a unique, non-null pointer.
            size = max(4, (i.size + 3) & ~3)
            self.emit(f'  li $t0, {size}')
            self._heap_alloc('$t0', '$t3')
            self.emit('  move $t0, $t3', f'  li $t1, {size // 4}')
            self._zero_words('$t0', '$t1')
            self._store(i.dest, '$t3')
        elif isinstance(i, tac.NewArray):
            self._load(i.count, '$t0')
            self.emit('  bltz $t0, _mips_size_error',
                      '  li $t1, 536870910',
                      '  bgt $t0, $t1, _mips_size_error',
                      '  move $t4, $t0',
                      '  sll $t1, $t0, 2', '  addiu $t1, $t1, 4')
            self.needs_size_error = True
            self._heap_alloc('$t1', '$t3')
            self.emit('  sw $t4, 0($t3)', '  addiu $t0, $t3, 4',
                      '  move $t1, $t4')
            self._zero_words('$t0', '$t1')
            self._store(i.dest, '$t3')
        elif isinstance(i, tac.LoadIndex):
            self._array_address(i.base, i.index)
            self.emit('  lw $t3, 0($t0)')
            self._store(i.dest, '$t3')
        elif isinstance(i, tac.StoreIndex):
            self._array_address(i.base, i.index)
            self._load(i.src, '$t3')
            self.emit('  sw $t3, 0($t0)')
        elif isinstance(i, tac.Len):
            self._load(i.array, '$t0')
            self._check_ref('$t0')
            self.emit('  lw $t3, 0($t0)')
            self._store(i.dest, '$t3')
        elif isinstance(i, (tac.LoadField, tac.StoreField)):
            if not isinstance(i.offset, int) or i.offset < 0 or i.offset % 4:
                raise MIPSError(f'Offset de atributo invalido: {i.offset}')
            self._load(i.obj, '$t0')
            self._check_ref('$t0')
            self.emit(f'  li $t1, {i.offset}', '  addu $t0, $t0, $t1')
            if isinstance(i, tac.LoadField):
                self.emit('  lw $t3, 0($t0)')
                self._store(i.dest, '$t3')
            else:
                self._load(i.src, '$t3')
                self.emit('  sw $t3, 0($t0)')
        else:
            raise MIPSError(f'Instruccion de memoria desconocida: {i}')

    def _zero_words(self, ptr, count):
        label = f'_mips_zero_{self.zero_counter}'
        self.zero_counter += 1
        self.emit(f'{label}:', f'  beq {count}, $zero, {label}_end',
                  f'  sw $zero, 0({ptr})', f'  addiu {ptr}, {ptr}, 4',
                  f'  addiu {count}, {count}, -1', f'  j {label}',
                  f'{label}_end:')

    def _instruction(self, i):
        if isinstance(i, tac.FuncBegin):
            if self.pending:
                raise MIPSError('Parámetros pendientes al iniciar una función')
            self.current = i.label
            self.emit(f'{i.label}:')
            if i.label == 'main':
                self.emit(*FrameManager.reserve(self._size(i.label)), '  move $fp, $sp')
            else:
                self.emit('  move $fp, $sp', '  sw $ra, 4($fp)')
        elif isinstance(i, tac.Enter):
            if i.size > self._size(self.current):
                raise MIPSError(f'Marco insuficiente: {self.current}')
        elif isinstance(i, tac.Copy):
            r = self.regs.getReg()
            self._load(i.src, r)
            self._store(i.dest, r)
            self._set_type(i.dest, self._type_of(i.src))
            self.regs.release(r)
        elif isinstance(i, tac.Binary):
            self._binary(i)
        elif isinstance(i, tac.Unary):
            a, b = self.regs.getReg(), self.regs.getReg()
            self._load(i.src, a)
            if i.op == '-':
                self.emit(f'  subu {b}, $zero, {a}')
            elif i.op == '!':
                self.emit(f'  sltiu {b}, {a}, 1')
            else:
                raise MIPSError(f'Operador unario no soportado: {i.op}')
            self._store(i.dest, b)
            self._set_type(i.dest, Type.BOOLEAN if i.op == "!" else Type.INTEGER)
            self.regs.release(a, b)
        elif isinstance(i, tac.Label):
            self.emit(f'{i.name}:')
        elif isinstance(i, tac.Goto):
            self.emit(f'  j {i.label}')
        elif isinstance(i, tac.IfGoto):
            self._load(i.cond, '$t0')
            self.emit(f'  {"beq" if i.negate else "bne"} $t0, $zero, {i.label}')
        elif isinstance(i, tac.IfRel):
            self._load(i.left, '$t0')
            self._load(i.right, '$t1')
            mapping = {'==':'beq','!=':'bne','<':'blt','<=':'ble','>':'bgt','>=':'bge'}
            if i.op not in mapping:
                raise MIPSError(f'Comparación desconocida: {i.op}')
            self.emit(f'  {mapping[i.op]} $t0, $t1, {i.label}')
        elif isinstance(i, tac.Param):
            self.pending.append(i.value)
        elif isinstance(i, tac.Call):
            self._call(i)
        elif isinstance(i, tac.Return):
            if i.value is not None:
                self._load(i.value, '$v0')
            else:
                self.emit('  move $v0, $zero')
            if self.current == 'main':
                self.emit('  li $v0, 10', '  syscall')
            else:
                self.emit('  sw $v0, 0($fp)', '  lw $ra, 4($fp)', '  lw $t9, 8($fp)',
                          *FrameManager.restore(self._size(self.current)),
                          '  move $fp, $t9', '  jr $ra')
        elif isinstance(i, (tac.New, tac.NewArray, tac.LoadIndex, tac.StoreIndex,
                            tac.LoadField, tac.StoreField, tac.Len)):
            self._memory_instruction(i)
        elif isinstance(i, tac.Halt):
            self.emit('  li $v0, 10', '  syscall')
        else:
            raise MIPSError(f'Instrucción TAC no implementada: {type(i).__name__}: {i}')

    def generate(self):
        self.needs_div_zero = False
        self.needs_null_error = False
        self.needs_bounds_error = False
        self.needs_size_error = False
        self.zero_counter = 0
        self.value_types.clear()
        self.needs_concat = False
        self.needs_print_bool = False
        self.regs.clear()
        if 'main' not in self.labels:
            raise MIPSError('La primera versión requiere la etiqueta main')
        self.emitter.data.append('_globals: .space ' + str(max(4, self.table.global_size() if self.table else 4)))
        self.emit('  la $gp, _globals', '  j main')
        for i in self.instructions:
            self._instruction(i)
        if self.pending:
            raise MIPSError('Parámetros sin llamada al final del programa')
        for needed, label, message in (
            (self.needs_div_zero, '_mips_div_zero', 'Division by zero'),
            (self.needs_null_error, '_mips_null_error', 'Null reference'),
            (self.needs_bounds_error, '_mips_bounds_error', 'Array index out of bounds'),
            (self.needs_size_error, '_mips_size_error', 'Invalid array size'),
        ):
            if needed:
                msg_label = label + '_message'
                encoded = message.encode('ascii') + b'\n\0'
                self.emitter.data.append(f'{msg_label}: .byte ' + ', '.join(map(str, encoded)))
                self.emit(f'{label}:', f'  la $a0, {msg_label}',
                          '  li $v0, 4', '  syscall', '  li $v0, 10', '  syscall')
        if self.needs_print_bool:
            self.emitter.data.extend([
                '_mips_true: .asciiz "true"',
                '_mips_false: .asciiz "false"',
            ])
            self.emit('_mips_print_bool:', '  beq $a0, $zero, _mips_bool_false',
                      '  la $a0, _mips_true', '  j _mips_bool_emit',
                      '_mips_bool_false:', '  la $a0, _mips_false',
                      '_mips_bool_emit:', '  li $v0, 4', '  syscall', '  jr $ra')
        if self.needs_concat:
            self._emit_concat_runtime()
        return self.emitter.render()

    def _emit_concat_runtime(self):
        # a0/a1: two zero-terminated strings; v0: newly allocated string.
        # t0..t7 are caller-clobbered in this backend.
        self.emit(
            '_mips_concat:',
            '  move $t6, $a0', '  move $t7, $a1',
            '  move $t0, $a0', '  move $t1, $a1',
            '  move $t2, $zero',
            '_mips_concat_len_a:', '  lbu $t3, 0($t0)',
            '  beq $t3, $zero, _mips_concat_len_b_start',
            '  addiu $t2, $t2, 1', '  addiu $t0, $t0, 1',
            '  j _mips_concat_len_a',
            '_mips_concat_len_b_start:', '  move $t0, $a1',
            '_mips_concat_len_b:', '  lbu $t3, 0($t0)',
            '  beq $t3, $zero, _mips_concat_allocate',
            '  addiu $t2, $t2, 1', '  addiu $t0, $t0, 1',
            '  j _mips_concat_len_b',
            '_mips_concat_allocate:', '  addiu $a0, $t2, 1',
            '  li $v0, 9', '  syscall',
            '  move $t4, $v0', '  move $t5, $v0',
            # syscall 9 only promises v0, so the original pointers must be
            # saved outside argument registers before allocation.
            '  move $t0, $t6',
            '_mips_concat_copy_a:', '  lbu $t3, 0($t0)',
            '  beq $t3, $zero, _mips_concat_copy_b_start',
            '  sb $t3, 0($t5)', '  addiu $t0, $t0, 1',
            '  addiu $t5, $t5, 1', '  j _mips_concat_copy_a',
            '_mips_concat_copy_b_start:', '  move $t0, $t7',
            '_mips_concat_copy_b:', '  lbu $t3, 0($t0)',
            '  sb $t3, 0($t5)', '  beq $t3, $zero, _mips_concat_done',
            '  addiu $t0, $t0, 1', '  addiu $t5, $t5, 1',
            '  j _mips_concat_copy_b',
            '_mips_concat_done:', '  move $v0, $t4', '  jr $ra',
        )

    def save(self, path):
        result = self.generate()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(result)

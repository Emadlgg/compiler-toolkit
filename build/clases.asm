.data
_globals: .space 12
_mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
  li $t0, 8
  move $a0, $t0
  li $v0, 9
  syscall
  move $t3, $v0
  move $t0, $t3
  li $t1, 2
_mips_zero_0:
  beq $t1, $zero, _mips_zero_0_end
  sw $zero, 0($t0)
  addiu $t0, $t0, 4
  addiu $t1, $t1, -1
  j _mips_zero_0
_mips_zero_0_end:
  sw $t3, 16($fp)
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Base__init
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  li $t0, 7
  sw $t0, 20($sp)
  jal Base_constructor
  lw $t0, 16($fp)
  sw $t0, 0($gp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 0($gp)
  sw $t0, 16($sp)
  li $t0, 3
  sw $t0, 20($sp)
  jal Base_sumar
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 0($gp)
  sw $t0, 16($sp)
  jal Base_descripcion
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $t0, 12
  move $a0, $t0
  li $v0, 9
  syscall
  move $t3, $v0
  move $t0, $t3
  li $t1, 3
_mips_zero_1:
  beq $t1, $zero, _mips_zero_1_end
  sw $zero, 0($t0)
  addiu $t0, $t0, 4
  addiu $t1, $t1, -1
  j _mips_zero_1
_mips_zero_1_end:
  sw $t3, 16($fp)
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Base__init
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Derivada__init
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  li $t0, 10
  sw $t0, 20($sp)
  li $t0, 3
  sw $t0, 24($sp)
  jal Derivada_constructor
  lw $t0, 16($fp)
  sw $t0, 4($gp)
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 4($gp)
  sw $t0, 16($sp)
  jal Derivada_total
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 4($gp)
  sw $t0, 16($sp)
  jal Derivada_descripcion
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 4($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $t0, 16
  move $a0, $t0
  li $v0, 9
  syscall
  move $t3, $v0
  move $t0, $t3
  li $t1, 4
_mips_zero_2:
  beq $t1, $zero, _mips_zero_2_end
  sw $zero, 0($t0)
  addiu $t0, $t0, 4
  addiu $t1, $t1, -1
  j _mips_zero_2
_mips_zero_2_end:
  sw $t3, 16($fp)
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Base__init
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Derivada__init
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Nieta__init
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  li $t0, 20
  sw $t0, 20($sp)
  jal Nieta_constructor
  lw $t0, 16($fp)
  sw $t0, 8($gp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 8($gp)
  sw $t0, 16($sp)
  jal Nieta_combinado
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 8($gp)
  sw $t0, 16($sp)
  jal Derivada_descripcion
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 8($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 4($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 10
  syscall
Base_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 20($fp)
  sw $t3, 0($t0)
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
Base_sumar:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 24($fp)
  lw $t0, 24($fp)
  lw $t1, 20($fp)
  addu $t2, $t0, $t1
  sw $t2, 24($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 24($fp)
  sw $t3, 0($t0)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 24($fp)
  lw $t0, 24($fp)
  li $t1, 1
  addu $t2, $t0, $t1
  sw $t2, 24($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 24($fp)
  sw $t3, 0($t0)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 24($fp)
  lw $v0, 24($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
Base_descripcion:
  move $fp, $sp
  sw $ra, 4($fp)
  li $v0, 100
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
Base__init:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  li $t3, 3
  sw $t3, 0($t0)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  li $t3, 0
  sw $t3, 0($t0)
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
Derivada_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 20($fp)
  sw $t3, 0($t0)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 8
  addu $t0, $t0, $t1
  lw $t3, 24($fp)
  sw $t3, 0($t0)
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
Derivada_descripcion:
  move $fp, $sp
  sw $ra, 4($fp)
  li $v0, 200
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
Derivada_total:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 8
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 20($fp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  lw $t0, 20($fp)
  sw $t0, 20($sp)
  jal Base_sumar
  sw $v0, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
Derivada__init:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 8
  addu $t0, $t0, $t1
  li $t3, 2
  sw $t3, 0($t0)
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
Nieta_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 20($fp)
  sw $t3, 0($t0)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 8
  addu $t0, $t0, $t1
  li $t3, 4
  sw $t3, 0($t0)
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
Nieta_combinado:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Derivada_total
  sw $v0, 20($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 12
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 24($fp)
  lw $t0, 20($fp)
  lw $t1, 24($fp)
  addu $t2, $t0, $t1
  sw $t2, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
Nieta__init:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 12
  addu $t0, $t0, $t1
  li $t3, 5
  sw $t3, 0($t0)
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
_mips_null_error:
  la $a0, _mips_null_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall

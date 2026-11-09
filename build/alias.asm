.data
_globals: .space 4
_mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
  li $t0, 4
  move $a0, $t0
  li $v0, 9
  syscall
  move $t3, $v0
  move $t0, $t3
  li $t1, 1
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
  jal Animal_constructor
  lw $t0, 16($fp)
  sw $t0, 0($gp)
  lw $t0, 0($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 10
  syscall
Animal_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
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

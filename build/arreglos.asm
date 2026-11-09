.data
_globals: .space 8
_mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0
_mips_bounds_error_message: .byte 65, 114, 114, 97, 121, 32, 105, 110, 100, 101, 120, 32, 111, 117, 116, 32, 111, 102, 32, 98, 111, 117, 110, 100, 115, 10, 0
_mips_size_error_message: .byte 73, 110, 118, 97, 108, 105, 100, 32, 97, 114, 114, 97, 121, 32, 115, 105, 122, 101, 10, 0

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -24
  move $fp, $sp
  li $t0, 5
  sw $t0, 0($gp)
  lw $t0, 0($gp)
  bltz $t0, _mips_size_error
  li $t1, 536870910
  bgt $t0, $t1, _mips_size_error
  move $t4, $t0
  sll $t1, $t0, 2
  addiu $t1, $t1, 4
  move $a0, $t1
  li $v0, 9
  syscall
  move $t3, $v0
  sw $t4, 0($t3)
  addiu $t0, $t3, 4
  move $t1, $t4
_mips_zero_0:
  beq $t1, $zero, _mips_zero_0_end
  sw $zero, 0($t0)
  addiu $t0, $t0, 4
  addiu $t1, $t1, -1
  j _mips_zero_0
_mips_zero_0_end:
  sw $t3, 4($gp)
  lw $t0, 4($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  bltz $t1, _mips_bounds_error
  lw $t2, 0($t0)
  bge $t1, $t2, _mips_bounds_error
  sll $t1, $t1, 2
  addu $t0, $t0, $t1
  addiu $t0, $t0, 4
  li $t3, 10
  sw $t3, 0($t0)
  lw $t0, 4($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 1
  bltz $t1, _mips_bounds_error
  lw $t2, 0($t0)
  bge $t1, $t2, _mips_bounds_error
  sll $t1, $t1, 2
  addu $t0, $t0, $t1
  addiu $t0, $t0, 4
  li $t3, 20
  sw $t3, 0($t0)
  lw $t0, 4($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  bltz $t1, _mips_bounds_error
  lw $t2, 0($t0)
  bge $t1, $t2, _mips_bounds_error
  sll $t1, $t1, 2
  addu $t0, $t0, $t1
  addiu $t0, $t0, 4
  lw $t3, 0($t0)
  sw $t3, 16($fp)
  lw $t0, 4($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 1
  bltz $t1, _mips_bounds_error
  lw $t2, 0($t0)
  bge $t1, $t2, _mips_bounds_error
  sll $t1, $t1, 2
  addu $t0, $t0, $t1
  addiu $t0, $t0, 4
  lw $t3, 0($t0)
  sw $t3, 20($fp)
  lw $t0, 16($fp)
  lw $t1, 20($fp)
  addu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 10
  syscall
_mips_null_error:
  la $a0, _mips_null_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall
_mips_bounds_error:
  la $a0, _mips_bounds_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall
_mips_size_error:
  la $a0, _mips_size_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall

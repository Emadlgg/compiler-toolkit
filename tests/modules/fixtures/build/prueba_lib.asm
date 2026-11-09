.data
_globals: .space 4
_mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0
_mips_null_text: .asciiz "null"

_obj0__str_0: .byte 82, 101, 120, 0
_obj0__mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0
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
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  lw $t0, 0($gp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -20
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 0($gp)
  sw $t0, 16($sp)
  jal Animal_crecer
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  li $v0, 10
  syscall
_mips_null_error:
  la $a0, _mips_null_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall
_mips_print_str:
  bne $a0, $zero, _mips_print_str_go
  la $a0, _mips_null_text
_mips_print_str_go:
  li $v0, 4
  syscall
  jr $ra
Animal_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -4
  sw $s0, -4($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  beq $t0, $zero, _obj0__mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  la $t3, _obj0__str_0
  sw $t3, 0($t0)
  move $t0, $s0
  beq $t0, $zero, _obj0__mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  li $t3, 5
  sw $t3, 0($t0)
  move $v0, $zero
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
Animal_crecer:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -4
  sw $s0, -4($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  beq $t0, $zero, _obj0__mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 20($fp)
  lw $t0, 20($fp)
  li $t1, 1
  addu $t2, $t0, $t1
  sw $t2, 20($fp)
  move $t0, $s0
  beq $t0, $zero, _obj0__mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 20($fp)
  sw $t3, 0($t0)
  move $t0, $s0
  beq $t0, $zero, _obj0__mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 20($fp)
  lw $v0, 20($fp)
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
_obj0__mips_null_error:
  la $a0, _obj0__mips_null_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall

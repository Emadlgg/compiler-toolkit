.data
_globals: .space 8
_str_0: .byte 61, 61, 61, 32, 73, 77, 80, 79, 82, 84, 65, 67, 73, 79, 78, 32, 68, 69, 83, 68, 69, 32, 67, 79, 68, 73, 71, 79, 32, 70, 85, 69, 78, 84, 69, 32, 61, 61, 61, 0
_mips_null_text: .asciiz "null"

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
  la $a0, _str_0
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 10
  sw $t0, 16($sp)
  li $t0, 20
  sw $t0, 20($sp)
  jal sumar
  sw $v0, 0($gp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 4
  sw $t0, 16($sp)
  li $t0, 5
  sw $t0, 20($sp)
  jal multiplicar
  sw $v0, 4($gp)
  lw $a0, 0($gp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  lw $a0, 4($gp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  li $v0, 10
  syscall
sumar:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  lw $t1, 20($fp)
  addu $t2, $t0, $t1
  sw $t2, 24($fp)
  lw $v0, 24($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
multiplicar:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  lw $t1, 20($fp)
  mul $t2, $t0, $t1
  sw $t2, 24($fp)
  lw $v0, 24($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
_mips_print_str:
  bne $a0, $zero, _mips_print_str_go
  la $a0, _mips_null_text
_mips_print_str_go:
  li $v0, 4
  syscall
  jr $ra

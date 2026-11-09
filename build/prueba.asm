.data
_globals: .space 4
_str_0: .byte 97, 110, 97, 0
_str_1: .byte 104, 111, 108, 97, 32, 0
_mips_null_text: .asciiz "null"

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -24
  move $fp, $sp
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 2
  sw $t0, 16($sp)
  li $t0, 3
  sw $t0, 20($sp)
  jal suma
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 5
  sw $t0, 16($sp)
  jal fact
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 10
  sw $t0, 16($sp)
  jal fib
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  la $t0, _str_0
  sw $t0, 16($sp)
  jal saludar
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 1
  sw $t0, 16($sp)
  li $t0, 2
  sw $t0, 20($sp)
  jal suma
  sw $v0, 16($fp)
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal doble
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 1
  sw $t0, 16($sp)
  li $t0, 2
  sw $t0, 20($sp)
  jal suma
  sw $v0, 16($fp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 3
  sw $t0, 16($sp)
  li $t0, 4
  sw $t0, 20($sp)
  jal suma
  sw $v0, 20($fp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  lw $t0, 20($fp)
  sw $t0, 20($sp)
  jal suma
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  li $v0, 10
  syscall
suma:
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
fact:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  li $t1, 1
  bgt $t0, $t1, L1
  li $v0, 1
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
L1:
  lw $t0, 16($fp)
  li $t1, 1
  subu $t2, $t0, $t1
  sw $t2, 20($fp)
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 20($fp)
  sw $t0, 16($sp)
  jal fact
  sw $v0, 20($fp)
  lw $t0, 16($fp)
  lw $t1, 20($fp)
  mul $t2, $t0, $t1
  sw $t2, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
fib:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  li $t1, 2
  bge $t0, $t1, L2
  lw $v0, 16($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
L2:
  lw $t0, 16($fp)
  li $t1, 1
  subu $t2, $t0, $t1
  sw $t2, 20($fp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 20($fp)
  sw $t0, 16($sp)
  jal fib
  sw $v0, 20($fp)
  lw $t0, 16($fp)
  li $t1, 2
  subu $t2, $t0, $t1
  sw $t2, 24($fp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 24($fp)
  sw $t0, 16($sp)
  jal fib
  sw $v0, 24($fp)
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
saludar:
  move $fp, $sp
  sw $ra, 4($fp)
  la $a0, _str_1
  lw $a1, 16($fp)
  jal _mips_concat
  sw $v0, 20($fp)
  lw $a0, 20($fp)
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
doble:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  lw $t0, 16($fp)
  sw $t0, 20($sp)
  jal suma
  sw $v0, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
_mips_concat:
  move $t6, $a0
  move $t7, $a1
  move $t0, $a0
  move $t1, $a1
  move $t2, $zero
_mips_concat_len_a:
  lbu $t3, 0($t0)
  beq $t3, $zero, _mips_concat_len_b_start
  addiu $t2, $t2, 1
  addiu $t0, $t0, 1
  j _mips_concat_len_a
_mips_concat_len_b_start:
  move $t0, $a1
_mips_concat_len_b:
  lbu $t3, 0($t0)
  beq $t3, $zero, _mips_concat_allocate
  addiu $t2, $t2, 1
  addiu $t0, $t0, 1
  j _mips_concat_len_b
_mips_concat_allocate:
  addiu $a0, $t2, 1
  li $v0, 9
  syscall
  move $t4, $v0
  move $t5, $v0
  move $t0, $t6
_mips_concat_copy_a:
  lbu $t3, 0($t0)
  beq $t3, $zero, _mips_concat_copy_b_start
  sb $t3, 0($t5)
  addiu $t0, $t0, 1
  addiu $t5, $t5, 1
  j _mips_concat_copy_a
_mips_concat_copy_b_start:
  move $t0, $t7
_mips_concat_copy_b:
  lbu $t3, 0($t0)
  sb $t3, 0($t5)
  beq $t3, $zero, _mips_concat_done
  addiu $t0, $t0, 1
  addiu $t5, $t5, 1
  j _mips_concat_copy_b
_mips_concat_done:
  move $v0, $t4
  jr $ra
_mips_print_str:
  bne $a0, $zero, _mips_print_str_go
  la $a0, _mips_null_text
_mips_print_str_go:
  li $v0, 4
  syscall
  jr $ra

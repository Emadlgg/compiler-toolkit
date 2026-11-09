.data
_globals: .space 4

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
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
  addiu $sp, $sp, -32
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 1
  sw $t0, 16($sp)
  li $t0, 2
  sw $t0, 20($sp)
  li $t0, 3
  sw $t0, 24($sp)
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
fact:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -4
  sw $s0, -4($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  li $t1, 1
  bgt $t0, $t1, L1
  li $v0, 1
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
L1:
  move $t0, $s0
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
  move $t0, $s0
  lw $t1, 20($fp)
  mul $t2, $t0, $t1
  sw $t2, 20($fp)
  lw $v0, 20($fp)
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
fib:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -4
  sw $s0, -4($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  li $t1, 2
  bge $t0, $t1, L2
  move $v0, $s0
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
L2:
  move $t0, $s0
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
  move $t0, $s0
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
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
suma:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  lw $t1, 20($fp)
  addu $t2, $t0, $t1
  sw $t2, 28($fp)
  lw $t0, 28($fp)
  lw $t1, 24($fp)
  addu $t2, $t0, $t1
  sw $t2, 28($fp)
  lw $v0, 28($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 32
  move $fp, $t9
  jr $ra

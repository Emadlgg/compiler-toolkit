.data
_globals: .space 4

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
  addiu $sp, $sp, -32
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 4
  sw $t0, 16($sp)
  jal suma
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -36
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 4
  sw $t0, 16($sp)
  jal f
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -68
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  jal diez
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
  li $t0, 5
  sw $t0, 16($sp)
  jal cnt
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
  li $t0, 10
  sw $t0, 16($sp)
  jal g
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
  addiu $sp, $sp, -12
  sw $s0, -4($fp)
  sw $s1, -8($fp)
  sw $s2, -12($fp)
  lw $s2, 16($fp)
  li $t0, 0
  move $s1, $t0
  li $t0, 1
  move $s0, $t0
L1:
  move $t0, $s0
  move $t1, $s2
  bgt $t0, $t1, L2
  move $t0, $s1
  move $t1, $s0
  addu $t2, $t0, $t1
  move $s1, $t2
  move $t0, $s0
  li $t1, 1
  addu $t2, $t0, $t1
  move $s0, $t2
  j L1
L2:
  move $v0, $s1
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  lw $s2, -12($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 32
  move $fp, $t9
  jr $ra
f:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -12
  sw $s0, -4($fp)
  sw $s1, -8($fp)
  sw $s2, -12($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  li $t1, 2
  mul $t2, $t0, $t1
  move $s1, $t2
  addiu $sp, $sp, -32
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  move $t0, $s0
  sw $t0, 16($sp)
  jal suma
  move $s2, $v0
  move $t0, $s1
  move $t1, $s2
  addu $t2, $t0, $t1
  sw $t2, 28($fp)
  addiu $sp, $sp, -32
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 3
  sw $t0, 16($sp)
  jal suma
  sw $v0, 32($fp)
  lw $t0, 28($fp)
  lw $t1, 32($fp)
  addu $t2, $t0, $t1
  sw $t2, 28($fp)
  lw $v0, 28($fp)
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  lw $s2, -12($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 36
  move $fp, $t9
  jr $ra
diez:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -32
  sw $s0, -4($fp)
  sw $s1, -8($fp)
  sw $s2, -12($fp)
  sw $s3, -16($fp)
  sw $s4, -20($fp)
  sw $s5, -24($fp)
  sw $s6, -28($fp)
  sw $s7, -32($fp)
  li $t0, 1
  move $s2, $t0
  li $t0, 2
  move $s3, $t0
  li $t0, 3
  move $s4, $t0
  li $t0, 4
  move $s5, $t0
  li $t0, 5
  move $s6, $t0
  li $t0, 6
  move $s7, $t0
  li $t0, 7
  sw $t0, 40($fp)
  li $t0, 8
  sw $t0, 44($fp)
  li $t0, 9
  sw $t0, 48($fp)
  li $t0, 10
  sw $t0, 52($fp)
  li $t0, 0
  move $s0, $t0
  li $t0, 0
  move $s1, $t0
L3:
  move $t0, $s0
  li $t1, 3
  bge $t0, $t1, L4
  move $t0, $s1
  move $t1, $s2
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  move $t1, $s3
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  move $t1, $s4
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  move $t1, $s5
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  move $t1, $s6
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  move $t1, $s7
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  lw $t1, 40($fp)
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  lw $t1, 44($fp)
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  lw $t1, 48($fp)
  addu $t2, $t0, $t1
  sw $t2, 64($fp)
  lw $t0, 64($fp)
  lw $t1, 52($fp)
  addu $t2, $t0, $t1
  move $s1, $t2
  move $t0, $s0
  li $t1, 1
  addu $t2, $t0, $t1
  move $s0, $t2
  j L3
L4:
  move $v0, $s1
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  lw $s2, -12($fp)
  lw $s3, -16($fp)
  lw $s4, -20($fp)
  lw $s5, -24($fp)
  lw $s6, -28($fp)
  lw $s7, -32($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 68
  move $fp, $t9
  jr $ra
cnt:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -8
  sw $s0, -4($fp)
  sw $s1, -8($fp)
  lw $s1, 16($fp)
  li $t0, 0
  sw $t0, 20($fp)
  li $t0, 0
  move $s0, $t0
L5:
  move $t0, $s0
  move $t1, $s1
  bge $t0, $t1, L6
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  move $t9, $fp
  sw $t9, 12($sp)
  move $t0, $s0
  sw $t0, 16($sp)
  jal cnt_add
  sw $v0, 28($fp)
  move $t0, $s0
  li $t1, 1
  addu $t2, $t0, $t1
  move $s0, $t2
  j L5
L6:
  lw $v0, 20($fp)
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 32
  move $fp, $t9
  jr $ra
cnt_add:
  move $fp, $sp
  sw $ra, 4($fp)
  move $t9, $fp
  lw $t9, 12($t9)
  lw $t0, 20($t9)
  lw $t1, 16($fp)
  addu $t2, $t0, $t1
  move $t9, $fp
  lw $t9, 12($t9)
  sw $t2, 20($t9)
  move $t9, $fp
  lw $t9, 12($t9)
  lw $v0, 20($t9)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
g:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -12
  sw $s0, -4($fp)
  sw $s1, -8($fp)
  sw $s2, -12($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  li $t1, 0
  bne $t0, $t1, L7
  li $v0, 0
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  lw $s2, -12($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 32
  move $fp, $t9
  jr $ra
L7:
  move $t0, $s0
  move $s1, $t0
  move $t0, $s0
  li $t1, 1
  subu $t2, $t0, $t1
  sw $t2, 28($fp)
  addiu $sp, $sp, -32
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 28($fp)
  sw $t0, 16($sp)
  jal g
  move $s2, $v0
  move $t0, $s1
  move $t1, $s2
  addu $t2, $t0, $t1
  sw $t2, 28($fp)
  lw $v0, 28($fp)
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  lw $s2, -12($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 32
  move $fp, $t9
  jr $ra

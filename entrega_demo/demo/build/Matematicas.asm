.data
_globals: .space 4

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -16
  move $fp, $sp
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

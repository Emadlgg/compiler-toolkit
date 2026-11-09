.data
_globals: .space 20
_str_0: .byte 104, 111, 108, 97, 0
_str_1: .byte 32, 0
_str_2: .byte 109, 117, 110, 100, 111, 0
_mips_div_zero_message: .byte 68, 105, 118, 105, 115, 105, 111, 110, 32, 98, 121, 32, 122, 101, 114, 111, 10, 0

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
  li $t0, 7
  sw $t0, 0($gp)
  li $t0, 3
  sw $t0, 4($gp)
  lw $t0, 4($gp)
  li $t1, 2
  mul $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $t0, 0($gp)
  lw $t1, 16($fp)
  addu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 0($gp)
  lw $t1, 4($gp)
  addu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $t0, 16($fp)
  li $t1, 2
  mul $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 0($gp)
  lw $t1, 4($gp)
  subu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $t0, 16($fp)
  li $t1, 1
  subu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 0($gp)
  lw $t1, 4($gp)
  beq $t1, $zero, _mips_div_zero
  div $t0, $t1
  mflo $t2
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 0($gp)
  lw $t1, 4($gp)
  beq $t1, $zero, _mips_div_zero
  div $t0, $t1
  mfhi $t2
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  lw $t0, 0($gp)
  subu $t1, $zero, $t0
  sw $t1, 16($fp)
  lw $t0, 16($fp)
  li $t1, 10
  addu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $t0, 3
  li $t1, 4
  mul $t2, $t0, $t1
  sw $t2, 16($fp)
  li $t0, 2
  lw $t1, 16($fp)
  addu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $t0, 16($fp)
  li $t1, 5
  subu $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  la $a0, _str_0
  la $a1, _str_1
  jal _mips_concat
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  la $a1, _str_2
  jal _mips_concat
  sw $v0, 8($gp)
  lw $a0, 8($gp)
  li $v0, 4
  syscall
  li $t0, 10
  sw $t0, 12($gp)
  lw $t0, 12($gp)
  li $t1, 1
  addu $t2, $t0, $t1
  sw $t2, 12($gp)
  lw $a0, 12($gp)
  li $v0, 1
  syscall
  li $t0, 0
  sw $t0, 16($gp)
  li $t0, 5
  sw $t0, 12($gp)
  lw $t0, 12($gp)
  sw $t0, 16($gp)
  lw $a0, 16($gp)
  li $v0, 1
  syscall
  lw $a0, 12($gp)
  li $v0, 1
  syscall
  li $v0, 10
  syscall
_mips_div_zero:
  la $a0, _mips_div_zero_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall
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

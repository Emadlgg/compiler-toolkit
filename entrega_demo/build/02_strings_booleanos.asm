.data
_globals: .space 12
_str_0: .byte 67, 111, 109, 112, 105, 115, 99, 114, 105, 112, 116, 0
_str_1: .byte 72, 111, 108, 97, 32, 0
_str_2: .byte 72, 111, 108, 97, 32, 67, 111, 109, 112, 105, 115, 99, 114, 105, 112, 116, 0
_str_3: .byte 109, 97, 121, 111, 114, 0
_str_4: .byte 109, 101, 110, 111, 114, 0
_mips_true: .asciiz "true"
_mips_false: .asciiz "false"
_mips_null_text: .asciiz "null"

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
  la $t0, _str_0
  sw $t0, 0($gp)
  la $a0, _str_1
  lw $a1, 0($gp)
  jal _mips_concat
  sw $v0, 4($gp)
  lw $a0, 4($gp)
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  lw $a0, 4($gp)
  la $a1, _str_2
  jal _mips_streq
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  jal _mips_print_bool
  li $v0, 11
  li $a0, 10
  syscall
  li $t0, 7
  sw $t0, 8($gp)
  lw $t0, 8($gp)
  li $t1, 5
  ble $t0, $t1, L1
  lw $t0, 8($gp)
  li $t1, 10
  bge $t0, $t1, L1
  li $t0, 1
  sw $t0, 16($fp)
  j L2
L1:
  li $t0, 0
  sw $t0, 16($fp)
L2:
  lw $a0, 16($fp)
  jal _mips_print_bool
  li $v0, 11
  li $a0, 10
  syscall
  lw $t0, 8($gp)
  li $t1, 7
  seq $t2, $t0, $t1
  sw $t2, 16($fp)
  lw $t0, 16($fp)
  sltiu $t1, $t0, 1
  sw $t1, 16($fp)
  lw $a0, 16($fp)
  jal _mips_print_bool
  li $v0, 11
  li $a0, 10
  syscall
  lw $t0, 8($gp)
  li $t1, 5
  ble $t0, $t1, L3
  la $t0, _str_3
  sw $t0, 16($fp)
  j L4
L3:
  la $t0, _str_4
  sw $t0, 16($fp)
L4:
  lw $a0, 16($fp)
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  li $v0, 10
  syscall
_mips_print_bool:
  beq $a0, $zero, _mips_bool_false
  la $a0, _mips_true
  j _mips_bool_emit
_mips_bool_false:
  la $a0, _mips_false
_mips_bool_emit:
  li $v0, 4
  syscall
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
_mips_streq:
  beq $a0, $a1, _mips_streq_yes
  beq $a0, $zero, _mips_streq_no
  beq $a1, $zero, _mips_streq_no
_mips_streq_loop:
  lbu $t0, 0($a0)
  lbu $t1, 0($a1)
  bne $t0, $t1, _mips_streq_no
  beq $t0, $zero, _mips_streq_yes
  addiu $a0, $a0, 1
  addiu $a1, $a1, 1
  j _mips_streq_loop
_mips_streq_yes:
  li $v0, 1
  jr $ra
_mips_streq_no:
  move $v0, $zero
  jr $ra

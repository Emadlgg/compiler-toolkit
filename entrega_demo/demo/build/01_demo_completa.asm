.data
_globals: .space 12
_str_0: .byte 65, 110, 97, 0
_str_1: .byte 61, 61, 61, 32, 68, 65, 84, 79, 83, 32, 68, 69, 76, 32, 69, 83, 84, 85, 68, 73, 65, 78, 84, 69, 32, 61, 61, 61, 0
_str_2: .byte 65, 112, 114, 111, 98, 97, 100, 111, 0
_str_3: .byte 82, 101, 112, 114, 111, 98, 97, 100, 111, 0
_str_4: .byte 61, 61, 61, 32, 80, 82, 79, 77, 69, 68, 73, 79, 32, 61, 61, 61, 0
_str_5: .byte 61, 61, 61, 32, 67, 73, 67, 76, 79, 32, 61, 61, 61, 0
_str_6: .byte 61, 61, 61, 32, 82, 69, 67, 85, 82, 83, 73, 86, 73, 68, 65, 68, 32, 61, 61, 61, 0
_mips_div_zero_message: .byte 68, 105, 118, 105, 115, 105, 111, 110, 32, 98, 121, 32, 122, 101, 114, 111, 10, 0
_mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0
_mips_null_text: .asciiz "null"

.text
.globl main
  la $gp, _globals
  j main
main:
  addiu $sp, $sp, -20
  move $fp, $sp
  li $t0, 12
  move $a0, $t0
  li $v0, 9
  syscall
  move $t3, $v0
  move $t0, $t3
  li $t1, 3
_mips_zero_0:
  beq $t1, $zero, _mips_zero_0_end
  sw $zero, 0($t0)
  addiu $t0, $t0, 4
  addiu $t1, $t1, -1
  j _mips_zero_0
_mips_zero_0_end:
  sw $t3, 16($fp)
  addiu $sp, $sp, -32
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  la $t0, _str_0
  sw $t0, 20($sp)
  li $t0, 20
  sw $t0, 24($sp)
  li $t0, 85
  sw $t0, 28($sp)
  jal Estudiante_constructor
  lw $t0, 16($fp)
  sw $t0, 0($gp)
  la $a0, _str_1
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 0($gp)
  sw $t0, 16($sp)
  jal Persona_mostrarEdad
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
  lw $t0, 0($gp)
  sw $t0, 16($sp)
  jal Estudiante_aprobado
  sw $v0, 16($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, L3
  la $a0, _str_2
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  j L2
L3:
  la $a0, _str_3
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
L2:
  la $a0, _str_4
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -28
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 80
  sw $t0, 16($sp)
  li $t0, 90
  sw $t0, 20($sp)
  jal calcularPromedio
  sw $v0, 4($gp)
  lw $a0, 4($gp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  la $a0, _str_5
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  li $t0, 0
  sw $t0, 8($gp)
L4:
  lw $t0, 8($gp)
  li $t1, 3
  bge $t0, $t1, L5
  lw $a0, 8($gp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  lw $t0, 8($gp)
  li $t1, 1
  addu $t2, $t0, $t1
  sw $t2, 8($gp)
  j L4
L5:
  la $a0, _str_6
  jal _mips_print_str
  li $v0, 11
  li $a0, 10
  syscall
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  li $t0, 5
  sw $t0, 16($sp)
  jal factorial
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  li $v0, 10
  syscall
Persona_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -4
  sw $s0, -4($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 20($fp)
  sw $t3, 0($t0)
  move $t0, $s0
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 24($fp)
  sw $t3, 0($t0)
  move $v0, $zero
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
Persona_mostrarEdad:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
Estudiante_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -4
  sw $s0, -4($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  beq $t0, $zero, _mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  lw $t3, 20($fp)
  sw $t3, 0($t0)
  move $t0, $s0
  beq $t0, $zero, _mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  lw $t3, 24($fp)
  sw $t3, 0($t0)
  move $t0, $s0
  beq $t0, $zero, _mips_null_error
  li $t1, 8
  addu $t0, $t0, $t1
  lw $t3, 28($fp)
  sw $t3, 0($t0)
  move $v0, $zero
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 32
  move $fp, $t9
  jr $ra
Estudiante_aprobado:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _mips_null_error
  li $t1, 8
  addu $t0, $t0, $t1
  lw $t3, 0($t0)
  sw $t3, 20($fp)
  lw $t0, 20($fp)
  li $t1, 61
  sge $t2, $t0, $t1
  sw $t2, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
calcularPromedio:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  lw $t1, 20($fp)
  addu $t2, $t0, $t1
  sw $t2, 24($fp)
  lw $t0, 24($fp)
  li $t1, 2
  beq $t1, $zero, _mips_div_zero
  div $t0, $t1
  mflo $t2
  sw $t2, 24($fp)
  lw $v0, 24($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 28
  move $fp, $t9
  jr $ra
factorial:
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
  jal factorial
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
_mips_div_zero:
  la $a0, _mips_div_zero_message
  li $v0, 4
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

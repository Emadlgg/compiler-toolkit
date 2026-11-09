.data
_globals: .space 4
_mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0

_obj0__mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0
_obj1__mips_null_error_message: .byte 78, 117, 108, 108, 32, 114, 101, 102, 101, 114, 101, 110, 99, 101, 10, 0
_obj2__mips_div_zero_message: .byte 68, 105, 118, 105, 115, 105, 111, 110, 32, 98, 121, 32, 122, 101, 114, 111, 10, 0
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
  jal Libro_constructor
  lw $t0, 16($fp)
  sw $t0, 0($gp)
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 0($gp)
  sw $t0, 16($sp)
  jal Producto_obtenerPrecio
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
  jal Libro_precioConDescuento
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
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
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 0($gp)
  sw $t0, 16($sp)
  jal Producto_obtenerPrecio
  sw $v0, 16($fp)
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  li $t0, 100
  sw $t0, 20($sp)
  jal maximo
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
  li $t0, 200
  sw $t0, 16($sp)
  jal iva
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
  li $t0, 21
  sw $t0, 16($sp)
  jal doble
  sw $v0, 16($fp)
  lw $a0, 16($fp)
  li $v0, 1
  syscall
  li $v0, 11
  li $a0, 10
  syscall
  li $v0, 10
  syscall
doble:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  li $t1, 2
  mul $t2, $t0, $t1
  sw $t2, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
_mips_null_error:
  la $a0, _mips_null_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall
Producto_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _obj0__mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  li $t3, 100
  sw $t3, 0($t0)
  move $v0, $zero
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
Producto_obtenerPrecio:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  beq $t0, $zero, _obj0__mips_null_error
  li $t1, 0
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
_obj0__mips_null_error:
  la $a0, _obj0__mips_null_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall
Libro_constructor:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -4
  sw $s0, -4($fp)
  lw $s0, 16($fp)
  move $t0, $s0
  beq $t0, $zero, _obj1__mips_null_error
  li $t1, 0
  addu $t0, $t0, $t1
  li $t3, 80
  sw $t3, 0($t0)
  move $t0, $s0
  beq $t0, $zero, _obj1__mips_null_error
  li $t1, 4
  addu $t0, $t0, $t1
  li $t3, 250
  sw $t3, 0($t0)
  move $v0, $zero
  lw $s0, -4($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 20
  move $fp, $t9
  jr $ra
Libro_precioConDescuento:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -24
  sw $fp, 8($sp)
  sw $zero, 12($sp)
  lw $t0, 16($fp)
  sw $t0, 16($sp)
  jal Producto_obtenerPrecio
  sw $v0, 20($fp)
  lw $t0, 20($fp)
  li $t1, 10
  subu $t2, $t0, $t1
  sw $t2, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
_obj1__mips_null_error:
  la $a0, _obj1__mips_null_error_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall
maximo:
  move $fp, $sp
  sw $ra, 4($fp)
  addiu $sp, $sp, -8
  sw $s0, -4($fp)
  sw $s1, -8($fp)
  lw $s0, 16($fp)
  lw $s1, 20($fp)
  move $t0, $s0
  move $t1, $s1
  ble $t0, $t1, _obj2_L1
  move $v0, $s0
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
_obj2_L1:
  move $v0, $s1
  lw $s0, -4($fp)
  lw $s1, -8($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
iva:
  move $fp, $sp
  sw $ra, 4($fp)
  lw $t0, 16($fp)
  li $t1, 12
  mul $t2, $t0, $t1
  sw $t2, 20($fp)
  lw $t0, 20($fp)
  li $t1, 100
  beq $t1, $zero, _obj2__mips_div_zero
  div $t0, $t1
  mflo $t2
  sw $t2, 20($fp)
  lw $v0, 20($fp)
  sw $v0, 0($fp)
  lw $ra, 4($fp)
  lw $t9, 8($fp)
  addiu $sp, $fp, 24
  move $fp, $t9
  jr $ra
_obj2__mips_div_zero:
  la $a0, _obj2__mips_div_zero_message
  li $v0, 4
  syscall
  li $v0, 10
  syscall

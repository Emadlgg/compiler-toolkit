.data
.align 2

.text
.globl main

main:
    li $a0, 20
    li $a1, 22
    jal suma

    move $a0, $v0
    li $v0, 1
    syscall

    li $v0, 10
    syscall

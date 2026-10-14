func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    a = 7
    b = 3
    t0 = b * 2
    t0 = a + t0
    param t0
    call print, 1
    t0 = a + b
    t0 = t0 * 2
    param t0
    call print, 1
    t0 = a - b
    t0 = t0 - 1
    param t0
    call print, 1
    t0 = a / b
    param t0
    call print, 1
    t0 = a % b
    param t0
    call print, 1
    t0 = -a
    t0 = t0 + 10
    param t0
    call print, 1
    t0 = 3 * 4
    t0 = 2 + t0
    t0 = t0 - 5
    param t0
    call print, 1
    t0 = concat "hola", " "
    s = concat t0, "mundo"
    param s
    call print, 1
    x = 10
    x = x + 1
    param x
    call print, 1
    y = 0
    x = 5
    y = x
    param y
    call print, 1
    param x
    call print, 1
    halt

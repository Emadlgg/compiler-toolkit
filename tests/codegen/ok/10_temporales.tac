func main:                             ; nivel 0, registro de 28 bytes
    enter 28
    a = 1
    b = 2
    c = 3
    d = 4
    t0 = a + b
    t1 = c + d
    t0 = t0 * t1
    t1 = a * d
    t2 = b + c
    t1 = t1 / t2
    r = t0 - t1
    param r
    call print, 1
    t0 = a + b
    t0 = t0 + c
    t0 = t0 + d
    t0 = t0 + a
    t0 = t0 + b
    t0 = t0 + c
    s = t0 + d
    param s
    call print, 1
    halt

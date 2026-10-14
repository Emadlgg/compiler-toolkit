func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    t0 = false
    cond = t0
    neg = !cond
    t0 = true
    otra = t0
    concat_v = concat "a", "b"
    len_v = 3
    t0_v = 7
    param cond
    call print, 1
    param neg
    call print, 1
    param otra
    call print, 1
    param concat_v
    call print, 1
    t0 = len_v + t0_v
    param t0
    call print, 1
    halt

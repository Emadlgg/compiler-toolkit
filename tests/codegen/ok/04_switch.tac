func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    param 1
    t0 = call nombre, 1
    param t0
    call print, 1
    param 2
    t0 = call nombre, 1
    param t0
    call print, 1
    param 9
    t0 = call nombre, 1
    param t0
    call print, 1
    if 1 == 1 goto L6
    if 1 == 2 goto L7
    if 1 == 3 goto L8
    goto L5
  L6:
    param "a"
    call print, 1
  L7:
    param "b"
    call print, 1
    goto L5
  L8:
    param "c"
    call print, 1
  L5:
    c = 0
  L9:
    if c >= 4 goto L10
    c = c + 1
    if c == 2 goto L9
    param c
    call print, 1
    goto L9
  L10:
    halt

func nombre:                           ; nivel 1, registro de 24 bytes
    enter 24
    r = "otro"
    if n == 1 goto L2
    if n == 2 goto L3
    goto L4
  L2:
    r = "uno"
    goto L1
  L3:
    r = "dos"
    goto L1
  L4:
    r = "muchos"
  L1:
    return r

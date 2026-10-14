func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    n = 0
    i = 0
  L1:
    if i > 2 goto L3
    n = n + 1
    i = i + 1
    goto L1
  L3:
    param n
    call print, 1
    m = 0
  L5:
    if m >= 3 goto L7
    m = m + 1
    goto L5
  L7:
    param m
    call print, 1
    halt

func main:                             ; nivel 0, registro de 24 bytes
    enter 24
    param 1
    t1 = call f, 1
    ifFalse t1 goto L1
    param 2
    t1 = call t, 1
    ifFalse t1 goto L1
    t0 = true
    goto L2
  L1:
    t0 = false
  L2:
    r = t0
    param r
    call print, 1
    param 3
    t1 = call t, 1
    if t1 goto L5
    param 4
    t1 = call f, 1
    ifFalse t1 goto L3
  L5:
    t0 = true
    goto L4
  L3:
    t0 = false
  L4:
    r = t0
    param r
    call print, 1
    param 5
    t1 = call f, 1
    if t1 goto L8
    param 6
    t1 = call t, 1
    ifFalse t1 goto L6
  L8:
    t0 = true
    goto L7
  L6:
    t0 = false
  L7:
    r = t0
    param r
    call print, 1
    param 7
    t1 = call t, 1
    ifFalse t1 goto L9
    param 8
    t1 = call f, 1
    ifFalse t1 goto L9
    t0 = true
    goto L10
  L9:
    t0 = false
  L10:
    r = t0
    param r
    call print, 1
    t0 = !r
    param t0
    call print, 1
    param 9
    t0 = call t, 1
    ifFalse t0 goto L11
    param 10
    t0 = call f, 1
    if t0 goto L11
    param 100
    call print, 1
  L11:
    param 11
    t0 = call f, 1
    if t0 goto L14
    param 12
    t0 = call f, 1
    ifFalse t0 goto L13
  L14:
    param 200
    call print, 1
    goto L12
  L13:
    param 300
    call print, 1
  L12:
    a = 3
    b = 5
    t0 = a < b
    param t0
    call print, 1
    t0 = a >= b
    param t0
    call print, 1
    if a != 3 goto L15
    if b == 4 goto L15
    t0 = true
    goto L16
  L15:
    t0 = false
  L16:
    param t0
    call print, 1
    halt

func t:                                ; nivel 1, registro de 20 bytes
    enter 20
    param n
    call print, 1
    return true

func f:                                ; nivel 1, registro de 20 bytes
    enter 20
    param n
    call print, 1
    return false

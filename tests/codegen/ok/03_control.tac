func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    i = 0
  L1:
    if i >= 3 goto L2
    param i
    call print, 1
    i = i + 1
    goto L1
  L2:
  L3:
    param i
    call print, 1
    i = i - 1
    if i > 1 goto L3
    j = 0
  L6:
    if j >= 5 goto L8
    if j == 1 goto L7
    if j == 4 goto L8
    t0 = j * 10
    param t0
    call print, 1
  L7:
    j = j + 1
    goto L6
  L8:
    k = 0
  L11:
    k = k + 1
    if k <= 2 goto L11
    param k
    call print, 1
    n = 0
    p = 0
  L14:
    if p >= 3 goto L16
    q = 0
  L17:
    if q >= 3 goto L19
    if q == 2 goto L19
    n = n + 1
    q = q + 1
    goto L17
  L19:
    p = p + 1
    goto L14
  L16:
    param n
    call print, 1
    if n <= 5 goto L22
    param "grande"
    call print, 1
    goto L21
  L22:
    param "chico"
    call print, 1
  L21:
    halt

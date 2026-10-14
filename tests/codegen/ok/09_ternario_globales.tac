func main:                             ; nivel 0, registro de 24 bytes
    enter 24
    LIMITE = 10
    contador = 0
    call incrementar, 0
    call incrementar, 0
    param contador
    call print, 1
    x = 5
    if x <= 3 goto L1
    t0 = x
    goto L2
  L1:
    t0 = 3
  L2:
    m = t0
    param m
    call print, 1
    if x >= 3 goto L3
    t0 = "chico"
    goto L4
  L3:
    t0 = "grande"
  L4:
    param t0
    call print, 1
    if contador != 2 goto L5
    t0 = LIMITE * 2
    goto L6
  L5:
    t0 = 0
  L6:
    param t0
    call print, 1
    if x <= 3 goto L7
    if contador >= 5 goto L7
    t0 = true
    goto L8
  L7:
    t0 = false
  L8:
    bandera = t0
    param bandera
    call print, 1
    halt

func incrementar:                      ; nivel 1, registro de 20 bytes
    enter 20
    contador = contador + 1
    return

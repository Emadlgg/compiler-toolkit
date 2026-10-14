func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    base = 100
    param 1
    t0 = call exterior, 1
    param t0
    call print, 1
    t0 = call a1, 0
    param t0
    call print, 1
    param 4
    t0 = call contar, 1
    param t0
    call print, 1
    halt

func exterior:                         ; nivel 1, registro de 32 bytes
    enter 32
    x = 10
    param 5
    r = call exterior_interior, 1, link=0
    t0 = r + x
    return t0

func exterior_interior:                ; nivel 2, registro de 24 bytes
    enter 24
    x@1 = x@1 + 1
    t0 = call exterior_interior_profunda, 0, link=0
    return t0

func exterior_interior_profunda:       ; nivel 3, registro de 20 bytes
    enter 20
    t0 = x@2 + a@2
    t0 = t0 + b@1
    t0 = t0 + base
    return t0

func a1:                               ; nivel 1, registro de 24 bytes
    enter 24
    v = 5
    t0 = call a1_h2, 0, link=0
    return t0

func a1_h1:                            ; nivel 2, registro de 16 bytes
    enter 16
    return v@1

func a1_h2:                            ; nivel 2, registro de 20 bytes
    enter 20
    t0 = call a1_h1, 0, link=1
    t0 = t0 + 1
    return t0

func contar:                           ; nivel 1, registro de 24 bytes
    enter 24
    total = 0
    param n
    call contar_paso, 1, link=0
    return total

func contar_paso:                      ; nivel 2, registro de 24 bytes
    enter 24
    if k <= 0 goto L1
    total@1 = total@1 + k
    t0 = k - 1
    param t0
    call contar_paso, 1, link=1
  L1:
    return

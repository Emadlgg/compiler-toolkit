func main:                             ; nivel 0, registro de 24 bytes
    enter 24
    param 2
    param 3
    t0 = call suma, 2
    param t0
    call print, 1
    param 5
    t0 = call fact, 1
    param t0
    call print, 1
    param 10
    t0 = call fib, 1
    param t0
    call print, 1
    param "ana"
    call saludar, 1
    param 1
    param 2
    t0 = call suma, 2
    param t0
    t0 = call doble, 1
    param t0
    call print, 1
    param 1
    param 2
    t0 = call suma, 2
    param 3
    param 4
    t1 = call suma, 2
    param t0
    param t1
    t0 = call suma, 2
    param t0
    call print, 1
    halt

func suma:                             ; nivel 1, registro de 28 bytes
    enter 28
    t0 = a + b
    return t0

func fact:                             ; nivel 1, registro de 24 bytes
    enter 24
    if n > 1 goto L1
    return 1
  L1:
    t0 = n - 1
    param t0
    t0 = call fact, 1
    t0 = n * t0
    return t0

func fib:                              ; nivel 1, registro de 28 bytes
    enter 28
    if n >= 2 goto L2
    return n
  L2:
    t0 = n - 1
    param t0
    t0 = call fib, 1
    t1 = n - 2
    param t1
    t1 = call fib, 1
    t0 = t0 + t1
    return t0

func saludar:                          ; nivel 1, registro de 24 bytes
    enter 24
    t0 = concat "hola ", nombre
    param t0
    call print, 1
    return

func doble:                            ; nivel 1, registro de 24 bytes
    enter 24
    param x
    param x
    t0 = call suma, 2
    return t0

func main:                             ; nivel 0, registro de 32 bytes
    enter 32
    t0 = new Vehiculo, 12
    param t0
    call Vehiculo__init, 1
    param t0
    param "camion"
    call Vehiculo_constructor, 2
    v = t0
    param v
    t0 = call Vehiculo_describir, 1
    param t0
    call print, 1
    param v
    param 30
    t0 = call Vehiculo_acelerar, 2
    param t0
    call print, 1
    t0 = v.ruedas                      ; offset +0
    param t0
    call print, 1
    t0 = new Auto, 16
    param t0
    call Vehiculo__init, 1
    param t0
    call Auto__init, 1
    param t0
    param "sedan"
    param 4
    call Auto_constructor, 3
    a = t0
    param a
    t0 = call Vehiculo_describir, 1
    param t0
    call print, 1
    param a
    t0 = call Auto_turbo, 1
    param t0
    call print, 1
    t0 = a.velocidad                   ; offset +4
    param t0
    call print, 1
    t0 = a.puertas                     ; offset +12
    param t0
    call print, 1
    t0 = new Moto, 12
    param t0
    call Vehiculo__init, 1
    param t0
    param "ninja"
    call Moto_constructor, 2
    m = t0
    param m
    t0 = call Moto_describir, 1
    param t0
    call print, 1
    t0 = m.ruedas                      ; offset +0
    param t0
    call print, 1
    param m
    t0 = call Moto_caballito, 1
    param t0
    call print, 1
    param m
    param 10
    t0 = call Vehiculo_acelerar, 2
    param t0
    call print, 1
    t0 = new Deportivo, 20
    param t0
    call Vehiculo__init, 1
    param t0
    call Auto__init, 1
    param t0
    call Deportivo__init, 1
    param t0
    param "ferrari"
    call Deportivo_constructor, 2
    d = t0
    param d
    t0 = call Vehiculo_describir, 1
    param t0
    call print, 1
    param d
    t0 = call Auto_turbo, 1
    param t0
    call print, 1
    t0 = d.puertas                     ; offset +12
    param t0
    call print, 1
    t0 = d.ruedas                      ; offset +0
    param t0
    call print, 1
    param d
    t0 = call Deportivo_estado, 1
    param t0
    call print, 1
    d.bajado = false                   ; offset +16
    param d
    t0 = call Deportivo_estado, 1
    param t0
    call print, 1
    t0 = v.velocidad                   ; offset +4
    param t0
    call print, 1
    t0 = a.velocidad                   ; offset +4
    param t0
    call print, 1
    t0 = m.velocidad                   ; offset +4
    param t0
    call print, 1
    t0 = d.velocidad                   ; offset +4
    param t0
    call print, 1
    t0 = new Garage, 4
    param t0
    param a
    call Garage_constructor, 2
    g = t0
    param g
    t0 = call Garage_velocidadGuardada, 1
    param t0
    call print, 1
    param a
    param 5
    t0 = call Vehiculo_acelerar, 2
    param g
    t0 = call Garage_velocidadGuardada, 1
    param t0
    call print, 1
    t0 = g.guardado                    ; offset +0
    t0 = t0.puertas                    ; offset +12
    param t0
    call print, 1
    t0 = newarray 2
    t1 = new Moto, 12
    param t1
    call Vehiculo__init, 1
    param t1
    param "a"
    call Moto_constructor, 2
    t0[0] = t1
    t1 = new Moto, 12
    param t1
    call Vehiculo__init, 1
    param t1
    param "b"
    call Moto_constructor, 2
    t0[1] = t1
    motos = t0
    total = 0
    t0 = motos
    t1 = len t0
    t2 = 0
  L1:
    if t2 >= t1 goto L3
    x = t0[t2]
    t3 = x.ruedas                      ; offset +0
    total = total + t3
    param x
    t3 = call Moto_caballito, 1
    param t3
    call print, 1
    t2 = t2 + 1
    goto L1
  L3:
    param total
    call print, 1
    halt

func Vehiculo_constructor:             ; nivel 1, registro de 24 bytes
    enter 24
    this.nombre = n                    ; offset +8
    return

func Vehiculo_acelerar:                ; nivel 1, registro de 28 bytes
    enter 28
    t0 = this.velocidad                ; offset +4
    t0 = t0 + delta
    this.velocidad = t0                ; offset +4
    t0 = this.velocidad                ; offset +4
    return t0

func Vehiculo_describir:               ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.nombre                   ; offset +8
    return t0

func Vehiculo__init:                   ; nivel 1, registro de 20 bytes
    enter 20
    this.ruedas = 4                    ; offset +0
    this.velocidad = 0                 ; offset +4
    this.nombre = "vehiculo"           ; offset +8
    return

func Auto_constructor:                 ; nivel 1, registro de 28 bytes
    enter 28
    this.nombre = n                    ; offset +8
    this.puertas = p                   ; offset +12
    return

func Auto_turbo:                       ; nivel 1, registro de 24 bytes
    enter 24
    param this
    param 50
    t0 = call Vehiculo_acelerar, 2
    param this
    param 50
    t0 = call Vehiculo_acelerar, 2
    return t0

func Auto__init:                       ; nivel 1, registro de 20 bytes
    enter 20
    this.puertas = 4                   ; offset +12
    return

func Moto_constructor:                 ; nivel 1, registro de 24 bytes
    enter 24
    this.nombre = n                    ; offset +8
    this.ruedas = 2                    ; offset +0
    return

func Moto_describir:                   ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.nombre                   ; offset +8
    t0 = concat "moto ", t0
    return t0

func Moto_caballito:                   ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.nombre                   ; offset +8
    t0 = concat t0, " en dos ruedas"
    return t0

func Deportivo_constructor:            ; nivel 1, registro de 24 bytes
    enter 24
    this.nombre = n                    ; offset +8
    this.puertas = 2                   ; offset +12
    return

func Deportivo_estado:                 ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.bajado                   ; offset +16
    return t0

func Deportivo__init:                  ; nivel 1, registro de 20 bytes
    enter 20
    this.bajado = true                 ; offset +16
    return

func Garage_constructor:               ; nivel 1, registro de 24 bytes
    enter 24
    this.guardado = a                  ; offset +0
    return

func Garage_velocidadGuardada:         ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.guardado                 ; offset +0
    t0 = t0.velocidad                  ; offset +4
    return t0

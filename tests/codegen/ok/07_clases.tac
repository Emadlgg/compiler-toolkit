func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    t0 = new Animal, 8
    param t0
    call Animal__init, 1
    param t0
    param "gato"
    call Animal_constructor, 2
    a = t0
    param a
    t0 = call Animal_describir, 1
    param t0
    call print, 1
    param a
    t0 = call Animal_contarPatas, 1
    param t0
    call print, 1
    t0 = new Perro, 12
    param t0
    call Animal__init, 1
    param t0
    call Perro__init, 1
    param t0
    param "rex"
    param "lab"
    call Perro_constructor, 3
    p = t0
    param p
    t0 = call Perro_ladrar, 1
    param t0
    call print, 1
    param p
    t0 = call Animal_describir, 1
    param t0
    call print, 1
    t0 = p.raza                        ; offset +8
    param t0
    call print, 1
    p.patas = 3                        ; offset +4
    param p
    t0 = call Animal_contarPatas, 1
    param t0
    call print, 1
    p.raza = "pug"                     ; offset +8
    t0 = p.raza                        ; offset +8
    param t0
    call print, 1
    t0 = new Contador, 4
    param t0
    call Contador__init, 1
    c = t0
    param c
    t0 = call Contador_inc, 1
    param c
    t0 = call Contador_inc, 1
    param c
    t0 = call Contador_inc, 1
    param t0
    call print, 1
    halt

func Animal_constructor:               ; nivel 1, registro de 24 bytes
    enter 24
    this.nombre = n                    ; offset +0
    return

func Animal_describir:                 ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.nombre                   ; offset +0
    return t0

func Animal_contarPatas:               ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.patas                    ; offset +4
    return t0

func Animal__init:                     ; nivel 1, registro de 20 bytes
    enter 20
    this.nombre = "sin nombre"         ; offset +0
    this.patas = 4                     ; offset +4
    return

func Perro_constructor:                ; nivel 1, registro de 28 bytes
    enter 28
    this.nombre = n                    ; offset +0
    this.raza = r                      ; offset +8
    return

func Perro_ladrar:                     ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.nombre                   ; offset +0
    t0 = concat t0, " ladra"
    return t0

func Perro__init:                      ; nivel 1, registro de 20 bytes
    enter 20
    this.raza = "mestizo"              ; offset +8
    return

func Contador_inc:                     ; nivel 1, registro de 24 bytes
    enter 24
    t0 = this.n                        ; offset +0
    t0 = t0 + 1
    this.n = t0                        ; offset +0
    t0 = this.n                        ; offset +0
    return t0

func Contador__init:                   ; nivel 1, registro de 20 bytes
    enter 20
    this.n = 0                         ; offset +0
    return

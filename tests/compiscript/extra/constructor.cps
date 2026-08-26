class Persona {
    function constructor(nombre: string) {
    }
}

// Correcto
let p1: Persona = new Persona("Juan");

// Debe dar error: constructor espera string
let p2: Persona = new Persona(123);

// Debe dar error: falta argumento
let p3: Persona = new Persona();
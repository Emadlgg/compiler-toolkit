class Persona {
    let nombre: string;
}

let p: Persona = new Persona();

// Debe dar error: atributo inexistente
let x = p.edad;
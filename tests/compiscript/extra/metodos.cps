class Persona {
    function saludar(): string {
        return "Hola";
    }
}

let p: Persona = new Persona();

// Debe dar error: método inexistente
let x = p.despedir();
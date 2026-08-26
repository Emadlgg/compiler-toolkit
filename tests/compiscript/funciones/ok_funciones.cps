function suma(a: integer, b: integer): integer {
    return a + b;
}

function saludar(nombre: string): string {
    return "Hola " + nombre;
}

function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

let r = suma(5, 3);
let s = saludar("Mundo");
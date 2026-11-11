class Persona {
    let nombre: string;
    let edad: integer;

    function constructor(nombre: string, edad: integer) {
        this.nombre = nombre;
        this.edad = edad;
    }

    function mostrarEdad(): integer {
        return this.edad;
    }
}

class Estudiante : Persona {
    let nota: integer;

    function constructor(nombre: string, edad: integer, nota: integer) {
        this.nombre = nombre;
        this.edad = edad;
        this.nota = nota;
    }

    function aprobado(): boolean {
        return this.nota >= 61;
    }
}

function calcularPromedio(a: integer, b: integer): integer {
    return (a + b) / 2;
}

function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    }

    return n * factorial(n - 1);
}

let estudiante: Estudiante = new Estudiante("Ana", 20, 85);

print("=== DATOS DEL ESTUDIANTE ===");
print(estudiante.mostrarEdad());

if (estudiante.aprobado()) {
    print("Aprobado");
} else {
    print("Reprobado");
}

print("=== PROMEDIO ===");

let promedio: integer = calcularPromedio(80, 90);
print(promedio);

print("=== CICLO ===");

let contador: integer = 0;

while (contador < 3) {
    print(contador);
    contador = contador + 1;
}

print("=== RECURSIVIDAD ===");
print(factorial(5));

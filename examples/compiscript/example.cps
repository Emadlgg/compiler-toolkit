// ============================================================
// stress_test.cps
// Prueba grande para el analizador semantico de Compiscript
//
// Contiene:
//   - variables y constantes
//   - tipos
//   - arreglos
//   - funciones
//   - recursion
//   - clases
//   - constructores
//   - herencia
//   - this
//   - if / else
//   - while / do-while
//   - for / foreach
//   - switch
//   - try / catch
//   - errores semanticos intencionales
// ============================================================


// ============================================================
// 1. VARIABLES Y CONSTANTES VALIDAS
// ============================================================

let edad: integer = 21;
let nombre: string = "Osman";
let activo: boolean = true;

let contador = 0;
let mensaje = "Compiscript funcionando";

const LIMITE: integer = 10;
const SALUDO: string = "Hola";

let numeros: integer[] = [1, 2, 3, 4, 5];
let matriz: integer[][] = [[1, 2], [3, 4]];

print(nombre);
print(edad);
print(mensaje);


// ============================================================
// 2. OPERACIONES VALIDAS
// ============================================================

let a: integer = 10;
let b: integer = 20;

let suma: integer = a + b;
let resta: integer = b - a;
let multiplicacion: integer = a * b;
let division: integer = b / a;
let modulo: integer = b % a;

let comparacion: boolean = a < b;
let igualdad: boolean = a == b;

let condicion: boolean = activo && comparacion;
let otraCondicion: boolean = activo || igualdad;

let textoCompleto: string = SALUDO + nombre;


// ============================================================
// 3. FUNCIONES VALIDAS
// ============================================================

function sumar(x: integer, y: integer): integer {
    return x + y;
}

function restar(x: integer, y: integer): integer {
    return x - y;
}

function esMayor(x: integer, y: integer): boolean {
    return x > y;
}

function obtenerSaludo(persona: string): string {
    return "Hola " + persona;
}

function mostrarMensaje(texto: string): void {
    print(texto);
}

let resultadoSuma: integer = sumar(10, 20);
let resultadoResta: integer = restar(50, 15);
let resultadoBooleano: boolean = esMayor(100, 20);

mostrarMensaje("Probando funciones");


// ============================================================
// 4. RECURSION
// ============================================================

function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    }

    return n * factorial(n - 1);
}

let resultadoFactorial: integer = factorial(5);


// ============================================================
// 5. SCOPES
// ============================================================

let globalX: integer = 100;

{
    let localX: integer = 20;
    let localTexto: string = "scope interno";

    print(globalX);
    print(localX);

    {
        let nivelDos: integer = 300;
        print(nivelDos);
        print(localX);
        print(globalX);
    }
}


// ============================================================
// 6. IF / ELSE
// ============================================================

if (edad >= 18) {
    let estado: string = "adulto";
    print(estado);
} else {
    let estado: string = "menor";
    print(estado);
}

if (activo && edad > 10) {
    print("Usuario activo");
}


// ============================================================
// 7. WHILE
// ============================================================

let i: integer = 0;

while (i < 5) {
    print(i);
    i = i + 1;
}


// ============================================================
// 8. DO WHILE
// ============================================================

let j: integer = 3;

do {
    j = j - 1;
    print(j);
} while (j > 0);


// ============================================================
// 9. FOR
// ============================================================

for (let k: integer = 0; k < 5; k = k + 1) {
    print(k);
}


// ============================================================
// 10. FOREACH
// ============================================================

foreach (numero in numeros) {
    print(numero);
}


// ============================================================
// 11. SWITCH
// ============================================================

let opcion: integer = 2;

switch (opcion) {
    case 1:
        print("Opcion uno");
        break;

    case 2:
        print("Opcion dos");
        break;

    case 3:
        print("Opcion tres");
        break;

    default:
        print("Otra opcion");
}


// ============================================================
// 12. TRY / CATCH
// ============================================================

try {
    let elemento = numeros[0];
    print(elemento);
} catch (error) {
    print(error);
}


// ============================================================
// 13. CLASE PERSONA
// ============================================================

class Persona {

    let nombre: string;
    let edad: integer;

    function constructor(n: string, e: integer): void {
        this.nombre = n;
        this.edad = e;
    }

    function obtenerNombre(): string {
        return this.nombre;
    }

    function obtenerEdad(): integer {
        return this.edad;
    }

    function esAdulto(): boolean {
        return this.edad >= 18;
    }
}


// ============================================================
// 14. INSTANCIAS VALIDAS
// ============================================================

let persona1: Persona = new Persona("Ana", 25);
let persona2: Persona = new Persona("Carlos", 17);

let nombrePersona: string = persona1.obtenerNombre();
let edadPersona: integer = persona1.obtenerEdad();
let adulto: boolean = persona1.esAdulto();


// ============================================================
// 15. HERENCIA
// ============================================================

class Estudiante : Persona {

    let carnet: string;

    function obtenerCarnet(): string {
        return this.carnet;
    }
}


// ============================================================
// 16. ARREGLOS
// ============================================================

let valores: integer[] = [10, 20, 30, 40];

let primero: integer = valores[0];
let segundo: integer = valores[1];

print(primero);
print(segundo);


// ============================================================
// 17. TERNARIO
// ============================================================

let resultadoTernario: string =
    edad >= 18 ? "Mayor" : "Menor";


// ============================================================
// A PARTIR DE AQUI HAY ERRORES INTENCIONALES
// ============================================================


// ============================================================
// ERROR 1
// Variable no declarada
// ============================================================

print(variableQueNoExiste);


// ============================================================
// ERROR 2
// Redeclaracion en el mismo scope
// ============================================================

let duplicada: integer = 10;
let duplicada: integer = 20;


// ============================================================
// ERROR 3
// Tipo incorrecto
// Esperado integer, recibido string
// ============================================================

let numeroIncorrecto: integer = "esto no es un numero";


// ============================================================
// ERROR 4
// Tipo incorrecto
// Esperado boolean, recibido integer
// ============================================================

let booleanIncorrecto: boolean = 123;


// ============================================================
// ERROR 5
// Operacion invalida
// integer + string
// ============================================================

let operacionIncorrecta = 10 + "hola";


// ============================================================
// ERROR 6
// Operacion aritmetica con boolean
// ============================================================

let otraOperacionIncorrecta = true * 10;


// ============================================================
// ERROR 7
// Reasignacion de constante
// ============================================================

const NO_CAMBIAR: integer = 100;

NO_CAMBIAR = 200;


// ============================================================
// ERROR 8
// Llamada con cantidad incorrecta de argumentos
// sumar espera 2
// ============================================================

let llamadaIncorrecta = sumar(10);


// ============================================================
// ERROR 9
// Tipo incorrecto como argumento
// sumar espera integer, integer
// ============================================================

let argumentosIncorrectos = sumar("hola", 20);


// ============================================================
// ERROR 10
// Variable no declarada dentro de funcion
// ============================================================

function funcionConError(): integer {

    let interno: integer = 10;

    print(noDeclaradaDentro);

    return interno;
}


// ============================================================
// ERROR 11
// return fuera de una funcion
// ============================================================

return 100;


// ============================================================
// ERROR 12
// break fuera de un loop
// ============================================================

break;


// ============================================================
// ERROR 13
// continue fuera de un loop
// ============================================================

continue;


// ============================================================
// ERROR 14
// condicion de if no booleana
// ============================================================

if (123) {
    print("Esto deberia generar error");
}


// ============================================================
// ERROR 15
// condicion de while no booleana
// ============================================================

while ("hola") {
    print("Condicion incorrecta");
    break;
}


// ============================================================
// ERROR 16
// retorno incorrecto
// La funcion promete integer
// ============================================================

function retornoIncorrecto(): integer {
    return "string incorrecto";
}


// ============================================================
// ERROR 17
// Funcion void retornando un valor
// ============================================================

function voidIncorrecto(): void {
    return 100;
}


// ============================================================
// ERROR 18
// Codigo muerto despues de return
// ============================================================

function codigoMuerto(): integer {

    let valor: integer = 50;

    return valor;

    let nuncaEjecutada: integer = 999;
}


// ============================================================
// ERROR 19
// Clase que no existe
// ============================================================

let objetoFantasma = new ClaseQueNoExiste();


// ============================================================
// ERROR 20
// Constructor con cantidad incorrecta de argumentos
// Persona necesita string, integer
// ============================================================

let personaIncorrecta = new Persona("SoloNombre");


// ============================================================
// ERROR 21
// Constructor con tipos incorrectos
// ============================================================

let personaTiposIncorrectos =
    new Persona(123, "veinte");


// ============================================================
// ERROR 22
// Atributo que no existe
// ============================================================

let atributoFantasma = persona1.apellido;


// ============================================================
// ERROR 23
// Metodo que no existe
// ============================================================

persona1.metodoFantasma();


// ============================================================
// ERROR 24
// this fuera de una clase
// ============================================================

let thisIncorrecto = this;


// ============================================================
// ERROR 25
// Array indexado con string
// ============================================================

let indiceIncorrecto = valores["uno"];


// ============================================================
// ERROR 26
// Array con tipos incompatibles
// ============================================================

let arregloIncorrecto = [1, 2, "tres", 4];


// ============================================================
// ERROR 27
// Ternario con condicion no booleana
// ============================================================

let ternarioIncorrecto =
    100 ? "verdadero" : "falso";


// ============================================================
// FIN
// ============================================================

print("Fin del stress test");
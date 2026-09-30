let limite: integer = 18;
let nombre: string = "Ana";

function verificar(edad: integer): boolean {
    let contador: integer = 1;

    if (edad >= limite) {
        contador = "incorrecto";
        return true;
    }

    return edad;
}

let resultado = verificar(20);
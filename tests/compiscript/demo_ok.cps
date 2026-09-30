let limite: integer = 18;
let mensaje = "Analizando usuario";

function esMayor(edad: integer): boolean {
    if (edad >= limite) {
        return true;
    }

    return false;
}

let edad: integer = 20;
let resultado = esMayor(edad);

if (resultado) {
    print(mensaje);
}
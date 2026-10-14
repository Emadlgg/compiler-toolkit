// Operador ternario, constantes y variables globales usadas desde funciones
const LIMITE: integer = 10;
let contador: integer = 0;
function incrementar(): void { contador = contador + 1; }

incrementar();
incrementar();
print(contador);

let x: integer = 5;
let m: integer = x > 3 ? x : 3;
print(m);
print(x < 3 ? "chico" : "grande");
print(contador == 2 ? LIMITE * 2 : 0);
let bandera: boolean = x > 3 && contador < 5;
print(bandera);

import { sumar, multiplicar } from "./build/Matematicas.cplobj";

print("=== IMPORTACION DESDE BIBLIOTECA ===");

let resultado1: integer = sumar(10, 20);
let resultado2: integer = multiplicar(4, 5);

print(resultado1);
print(resultado2);

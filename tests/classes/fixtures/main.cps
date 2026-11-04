import { Base } from "./Base";
import { Derivada } from "./Derivada";
import { Nieta } from "./Nieta";

let a = new Base(7);
print(a.sumar(3));           // 10
print(a.descripcion());      // 100

let b = new Derivada(10, 3);
print(b.total());            // 13: metodo heredado y atributos propios
print(b.descripcion());      // 200: metodo redefinido
print(b.pasos);              // 1: atributo heredado

let c = new Nieta(20);
print(c.combinado());        // 29: 20 + 4 + 5
print(c.descripcion());      // 200: redefinicion heredada
print(c.pasos);              // 1: estado propio de cada instancia
print(b.pasos);              // 1: sin interferencia entre instancias

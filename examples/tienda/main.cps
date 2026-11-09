import { Libro } from "./build/Libro.cplobj";
import { maximo, iva } from "./build/Utilidades.cplobj";
import { doble } from "./Calculadora";

let l = new Libro();
print(l.obtenerPrecio());
print(l.precioConDescuento());
print(l.paginas);
print(maximo(l.obtenerPrecio(), 100));
print(iva(200));
print(doble(21));

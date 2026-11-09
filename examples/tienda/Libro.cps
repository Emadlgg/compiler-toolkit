import { Producto } from "./build/Producto.cplobj";

export class Libro : Producto {
    let paginas: integer;
    function constructor() { this.precio = 80; this.paginas = 250; }
    function precioConDescuento(): integer { return this.obtenerPrecio() - 10; }
}

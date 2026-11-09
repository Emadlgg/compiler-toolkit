import { Animal } from "./build/Animal.cplobj";

export class Perro : Animal {
    let bono: integer;
    function constructor() { this.edad = 5; this.bono = 2; }
    function total(): integer { return this.obtener() + this.bono; }
}

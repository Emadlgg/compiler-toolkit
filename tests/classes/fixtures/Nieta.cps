import { Derivada } from "./Derivada";

export class Nieta : Derivada {
    let bono: integer = 5;

    function constructor(inicial: integer) {
        this.valor = inicial;
        this.extra = 4;
    }

    function combinado(): integer {
        return this.total() + this.bono;
    }
}

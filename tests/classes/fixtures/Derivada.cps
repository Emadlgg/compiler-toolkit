import { Base } from "./Base";

export class Derivada : Base {
    let extra: integer = 2;

    function constructor(inicial: integer, incremento: integer) {
        this.valor = inicial;
        this.extra = incremento;
    }

    function descripcion(): integer {
        return 200;
    }

    function total(): integer {
        return this.sumar(this.extra);
    }
}

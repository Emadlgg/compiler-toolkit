export class Base {
    let valor: integer = 3;
    let pasos: integer = 0;

    function constructor(inicial: integer) {
        this.valor = inicial;
    }

    function sumar(delta: integer): integer {
        this.valor = this.valor + delta;
        this.pasos = this.pasos + 1;
        return this.valor;
    }

    function descripcion(): integer {
        return 100;
    }
}

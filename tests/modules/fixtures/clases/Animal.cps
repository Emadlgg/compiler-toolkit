export class Animal {
    let nombre: string;
    let edad: integer;

    function constructor() {
        this.nombre = "Rex";
        this.edad = 5;
    }

    function crecer(): integer {
        this.edad = this.edad + 1;
        return this.edad;
    }
}

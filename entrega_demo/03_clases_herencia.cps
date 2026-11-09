class Persona {
    let nombre: string;
    let edad: integer;
    function constructor() {
        this.nombre = "Ana";
        this.edad = 20;
    }
    function cumplir(): integer {
        this.edad = this.edad + 1;
        return this.edad;
    }
}
class Estudiante : Persona {
    let carnet: integer;
    function constructor() {
        this.nombre = "Luis";
        this.edad = 19;
        this.carnet = 2024;
    }
    function id(): integer { return this.carnet; }
}
let e = new Estudiante();
print(e.nombre);
print(e.cumplir());
print(e.id());

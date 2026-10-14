// Objetos, constructor, atributos con valor inicial, métodos, this y herencia
class Animal {
    let nombre: string = "sin nombre";
    let patas: integer = 4;
    function constructor(n: string) { this.nombre = n; }
    function describir(): string { return this.nombre; }
    function contarPatas(): integer { return this.patas; }
}

class Perro : Animal {
    let raza: string = "mestizo";
    function constructor(n: string, r: string) {
        this.nombre = n;
        this.raza = r;
    }
    function ladrar(): string { return this.nombre + " ladra"; }
}

let a = new Animal("gato");
print(a.describir());
print(a.contarPatas());

let p = new Perro("rex", "lab");
print(p.ladrar());
print(p.describir());
print(p.raza);
p.patas = 3;
print(p.contarPatas());
p.raza = "pug";
print(p.raza);

class Contador {
    let n: integer = 0;
    function inc(): integer {
        this.n = this.n + 1;
        return this.n;
    }
}
let c = new Contador();
c.inc();
c.inc();
print(c.inc());

// Herencia en tres niveles (Vehiculo -> Auto -> Deportivo), un método redefinido (Moto),
// métodos que llaman a otros métodos, composición (Garage guarda un Auto) y una lista de objetos
class Vehiculo {
    let ruedas: integer = 4;
    let velocidad: integer = 0;
    let nombre: string = "vehiculo";
    function constructor(n: string) { this.nombre = n; }
    function acelerar(delta: integer): integer {
        this.velocidad = this.velocidad + delta;
        return this.velocidad;
    }
    function describir(): string { return this.nombre; }
}

class Auto : Vehiculo {
    let puertas: integer = 4;
    function constructor(n: string, p: integer) {
        this.nombre = n;
        this.puertas = p;
    }
    function turbo(): integer {
        this.acelerar(50);
        return this.acelerar(50);
    }
}

class Moto : Vehiculo {
    function constructor(n: string) {
        this.nombre = n;
        this.ruedas = 2;
    }
    function describir(): string { return "moto " + this.nombre; }
    function caballito(): string { return this.nombre + " en dos ruedas"; }
}

class Deportivo : Auto {
    let bajado: boolean = true;
    function constructor(n: string) {
        this.nombre = n;
        this.puertas = 2;
    }
    function estado(): boolean { return this.bajado; }
}

class Garage {
    let guardado: Auto;
    function constructor(a: Auto) { this.guardado = a; }
    function velocidadGuardada(): integer { return this.guardado.velocidad; }
}

let v = new Vehiculo("camion");
print(v.describir());
print(v.acelerar(30));
print(v.ruedas);

let a = new Auto("sedan", 4);
print(a.describir());
print(a.turbo());
print(a.velocidad);
print(a.puertas);

let m = new Moto("ninja");
print(m.describir());
print(m.ruedas);
print(m.caballito());
print(m.acelerar(10));

let d = new Deportivo("ferrari");
print(d.describir());
print(d.turbo());
print(d.puertas);
print(d.ruedas);
print(d.estado());
d.bajado = false;
print(d.estado());

print(v.velocidad);
print(a.velocidad);
print(m.velocidad);
print(d.velocidad);

let g = new Garage(a);
print(g.velocidadGuardada());
a.acelerar(5);
print(g.velocidadGuardada());
print(g.guardado.puertas);

let motos: Moto[] = [new Moto("a"), new Moto("b")];
let total: integer = 0;
foreach (x in motos) {
    total = total + x.ruedas;
    print(x.caballito());
}
print(total);

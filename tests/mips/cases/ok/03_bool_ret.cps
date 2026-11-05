function esPar(n: integer): boolean { return n % 2 == 0; }
print(esPar(4));
print(esPar(3));
let r: boolean = esPar(2);
print(r);
class A { function ok(): boolean { return true; } }
let a = new A();
print(a.ok());

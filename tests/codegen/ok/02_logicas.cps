// Cortocircuito: las funciones imprimen su argumento para ver qué se evalúa
function t(n: integer): boolean { print(n); return true; }
function f(n: integer): boolean { print(n); return false; }

let r: boolean = f(1) && t(2);
print(r);
r = t(3) || f(4);
print(r);
r = f(5) || t(6);
print(r);
r = t(7) && f(8);
print(r);
print(!r);

if (t(9) && !f(10)) { print(100); }
if (f(11) || f(12)) { print(200); } else { print(300); }

let a: integer = 3;
let b: integer = 5;
print(a < b);
print(a >= b);
print(a == 3 && b != 4);

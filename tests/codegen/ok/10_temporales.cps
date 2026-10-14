// Expresión larga: sirve para ver que los temporales se reciclan
let a: integer = 1;
let b: integer = 2;
let c: integer = 3;
let d: integer = 4;
let r: integer = (a + b) * (c + d) - (a * d) / (b + c);
print(r);
let s: integer = a + b + c + d + a + b + c + d;
print(s);

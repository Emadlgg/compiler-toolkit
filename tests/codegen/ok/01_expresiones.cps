// Precedencia, asociatividad, unarios, cadenas y asignaciones encadenadas
let a: integer = 7;
let b: integer = 3;
print(a + b * 2);
print((a + b) * 2);
print(a - b - 1);
print(a / b);
print(a % b);
print(-a + 10);
print(2 + 3 * 4 - 5);
let s: string = "hola" + " " + "mundo";
print(s);
let x: integer = 10;
x = x + 1;
print(x);
let y: integer = 0;
y = x = 5;
print(y);
print(x);

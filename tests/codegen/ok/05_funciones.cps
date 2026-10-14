// Parámetros, valores de retorno, procedimientos y recursión
function suma(a: integer, b: integer): integer { return a + b; }

function fact(n: integer): integer {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}

function fib(n: integer): integer {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}

function saludar(nombre: string): void { print("hola " + nombre); }
function doble(x: integer): integer { return suma(x, x); }

print(suma(2, 3));
print(fact(5));
print(fib(10));
saludar("ana");
print(doble(suma(1, 2)));
print(suma(suma(1, 2), suma(3, 4)));

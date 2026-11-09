function fact(n: integer): integer {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
function fib(n: integer): integer {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}
function suma(a: integer, b: integer, c: integer): integer {
    return a + b + c;
}
print(fact(5));
print(fib(10));
print(suma(1, 2, 3));

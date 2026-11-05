function fib(n: integer): integer { if (n < 2) { return n; } return fib(n-1) + fib(n-2); }
function fact(n: integer): integer { if (n <= 1) { return 1; } return n * fact(n-1); }
function suma(n: integer): integer { if (n == 0) { return 0; } return n + suma(n-1); }
print(fib(20));
print(fact(10));
print(suma(5000));

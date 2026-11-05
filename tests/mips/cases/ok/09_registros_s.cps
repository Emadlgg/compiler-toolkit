function suma(n: integer): integer {
    let acc: integer = 0;
    let i: integer = 1;
    while (i <= n) { acc = acc + i; i = i + 1; }
    return acc;
}
function f(a: integer): integer {
    let x: integer = a * 2;
    let y: integer = suma(a);
    return x + y + suma(3);
}
function diez(): integer {
    let a: integer = 1; let b: integer = 2; let c: integer = 3; let d: integer = 4;
    let e: integer = 5; let f2: integer = 6; let g: integer = 7; let h: integer = 8;
    let i: integer = 9; let j: integer = 10; let k: integer = 0; let s: integer = 0;
    while (k < 3) { s = s + a + b + c + d + e + f2 + g + h + i + j; k = k + 1; }
    return s;
}
function cnt(n: integer): integer {
    let total: integer = 0;
    function add(x: integer): integer { total = total + x; return total; }
    let i: integer = 0;
    while (i < n) { add(i); i = i + 1; }
    return total;
}
function g(n: integer): integer {
    if (n == 0) { return 0; }
    let local: integer = n;
    let r: integer = g(n - 1);
    return local + r;
}
print(suma(4));
print(f(4));
print(diez());
print(cnt(5));
print(g(10));

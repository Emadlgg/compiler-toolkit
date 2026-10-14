// Funciones anidadas que leen y modifican variables del entorno donde se definieron
let base: integer = 100;

function exterior(a: integer): integer {
    let x: integer = 10;
    function interior(b: integer): integer {
        function profunda(): integer {
            return x + a + b + base;
        }
        x = x + 1;
        return profunda();
    }
    let r: integer = interior(5);
    return r + x;
}
print(exterior(1));

function a1(): integer {
    let v: integer = 5;
    function h1(): integer { return v; }
    function h2(): integer { return h1() + 1; }
    return h2();
}
print(a1());

function contar(n: integer): integer {
    let total: integer = 0;
    function paso(k: integer): void {
        if (k > 0) {
            total = total + k;
            paso(k - 1);
        }
    }
    paso(n);
    return total;
}
print(contar(4));

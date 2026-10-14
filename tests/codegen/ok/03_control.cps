// while, do-while, for, break, continue y bucles anidados
let i: integer = 0;
while (i < 3) { print(i); i = i + 1; }

do { print(i); i = i - 1; } while (i > 1);

for (let j: integer = 0; j < 5; j = j + 1) {
    if (j == 1) { continue; }
    if (j == 4) { break; }
    print(j * 10);
}

let k: integer = 0;
while (true) {
    k = k + 1;
    if (k > 2) { break; }
}
print(k);

let n: integer = 0;
for (let p: integer = 0; p < 3; p = p + 1) {
    for (let q: integer = 0; q < 3; q = q + 1) {
        if (q == 2) { break; }
        n = n + 1;
    }
}
print(n);
if (n > 5) { print("grande"); } else { print("chico"); }

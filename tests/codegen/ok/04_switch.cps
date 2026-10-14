// switch con break, default, caída entre casos y continue hacia el bucle de afuera
function nombre(n: integer): string {
    let r: string = "otro";
    switch (n) {
        case 1: r = "uno"; break;
        case 2: r = "dos"; break;
        default: r = "muchos";
    }
    return r;
}
print(nombre(1));
print(nombre(2));
print(nombre(9));

switch (1) {
    case 1: print("a");
    case 2: print("b"); break;
    case 3: print("c");
}

let c: integer = 0;
while (c < 4) {
    c = c + 1;
    switch (c) {
        case 2: continue;
        default: print(c);
    }
}

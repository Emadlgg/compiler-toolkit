// No existen funciones de primera clase: usar una función como valor no se puede traducir
function suma(a: integer, b: integer): integer { return a + b; }
let g = suma;

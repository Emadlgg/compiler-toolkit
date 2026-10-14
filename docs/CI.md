# Lenguaje intermedio de Compiscript (TAC)

Este documento describe el código de tres direcciones que genera el compilador: sus instrucciones, las convenciones de llamadas, objetos y listas, cómo se traduce cada construcción del lenguaje y qué supuestos se tomaron. Los ejemplos de traducción los produjo el propio compilador (`python compiscript.py archivo.cps --tac`); no están escritos a mano.

## 1. Forma de un programa

El TAC de un programa es una lista de bloques. El primero es `main`, con el código que está fuera de cualquier función. Después va un bloque por cada función, método o inicializador de clase, en el orden en que se declaran (una función anidada aparece después de la que la contiene).

```
func main:                  ; nivel 0, registro de 20 bytes
    enter 20
    ...
    halt

func suma:                  ; nivel 1, registro de 28 bytes
    enter 28
    ...
    return t0
```

* `func nombre:` abre un bloque. El comentario indica el nivel léxico y el tamaño del registro de activación.
* `enter n` reserva el registro de activación de `n` bytes. Es la primera instrucción de cada bloque.
* `main` termina con `halt`; las funciones terminan con `return`.
* Las variables globales no viven en el registro de `main`: están en un área de datos aparte, cada una en su offset.
* Las etiquetas de salto se llaman `L1`, `L2`, … y no se repiten en el programa. Las que ningún salto usa se eliminan, y también el código que queda inalcanzable después de un `goto` o un `return`.

## 2. Operandos

| Operando | Significado |
| -------- | ----------- |
| `t0`, `t1`, … | Temporal. Vive en el registro de activación de la función; cada función numera los suyos desde `t0`. |
| `5`, `"hola"`, `true`, `false`, `null` | Constantes. Una cadena es una referencia a un literal. |
| `x` | Variable global, o variable local o parámetro de la función actual. |
| `x@k` | Variable declarada en una función que contiene a la actual, `k` niveles léxicos más arriba. Se llega a ella siguiendo `k` enlaces de acceso. |
| `this` | Objeto receptor dentro de un método. Es el primer parámetro. |

Si el programa tiene una variable llamada `t3` o `L2`, o que se llama igual que una instrucción (`concat`, `len`, `call`, `param`, …), el compilador la muestra con un `_v` al final (`t3_v`, `concat_v`) para que no se confunda con un temporal, una etiqueta o una instrucción. Si dos variables distintas de una misma función comparten nombre (una dentro de un bloque que tapa a la de afuera), la segunda se muestra como `x_2`.

## 3. Instrucciones

| Instrucción | Qué hace |
| ----------- | -------- |
| `x = y` | Copia. |
| `x = y op z` | Operación binaria. `op` es `+ - * / %` o una comparación `== != < <= > >=`. La división es entera. |
| `x = concat y, z` | Concatena cadenas. Se usa en lugar de `+` cuando algún operando es `string`. |
| `x = -y`, `x = !y` | Negación aritmética y lógica. |
| `L:` | Define una etiqueta. |
| `goto L` | Salto incondicional. |
| `if x goto L` | Salta si `x` es verdadero. |
| `ifFalse x goto L` | Salta si `x` es falso. |
| `if x op y goto L` | Salta si se cumple la comparación. |
| `param x` | Empuja el argumento `x` para la próxima llamada. |
| `call f, n` | Llama a `f` con los últimos `n` parámetros empujados. |
| `x = call f, n` | Igual, y deja en `x` el valor de retorno. |
| `call f, n, link=k` | Llamada a una función anidada (sección 5). |
| `return`, `return x` | Termina la función, con o sin valor. |
| `x = a[i]` | Lee el elemento `i` de la lista `a`. |
| `a[i] = x` | Escribe el elemento `i` de la lista `a`. |
| `x = o.campo` | Lee un atributo. El comentario `; offset +n` da su desplazamiento dentro del objeto. |
| `o.campo = x` | Escribe un atributo. |
| `x = new C, n` | Crea un objeto de la clase `C` de `n` bytes. |
| `x = newarray n` | Crea una lista de `n` elementos. |
| `x = len a` | Cantidad de elementos de la lista `a`. |
| `enter n` | Reserva el registro de activación (`n` bytes). |
| `halt` | Fin del programa. |

Los índices de las listas cuentan elementos, no bytes. Cada elemento ocupa una palabra de 4 bytes, así que la fase siguiente multiplica el índice por 4.

`print` no es una instrucción propia: se traduce como llamada a la función predefinida `print` (`param x` y luego `call print, 1`).

## 4. Variables temporales

Los temporales se asignan y reciclan con un pool por función (`compiscript/temps.py`):

* Al necesitar un temporal se toma el libre de menor índice; si no hay, se crea uno nuevo.
* Un temporal se libera apenas se usa como operando, porque cada uno se consume una sola vez.
* Los operandos de una instrucción se liberan **antes** de pedir el temporal del resultado, así que el resultado puede reutilizar uno de ellos. De ahí salen instrucciones como `t0 = t0 + t1`: se lee antes de escribir, y es válido.
* Algunos temporales se reservan a propósito hasta terminar: el resultado de un `&&`, `||` o `?:` mientras se calculan sus ramas, y la lista, el largo y el índice de un `foreach` durante todo el bucle.
* Cuando una expresión deja su resultado en un temporal recién calculado y ese valor se asigna a una variable, la instrucción que lo calculó escribe directo en la variable. Se evita así `t0 = a + b` seguido de `x = t0`.

La cantidad de temporales distintos que usó una función se suma al tamaño de su registro de activación.

La expresión `a + b * c` y su reasignación con paréntesis:

```
let a: integer = 1;
let b: integer = 2;
let c: integer = 3;
let r: integer = a + b * c;
r = (a + b) * c;
```
```
a = 1
b = 2
c = 3
t0 = b * c
r = a + t0
t0 = a + b
r = t0 * c
```

Una expresión más grande necesita solo tres temporales, y la suma encadenada reutiliza siempre el mismo:

```
let a: integer = 1;
let b: integer = 2;
let c: integer = 3;
let d: integer = 4;
let r: integer = (a + b) * (c + d) - (a * d) / (b + c);
```
```
a = 1
b = 2
c = 3
d = 4
t0 = a + b
t1 = c + d
t0 = t0 * t1
t1 = a * d
t2 = b + c
t1 = t1 / t2
r = t0 - t1
```

## 5. Registros de activación y llamadas

Cada llamada crea un registro de activación. Los offsets son bytes desde `fp`:

| Offset | Contenido |
| ------ | --------- |
| `fp+0` | Valor de retorno |
| `fp+4` | Dirección de retorno |
| `fp+8` | Enlace de control (el `fp` del llamador) |
| `fp+12` | Enlace de acceso (el `fp` de la función que contiene a la llamada en el código fuente) |
| `fp+16` | Parámetros; en un método, `this` va primero |
| … | Variables locales |
| … | Temporales |

Convenciones:

* **Argumentos.** El llamador evalúa todos los argumentos, luego emite un `param` por cada uno en orden y después el `call`. El llamado los encuentra desde `fp+16`.
* **Retorno.** `return x` deja el valor en `fp+0` del registro del llamado y `t = call f, n` lo recoge.
* **Bloques.** Las variables de un bloque se guardan en el registro de la función que lo contiene. Bloques hermanos reutilizan los mismos espacios; el tamaño del registro es el máximo que llegan a ocupar.
* **Niveles.** `main` está en el nivel 0. Una función declarada al nivel superior, y cualquier método, está en el nivel 1; cada función anidada suma uno.
* **Funciones anidadas.** Una función puede leer y modificar las variables de las funciones que la contienen. Se llega a ellas con los enlaces de acceso: `x@k` significa seguir `k` enlaces desde el registro actual y tomar `x` en su offset, con `k` igual al nivel de la función actual menos el de la función donde se declara `x`. En la llamada, `link=k` indica qué registro será el enlace de acceso del llamado: `k` es el nivel del llamador menos el de la función que declara al llamado (`link=0` es el propio registro del llamador). Las llamadas a funciones globales y a métodos no llevan `link`, porque no capturan entorno.

La traducción de una función recursiva:

```
function fact(n: integer): integer {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
print(fact(5));
```
```
func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    param 5
    t0 = call fact, 1
    param t0
    call print, 1
    halt

func fact:                             ; nivel 1, registro de 24 bytes
    enter 24
    if n > 1 goto L1
    return 1
  L1:
    t0 = n - 1
    param t0
    t0 = call fact, 1
    t0 = n * t0
    return t0
```

Una función anidada que lee `a` y modifica `x`, que son de `exterior`:

```
function exterior(a: integer): integer {
    let x: integer = 10;
    function interior(b: integer): integer {
        x = x + 1;
        return x + a + b;
    }
    return interior(5);
}
print(exterior(1));
```
```
func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    param 1
    t0 = call exterior, 1
    param t0
    call print, 1
    halt

func exterior:                         ; nivel 1, registro de 28 bytes
    enter 28
    x = 10
    param 5
    t0 = call exterior_interior, 1, link=0
    return t0

func exterior_interior:                ; nivel 2, registro de 24 bytes
    enter 24
    x@1 = x@1 + 1
    t0 = x@1 + a@1
    t0 = t0 + b
    return t0
```

En `exterior_interior` (nivel 2), `x@1` y `a@1` son variables de `exterior` (nivel 1). La llamada a `interior` va con `link=0` porque `interior` está declarada dentro del propio `exterior`.

El reporte de memoria (`--frames`, o la pestaña *Memoria CPS* de la GUI) muestra cómo queda cada registro:

```
function suma(a: integer, b: integer): integer {
    let r: integer = a + b;
    return r;
}
let total: integer = suma(1, 2);
```
```
Datos globales  (4 bytes)
  global+0    total

Registro de activación: main  (nivel 0, 20 bytes)
  fp+0    valor de retorno
  fp+4    dirección de retorno
  fp+8    enlace de control
  fp+12   enlace de acceso
  fp+16   temporal t0

Registro de activación: suma  (nivel 1, 32 bytes)
  fp+0    valor de retorno
  fp+4    dirección de retorno
  fp+8    enlace de control
  fp+12   enlace de acceso
  fp+16   parámetro a
  fp+20   parámetro b
  fp+24   local r
  fp+28   temporal t0
```

## 6. Traducción de cada construcción

### Expresiones con cadenas y literales

```
let s: string = "hola" + " " + "mundo";
let n: integer = -5;
let ok: boolean = !true;
```
```
t0 = concat "hola", " "
s = concat t0, "mundo"
n = -5
ok = false
```

Los literales con signo y la negación de un literal booleano se resuelven en compilación. No se hace ningún otro plegado de constantes.

### Condiciones y operadores lógicos

Una condición (`if`, `while`, `for`, `do-while`, `?:`) se traduce con saltos y cortocircuito: `&&`, `||` y `!` no producen un valor, solo deciden a dónde saltar. Una comparación simple se convierte en un único `if x op y goto`, con la comparación negada cuando hace falta saltar al caso falso.

```
let a: integer = 1;
let b: integer = 2;
let c: integer = 3;
if (a < b && c > 0) { print(1); } else { print(2); }
```
```
a = 1
b = 2
c = 3
if a >= b goto L2
if c <= 0 goto L2
param 1
call print, 1
goto L1
L2:
param 2
call print, 1
L1:
```

Si el operador lógico se usa como dato (se asigna, se pasa como argumento) se materializa con saltos y queda `true` o `false` en un temporal. La segunda condición no se evalúa si la primera ya decide el resultado:

```
let a: integer = 1;
let c: integer = 3;
let ok: boolean = a < 2 || c == 0;
```
```
a = 1
c = 3
if a < 2 goto L3
if c != 0 goto L1
L3:
t0 = true
goto L2
L1:
t0 = false
L2:
ok = t0
```

El operador ternario:

```
let a: integer = 4;
let m: integer = a > 3 ? a : 3;
```
```
a = 4
if a <= 3 goto L1
t0 = a
goto L2
L1:
t0 = 3
L2:
m = t0
```

### Bucles

`break` salta a la etiqueta del final del bucle más cercano (o del `switch`); `continue` salta a la condición en `while`, al paso de actualización en `for` y a la condición en `do-while`. Un `continue` dentro de un `switch` va al bucle que contiene al `switch`.

```
let i: integer = 0;
while (i < 5) {
    i = i + 1;
    if (i == 2) { continue; }
    if (i == 4) { break; }
    print(i);
}
```
```
i = 0
L1:
if i >= 5 goto L2
i = i + 1
if i == 2 goto L1
if i == 4 goto L2
param i
call print, 1
goto L1
L2:
```

`for` y `do-while`:

```
let s: integer = 0;
for (let i: integer = 0; i < 3; i = i + 1) { s = s + i; }
```
```
s = 0
i = 0
L1:
if i >= 3 goto L3
s = s + i
i = i + 1
goto L1
L3:
```
```
let i: integer = 3;
do { i = i - 1; } while (i > 0);
```
```
i = 3
L1:
i = i - 1
if i > 0 goto L1
```

### switch

El valor se evalúa una vez, se compara contra cada `case` en orden y, si ninguno coincide, se salta al `default` o al final. Los cuerpos van en secuencia: sin `break`, la ejecución sigue con el caso siguiente.

```
let n: integer = 2;
switch (n) {
    case 1: print(10); break;
    case 2: print(20);
    default: print(0);
}
```
```
n = 2
if n == 1 goto L2
if n == 2 goto L3
goto L4
L2:
param 10
call print, 1
goto L1
L3:
param 20
call print, 1
L4:
param 0
call print, 1
L1:
```

### Clases y objetos

* `new C(args)` crea el objeto con `new C, n` (el tamaño sale de la tabla de símbolos), llama a las funciones que dan valor inicial a los atributos (una por clase que tenga atributos con valor, de la clase base a la derivada) y después al constructor, con el objeto como primer parámetro.
* Los atributos con valor inicial se asignan en una función `C__init` que genera el compilador.
* Un método se llama como función con el receptor como primer `param`. Se elige por el tipo estático del receptor y su etiqueta es `Clase_metodo`.
* Los atributos de una clase derivada van después de los de la base, así que los heredados conservan su offset.

```
class Punto {
    let x: integer = 0;
    let y: integer = 0;
    function constructor(a: integer, b: integer) { this.x = a; this.y = b; }
    function suma(): integer { return this.x + this.y; }
}
let p = new Punto(3, 4);
p.x = 10;
print(p.suma());
```
```
func main:                             ; nivel 0, registro de 20 bytes
    enter 20
    t0 = new Punto, 8
    param t0
    call Punto__init, 1
    param t0
    param 3
    param 4
    call Punto_constructor, 3
    p = t0
    p.x = 10                           ; offset +0
    param p
    t0 = call Punto_suma, 1
    param t0
    call print, 1
    halt

func Punto_constructor:                ; nivel 1, registro de 28 bytes
    enter 28
    this.x = a                         ; offset +0
    this.y = b                         ; offset +4
    return

func Punto_suma:                       ; nivel 1, registro de 28 bytes
    enter 28
    t0 = this.x                        ; offset +0
    t1 = this.y                        ; offset +4
    t0 = t0 + t1
    return t0

func Punto__init:                      ; nivel 1, registro de 20 bytes
    enter 20
    this.x = 0                         ; offset +0
    this.y = 0                         ; offset +4
    return
```

### Listas

Un literal de lista crea la lista con `newarray` y asigna cada elemento. Las listas anidadas se construyen de adentro hacia afuera. `foreach` guarda la lista, su largo y un índice en temporales que no se reciclan durante el bucle.

```
let v: integer[] = [10, 20, 30];
v[1] = v[0] + v[2];
let m: integer[][] = [[1, 2], [3, 4]];
print(m[1][0]);
```
```
t0 = newarray 3
t0[0] = 10
t0[1] = 20
t0[2] = 30
v = t0
t0 = v[0]
t1 = v[2]
t0 = t0 + t1
v[1] = t0
t0 = newarray 2
t1 = newarray 2
t1[0] = 1
t1[1] = 2
t0[0] = t1
t1 = newarray 2
t1[0] = 3
t1[1] = 4
t0[1] = t1
m = t0
t0 = m[1]
t0 = t0[0]
param t0
call print, 1
```
```
let v: integer[] = [1, 2, 3];
let t: integer = 0;
foreach (x in v) { t = t + x; }
```
```
t0 = newarray 3
t0[0] = 1
t0[1] = 2
t0[2] = 3
v = t0
t = 0
t0 = v
t1 = len t0
t2 = 0
L1:
if t2 >= t1 goto L3
x = t0[t2]
t = t + x
t2 = t2 + 1
goto L1
L3:
```

## 7. Supuestos y límites

1. Todo valor ocupa una palabra de 4 bytes: enteros, booleanos y también las referencias a cadenas, listas y objetos.
2. `new` entrega memoria en cero, así que un atributo sin valor inicial queda en cero. Una variable declarada sin inicializador no genera código.
3. La evaluación va de izquierda a derecha, y los argumentos de una llamada se evalúan todos antes de emitir los `param`.
4. `==` entre cadenas compara contenido.
5. Los métodos se resuelven por el tipo estático del receptor; no hay despacho dinámico. Si una subclase redefine un método y se llama desde una variable declarada con la clase base, se ejecuta el de la base.
6. El constructor de una subclase no llama al de la clase base (la gramática no tiene `super`).
7. Las funciones anidadas acceden al entorno por enlaces de acceso, así que solo funcionan mientras la función que las define sigue activa. En Compiscript eso siempre se cumple porque las funciones no son valores.
8. Las funciones deben declararse antes de usarse (no se elevan), como exige el análisis semántico.
9. El generador solo corre si el programa no tiene errores léxicos, sintácticos ni semánticos (el código muerto cuenta como error semántico).
10. Construcciones válidas que el generador no soporta y reporta como *Error de generación*: `try/catch`, usar el nombre de una función o método como valor, y llamar al resultado de una expresión (`f()()`).

## 8. Cómo se prueba

`tests/codegen/run_tests.py` compila cada programa de `tests/codegen/ok/`, compara su TAC con el `.tac` guardado y además **ejecuta** el TAC en un intérprete mínimo (`tests/codegen/tac_vm.py`) para comparar lo que imprime con el `.out`, que se calculó a mano. Así se comprueba que el código intermedio hace lo que debe y no solo que se ve bien. Los programas de `tests/codegen/error/` verifican que los errores se reporten con su tipo y ubicación y que no se genere código cuando hay errores previos.

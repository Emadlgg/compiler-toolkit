# Generación de código MIPS (Fase 3)

Último paso del compilador de Compiscript: traduce el TAC a ensamblador MIPS32 y lo ejecuta en MARS.

```text
.cps -> ANTLR -> semántico -> TAC -> MIPSGenerator -> .asm -> MARS (java -jar tools/Mars.jar nc)
```

## Cómo ejecutarlo

```powershell
python compiscript.py programa.cps --mips --output build/programa.asm
java -jar tools/Mars.jar nc build/programa.asm
```

En el IDE (`python gui/app.py`, pestaña Compiscript): **BUILD MIPS** genera el `.asm` y **RUN MIPS** además lo ejecuta en MARS (pestañas *MIPS CPS* y *Consola MIPS*). Requiere Java y `tools/Mars.jar` (o la variable `MARS_JAR`).

## Secuencia de llamada y retorno (`mips/frames.py`, `mips/generator.py`)

Registro de activación (la pila crece hacia abajo, `$fp` apunta al inicio del marco):

| Offset | Contenido |
|---|---|
| `fp+0`  | valor de retorno |
| `fp+4`  | `$ra` |
| `fp+8`  | `$fp` del llamador |
| `fp+12` | enlace estático (para funciones anidadas) |
| `fp+16…`| parámetros, locales y temporales |

Llamador: reserva el marco con `$sp`, guarda `$fp`, el enlace estático y escribe cada argumento en `16+4i($sp)`; luego `jal`.
Llamado: `move $fp,$sp` y guarda `$ra`. Al retornar deja el valor en `0($fp)` y en `$v0`, restaura `$ra`, `$sp = $fp + tamaño` y `$fp`, y hace `jr $ra`.

## Asignación de registros (`mips/registers.py`)

Un solo algoritmo, `RegisterAllocator.getReg(owner)`, administra dos conjuntos de registros:

| Conjunto | Uso |
|---|---|
| `$t0–$t7` (temporales) | Scratch dentro de una instrucción TAC (operandos de operaciones, comparaciones, paso de argumentos). Se piden con `getReg()` y se liberan al terminar. Los temporales del TAC se guardan en su slot de la pila. |
| `$s0–$s7` (guardados) | Variables locales y parámetros que viven en registro durante toda la función. |

**Elección de variables en `$s`** (`MIPSGenerator._plan_saved_registers`): por función se cuentan los usos de cada variable, ponderando x10 por cada nivel de bucle (salto hacia atrás), y se asignan las 8 con más peso. No entran variables globales (van en `$gp`) ni las que una función anidada alcanza por el enlace estático, porque esas deben seguir en memoria.

**Preservación:** como `$s` son registros preservados, el llamado los guarda en el prólogo y los restaura antes de `jr $ra`. El área de guardado queda bajo `$fp` (`-4($fp)`, `-8($fp)`…), así el tamaño del registro de activación y el contrato entre llamador y llamado no cambian. Los parámetros asignados a `$s` se cargan desde `16+4i($fp)` en el prólogo.

**Uso de la pila:** si no quedan registros libres, `getReg()` expulsa uno (round-robin) mediante el callback de *spill*. Las variables que no ganan un `$s`, los temporales del TAC y los globales siempre tienen su lugar en la pila o en `$gp`.

## Runtime incluido

`print` (enteros, booleanos `true/false`, strings; siempre con salto de línea), concatenación y comparación de strings, división entre cero, referencia nula, índice fuera de rango y tamaño de arreglo inválido (mensaje y salida limpia).

## Pruebas

```powershell
python tests/mips/run_tests.py -v     # compila cada .cps, lo corre en MARS y compara contra el .out
pytest tests -q                       # pruebas unitarias e integración
```

En el IDE, el botón **TEST MIPS** corre esa misma batería y muestra el resultado de cada prueba en la pestaña *Pruebas CPS* (necesita Java y `tools/Mars.jar`); **TEST CPS** corre la batería del TAC. Al hacer clic en una prueba se abre en el editor para correrla con RUN MIPS.

Casos exitosos: `tests/codegen/ok` y `tests/mips/cases/ok`. Casos fallidos: `tests/mips/cases/error` (cada línea del `.err` debe aparecer en el log del compilador o en la salida de MARS).

## Limitaciones conocidas

- `try/catch` no está soportado por el generador de TAC.
- `print` de objetos o arreglos completos da error de generación.
- Enteros de 32 bits (desbordan como en MIPS).

## Bibliotecas de clases (`export`, BUILD LIB, `.cplobj`)

Una clase se puede guardar en un archivo y usarse desde otro documento:

1. En el `.cps` que define la clase, márcala con `export class Animal { ... }` (necesita al menos un constructor o un método).
2. En el IDE pulsa **BUILD LIB** (o `python compiscript.py Animal.cps --build-library --output build/Animal.cplobj`).
3. En el otro documento: `import { Animal } from "./build/Animal.cplobj";`. La ruta es relativa a la carpeta del archivo que importa.
4. Después de cambiar la clase hay que volver a pulsar BUILD LIB; el `.cplobj` es una copia compilada.

También se puede importar por código fuente (`import { Animal } from "./Animal";`) sin compilar la biblioteca.

### Importar y heredar entre archivos

- Un archivo puede heredar de una clase importada desde un `.cplobj` (`class Perro : Animal`).
- Cadena de archivos: `main.cps` importa `Perro` por fuente (`import { Perro } from "./Perro";`) y `Perro.cps` importa `Animal.cplobj`. Los `import` de `.cplobj` valen en cualquier módulo `.cps` del proyecto.
- Padre e hijo pueden ir juntos en una biblioteca (un solo archivo con ambos `export`). Al importar el hijo hay que importar también el padre: `import { Animal, Perro } from "./build/Familia.cplobj";`.
- Una biblioteca puede depender de otra: `Perro.cps` (con `import { Animal } from "./build/Animal.cplobj";` y `export class Perro : Animal`) se compila con BUILD LIB a `build/Perro.cplobj`. El paquete guarda `Animal.cplobj` como dependencia con su hash SHA-256; si esa dependencia cambia o falta, el compilador lo rechaza con un mensaje claro. Compila primero la biblioteca padre, y deja ambas en la misma carpeta `build/`.
- Al importar `Perro.cplobj`, su padre se enlaza solo (no hace falta importarlo) y sus miembros heredados se resuelven. Funciona con cadenas más largas (`Cachorro` → `Perro` → `Animal`).
- Si cambias una biblioteca padre, vuelve a compilar también las hijas: el hash de la dependencia ya no coincide.
- Una biblioteca solo puede importar otras bibliotecas compiladas (`.cplobj`), no archivos `.cps` por código fuente. Tampoco admite variables globales.

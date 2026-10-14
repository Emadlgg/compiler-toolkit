# Arquitectura: generación de código intermedio para Compiscript

Este documento explica cómo está organizada la implementación y cómo ejecutarla. El lenguaje intermedio (instrucciones, convenciones y ejemplos de traducción) está documentado en [`CI.md`](CI.md).

## 1. Recorrido de un programa

```
archivo .cps
     │
     ▼
 Análisis léxico y sintáctico (ANTLR)        compiscript/generated/
     │  árbol sintáctico
     ▼
 Análisis semántico                          compiscript/semantic.py
     │  valida el programa y construye la tabla de símbolos
     │  y anota el árbol: tipos, scopes y símbolos de cada nodo
     ▼
 Generación de código intermedio             compiscript/codegen.py
     │  recorre el árbol, consulta la tabla de símbolos
     │  y produce el TAC
     ▼
 TAC  +  reporte de memoria  +  errores
```

Cada fase solo corre si la anterior terminó sin errores. Los errores léxicos y sintácticos detienen el análisis semántico; los semánticos detienen la generación de código. El generador puede agregar sus propios errores (construcciones válidas que no soporta, como `try/catch`).

## 2. Módulos

| Archivo | Responsabilidad |
| ------- | --------------- |
| `compiscript/symbol_table.py` | Tabla de símbolos con scopes anidados. Guarda, además del tipo, dónde vive cada símbolo en memoria. |
| `compiscript/semantic.py` | Visitor semántico. Valida tipos, declaraciones, llamadas, asignaciones y flujo, y deja anotado el árbol. |
| `compiscript/errors.py` | Errores léxicos, sintácticos, semánticos y de generación, con tipo y ubicación. |
| `compiscript/tac.py` | Operandos e instrucciones del TAC y su formato de salida. |
| `compiscript/temps.py` | Pool de temporales: asignación y reciclaje. |
| `compiscript/codegen.py` | Generador de TAC. |
| `compiscript/activation_record.py` | Arma el reporte de memoria: datos globales, layout de clases y registro de activación de cada función. |
| `compiscript.py` | Línea de comandos. |
| `gui/app.py` | IDE: editor, tokens, árbol, errores, símbolos, TAC y memoria. |
| `tests/codegen/` | Batería de pruebas del generador. |

## 3. Tabla de símbolos extendida

Cada símbolo guarda lo que necesita el generador:

| Campo | Significado |
| ----- | ----------- |
| `storage` | `global`, `local`, `param`, `field`, `function`, `method`, `class` o `builtin` |
| `offset` | Desplazamiento en bytes dentro de su área: datos globales, registro de activación u objeto |
| `size` | Tamaño en bytes. Todo valor ocupa una palabra de 4 bytes; en una clase es el tamaño del objeto |
| `label` | Etiqueta de funciones y métodos (`suma`, `Perro_ladrar`, `exterior_interior`). Es única en todo el programa |
| `depth` | Nivel léxico del ámbito donde se declara; sirve para calcular los enlaces de acceso |
| `frame_size` | En funciones, tamaño de su registro de activación sin contar los temporales |

El `offset` se asigna al declarar el símbolo:

* En el scope global, cada variable recibe el siguiente espacio libre del área de datos.
* En una función, los parámetros empiezan en `fp+16` (después de los cuatro campos fijos del registro) y las variables locales van a continuación. En un método, `this` es el primer parámetro.
* Los bloques anidados (`{}`, `if`, bucles, `switch`) toman espacio del registro de la función que los contiene y lo devuelven al salir, de modo que bloques hermanos reutilizan los mismos espacios. El tamaño final del registro es el máximo que se llegó a ocupar.
* En una clase, los atributos empiezan donde terminan los de la clase base, así que los heredados conservan su offset.

El estado completo se puede ver con `--symbols` (símbolos con su ubicación) y `--frames` (la organización de memoria por función).

### Anotaciones del árbol

Después de analizar, el `SemanticAnalyzer` expone tres diccionarios que el generador usa para no repetir trabajo:

* `node_types[nodo]`: tipo inferido de cada nodo (por ejemplo, para distinguir `+` numérico de la concatenación de cadenas).
* `node_scopes[nodo]`: scope que abre cada bloque, función, clase o bucle.
* `node_symbols[nodo]`: símbolo al que se resuelve un identificador, una declaración, una llamada, un acceso a miembro o un `new`.

## 4. El generador

`CodeGenerator` es un visitor del árbol de ANTLR. Trabaja con un `FuncContext` por función, que reúne su código, su pool de temporales, su pila de bucles (para `break` y `continue`) y su nivel léxico. El programa principal también es un contexto (`main`).

Piezas que conviene conocer:

* **Condiciones.** `jump_false(expr, L)` y `jump_true(expr, L)` generan los saltos de una condición con cortocircuito y llaman una a la otra para `&&`, `||` y `!`. Una comparación simple se traduce directamente a `if x op y goto L`.
* **Valores lógicos.** Cuando `&&` o `||` se usan como dato, `_materialize` los convierte en saltos que dejan `true` o `false` en un temporal.
* **Asignación.** `assign_to(destino, valor)` escribe el resultado directamente en la variable cuando la instrucción anterior acaba de calcularlo, en lugar de emitir una copia.
* **Funciones.** Cada función se genera en su propio contexto y queda como un bloque aparte. El orden de salida es el de declaración.
* **Cierre de cada función.** Se quita el código inalcanzable, se simplifican los saltos (`if c goto A; goto B; A:` pasa a `if !c goto B; A:`) y se eliminan las etiquetas sin uso. Las tres limpiezas se repiten hasta que ninguna cambia nada, porque cada una puede dejar a la vista trabajo para las otras. Al final se fija el tamaño del registro: lo que ya calculó la tabla de símbolos más los temporales que se usaron.

## 5. Cómo ejecutarlo

Requisitos: Python 3.11 y las dependencias del proyecto.

```bash
python -m pip install -r requirements.txt
```

### Línea de comandos

```bash
python compiscript.py programa.cps --tac       # código intermedio
python compiscript.py programa.cps --frames    # registros de activación y layouts
python compiscript.py programa.cps --symbols   # tabla de símbolos con direcciones
python compiscript.py programa.cps --all       # todo lo anterior y el árbol sintáctico
```

Si el programa tiene errores, se listan con su tipo y ubicación y no se genera código.

### Interfaz gráfica

```bash
python gui/app.py
```

Al abrir la pestaña *Compiscript*, cargar o escribir un `.cps` y compilar:

* *Errores Léxicos*, *Errores Sintácticos* y *Errores Semánticos*: errores encontrados (los de generación también salen en la última).
* *Símbolos*: tabla de símbolos con tipo, scope, offset, tamaño y etiqueta.
* *TAC CPS*: el código intermedio generado.
* *Memoria CPS*: datos globales, layout de las clases y registro de activación de cada función.

### Pruebas

```bash
python tests/codegen/run_tests.py        # corre toda la batería
python tests/codegen/run_tests.py -v     # muestra cada prueba
python tests/codegen/run_tests.py --update   # regenera los .tac esperados
```

La batería tiene tres partes:

* **Casos exitosos** (`tests/codegen/ok/`): para cada `.cps`, se compara el TAC con el `.tac` guardado y se ejecuta en un intérprete mínimo (`tac_vm.py`) para comparar lo que imprime con el `.out`. El `.out` se calculó a mano, independiente del generador.
* **Casos fallidos** (`tests/codegen/error/`): cada línea del `.err` debe aparecer entre los mensajes de error, y no debe generarse TAC cuando hay errores previos.
* **Pruebas unitarias** del pool de temporales.

`--update` solo debe usarse después de revisar que el cambio en el TAC es el esperado; la comprobación por ejecución sigue validando que el programa se comporta igual.

Las pruebas del análisis semántico anteriores siguen en `tests/compiscript/`, y se corren con `python compiscript.py archivo.cps`.

## 6. Cómo agregar una construcción nueva

1. Si la construcción es nueva en la gramática, regenerar el parser con ANTLR y hacer que el analizador semántico la valide y anote (`node_types`, `node_symbols`, `node_scopes`).
2. Si necesita una instrucción nueva, definirla en `tac.py` con su `__str__` y documentarla en `docs/CI.md`.
3. Agregar el método `visitXxx` en `codegen.py`. Cada visita de expresión devuelve el operando donde quedó el resultado y es responsable de liberar los temporales que consumió (`self.release`).
4. Agregar un programa en `tests/codegen/ok/` con su `.out` calculado a mano, y generar su `.tac` con `--update`. Si la construcción puede fallar, agregar un caso en `tests/codegen/error/`.

Si el intérprete de pruebas no entiende una instrucción nueva, hay que enseñársela en `tests/codegen/tac_vm.py`.

## 7. Límites conocidos

Los supuestos de traducción y las construcciones no soportadas están en la sección 7 de [`CI.md`](CI.md).

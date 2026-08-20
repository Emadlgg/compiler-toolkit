# Generador de Compiladores — YALex, YAPar y Compiscript

Proyecto desarrollado para el curso **Diseño de Lenguajes de Programación** de la Universidad del Valle de Guatemala.

El proyecto implementa distintas fases de construcción de compiladores:

- **YALex** — Generador de analizadores léxicos a partir de especificaciones `.yal`.
- **YAPar** — Generador de analizadores sintácticos SLR(1), LALR y LL(1) a partir de gramáticas `.yapar`.
- **Compiscript** — Analizador sintáctico y semántico basado en ANTLR4 para un subconjunto de TypeScript.
- **GUI** — Interfaz gráfica tipo IDE para ejecutar y visualizar los analizadores.

Java y SQL se utilizan como casos de prueba para YALex y YAPar, mientras que Compiscript incorpora análisis semántico, manejo de ámbitos y tabla de símbolos.

---

# Características

## YALex — Análisis Léxico

YALex permite generar automáticamente un lexer en Python a partir de una especificación `.yal`.

Implementa:

- Parser de especificaciones YALex.
- Parser de expresiones regulares.
- Construcción de Thompson.
- Construcción de AFN.
- Conversión AFN → AFD mediante construcción de subconjuntos.
- Longest match.
- Prioridad de reglas según orden de definición.
- Generación automática de lexers en Python.
- Manejo de tokens ignorados.
- Visualización de árboles de expresiones regulares.
- Visualización del AFD mediante Graphviz.

### Pipeline

```text
archivo.yal
    ↓
Parser YALex
    ↓
Expresiones regulares
    ↓
Árboles de expresión
    ↓
Construcción de Thompson
    ↓
AFNs
    ↓
AFN combinado
    ↓
Construcción de subconjuntos
    ↓
AFD
    ↓
Lexer generado en Python
```

---

## YAPar — Análisis Sintáctico

YAPar genera analizadores sintácticos a partir de archivos `.yapar`.

Implementa tres métodos:

- **SLR(1)**
- **LALR**
- **LL(1)**

Incluye:

- Parser de gramáticas `.yapar`.
- Cálculo de FIRST.
- Cálculo de FOLLOW.
- Construcción del autómata LR(0).
- Construcción de tablas SLR(1).
- Construcción de tablas LALR.
- Construcción de tablas LL(1).
- Detección de conflictos.
- Motor Shift-Reduce para SLR/LALR.
- Motor predictivo para LL(1).
- Visualización de estados y tablas.
- Reporte ACCEPT/REJECT.

### Pipeline

```text
archivo.yapar
      ↓
Parser YAPar
      ↓
Producciones
      ↓
FIRST / FOLLOW
      ↓
Autómata LR(0)
      ↓
┌────────┬────────┬────────┐
│ SLR(1) │  LALR  │ LL(1)  │
└────────┴────────┴────────┘
      ↓
Análisis sintáctico
      ↓
ACCEPT / REJECT
```

---

# Compiscript — Análisis Semántico

Compiscript es un lenguaje basado en un subconjunto de TypeScript.

Para esta fase se utiliza **ANTLR4** para generar el lexer y parser a partir de `Compiscript.g4`. Sobre el árbol sintáctico generado se ejecuta un Visitor encargado del análisis semántico.

La especificación del proyecto requiere verificar tipos, ámbitos, funciones, control de flujo, clases, listas y otras reglas semánticas. :contentReference[oaicite:0]{index=0}

## Pipeline

```text
archivo.cps
    ↓
ANTLR Lexer
    ↓
ANTLR Parser
    ↓
Árbol sintáctico
    ↓
SemanticAnalyzer
    ↓
Tabla de símbolos
    ↓
Errores semánticos
```

## Sistema de tipos

Se manejan los tipos:

```text
integer
string
boolean
null
void
any
```

El analizador valida:

- Operaciones aritméticas.
- Operaciones lógicas.
- Comparaciones.
- Asignaciones.
- Compatibilidad entre tipos.
- Inferencia básica de tipos.
- Tipos de retorno.

## Ámbitos

La tabla de símbolos implementa scopes anidados para:

- Scope global.
- Funciones.
- Clases.
- Bloques.
- Bucles.

Se detecta:

- Uso de variables no declaradas.
- Redeclaraciones en el mismo ámbito.
- Acceso a variables de ámbitos superiores.
- Variables locales.
- Parámetros de funciones.
- Closures y funciones anidadas.

## Funciones

Se valida:

- Número de argumentos.
- Tipo de argumentos.
- Tipo de retorno.
- Parámetros duplicados.
- Redeclaración de funciones.
- Recursividad.
- Funciones anidadas.
- `return` fuera de funciones.

## Control de flujo

Se soportan y validan:

- `if / else`
- `while`
- `do-while`
- `for`
- `foreach`
- `switch`
- `break`
- `continue`
- `return`

Las condiciones deben tener un tipo compatible con `boolean`.

También se detecta código muerto después de instrucciones como `return`, `break` o `continue`.

## Clases y objetos

Se soportan:

- Declaración de clases.
- Atributos.
- Métodos.
- Constructores.
- Herencia.
- `this`.
- Creación de objetos mediante `new`.

El analizador valida:

- Existencia de clases.
- Existencia de atributos.
- Existencia de métodos.
- Argumentos de métodos.
- Argumentos del constructor.
- Tipos de argumentos.
- Uso de `this` dentro de una clase.
- Búsqueda de miembros heredados.

## Listas

Se valida:

- Compatibilidad entre tipos de elementos.
- Tipo de los elementos.
- Acceso mediante índices.
- Índices de tipo `integer`.

Ejemplo:

```text
[1, 2, 3]          ✓

[1, "hola", 3]     ✗ Tipos incompatibles

numeros[0]         ✓

numeros["hola"]    ✗ El índice debe ser integer
```

Estas validaciones corresponden a los requisitos de clases, listas y estructuras de datos de la especificación. :contentReference[oaicite:1]{index=1}

---

# Casos de prueba YALex + YAPar

Actualmente se incluyen dos lenguajes de prueba:

```text
Java
SQL
```

## Java

Archivos:

```text
java.yal
java_grammar.yapar
```

La gramática utilizada soporta, entre otras construcciones:

- Clases.
- Métodos.
- Variables.
- Expresiones.
- `if / else`.
- `while`.
- `for`.
- `return`.
- Arreglos.
- Llamadas a métodos.
- Creación de objetos.

Resultados obtenidos:

```text
Estados LR(0):      230
Transiciones:       1166

Conflictos:

SLR(1):     9
LALR:       5
LL(1):      342
```

La gramática contiene recursión izquierda, por ejemplo:

```text
expr:
    expr OP_PLUS term
```

Por esta razón los métodos LR pueden manejar mejor esta gramática que LL(1).

---

## SQL

También se incluye un subset de SQL para probar YALex y YAPar.

Archivos:

```text
sql.yal
sql_grammar.yapar
examples/sql/query.sql
```

El subset soporta:

- `SELECT`
- `FROM`
- `WHERE`
- `INSERT`
- `INTO`
- `VALUES`
- `UPDATE`
- `SET`
- `DELETE`
- `AND`
- `OR`
- `NOT`
- `NULL`
- Comparaciones.
- Identificadores.
- Strings.
- Enteros.
- Floats.

### Resultados obtenidos

YALex:

```text
Estados AFD: 414
Errores léxicos: 0
```

YAPar:

```text
Producciones:     18
Estados LR(0):    83
Transiciones:     134

Conflictos:

SLR(1):      0
LALR:        0
LL(1):      18
```

Resultado del archivo `query.sql`:

| Método | Resultado |
|---|---|
| SLR(1) | ✓ ACEPTADA |
| LALR | ✓ ACEPTADA |
| LL(1) | ✗ RECHAZADA |

---

# Estructura del Proyecto

```text
proyecto/
│
├── automata/
│   ├── __init__.py
│   ├── afd.py
│   ├── afn.py
│   ├── subset.py
│   └── thompson.py
│
├── regex/
│   ├── __init__.py
│   ├── regex_node.py
│   └── regex_parser.py
│
├── yalex/
│   ├── __init__.py
│   ├── generator.py
│   ├── lexer_builder.py
│   ├── visualizer.py
│   ├── yalex_parser.py
│   └── yalex_reader.py
│
├── yapar/
│   ├── __init__.py
│   ├── first_follow.py
│   ├── lalr_table.py
│   ├── ll1_table.py
│   ├── lr0.py
│   ├── parser_engine.py
│   ├── slr_table.py
│   └── yapar_parser.py
│
├── compiscript/
│   ├── __init__.py
│   ├── errors.py
│   ├── semantic.py
│   ├── symbol_table.py
│   └── generated/
│       ├── __init__.py
│       ├── CompiscriptLexer.py
│       ├── CompiscriptParser.py
│       └── CompiscriptVisitor.py
│
├── gui/
│   ├── __init__.py
│   └── app.py
│
├── tests/
│   ├── tipos/
│   ├── ambitos/
│   ├── funciones/
│   ├── control_flujo/
│   ├── clases/
│   └── extra/
│
├── examples/
│   ├── java/
│   │   ├── correcto.txt
│   │   ├── errores.txt
│   │   └── input_java.txt
│   └── sql/
│       └── query.sql
│
├── Compiscript.g4
├── java.yal
├── java_grammar.yapar
├── sql.yal
├── sql_grammar.yapar
│
├── yalex.py
├── yapar.py
├── compiscript.py
│
├── antlr.jar
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Instalación

## Requisitos

- Python 3.11
- Java
- Graphviz
- ANTLR4

Instalar las dependencias de Python:

```bash
pip install -r requirements.txt
```

Graphviz también debe estar instalado en el sistema operativo.

### Windows

Instalar Graphviz y agregarlo al `PATH`.

### Ubuntu / Debian

```bash
sudo apt install graphviz
```

### macOS

```bash
brew install graphviz
```

---

# Uso de YALex

## Generar lexer Java

```bash
python yalex.py java.yal -o java_lexer.py
```

Generar también visualizaciones:

```bash
python yalex.py java.yal -o java_lexer.py --all
```

Flags:

```text
--tree    Árboles de expresiones regulares
--afd     Autómata finito determinista
--all     Todas las visualizaciones
```

---

## Generar lexer SQL

```bash
python yalex.py sql.yal -o sql_lexer.py --all
```

Ejecutar:

```bash
python sql_lexer.py examples/sql/query.sql --verbose
```

---

# Uso de YAPar

## Java

SLR:

```bash
python yapar.py java_grammar.yapar -l java.yal -i examples/java/input_java.txt
```

LALR:

```bash
python yapar.py java_grammar.yapar -l java.yal -i examples/java/input_java.txt --method lalr
```

LL(1):

```bash
python yapar.py java_grammar.yapar -l java.yal -i examples/java/input_java.txt --method ll1
```

Todos:

```bash
python yapar.py java_grammar.yapar -l java.yal -i examples/java/input_java.txt --all
```

## SQL

```bash
python yapar.py sql_grammar.yapar -l sql.yal -i examples/sql/query.sql --all
```

Resultado esperado:

```text
SLR   → ACEPTADA
LALR  → ACEPTADA
LL(1) → RECHAZADA
```

---

# Uso de Compiscript

Ejecutar análisis semántico:

```bash
python compiscript.py archivo.cps
```

Mostrar árbol:

```bash
python compiscript.py archivo.cps --tree
```

Mostrar tabla de símbolos:

```bash
python compiscript.py archivo.cps --symbols
```

Mostrar toda la información:

```bash
python compiscript.py archivo.cps --all
```

Ejemplo:

```bash
python compiscript.py tests/funciones/ok_funciones.cps --all
```

---

# Pruebas de Compiscript

La batería de pruebas está dividida por categoría:

```text
tests/
├── tipos/
├── ambitos/
├── funciones/
├── control_flujo/
├── clases/
└── extra/
```

Cada categoría principal contiene casos correctos y casos con errores.

Ejemplo:

```bash
python compiscript.py tests/tipos/ok_tipos.cps
python compiscript.py tests/tipos/error_tipos.cps
```

Los tests adicionales verifican:

- Constantes.
- Código muerto.
- Closures.
- Atributos.
- Métodos.
- Constructores.
- Listas.
- Índices.

La especificación requiere una batería de pruebas con casos exitosos y fallidos para las reglas semánticas. :contentReference[oaicite:2]{index=2}

---

# Interfaz Gráfica

Ejecutar:

```bash
python gui/app.py
```

La interfaz permite actualmente trabajar con YALex y YAPar, incluyendo:

- Edición de archivos.
- Generación de lexers.
- Ejecución de parsers.
- Visualización de tokens.
- FIRST/FOLLOW.
- Autómata LR(0).
- Tablas SLR/LALR/LL(1).
- Resultados de análisis.

La integración del análisis de Compiscript en la interfaz corresponde a la siguiente etapa del desarrollo.

El IDE final debe permitir escribir y compilar código Compiscript, tal como establece la especificación del proyecto. :contentReference[oaicite:3]{index=3}

---

# Tecnologías

- Python 3.11
- ANTLR4
- Graphviz
- Tkinter
- Java Runtime para ANTLR
- Git

---

# Video de Demostración

[Video de demostración](https://youtu.be/i4ffWxEBaM0)

---

# Autor

**Osman Emanuel de León García — 23428**

---

# Curso

**Diseño de Lenguajes de Programación**  
Universidad del Valle de Guatemala  
2026
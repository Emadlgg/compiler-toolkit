# ⚙️ Compiler Toolkit

### Generador de analizadores léxicos, sintácticos y semánticos

**Proyecto académico — Construcción de Compiladores**
Universidad del Valle de Guatemala · 2026

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python\&logoColor=white)
![ANTLR](https://img.shields.io/badge/ANTLR-4.13.2-EF7B4D)
![Graphviz](https://img.shields.io/badge/Graphviz-Visualización-2596BE)
![GUI](https://img.shields.io/badge/GUI-Tkinter-4B8BBE)
![Status](https://img.shields.io/badge/Estado-Completado-success)

---

## 📖 Sobre el proyecto

**Compiler Toolkit** reúne en una sola aplicación tres etapas fundamentales de la construcción de compiladores.

El proyecto implementa desde cero algoritmos clásicos de análisis léxico y sintáctico, además de integrar **ANTLR4** para construir el front-end de **Compiscript**, un lenguaje basado en un subconjunto de TypeScript.

El toolkit está compuesto por:

| Componente           | Entrada              | Resultado                               |
| -------------------- | -------------------- | --------------------------------------- |
| 🔤 **YALex**         | `.yal`               | Generador de analizadores léxicos       |
| 🌳 **YAPar**         | `.yapar`             | Parsers SLR(1), LALR y LL(1)            |
| 🧠 **Compiscript**   | `.cps`               | Análisis léxico, sintáctico y semántico |
| 🖥️ **Compiler IDE** | Todos los anteriores | Interfaz gráfica integrada              |

Además de las herramientas de línea de comandos, el proyecto incluye una interfaz gráfica desarrollada con **Tkinter**, desde la cual es posible explorar tokens, autómatas, tablas de parsing, árboles sintácticos, errores semánticos y tablas de símbolos.

---

# 🧭 Contenido

* [Arquitectura general](#-arquitectura-general)
* [YALex — Analizador léxico](#-yalex--generador-de-analizadores-léxicos)
* [YAPar — Analizador sintáctico](#-yapar--generador-de-analizadores-sintácticos)
* [Compiscript — Análisis semántico](#-compiscript--análisis-semántico)
* [Compiler IDE](#️-compiler-ide)
* [Instalación](#-instalación)
* [Inicio rápido](#-inicio-rápido)
* [Uso desde CLI](#️-uso-desde-cli)
* [Casos de prueba](#-casos-de-prueba)
* [Estructura del repositorio](#-estructura-del-repositorio)
* [Tecnologías](#️-tecnologías)
* [Autor](#-autor)

---

# 🏗 Arquitectura general

El proyecto está organizado como un conjunto de componentes independientes que pueden utilizarse desde línea de comandos o desde la interfaz gráfica.

```text
                         COMPILER TOOLKIT
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
           YALex             YAPar          Compiscript
              │                │                │
              ▼                ▼                ▼
        Regex Parser      Grammar Parser     ANTLR Lexer
              │                │                │
              ▼                ▼                ▼
           Thompson        FIRST/FOLLOW      ANTLR Parser
              │                │                │
              ▼                ▼                ▼
             AFN              LR(0)        Parse Tree
              │                │                │
              ▼          ┌─────┼─────┐          ▼
        Subconjuntos      │     │     │    SemanticAnalyzer
              │          SLR  LALR  LL(1)        │
              ▼                                ▼
             AFD                          SymbolTable
              │                                │
              ▼                                ▼
       Lexer generado                    Semantic Errors
              │
              └──────────────┬─────────────────┘
                             ▼
                       ┌───────────┐
                       │    GUI    │
                       │  Tkinter  │
                       └───────────┘
```

Esta separación permite estudiar individualmente cada fase del proceso de compilación y observar cómo los conceptos teóricos se traducen a implementaciones concretas.

---

# 🔤 YALex — Generador de Analizadores Léxicos

YALex genera automáticamente un **lexer ejecutable en Python** a partir de una especificación `.yal`.

El proceso implementa directamente los algoritmos fundamentales utilizados para convertir expresiones regulares en autómatas finitos.

## Pipeline

```text
archivo.yal
    │
    ▼
YALex Parser
    │
    ▼
Expresiones regulares
    │
    ▼
Árboles de expresión
    │
    ▼
Construcción de Thompson
    │
    ▼
AFN individuales
    │
    ▼
AFN combinado
    │
    ▼
Construcción de subconjuntos
    │
    ▼
AFD
    │
    ▼
Lexer Python
```

## Características

* Definiciones mediante `let`.
* Reglas léxicas mediante `rule`.
* Parser propio de expresiones regulares.
* Construcción de árboles de expresión.
* Construcción de Thompson.
* Generación y combinación de AFN.
* Conversión AFN → AFD mediante construcción de subconjuntos.
* Estrategia **longest match**.
* Prioridad según el orden de las reglas.
* Tokens ignorados.
* Generación automática de código Python.
* Visualización de árboles de expresiones regulares.
* Visualización del AFD mediante Graphviz.

## Módulos principales

```text
regex/
├── regex_node.py
└── regex_parser.py

automata/
├── afn.py
├── afd.py
├── thompson.py
└── subset.py

yalex/
├── generator.py
├── lexer_builder.py
├── visualizer.py
├── yalex_parser.py
└── yalex_reader.py
```

---

# 🌳 YAPar — Generador de Analizadores Sintácticos

YAPar recibe una gramática `.yapar` y construye analizadores sintácticos utilizando tres estrategias diferentes:

* **SLR(1)**
* **LALR**
* **LL(1)**

Esto permite comparar directamente métodos de parsing **bottom-up** y **top-down** sobre una misma gramática.

## Pipeline

```text
archivo.yapar
      │
      ▼
  YAPar Parser
      │
      ▼
 Producciones
      │
      ├──────────────► FIRST / FOLLOW
      │
      ▼
 Autómata LR(0)
      │
      ├────────────┬────────────┐
      ▼            ▼            ▼
    SLR(1)       LALR         LL(1)
      │            │            │
      └────────────┼────────────┘
                   ▼
             Parser Engine
                   │
                   ▼
             ACCEPT / REJECT
```

## Características

* Lectura de gramáticas `.yapar`.
* Declaración de terminales mediante `%token`.
* Tokens ignorados mediante `IGNORE`.
* Cálculo iterativo de **FIRST** y **FOLLOW**.
* Construcción de autómatas **LR(0)**.
* Operaciones `closure()` y `goto()`.
* Construcción de tablas **SLR(1)**.
* Construcción de tablas **LALR**.
* Construcción de tablas **LL(1)**.
* Detección y reporte de conflictos.
* Motor Shift-Reduce para SLR/LALR.
* Motor predictivo para LL(1).
* Visualización de estados LR(0).
* Reporte de aceptación o rechazo.

## Módulos principales

```text
yapar/
├── first_follow.py
├── lr0.py
├── slr_table.py
├── lalr_table.py
├── ll1_table.py
├── parser_engine.py
└── yapar_parser.py
```

---

# 🧠 Compiscript — Análisis Semántico

**Compiscript** es un lenguaje basado en un subconjunto de TypeScript.

A diferencia de YALex y YAPar, en esta etapa se utiliza **ANTLR4** para generar automáticamente el lexer y parser a partir de:

```text
grammars/compiscript/Compiscript.g4
```

Posteriormente, un analizador semántico propio recorre el árbol generado por ANTLR mediante el patrón **Visitor**.

## Pipeline

```text
archivo.cps
    │
    ▼
ANTLR Lexer
    │
    ├────► Errores léxicos
    ▼
ANTLR Parser
    │
    ├────► Errores sintácticos
    ▼
Parse Tree
    │
    ▼
SemanticAnalyzer
    │
    ├────► Errores semánticos
    ▼
SymbolTable
    │
    ▼
Scopes / Symbols / Types
```

En la interfaz gráfica, el análisis semántico se realiza únicamente cuando las fases léxica y sintáctica han terminado sin errores.

## Sistema de tipos

El analizador trabaja con tipos como:

```text
integer
string
boolean
null
void
any
```

También maneja tipos correspondientes a clases y representaciones internas para colecciones.

Entre las verificaciones realizadas se encuentran:

* Asignaciones.
* Compatibilidad de tipos.
* Operaciones aritméticas.
* Operaciones lógicas.
* Comparaciones.
* Inferencia básica.
* Tipos de retorno.

## Scopes y tabla de símbolos

Los ámbitos están organizados jerárquicamente:

```text
global
│
├── function
│   ├── block
│   └── loop
│
└── class
    └── method
        └── block
```

La resolución de símbolos comienza en el scope actual y continúa hacia sus scopes padre.

Esto permite representar:

* Variables globales y locales.
* Parámetros.
* Funciones.
* Clases.
* Métodos.
* Bloques.
* Ciclos.
* Funciones anidadas.
* Visibilidad léxica.

El analizador detecta, entre otros casos:

* Variables no declaradas.
* Redeclaraciones.
* Parámetros duplicados.
* Uso incorrecto de constantes.
* Llamadas con argumentos incompatibles.
* Uso inválido de `return`.
* Acceso a miembros inexistentes.

## Funciones

Se contempla:

* Declaración.
* Parámetros.
* Tipos de argumentos.
* Tipo de retorno.
* Recursividad.
* Funciones anidadas.
* Resolución de símbolos externos.

## Control de flujo

```text
if / else
while
do-while
for
foreach
switch / case
break
continue
return
try / catch
```

También se verifica el tipo de las condiciones y se detectan situaciones de código muerto después de determinadas instrucciones de transferencia.

## Clases y objetos

Compiscript incluye soporte para:

* Clases.
* Atributos.
* Métodos.
* Constructores.
* Herencia.
* `this`.
* Instanciación mediante `new`.
* Resolución de miembros heredados.

## Listas

El análisis contempla listas y acceso mediante índices.

```typescript
[1, 2, 3]          // válido
[1, "hola", 3]     // tipos incompatibles

numeros[0]         // válido
numeros["hola"]    // índice inválido
```

## Módulos principales

```text
compiscript/
├── errors.py
├── semantic.py
├── symbol_table.py
└── generated/
    ├── CompiscriptLexer.py
    ├── CompiscriptParser.py
    └── CompiscriptVisitor.py
```

---

# 🖥️ Compiler IDE

Los tres proyectos pueden utilizarse desde una interfaz gráfica integrada desarrollada con **Tkinter**.

```powershell
python gui/app.py
```

La aplicación utiliza una interfaz oscura inspirada en herramientas de desarrollo y permite trabajar con los componentes del compilador desde un mismo entorno.

## YALex / YAPar

La interfaz permite inspeccionar:

* Tokens.
* Reglas YALex.
* Resultado del parser.
* Tabla SLR(1).
* Tabla LALR.
* Tabla LL(1).
* Autómata LR(0).
* FIRST/FOLLOW.
* Gramática YAPar.

## Compiscript

El editor de Compiscript incluye:

* Editor de archivos `.cps`.
* Numeración de líneas.
* Resaltado de sintaxis.
* Posición de línea y columna.
* Tokens producidos por ANTLR.
* Árbol sintáctico gráfico.
* Zoom y desplazamiento del árbol.
* Errores léxicos.
* Errores sintácticos.
* Errores semánticos.
* Navegación desde errores hacia el editor.
* Tabla de símbolos organizada por scope.
* Referencia del lenguaje.
* Visualización de la gramática.

El análisis se ejecuta en un hilo separado para mantener responsiva la interfaz durante el procesamiento.

---

# 🚀 Instalación

## Requisitos

Se recomienda utilizar:

* **Python 3.11**
* **Java Runtime**
* **Graphviz**
* **Git**
* **Tkinter**

ANTLR 4.13.2 se encuentra incluido en `tools/antlr.jar`.

---

## 1. Clonar el repositorio

```bash
git clone https://github.com/Emadlgg/compiler-toolkit.git
cd compiler-toolkit
```

---

## 2. Crear un entorno virtual

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si se utiliza CMD:

```cmd
.venv\Scripts\activate.bat
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Instalar las dependencias

```bash
python -m pip install -r requirements.txt
```

Las principales dependencias Python son:

```text
antlr4-python3-runtime==4.13.2
graphviz==0.21
```

---

## 4. Instalar Graphviz

El paquete `graphviz` de Python funciona como interfaz hacia Graphviz. Para generar las visualizaciones también es necesario instalar **Graphviz en el sistema operativo**.

### Windows

Instalar Graphviz y asegurarse de que su carpeta `bin` se encuentre disponible en la variable de entorno `PATH`.

Para comprobar la instalación:

```powershell
dot -V
```

### Ubuntu / Debian

```bash
sudo apt install graphviz
```

### macOS

```bash
brew install graphviz
```

---

## 5. Verificar ANTLR

El proyecto incluye:

```text
tools/antlr.jar
```

correspondiente a **ANTLR 4.13.2**.

Puede comprobarse mediante:

```bash
java -jar tools/antlr.jar
```

La salida debe comenzar con:

```text
ANTLR Parser Generator  Version 4.13.2
```

### Regeneración de Compiscript

> [!IMPORTANT]
> Los archivos generados ya se encuentran incluidos en el repositorio.
> Este paso **no es necesario para ejecutar el proyecto**.

Solo debe realizarse si se modifica:

```text
grammars/compiscript/Compiscript.g4
```

Desde la raíz:

```powershell
java -jar tools/antlr.jar -Dlanguage=Python3 -visitor -Xexact-output-dir -o compiscript\generated grammars\compiscript\Compiscript.g4
```

La opción `-Xexact-output-dir` hace que los archivos sean escritos directamente en `compiscript/generated/`.

---

# ⚡ Inicio rápido

Una vez instaladas las dependencias, la forma más rápida de explorar el proyecto es ejecutar la interfaz gráfica:

```powershell
python gui/app.py
```

También pueden utilizarse individualmente los tres componentes:

```powershell
# Generador léxico
python yalex.py --help

# Generador sintáctico
python yapar.py --help

# Compiscript
python compiscript.py --help
```

---

# ⌨️ Uso desde CLI

Todos los comandos deben ejecutarse desde la **raíz del repositorio**.

## 🔤 YALex

### Java

Generar el lexer:

```powershell
python yalex.py grammars/java/java.yal -o java_lexer.py
```

Generar también las visualizaciones:

```powershell
python yalex.py grammars/java/java.yal -o java_lexer.py --all
```

Después puede ejecutarse el lexer generado:

```powershell
python java_lexer.py examples/java/input_java.txt --verbose
```

### SQL

```powershell
python yalex.py grammars/sql/sql.yal -o sql_lexer.py --all
python sql_lexer.py examples/sql/query.sql --verbose
```

### Opciones de visualización

```text
--tree       Árboles de expresiones regulares
--afd        Grafo del AFD
--all        Todas las visualizaciones
```

---

## 🌳 YAPar

### Java — SLR(1)

```powershell
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt
```

### Java — LALR

```powershell
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt --method lalr
```

### Java — LL(1)

```powershell
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt --method ll1
```

### Comparar los tres métodos

```powershell
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt --all
```

### SQL

```powershell
python yapar.py grammars/sql/sql_grammar.yapar -l grammars/sql/sql.yal -i examples/sql/query.sql --all
```

---

## 🧠 Compiscript

### Análisis estándar

```powershell
python compiscript.py archivo.cps
```

### Mostrar árbol sintáctico

```powershell
python compiscript.py archivo.cps --tree
```

### Mostrar tabla de símbolos

```powershell
python compiscript.py archivo.cps --symbols
```

### Mostrar toda la información

```powershell
python compiscript.py archivo.cps --all
```

Por ejemplo:

```powershell
python compiscript.py tests/compiscript/tipos/ok_tipos.cps --all
```

Una ejecución correcta produce, entre otros resultados:

```text
✓ Sin errores semánticos

══ TABLA DE SÍMBOLOS ══

┌─ global (global)
│  function print(value:any) → void
│  ...
└─
```

---

# 🧪 Casos de prueba

## Java

```text
grammars/java/java.yal
grammars/java/java_grammar.yapar
examples/java/input_java.txt
```

La gramática utilizada contempla construcciones como clases, métodos, variables, expresiones, condicionales, ciclos, retornos, arreglos, llamadas y creación de objetos.

Java también sirve para observar las diferencias entre las estrategias de parsing, particularmente cuando una gramática presenta características que dificultan su utilización mediante LL(1).

---

## SQL

```text
grammars/sql/sql.yal
grammars/sql/sql_grammar.yapar
examples/sql/query.sql
```

El subset utilizado contempla instrucciones y elementos como:

`SELECT`, `FROM`, `WHERE`, `INSERT`, `INTO`, `VALUES`, `UPDATE`, `SET`, `DELETE`, `AND`, `OR`, `NOT`, `NULL`, identificadores, strings, enteros, floats y comparaciones.

---

## Compiscript

Los casos de prueba funcionales están organizados por categoría:

```text
tests/compiscript/
├── tipos/
├── ambitos/
├── funciones/
├── control_flujo/
├── clases/
└── extra/
```

### Caso válido

```powershell
python compiscript.py tests/compiscript/tipos/ok_tipos.cps --all
```

### Caso con errores

```powershell
python compiscript.py tests/compiscript/tipos/error_tipos.cps --all
```

Los casos adicionales verifican:

* Constantes.
* Código muerto.
* Closures.
* Atributos.
* Métodos.
* Constructores.
* Listas.
* Índices.

---

# 📁 Estructura del repositorio

```text
compiler-toolkit/
│
├── automata/                    # AFN, AFD, Thompson y subconjuntos
│   ├── afd.py
│   ├── afn.py
│   ├── subset.py
│   └── thompson.py
│
├── regex/                       # Parser y representación de regex
│   ├── regex_node.py
│   └── regex_parser.py
│
├── yalex/                       # Generador léxico
│   ├── generator.py
│   ├── lexer_builder.py
│   ├── visualizer.py
│   ├── yalex_parser.py
│   └── yalex_reader.py
│
├── yapar/                       # Generador sintáctico
│   ├── first_follow.py
│   ├── lalr_table.py
│   ├── ll1_table.py
│   ├── lr0.py
│   ├── parser_engine.py
│   ├── slr_table.py
│   └── yapar_parser.py
│
├── compiscript/                 # Analizador semántico
│   ├── errors.py
│   ├── semantic.py
│   ├── symbol_table.py
│   └── generated/               # Lexer/parser generados por ANTLR
│
├── gui/
│   └── app.py                   # IDE gráfico
│
├── grammars/
│   ├── java/
│   ├── sql/
│   └── compiscript/
│       └── Compiscript.g4
│
├── examples/
├── tests/
│   └── compiscript/
│
├── tools/
│   └── antlr.jar                # ANTLR 4.13.2
│
├── yalex.py                     # CLI YALex
├── yapar.py                     # CLI YAPar
├── compiscript.py               # CLI Compiscript
├── requirements.txt
└── README.md
```

---

# 🛠️ Tecnologías

| Tecnología       | Uso                                  |
| ---------------- | ------------------------------------ |
| **Python 3.11**  | Implementación principal             |
| **ANTLR 4.13.2** | Lexer y parser de Compiscript        |
| **Graphviz**     | Visualización de autómatas y árboles |
| **Tkinter**      | Interfaz gráfica                     |
| **Java Runtime** | Ejecución del generador ANTLR        |
| **Git / GitHub** | Control de versiones                 |

---

# 📚 Conceptos implementados

El proyecto pone en práctica conceptos fundamentales de construcción de compiladores:

```text
Expresiones regulares
        │
        ▼
Construcción de Thompson
        │
        ▼
       AFN
        │
        ▼
Construcción de subconjuntos
        │
        ▼
       AFD

FIRST / FOLLOW
Closure / GOTO
LR(0)
SLR(1)
LALR
LL(1)

Árboles sintácticos
Visitors
Scopes
Tablas de símbolos
Sistemas de tipos
Análisis semántico
```

---

# ✅ Estado del proyecto

* [x] Generador léxico YALex
* [x] Construcción AFN/AFD
* [x] Construcción de Thompson
* [x] Generación automática de lexers
* [x] Visualización de árboles y AFD
* [x] Generador sintáctico YAPar
* [x] FIRST/FOLLOW
* [x] Autómata LR(0)
* [x] SLR(1)
* [x] LALR
* [x] LL(1)
* [x] Analizador de Compiscript con ANTLR4
* [x] Análisis semántico
* [x] Scopes y tabla de símbolos
* [x] Casos de prueba funcionales
* [x] Integración de los tres proyectos en GUI
* [x] Árbol sintáctico gráfico
* [x] Visualización de errores por fase
* [x] Tabla de símbolos gráfica

---

# 👨‍💻 Autor

**Osman Emanuel de León García — 23428**

Ingeniería en Ciencias de la Computación
Universidad del Valle de Guatemala

**Construcción de Compiladores — 2026**

---

> Este proyecto fue desarrollado con fines académicos como implementación práctica de las principales etapas del front-end de un compilador.

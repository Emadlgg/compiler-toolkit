# Generador de Compiladores --- YALex, YAPar y Compiscript

Proyecto académico desarrollado para el curso **Diseño de Lenguajes de
Programación** de la **Universidad del Valle de Guatemala (UVG)**.

El proyecto reúne tres etapas principales del diseño de compiladores:
generación de analizadores léxicos, generación de analizadores
sintácticos y análisis semántico. Además, incluye una interfaz gráfica
tipo IDE que integra los tres proyectos y permite inspeccionar
visualmente sus resultados.

> **Curso:** Diseño de Lenguajes de Programación\
> **Universidad:** Universidad del Valle de Guatemala\
> **Lenguaje principal:** Python 3.11\
> **Año:** 2026

------------------------------------------------------------------------

## Contenido

-   [Descripción general](#descripción-general)
-   [Proyecto 1 --- YALex](#proyecto-1--yalex)
-   [Proyecto 2 --- YAPar](#proyecto-2--yapar)
-   [Proyecto 3 --- Compiscript](#proyecto-3--compiscript)
-   [Interfaz gráfica](#interfaz-gráfica)
-   [Estructura del proyecto](#estructura-del-proyecto)
-   [Instalación](#instalación)
-   [Uso](#uso)
-   [Casos de prueba](#casos-de-prueba)
-   [Tecnologías utilizadas](#tecnologías-utilizadas)
-   [Video de demostración](#video-de-demostración)
-   [Autor](#autor)

------------------------------------------------------------------------

# Descripción general

El proyecto está dividido en tres componentes principales:

  -----------------------------------------------------------------------
  Proyecto                Entrada                 Función
  ----------------------- ----------------------- -----------------------
  **YALex**               `.yal`                  Genera analizadores
                                                  léxicos

  **YAPar**               `.yapar`                Genera analizadores
                                                  sintácticos SLR(1),
                                                  LALR y LL(1)

  **Compiscript**         `.cps`                  Realiza análisis
                                                  léxico, sintáctico y
                                                  semántico

  **GUI**                 `.yal`, `.yapar`,       Integra y visualiza los
                          `.txt`, `.cps`          tres proyectos
  -----------------------------------------------------------------------

Java y SQL se utilizan como casos de prueba para YALex y YAPar.
Compiscript, basado en un subconjunto de TypeScript, utiliza ANTLR4 y
agrega análisis semántico, scopes anidados, tabla de símbolos,
funciones, clases y control de flujo.

El flujo general del proyecto puede verse de la siguiente forma:

``` text
                    ┌──────────────┐
                    │ Código fuente│
                    └──────┬───────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
       YALex             YAPar           Compiscript
          │                │                 │
          ▼                ▼                 ▼
     Lexer / AFD      Parser / Tablas   ANTLR Lexer/Parser
                                             │
                                             ▼
                                     Análisis semántico
                                             │
                                             ▼
                                      Tabla de símbolos
```

------------------------------------------------------------------------

# Proyecto 1 --- YALex

## Generador de Analizadores Léxicos

YALex permite construir automáticamente un lexer en Python a partir de
una especificación `.yal`.

### Características

-   Lectura y parseo de especificaciones YALex.
-   Definiciones mediante `let`.
-   Reglas léxicas mediante `rule`.
-   Parser propio de expresiones regulares.
-   Construcción de árboles de expresión.
-   Construcción de Thompson.
-   Generación de AFN.
-   Unión de múltiples AFN.
-   Conversión AFN → AFD mediante construcción de subconjuntos.
-   Longest match.
-   Prioridad de reglas según su orden de definición.
-   Tokens ignorados.
-   Generación automática de un lexer ejecutable en Python.
-   Visualización de árboles de expresiones regulares.
-   Visualización del AFD mediante Graphviz.

### Pipeline

``` text
archivo.yal
    │
    ▼
Parser YALex
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
AFNs individuales
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
Lexer generado en Python
```

### Módulos principales

``` text
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

------------------------------------------------------------------------

# Proyecto 2 --- YAPar

## Generador de Analizadores Sintácticos

YAPar genera analizadores sintácticos a partir de archivos `.yapar`.

Se implementaron tres métodos:

-   **SLR(1)**
-   **LALR**
-   **LL(1)**

### Características

-   Parser de gramáticas `.yapar`.
-   Declaración de terminales mediante `%token`.
-   Tokens ignorados mediante `IGNORE`.
-   Manejo de producciones.
-   Cálculo iterativo de FIRST.
-   Cálculo iterativo de FOLLOW.
-   Construcción del autómata LR(0).
-   Closure y GOTO.
-   Construcción de tablas SLR(1).
-   Construcción de tablas LALR.
-   Construcción de tablas LL(1).
-   Detección y reporte de conflictos.
-   Motor Shift-Reduce para SLR/LALR.
-   Motor predictivo para LL(1).
-   Visualización de estados LR(0).
-   Visualización de tablas de parsing.
-   Reporte de aceptación o rechazo.

### Pipeline

``` text
archivo.yapar
      │
      ▼
 Parser YAPar
      │
      ▼
 Producciones
      │
      ▼
FIRST / FOLLOW
      │
      ▼
Autómata LR(0)
      │
      ├──────────────┬──────────────┐
      ▼              ▼              ▼
   SLR(1)          LALR           LL(1)
      │              │              │
      └──────────────┼──────────────┘
                     ▼
             Análisis sintáctico
                     │
                     ▼
              ACCEPT / REJECT
```

### Módulos principales

``` text
yapar/
├── first_follow.py
├── lr0.py
├── slr_table.py
├── lalr_table.py
├── ll1_table.py
├── parser_engine.py
└── yapar_parser.py
```

------------------------------------------------------------------------

# Proyecto 3 --- Compiscript

## Analizador Semántico

Compiscript es un lenguaje basado en un subconjunto de TypeScript. Para
esta etapa se utiliza **ANTLR4** para generar el lexer y parser a partir
de:

``` text
grammars/compiscript/Compiscript.g4
```

Sobre el árbol generado por ANTLR se ejecuta un `SemanticAnalyzer`
basado en el patrón Visitor.

### Pipeline

``` text
archivo.cps
    │
    ▼
ANTLR Lexer
    │
    ├──► Errores léxicos
    │
    ▼
ANTLR Parser
    │
    ├──► Errores sintácticos
    │
    ▼
Árbol sintáctico
    │
    ▼
SemanticAnalyzer
    │
    ├──► Errores semánticos
    │
    ▼
Tabla de símbolos
```

El análisis semántico se ejecuta únicamente cuando el análisis léxico y
sintáctico finaliza correctamente. De esta forma no se construye una
tabla de símbolos a partir de un programa sintácticamente inválido.

## Sistema de tipos

Se manejan tipos como:

``` text
integer
string
boolean
null
void
any
```

El analizador verifica, entre otros:

-   Asignaciones.
-   Compatibilidad de tipos.
-   Operaciones aritméticas.
-   Operaciones lógicas.
-   Comparaciones.
-   Inferencia básica de tipos.
-   Tipos de retorno.

## Ámbitos y tabla de símbolos

La implementación utiliza scopes anidados para representar:

-   Scope global.
-   Funciones.
-   Clases.
-   Métodos.
-   Bloques.
-   Bucles.

Se validan casos como:

-   Variables no declaradas.
-   Redeclaraciones dentro del mismo ámbito.
-   Acceso a símbolos de ámbitos superiores.
-   Variables locales.
-   Parámetros.
-   Constantes.
-   Closures y funciones anidadas.

## Funciones

El análisis de funciones contempla:

-   Cantidad de argumentos.
-   Tipos de argumentos.
-   Tipo de retorno.
-   Parámetros duplicados.
-   Redeclaración.
-   Recursividad.
-   Funciones anidadas.
-   `return` fuera de una función.

## Control de flujo

Se soportan construcciones como:

``` text
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

También se valida el tipo de las condiciones y se detectan situaciones
como código muerto después de instrucciones de transferencia cuando
corresponde.

## Clases y objetos

Compiscript contempla:

-   Declaración de clases.
-   Atributos.
-   Métodos.
-   Constructores.
-   Herencia.
-   `this`.
-   Creación de objetos mediante `new`.
-   Búsqueda de miembros heredados.

El analizador puede validar la existencia de clases, atributos y
métodos, así como los argumentos y tipos utilizados en llamadas y
constructores.

## Listas

Se incluyen validaciones para:

-   Compatibilidad entre elementos.
-   Tipo de elementos.
-   Acceso mediante índices.
-   Índices de tipo `integer`.

Ejemplo conceptual:

``` text
[1, 2, 3]          ✓
[1, "hola", 3]     ✗ Tipos incompatibles

numeros[0]         ✓
numeros["hola"]    ✗ El índice debe ser integer
```

### Módulos principales

``` text
compiscript/
├── errors.py
├── semantic.py
├── symbol_table.py
└── generated/
    ├── CompiscriptLexer.py
    ├── CompiscriptParser.py
    └── CompiscriptVisitor.py
```

------------------------------------------------------------------------

# Interfaz gráfica

El proyecto incluye una interfaz gráfica desarrollada con **Tkinter**,
diseñada como un pequeño IDE con estilo oscuro tipo terminal industrial.

Ejecutar con:

``` bash
python gui/app.py
```

## Funciones de la GUI

La interfaz integra YALex, YAPar y Compiscript en una sola aplicación.

### Editores

Incluye pestañas para:

-   YALex.
-   YAPar.
-   Entrada.
-   Compiscript.

El editor de Compiscript incluye numeración de líneas, resaltado de
sintaxis y posición actual del cursor.

### YALex / YAPar

La GUI permite visualizar:

-   Tokens.
-   Reglas YALex.
-   Resultado del parser.
-   Tabla SLR(1).
-   Tabla LALR.
-   Tabla LL(1).
-   Autómata LR(0).
-   FIRST/FOLLOW.
-   Gramática YAPar.

### Compiscript

La integración de Compiscript permite visualizar:

-   Tokens producidos por ANTLR.
-   Árbol sintáctico gráfico.
-   Errores léxicos.
-   Errores sintácticos.
-   Errores semánticos.
-   Tabla de símbolos organizada por scope.
-   Referencia del lenguaje.
-   Gramática de Compiscript.

El árbol sintáctico se muestra gráficamente dentro de la interfaz y
permite navegar estructuras grandes mediante desplazamiento y zoom.

Los errores se presentan por fase, línea y columna. Desde los paneles de
errores se puede navegar hacia la ubicación correspondiente en el
editor.

------------------------------------------------------------------------

# Casos de prueba

## Java

Los archivos principales son:

``` text
grammars/java/java.yal
grammars/java/java_grammar.yapar
examples/java/input_java.txt
```

La gramática utilizada contempla construcciones como clases, métodos,
variables, expresiones, condicionales, ciclos, retornos, arreglos,
llamadas y creación de objetos.

En las pruebas realizadas, la gramática Java produce múltiples
conflictos, especialmente en LL(1), debido a características como la
recursión izquierda. Los analizadores LR manejan mejor este tipo de
gramática.

## SQL

Archivos:

``` text
grammars/sql/sql.yal
grammars/sql/sql_grammar.yapar
examples/sql/query.sql
```

El subset utilizado contempla construcciones como:

-   `SELECT`
-   `FROM`
-   `WHERE`
-   `INSERT`
-   `INTO`
-   `VALUES`
-   `UPDATE`
-   `SET`
-   `DELETE`
-   `AND`
-   `OR`
-   `NOT`
-   `NULL`
-   Comparaciones.
-   Identificadores.
-   Strings.
-   Enteros.
-   Floats.

## Compiscript

Los casos de prueba se encuentran organizados por categoría:

``` text
tests/compiscript/
├── tipos/
├── ambitos/
├── funciones/
├── control_flujo/
├── clases/
└── extra/
```

Las categorías principales contienen casos correctos y casos diseñados
para producir errores.

Los casos adicionales verifican características como:

-   Constantes.
-   Código muerto.
-   Closures.
-   Atributos.
-   Métodos.
-   Constructores.
-   Listas.
-   Índices.

------------------------------------------------------------------------

# Estructura del proyecto

``` text
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
├── grammars/
│   ├── java/
│   │   ├── java.yal
│   │   └── java_grammar.yapar
│   ├── sql/
│   │   ├── sql.yal
│   │   └── sql_grammar.yapar
│   └── compiscript/
│       └── Compiscript.g4
│
├── examples/
│   ├── java/
│   │   ├── correcto.txt
│   │   ├── errores.txt
│   │   └── input_java.txt
│   ├── sql/
│   │   └── query.sql
│   └── compiscript/
│
├── tests/
│   └── compiscript/
│       ├── tipos/
│       ├── ambitos/
│       ├── funciones/
│       ├── control_flujo/
│       ├── clases/
│       └── extra/
│
├── tools/
│   └── antlr.jar
│
├── yalex.py
├── yapar.py
├── compiscript.py
├── requirements.txt
├── README.md
└── .gitignore
```

------------------------------------------------------------------------

# Instalación

## Requisitos

Se recomienda utilizar:

-   **Python 3.11**
-   **Java Runtime**
-   **Graphviz**
-   **ANTLR4**
-   **Tkinter**
-   **Git**

## 1. Clonar el repositorio

``` bash
git clone <URL-DEL-REPOSITORIO>
cd proyecto
```

> Reemplazar `<URL-DEL-REPOSITORIO>` con la URL final del repositorio.

## 2. Crear un entorno virtual

### Windows

``` powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Instalar dependencias

``` bash
pip install -r requirements.txt
```

Para Compiscript se utiliza el runtime de ANTLR4 para Python 3.

## 4. Graphviz

Graphviz debe estar instalado en el sistema para generar las
visualizaciones utilizadas por YALex.

### Windows

Instalar Graphviz y asegurarse de que su carpeta `bin` esté disponible
en la variable de entorno `PATH`.

### Ubuntu / Debian

``` bash
sudo apt install graphviz
```

### macOS

``` bash
brew install graphviz
```

## 5. Regenerar ANTLR (opcional)

El proyecto ya incluye los archivos Python generados en
`compiscript/generated/`. Solo es necesario regenerarlos si se modifica
`Compiscript.g4`.

Desde la raíz del proyecto:

``` bash
java -jar tools/antlr.jar -Dlanguage=Python3 grammars/compiscript/Compiscript.g4 -visitor -o compiscript/generated/
```

------------------------------------------------------------------------

# Uso

Todos los siguientes comandos deben ejecutarse desde la raíz del
proyecto.

## YALex

Mostrar ayuda:

``` bash
python yalex.py --help
```

### Generar lexer para Java

``` bash
python yalex.py grammars/java/java.yal -o java_lexer.py
```

Generar también todas las visualizaciones:

``` bash
python yalex.py grammars/java/java.yal -o java_lexer.py --all
```

Opciones principales:

``` text
--tree       Genera árboles de expresiones regulares
--afd        Genera el grafo del AFD
--all        Genera todas las visualizaciones
--verbose    Salida detallada al ejecutar con -run
```

### Generar lexer para SQL

``` bash
python yalex.py grammars/sql/sql.yal -o sql_lexer.py --all
```

Ejemplo de ejecución:

``` bash
python sql_lexer.py examples/sql/query.sql --verbose
```

------------------------------------------------------------------------

## YAPar

Mostrar ayuda:

``` bash
python yapar.py --help
```

### Java --- SLR(1)

``` bash
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt
```

### Java --- LALR

``` bash
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt --method lalr
```

### Java --- LL(1)

``` bash
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt --method ll1
```

### Ejecutar los tres métodos

``` bash
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/input_java.txt --all
```

### SQL

``` bash
python yapar.py grammars/sql/sql_grammar.yapar -l grammars/sql/sql.yal -i examples/sql/query.sql --all
```

------------------------------------------------------------------------

## Compiscript

Mostrar ayuda:

``` bash
python compiscript.py --help
```

Análisis estándar:

``` bash
python compiscript.py archivo.cps
```

Mostrar árbol sintáctico:

``` bash
python compiscript.py archivo.cps --tree
```

Mostrar tabla de símbolos:

``` bash
python compiscript.py archivo.cps --symbols
```

Mostrar toda la información:

``` bash
python compiscript.py archivo.cps --all
```

Ejemplo utilizando las pruebas:

``` bash
python compiscript.py tests/compiscript/funciones/ok_funciones.cps --all
```

------------------------------------------------------------------------

## GUI

Ejecutar la interfaz completa:

``` bash
python gui/app.py
```

Desde la GUI se pueden seleccionar archivos YALex, YAPar, archivos de
entrada y programas `.cps`, además de ejecutar los analizadores y
consultar sus diferentes vistas.

------------------------------------------------------------------------

# Pruebas de Compiscript

Ejemplo de programa válido:

``` bash
python compiscript.py tests/compiscript/tipos/ok_tipos.cps --all
```

Ejemplo diseñado para generar errores:

``` bash
python compiscript.py tests/compiscript/tipos/error_tipos.cps --all
```

Otros grupos disponibles:

``` text
tests/compiscript/ambitos/
tests/compiscript/funciones/
tests/compiscript/control_flujo/
tests/compiscript/clases/
tests/compiscript/extra/
```

------------------------------------------------------------------------

# Tecnologías utilizadas

  Tecnología         Uso
  ------------------ -----------------------------------------------
  **Python 3.11**    Implementación principal
  **ANTLR4**         Lexer y parser de Compiscript
  **Graphviz**       Visualización de autómatas y árboles de YALex
  **Tkinter**        Interfaz gráfica
  **Java Runtime**   Ejecución de ANTLR
  **Git / GitHub**   Control de versiones

------------------------------------------------------------------------

# Video de demostración

> **Pendiente de agregar.**

Cuando el video final esté disponible, colocar aquí el enlace:

``` text
Video demo: <URL-DEL-VIDEO>
```

```{=html}
<!--
Ejemplo:

[▶ Ver video de demostración](https://youtu.be/...)
-->
```

------------------------------------------------------------------------

# Estado del proyecto

-   [x] Generador léxico YALex.
-   [x] Construcción AFN/AFD.
-   [x] Generación automática de lexers.
-   [x] Visualización de árboles y AFD.
-   [x] Generador sintáctico YAPar.
-   [x] SLR(1).
-   [x] LALR.
-   [x] LL(1).
-   [x] FIRST/FOLLOW.
-   [x] Autómata LR(0).
-   [x] Analizador de Compiscript con ANTLR4.
-   [x] Análisis semántico.
-   [x] Scopes y tabla de símbolos.
-   [x] Pruebas semánticas.
-   [x] Integración completa en GUI.
-   [x] Árbol sintáctico gráfico de Compiscript.
-   [x] Paneles de errores léxicos, sintácticos y semánticos.
-   [x] Visualización de tabla de símbolos.
-   [ ] Video de demostración.

------------------------------------------------------------------------

# Autor

**Osman Emanuel de León García --- 23428**

Estudiante de Ingeniería en Ciencias de la Computación\
Universidad del Valle de Guatemala

------------------------------------------------------------------------

# Curso

**Diseño de Lenguajes de Programación**\
Universidad del Valle de Guatemala\
2026

# Compiler Lab — Toolkit de Construcción de Compiladores

**Proyecto académico · Construcción de Compiladores · Universidad del Valle de Guatemala · 2026**

Compiler Lab reúne herramientas de análisis léxico, sintáctico y semántico, generación de código intermedio e interpretación de SQL en una aplicación de escritorio desarrollada en Python. Los componentes pueden utilizarse por separado desde la terminal o desde la interfaz gráfica Tkinter.

## Contenido

1. [Componentes](#componentes)
2. [Requisitos e instalación](#requisitos-e-instalación)
3. [Inicio rápido](#inicio-rápido)
4. [Interfaz gráfica](#interfaz-gráfica)
5. [YALex](#yalex-generador-léxico)
6. [YAPar](#yapar-generador-sintáctico)
7. [Compiscript](#compiscript)
8. [SQL](#intérprete-sql-con-almacenamiento-en-archivos)
9. [Pruebas](#pruebas)
10. [Estructura del proyecto](#estructura-del-proyecto)
11. [Limitaciones y precauciones](#limitaciones-y-precauciones)
12. [Documentación complementaria](#documentación-complementaria)

## Componentes

| Herramienta | Entrada | Función principal | Salida |
|---|---|---|---|
| **YALex** | `.yal` | Construye un analizador léxico a partir de expresiones regulares | Lexer Python, tokens, autómatas y visualizaciones |
| **YAPar** | `.yapar`, `.yal`, `.txt` | Construye analizadores sintácticos SLR(1), LALR y LL(1) | Tablas, conflictos, aceptación/rechazo y pasos |
| **Compiscript** | `.cps` | Análisis léxico, sintáctico y semántico mediante ANTLR | Tokens, árbol, errores y tabla de símbolos |
| **Código intermedio CPS** | `.cps` válido | Genera código de tres direcciones (TAC) y reporte de memoria | TAC, temporales, offsets y registros de activación |
| **SQL** | `.sql` | Analiza y ejecuta sentencias SQL con almacenamiento propio | AST, errores, tablas CSV, metadatos e índices JSON |
| **GUI** | Archivos de las herramientas | Integra editores, controles y paneles de resultados | Aplicación Tkinter |

### Arquitectura general

```text
                        COMPILER LAB
                             |
          +------------------+------------------+
          |                  |                  |
        YALex              YAPar           Compiscript
          |                  |                  |
      Regex parser       Gramática         Lexer/Parser
          |               FIRST/FOLLOW         ANTLR
    Thompson -> AFN          |                  |
          |             LR(0), SLR,        Semántica
      Subconjuntos       LALR, LL(1)           |
          |                  |              Símbolos
         AFD              Parsing              |
          |                  |              TAC/Memoria
     Lexer Python            |                  |
          +------------------+------------------+
                             |
                      GUI (Tkinter)
                             |
                   SQL (módulo separado)
                             |
                   Lexer -> Parser -> AST
                             |
                       Semántica
                             |
                       Ejecutor
                             |
                    CSV + metadata.txt
                      + índices JSON
```

## Requisitos e instalación

- Python **3.11** (versión indicada por el proyecto).
- Dependencias Python definidas en `requirements.txt`: `antlr4-python3-runtime==4.13.2` y `graphviz==0.21`.
- **Graphviz de sistema** (ejecutable `dot` disponible en `PATH`) para generar imágenes de autómatas y árboles con Graphviz. La biblioteca Python `graphviz` por sí sola no instala ese ejecutable.
- **Tkinter** para la interfaz gráfica (normalmente incluido con Python para Windows).
- Java, únicamente si se necesita **regenerar** código desde gramáticas ANTLR usando el archivo JAR de `tools/`; no es necesario para usar los analizadores Python ya generados.

Desde PowerShell, en la raíz del repositorio:

```powershell
python --version
python -m pip install -r requirements.txt
```

Comprobar Tkinter y Graphviz:

```powershell
python -m tkinter
dot -V
```

Si `dot` no se reconoce, instala Graphviz y agrega su directorio `bin` al `PATH`. El motor SQL no necesita Graphviz para ejecutar consultas.

## Inicio rápido

Abrir la aplicación gráfica:

```powershell
python gui/app.py
```

Ejemplos de ejecución por consola:

```powershell
python yalex.py grammars/java/java.yal -o lexer_generado.py
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/correcto.txt --method slr
python compiscript.py examples/compiscript/example.cps --all
python sql.py examples/sql/query.sql --tokens --tree --ast
python ejecutar_sql.py examples/sql/universidad.sql --db database_demo
```

**Atención:** la última instrucción **ejecuta** el SQL y puede crear o modificar archivos. Usa una carpeta de pruebas y verifica antes que el script no cree tablas ya existentes. Algunos ejemplos requieren un esquema o datos previos; consulta su contenido antes de ejecutarlos.

## Interfaz gráfica

La aplicación `gui/app.py` incluye cinco áreas de trabajo: **YALex**, **YAPar**, **Entrada**, **Compiscript** y **SQL**. La barra lateral es contextual: al cambiar de herramienta solo se muestran los archivos, controles y acciones pertinentes. El contenido de cada editor se conserva al cambiar de pestaña.

| Área | Archivos/controles | Acciones |
|---|---|---|
| YALex | LEXER | SAVE |
| YAPar | LEXER, GRAMMAR, INPUT; SLR(1), LALR, LL(1), pasos | RUN, RUN ALL, SAVE |
| Entrada | LEXER, GRAMMAR, INPUT; opciones de parser | RUN, RUN ALL, SAVE |
| Compiscript | CPS | COMPILE CPS, TEST CPS, SAVE |
| SQL | SQL, DATABASE | ANALYZE SQL, EXECUTE SQL, SAVE |

### Paneles y resultados

- **YALex:** tokens y reglas léxicas.
- **YAPar / Entrada:** resultado, LR(0), FIRST/FOLLOW, SLR(1), LALR, LL(1) y gramática.
- **Compiscript:** tokens, árbol sintáctico, errores por fase, símbolos, TAC, memoria, pruebas y referencias del lenguaje.
- **SQL:** tokens, árbol sintáctico, AST, esquema, errores léxicos/sintácticos/semánticos y resultados en una tabla `ttk.Treeview` con selector de consultas.

**ANALYZE SQL** solo analiza y valida. **EXECUTE SQL** solicita confirmación y ejecuta sentencias sobre la carpeta DATABASE seleccionada. La ejecución puede modificar datos persistentes. Los botones **SAVE** conservan el comportamiento de guardado de archivos asociados a las herramientas; revisa las rutas seleccionadas antes de utilizarlos.

## YALex: generador léxico

YALex lee especificaciones `.yal`, interpreta expresiones regulares y genera analizadores léxicos ejecutables en Python.

**Proceso:** especificación → parser de regex → construcción de Thompson → AFN → construcción de subconjuntos → AFD → lexer generado.

Características implementadas: definiciones `let`, reglas `rule`, resolución de referencias, combinación de autómatas, estrategia de coincidencia más larga (*longest match*), prioridad de reglas, tokens ignorados y visualizaciones con Graphviz.

```powershell
# Generar un lexer
python yalex.py grammars/java/java.yal -o lexer_generado.py

# Generar lexer y gráficos
python yalex.py grammars/java/java.yal -o lexer_generado.py --all

# Generar y tokenizar texto directamente
python yalex.py grammars/java/java.yal -run "int x = 10;"

# Consultar opciones
python yalex.py --help
```

Módulos: `regex/`, `automata/` y `yalex/`. Las imágenes generadas requieren el ejecutable de Graphviz. Las rutas de salida de ejemplos son ilustrativas y pueden crear archivos en la carpeta de trabajo.

## YAPar: generador sintáctico

YAPar recibe gramáticas `.yapar` y, junto con un lexer YALex, permite analizar cadenas con distintos algoritmos:

- **SLR(1):** autómata LR(0), conjuntos FOLLOW y tabla ACTION/GOTO.
- **LALR:** construcción de tabla LALR y detección de conflictos.
- **LL(1):** tabla predictiva a partir de FIRST/FOLLOW.

Incluye cálculo de FIRST/FOLLOW, construcción de estados LR(0), tablas, conflictos, motores de análisis y opción para mostrar pasos.

```powershell
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/correcto.txt --method slr
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/correcto.txt --method lalr
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/correcto.txt --method ll1
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/correcto.txt --all --steps
python yapar.py --help
```

La aceptación de una cadena depende de que la gramática y el lexer sean compatibles. La detección de conflictos no implica que cualquier gramática sea válida para los tres métodos.

## Compiscript

Compiscript usa un lexer y parser generados por ANTLR. Sobre el árbol de análisis realiza comprobaciones semánticas y, cuando el programa es válido y las construcciones están soportadas, genera **código intermedio de tres direcciones (TAC)** y un reporte de memoria.

```text
archivo .cps
   -> ANTLR Lexer / Parser
   -> árbol sintáctico
   -> análisis semántico
   -> tabla de símbolos / ámbitos
   -> generación TAC
   -> reporte de memoria
```

Características: detección de errores léxicos, sintácticos y semánticos; ámbitos anidados; tipos y símbolos; funciones y clases; código intermedio; temporales; representación de datos globales, clases y registros de activación.

```powershell
python compiscript.py examples/compiscript/example.cps
python compiscript.py examples/compiscript/example.cps --tree
python compiscript.py examples/compiscript/example.cps --symbols
python compiscript.py examples/compiscript/example.cps --tac
python compiscript.py examples/compiscript/example.cps --frames
python compiscript.py examples/compiscript/example.cps --all
python compiscript.py --help
```

**Nota:** el análisis semántico y la generación de TAC no son equivalentes a ejecutar directamente el programa Compiscript como una aplicación independiente. La batería de pruebas de código intermedio incluye un intérprete de TAC para verificar salidas esperadas. Algunas construcciones sintácticamente válidas pueden no estar soportadas por el generador.

Módulos clave: `compiscript/semantic.py`, `symbol_table.py`, `codegen.py`, `tac.py`, `temps.py` y `activation_record.py`. Gramática: `grammars/compiscript/Compiscript.g4`.

## Intérprete SQL con almacenamiento en archivos

Este componente implementa un intérprete SQL **sin SQLite, MySQL, PostgreSQL ni otro DBMS** para almacenar o ejecutar consultas. Utiliza directorios, archivos CSV, `metadata.txt` y archivos JSON para índices.

**Proceso:** SQL → lexer → parser → AST → análisis semántico → motor de ejecución → archivos → resultados.

### Operaciones soportadas

| Categoría | Funcionalidades |
|---|---|
| Definición | `CREATE TABLE`, `DROP TABLE`, `CREATE INDEX`, `DROP INDEX` |
| Manipulación | `INSERT`, `UPDATE`, `DELETE` |
| Consulta | `SELECT`, `FROM`, `WHERE`, `ORDER BY`, `INNER JOIN` |
| Condiciones | `AND`, `OR`, `NOT`, `IN`, `NOT IN`, `EXISTS`, `NOT EXISTS`, comparaciones, `IS NULL` |
| Agregaciones | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `HAVING` |
| Subconsultas | `IN`, `NOT IN`, `EXISTS`, `NOT EXISTS` y escalares en condiciones |
| Tipos | `INT`, `FLOAT`, `VARCHAR(n)`, `BOOLEAN`, `DATE` (`YYYY-MM-DD`) |
| Restricciones | `PRIMARY KEY`, `UNIQUE`, `NOT NULL` |

### Archivos de almacenamiento

```text
database_demo/
├── metadata.txt
├── estudiantes.csv
├── inscripciones.csv
└── indexes/
    └── idx_edad.json
```

`metadata.txt` describe tablas, columnas, tipos, restricciones e índices. Los CSV guardan registros y los JSON mantienen correspondencias entre valores indexados y posiciones de filas. Los índices se reconstruyen al modificar los registros correspondientes.

### Análisis SQL sin ejecutar

`sql.py` muestra tokens, árbol sintáctico, AST y resultados del análisis semántico. **No modifica registros.**

```powershell
python sql.py examples/sql/query.sql --tokens --tree --ast
python sql.py examples/sql/query.sql --db database_demo --schema
python sql.py -e "SELECT nombre FROM estudiantes WHERE edad >= 18;" --tree
python sql.py --help
```

### Ejecución SQL real

`ejecutar_sql.py` procesa las sentencias y escribe resultados en archivos. Ejecuta en una base de datos de prueba, por ejemplo:

```powershell
python ejecutar_sql.py examples/sql/universidad.sql --db database_demo
```

Si la organización del proyecto movió los ejemplos de demostración a `examples/sql/demos/`, utiliza la ruta correspondiente:

```powershell
python ejecutar_sql.py examples/sql/demos/consultas_avanzadas.sql --db database_avanzadas_nueva
```

**Ejemplo autocontenido** (guardar como `ejemplo_personal.sql`):

```sql
CREATE TABLE estudiantes (
    id INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    edad INT
);
INSERT INTO estudiantes VALUES (1, 'Ana', 20);
INSERT INTO estudiantes VALUES (2, 'Luis', 22);
SELECT id, nombre FROM estudiantes WHERE edad >= 18 ORDER BY id;
UPDATE estudiantes SET edad = 23 WHERE id = 1;
SELECT * FROM estudiantes ORDER BY id;
```

```powershell
python ejecutar_sql.py ejemplo_personal.sql --db database_personal
```

No ejecutes repetidamente scripts que incluyen `CREATE TABLE` sobre la misma carpeta, pues una tabla existente produce un error semántico. Para repetir desde cero, usa una carpeta nueva o elimina **solo una base de prueba** que ya no necesites.

### Índices y subconsultas

Los índices se almacenan como archivos JSON y se mantienen al ejecutar `INSERT`, `UPDATE` y `DELETE`. El optimizador de consultas usa índices para **igualdades sencillas** de la forma `WHERE columna = literal`; no todas las expresiones complejas usan índices. El intérprete permite subconsultas correlacionadas y comprueba errores como subconsultas escalares con más de una fila.

### `NULL` y cadenas vacías

El almacenamiento actual distingue `NULL` de `''` (cadena vacía). En CSV antiguos creados antes de la corrección, las celdas vacías pueden ser ambiguas; haz respaldo antes de reutilizar datos anteriores.

## Pruebas

Ejecutar desde la raíz del repositorio:

```powershell
# Lexer, parser, AST y semántica SQL
python tests/sql/run_tests.py -v

# Generación de TAC y casos Compiscript
python tests/codegen/run_tests.py -v

# Auditoría funcional del intérprete SQL
python auditar_sql.py
```

En la última auditoría compartida durante el desarrollo, `auditar_sql.py` completó **10 pruebas sin fallos** (creación/consulta, persistencia, UPDATE/DELETE, restricciones, errores, índices, subconsultas y distinción de NULL frente a cadena vacía). Ese resultado corresponde al entorno donde se ejecutó; después de mover archivos o actualizar código, vuelve a correr las pruebas.

Las pruebas del intérprete SQL pueden usar carpetas temporales. No ejecutes demostraciones destructivas sobre bases de datos importantes. En la interfaz, **TEST CPS** ejecuta la batería de código intermedio de Compiscript.

## Estructura del proyecto

Estructura lógica de la versión organizada; las carpetas `docs/` y `examples/` pueden contener subcarpetas adicionales, y las bases de datos de prueba se generan al ejecutar los ejemplos:

```text
proyecto/
├── automata/              # AFN, AFD, Thompson, subconjuntos
├── regex/                 # Parser y nodos de expresiones regulares
├── yalex/                 # Lectura y generación de analizadores léxicos
├── yapar/                 # Gramáticas, FIRST/FOLLOW, LR, LL y parsers
├── compiscript/           # Semántica, símbolos, TAC y memoria
│   └── generated/         # Lexer y parser generados por ANTLR
├── sqlengine/             # Frontend, AST, semántica, motor y almacenamiento SQL
│   └── generated/         # Lexer y parser SQL generados por ANTLR
├── gui/
│   └── app.py             # Interfaz gráfica integrada
├── grammars/
│   ├── java/
│   ├── compiscript/
│   └── sql/
├── examples/
│   ├── java/
│   ├── compiscript/
│   └── sql/
├── tests/
│   ├── codegen/
│   ├── compiscript/
│   └── sql/
├── docs/                  # Arquitectura, TAC y documentación SQL
├── tools/                 # JAR ANTLR
├── database*/             # Bases de datos de ejemplo/prueba (generadas)
├── yalex.py               # CLI léxico
├── yapar.py               # CLI sintáctico
├── compiscript.py         # CLI Compiscript
├── sql.py                 # CLI de análisis SQL (no ejecuta)
├── ejecutar_sql.py        # CLI de ejecución SQL (modifica archivos)
├── auditar_sql.py         # Auditoría funcional SQL
├── requirements.txt
└── README.md
```

### Responsabilidades del motor SQL

| Módulo | Responsabilidad |
|---|---|
| `frontend.py` | Análisis léxico y sintáctico |
| `ast_builder.py`, `ast.py` | Construcción y representación del AST |
| `semantic.py`, `types.py` | Tipos, nombres, ámbitos y errores semánticos |
| `catalog.py`, `metadata.py` | Esquemas y metadatos |
| `storage.py` | Lectura/escritura de tablas CSV |
| `evaluator.py` | Evaluación de expresiones y conversión de tipos |
| `query_engine.py` | Consultas, JOIN, agregaciones, UPDATE y DELETE |
| `indexes.py` | Índices persistentes |
| `executor.py` | Coordinación de análisis y ejecución |

## Limitaciones y precauciones

1. **Ejecución SQL sin transacciones completas:** un script puede modificar archivos antes de encontrar un error posterior. Usa bases de prueba y realiza respaldos.
2. **Índices:** la optimización está enfocada en igualdades simples, no en todos los predicados o combinaciones posibles.
3. **Compatibilidad de datos antiguos:** el formato CSV anterior a la corrección de `NULL` no permitía distinguir siempre una cadena vacía de un valor nulo.
4. **Gramáticas y lenguajes:** los analizadores detectan conflictos y errores; no todas las gramáticas son aptas para SLR, LALR y LL(1).
5. **Compiscript:** ciertas construcciones aceptadas por el parser pueden no tener generación TAC completa; consulta los errores del generador y la documentación de código intermedio.
6. **Archivos generados:** los comandos pueden producir lexers, imágenes, CSV y JSON. No confundas estos artefactos con los archivos fuente del proyecto.
7. **Versiones:** utiliza el runtime ANTLR 4.13.2 indicado en `requirements.txt` para evitar incompatibilidades con el código generado.

## Documentación complementaria

- `docs/arquitectura.md`: arquitectura del análisis semántico y generación de TAC de Compiscript.
- `docs/CI.md`: convenciones e instrucciones del código intermedio.
- `docs/sql_ast.md`: representación del AST SQL.
- `docs/sql_semantico.md`: análisis semántico SQL.
- `python yalex.py --help`, `python yapar.py --help`, `python compiscript.py --help` y `python sql.py --help`: opciones de línea de comandos.

---

**Compiler Lab** es un proyecto educativo orientado a implementar y visualizar las etapas de construcción de compiladores, así como un intérprete SQL con almacenamiento propio basado en archivos.

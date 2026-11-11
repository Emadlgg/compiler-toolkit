<div align="center">

# Compiler Lab

### Del análisis léxico a la ejecución de código MIPS

**Plataforma educativa de construcción de compiladores e interpretación SQL**  
Construcción de Compiladores · Universidad del Valle de Guatemala · 2026

**Python** · **ANTLR 4** · **Tkinter** · **MIPS32 / MARS** · **Almacenamiento en archivos**

</div>

---
## Video de presentación

[Ver presentación de Compiler Lab (Proyectos 2.1 y 3)](https://youtu.be/gSKznUogy4g)

## Descripción

**Compiler Lab** reúne en una aplicación de escritorio las principales etapas de construcción de compiladores: análisis léxico, análisis sintáctico, análisis semántico, representación intermedia y generación de código ensamblador. Además, incorpora un **intérprete SQL propio** que almacena esquemas, registros e índices en archivos y directorios, sin delegar la ejecución de consultas a un gestor de bases de datos externo.

El proyecto integra cuatro áreas:

| Componente | Propósito | Tecnologías / salida |
|---|---|---|
| **YALex** | Generar analizadores léxicos a partir de expresiones regulares | AFN, AFD, lexer Python, visualizaciones |
| **YAPar** | Construir y explorar analizadores sintácticos | SLR(1), LALR, LL(1), tablas y conflictos |
| **Compiscript** | Analizar programas y generar código ejecutable | ANTLR, tabla de símbolos, TAC, MIPS32 |
| **SQL** | Analizar y ejecutar consultas con persistencia propia | AST, semántica, CSV, metadatos, índices JSON |

La interfaz **Compiler Lab**, desarrollada con Tkinter, permite trabajar con los cuatro componentes desde un mismo entorno.

## Arquitectura

```text
                         COMPILER LAB (Tkinter)
                                   |
              +--------------------+--------------------+
              |                    |                    |
         YALex / YAPar         Compiscript              SQL
              |                    |                    |
      Regex -> AFN -> AFD     Archivo .cps         Sentencias SQL
       FIRST / FOLLOW             |                    |
       SLR / LALR / LL1       Lexer + Parser        Lexer + Parser
              |                 (ANTLR)               (ANTLR)
        Tablas y trazas           |                    |
                            Análisis semántico       AST + semántica
                                   |                    |
                          Tabla de símbolos        Motor de consultas
                                   |                    |
                                  TAC               CSV + metadatos
                                   |                 + índices JSON
                              MIPS32 (.asm)
                                   |
                              MARS (Java)
```

### Generación de código Compiscript

El compilador transforma un archivo `.cps` en código de tres direcciones (**TAC**) y posteriormente en ensamblador **MIPS32**. La implementación incluye registros de activación, llamadas y retornos, paso de parámetros, uso de pila y asignación de registros mediante `getReg()`.

### Intérprete SQL

El intérprete procesa las consultas mediante lexer, parser, AST, análisis semántico y ejecución. La persistencia utiliza **archivos CSV, metadatos e índices JSON**. No utiliza SQLite, MySQL ni PostgreSQL como motor de ejecución.

---

## Requisitos

- **Python 3.11** como versión de referencia. Las pruebas del proyecto también se han ejecutado satisfactoriamente con **Python 3.12**.
- **Java** para ejecutar MIPS mediante MARS.
- **Tkinter** para el IDE (normalmente disponible en las instalaciones de Python para Windows).
- **Graphviz** y el ejecutable `dot` en el `PATH` para las visualizaciones de autómatas y árboles.
- Dependencias Python indicadas en `requirements.txt`, especialmente `antlr4-python3-runtime==4.13.2` y `graphviz==0.21`.

### Instalación

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Para comprobar el entorno:

```powershell
python --version
java -version
dot -V
python -m tkinter
```

> **Nota:** Graphviz para Python no instala automáticamente el ejecutable `dot`. Java y `tools/Mars.jar` son necesarios para ejecutar los programas MIPS, pero no para analizar SQL.

## Inicio rápido

### Abrir el IDE

```powershell
python gui/app.py
```

Desde el IDE puedes seleccionar las áreas **YALex**, **YAPar**, **Compiscript** y **SQL**, cargar archivos, editar código, ejecutar análisis y consultar los resultados.

### Ejecutar herramientas desde consola

```powershell
# Analizador léxico
python yalex.py grammars/java/java.yal -o lexer_generado.py

# Analizador sintáctico
python yapar.py grammars/java/java_grammar.yapar -l grammars/java/java.yal -i examples/java/correcto.txt --method slr

# Análisis de Compiscript
python compiscript.py examples/compiscript/example.cps --all

# Generar ensamblador MIPS
python compiscript.py entrega_demo/01_funciones_recursion.cps --mips --output build/programa.asm

# Ejecutar ensamblador en MARS
java -jar tools/Mars.jar nc build/programa.asm

# Analizar SQL sin ejecutarlo
python sql.py examples/sql/query.sql --tokens --tree --ast
```

Los comandos que escriben archivos pueden sobrescribir salidas existentes; utiliza rutas de prueba cuando corresponda.

---

## Uso del IDE

### SQL: analizar y ejecutar

1. Abre el IDE con `python gui/app.py` y selecciona **SQL**.
2. En el panel lateral, utiliza **DATABASE (+)** para seleccionar una carpeta de trabajo.
3. Escribe las sentencias SQL o carga un archivo con **SQL (+)**.
4. Pulsa **ANALYZE SQL** para revisar tokens, árbol sintáctico, AST, esquema y errores **sin modificar datos**.
5. Pulsa **EXECUTE SQL** y confirma la operación para ejecutar las sentencias.
6. Consulta **Resultados SQL** y selecciona el resultado de la consulta que quieras inspeccionar.

Ejemplo de una base nueva:

```sql
CREATE DATABASE universidad;
USE universidad;

CREATE TABLE estudiantes (
    id INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    edad INT
);

INSERT INTO estudiantes VALUES (1, 'Ana', 20);
INSERT INTO estudiantes VALUES (2, 'Luis', 22);

SELECT nombre, edad
FROM estudiantes
WHERE edad >= 18
ORDER BY edad DESC;
```

**Resultado esperado:** Luis (22) y Ana (20). Los registros se conservan en archivos y pueden consultarse después de reiniciar la aplicación.

> Ejecuta el ejemplo de creación sobre una carpeta de trabajo nueva. Si vuelves a ejecutar `CREATE DATABASE` o `CREATE TABLE` sobre objetos existentes, recibirás errores por duplicidad.

### SQL: funcionalidades incluidas

| Categoría | Operaciones |
|---|---|
| Definición | `CREATE TABLE`, `DROP TABLE`, `CREATE INDEX`, `DROP INDEX` |
| Datos | `INSERT`, `UPDATE`, `DELETE` |
| Consultas | `SELECT`, `WHERE`, `ORDER BY`, `AND`, `OR`, `INNER JOIN` |
| Agregación | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `HAVING` |
| Subconsultas | `IN`, `NOT IN`, `EXISTS`, `NOT EXISTS` y escalares |
| Tipos | `INT`, `FLOAT`, `VARCHAR(n)`, `BOOLEAN`, `DATE` |
| Bases de datos | `CREATE DATABASE`, `USE`, `SHOW DATABASES`, `SHOW TABLES` |

Ejemplo de índice:

```sql
CREATE INDEX idx_edad ON estudiantes (edad);
SELECT nombre FROM estudiantes WHERE edad = 20;
DROP INDEX idx_edad;
```

Los índices se guardan en archivos JSON y se actualizan al modificar registros. La optimización de consultas se centra en condiciones sencillas de igualdad (`columna = literal`); no debe asumirse que todos los predicados utilizan índices.

### Compiscript: generar y ejecutar MIPS

1. Selecciona **Compiscript** en el IDE.
2. Carga un archivo `.cps` desde **CPS (+)**.
3. Pulsa **COMPILE CPS** para revisar análisis, errores, símbolos y TAC.
4. Pulsa **BUILD MIPS** para generar ensamblador.
5. Abre **MIPS CPS** para inspeccionar el código generado.
6. Pulsa **RUN MIPS** y revisa **Consola MIPS**.
7. Utiliza **TEST MIPS** para ejecutar la batería de pruebas del generador desde el IDE.

**Demostraciones incluidas:**

| Archivo | Qué demuestra | Salida esperada |
|---|---|---|
| `entrega_demo/01_funciones_recursion.cps` | Funciones, parámetros y recursión | `120`, `55`, `6` |
| `entrega_demo/02_strings_booleanos.cps` | Strings, booleanos y condicionales | `Hola Compiscript`, `true`, `true`, `false`, `mayor` |
| `entrega_demo/03_clases_herencia.cps` | Clases, objetos y herencia | `Luis`, `20`, `2024` |
| `entrega_demo/04_ciclos_arreglos.cps` | Ciclos y arreglos | `24`, `0`, `1`, `2`, `0`, `10`, `7` |

También hay ejemplos de errores semánticos, sintácticos y de ejecución en `entrega_demo/`.

---

## Bibliotecas compiladas, importaciones y herencia

Compiler Lab permite **reutilizar clases entre archivos Compiscript**. Además de importar código fuente `.cps`, admite bibliotecas compiladas `.cplobj` que almacenan código MIPS y la información necesaria para enlazar las clases.

### 1. Definir y exportar una clase

En `Animal.cps`:

```typescript
export class Animal {
    let edad: integer;

    function constructor() {
        this.edad = 5;
    }
}
```

### 2. Construir la biblioteca

En el IDE utiliza **BUILD LIB**, o desde la consola:

```powershell
python compiscript.py Animal.cps --build-library --output build/Animal.cplobj
```

### 3. Importarla en otro archivo

```typescript
import { Animal } from "./build/Animal.cplobj";

export class Perro : Animal {
}
```

Las rutas de importación son relativas al archivo que realiza el `import`.

### 4. Compilar bibliotecas dependientes

Una biblioteca `Perro.cplobj` puede depender de `Animal.cplobj`. Compila primero la clase padre y después la hija. Las dependencias incluyen verificación de integridad mediante **SHA-256**: si cambia la biblioteca padre, debes reconstruir también las dependientes.

Para una demostración preparada, utiliza los archivos de `entrega_demo/biblioteca/` (`Animal.cps`, `Perro.cps`, `main.cps` y sus bibliotecas en `build/`).

**Restricciones conocidas:** al construir una biblioteca compilada, sus dependencias deben ser otras bibliotecas `.cplobj`, no archivos `.cps` importados como fuente. La construcción de bibliotecas tampoco admite variables globales. Consulta `docs/mips.md` para los detalles del enlace y las cadenas de herencia.

---

## Generación MIPS: detalles técnicos

- **Llamadas y retornos:** uso de `$sp`, `$fp`, `$ra`, `$v0`, argumentos y registros de activación.
- **Asignación de registros:** `RegisterAllocator.getReg(owner)` administra registros temporales `$t0–$t7`; se utilizan registros `$s0–$s7` para variables seleccionadas que permanecen vivas durante la función.
- **Uso de memoria:** temporales y valores sin registro disponible se mantienen en la pila; las variables globales se manejan mediante `$gp`.
- **Ejecución:** el ensamblador generado se valida mediante MARS.
- **Errores en tiempo de ejecución:** comprobaciones para división entre cero, referencias nulas y accesos inválidos a arreglos, entre otras.

Los detalles del diseño de marcos de activación, preservación de registros y enlace se documentan en [`docs/mips.md`](docs/mips.md).

## Pruebas y validación

Ejecuta desde la raíz del repositorio:

```powershell
# Suite general
python -m pytest tests -q --tb=short

# Pruebas específicas del generador MIPS (requiere Java y MARS)
python tests/mips/run_tests.py -v

# Pruebas del intérprete SQL
python tests/sql/run_tests.py -v

# Pruebas de generación TAC
python tests/codegen/run_tests.py -v
```

**Última validación reportada del proyecto:** `166 passed, 1 warning` en Python 3.12. La advertencia proviene de una prueba de biblioteca ZIP manipulada que genera una entrada duplicada `module.cps`; no fue una prueba fallida. Este resultado corresponde a la ejecución realizada durante el desarrollo y debe reproducirse en el entorno de entrega.

La batería incluye casos de análisis, generación de código, bibliotecas, importaciones y pruebas de integración. Las demostraciones del IDE complementan la suite automatizada, pero no la sustituyen.

---

## Estructura del repositorio

```text
proyecto/
├── automata/               # AFN, AFD y algoritmos de construcción
├── regex/                  # Expresiones regulares
├── yalex/                  # Generador léxico
├── yapar/                  # Generador sintáctico
├── compiscript/            # Semántica, TAC, memoria, MIPS y módulos
│   ├── generated/          # Analizadores generados por ANTLR
│   ├── mips/               # Generador, registros y marcos de activación
│   └── modules/            # Importaciones y bibliotecas compiladas
├── sqlengine/              # AST, semántica, ejecución y almacenamiento SQL
│   └── generated/          # Analizadores SQL generados por ANTLR
├── gui/                    # IDE Tkinter
├── grammars/               # Especificaciones de gramáticas
├── examples/               # Ejemplos de los lenguajes y herramientas
├── entrega_demo/           # Casos para presentación y bibliotecas
├── tests/                  # Pruebas automatizadas y fixtures
├── docs/                   # Documentación técnica
├── tools/                  # Herramientas Java: MARS y ANTLR
├── build/                  # Resultados y bibliotecas compiladas
├── compiscript.py          # CLI Compiscript
├── sql.py                  # CLI de análisis SQL
├── ejecutar_sql.py         # CLI de ejecución SQL
├── yalex.py                # CLI YALex
├── yapar.py                # CLI YAPar
├── requirements.txt
└── README.md
```

Las carpetas de bases de datos y salidas temporales pueden crearse durante la ejecución y estar excluidas mediante `.gitignore`.

## Documentación adicional

| Documento | Contenido |
|---|---|
| [`docs/arquitectura.md`](docs/arquitectura.md) | Arquitectura de Compiscript y análisis semántico |
| [`docs/CI.md`](docs/CI.md) | Código intermedio y convenciones TAC |
| [`docs/mips.md`](docs/mips.md) | Generación MIPS, registros, llamadas, bibliotecas y herencia |
| [`docs/sql_ast.md`](docs/sql_ast.md) | Diseño y construcción del AST SQL |
| [`docs/sql_semantico.md`](docs/sql_semantico.md) | Validaciones semánticas del intérprete SQL |

## Consideraciones y limitaciones

- El intérprete SQL **no es un servidor de base de datos**: opera sobre archivos locales y no proporciona transacciones completas, control de usuarios ni permisos de un DBMS.
- Una ejecución SQL puede escribir cambios antes de encontrar un error posterior. Usa una base de pruebas para las demostraciones.
- No todas las condiciones `WHERE` aprovechan índices; el uso optimizado está orientado a igualdades simples.
- En Compiscript, `try/catch` no está soportado por el generador TAC. La impresión directa de objetos o arreglos completos no está soportada por el generador MIPS.
- Los enteros MIPS son de 32 bits y pueden desbordarse.
- La compatibilidad entre código generado por ANTLR y el runtime instalado depende de la versión; utiliza las dependencias del proyecto.
- Los programas `.cps` pueden requerir compilación previa de bibliotecas externas cuando utilizan archivos `.cplobj`.

---

<div align="center">

**Compiler Lab**  
*Análisis, compilación, interpretación y ejecución: del código fuente al resultado.*

Proyecto académico · Universidad del Valle de Guatemala · 2026

</div>

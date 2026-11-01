# Análisis semántico del intérprete SQL

Antes de ejecutar una sentencia se verifica que tenga sentido: que las tablas, columnas e índices existan, que los tipos sean compatibles y que los valores de un `INSERT` sean correctos. Cada error dice qué pasó y **dónde** (línea y columna del nombre o de la expresión que está mal).

```
python sql.py consulta.sql --db carpeta_de_la_base
```

```
[Línea 1:7] Error semántico: La columna 'nmbre' no existe en la tabla 'estudiantes'. ¿Quisiste decir 'nombre'?
```

El análisis trabaja sobre el AST ([`sql_ast.md`](sql_ast.md)) y consulta el esquema de la base de datos (el catálogo).

## El esquema: `metadata.txt`

El esquema vive en el archivo `metadata.txt` de la carpeta de la base de datos. Es texto legible y se puede editar a mano:

```
table estudiantes
  column id INT PRIMARY KEY
  column nombre VARCHAR(50) NOT NULL
  column edad INT
  index idx_estudiantes_edad edad

table cursos
  column id INT PRIMARY KEY
  ...
```

* `table NOMBRE` abre una tabla; sus columnas e índices van debajo, con sangría.
* `column NOMBRE TIPO [PRIMARY KEY] [NOT NULL] [UNIQUE]`. Los tipos son `INT`, `FLOAT`, `VARCHAR(n)`, `BOOLEAN` y `DATE`.
* `index NOMBRE COLUMNA`: un índice sobre una columna de la tabla. Los nombres de índice son únicos en toda la base de datos.
* Las líneas en blanco y las que empiezan con `#` se ignoran.
* Un `metadata.txt` mal formado se rechaza diciendo la línea del problema.

`examples/sql/universidad_db/` trae el esquema de la base del enunciado. Si la carpeta no tiene `metadata.txt`, o no se indica ninguna, se parte de una base vacía y el script tiene que crear sus tablas.

El análisis de un script va sentencia por sentencia: cada `CREATE` o `DROP` sin errores se aplica a una **copia** del esquema, así que las sentencias siguientes ven las tablas e índices que el script va creando. Con `--schema` se muestra cómo queda el esquema al final. Un `CREATE` o `DROP` con errores no se aplica.

## Qué se verifica

| Lo que pide el enunciado | Ejemplo de mensaje |
| ------------------------ | ------------------ |
| Tabla inexistente | `La tabla 'estudiantez' no existe. ¿Quisiste decir 'estudiantes'?` |
| Columna inexistente | `La columna 'nmbre' no existe en la tabla 'estudiantes'. ¿Quisiste decir 'nombre'?` |
| Tipos incompatibles | `No se puede comparar INT con VARCHAR (operador '=')` |
| Valores incorrectos en INSERT | `La fila 1 tiene 2 valor(es) pero la tabla 'estudiantes' tiene 6 columna(s)` |
| | `El texto tiene 68 caracteres y la columna 'nombre' admite 50 (VARCHAR(50))` |
| | `La columna 'id' no admite NULL y el INSERT no le da un valor` |
| Referencias ambiguas o inválidas | `La columna 'id' es ambigua: existe en e y c. Escribe tabla.id` |
| | `La tabla o alias 'x' no existe en esta consulta` |
| Índice inexistente o duplicado | `El índice 'fantasma' no existe` |
| | `Ya existe un índice llamado 'idx_estudiantes_edad' (sobre estudiantes.edad)` |
| Subconsulta escalar con más de una columna | `Una subconsulta usada como valor debe devolver una sola columna pero devuelve 2` |

Los nombres de tablas, columnas, alias e índices **no distinguen mayúsculas**, pero se guardan y se muestran como se escribieron.

### Sentencias de definición

* `CREATE TABLE`: la tabla no puede existir; una columna no puede repetirse; `VARCHAR` necesita un largo mayor que cero; solo una columna puede ser `PRIMARY KEY`.
* `DROP TABLE`: la tabla tiene que existir. Sus índices se van con ella.
* `CREATE INDEX`: la tabla y la columna tienen que existir; el nombre del índice no puede estar usado; la columna no puede tener ya otro índice.
* `DROP INDEX`: el índice tiene que existir.

### INSERT, UPDATE y DELETE

* El `INSERT` verifica que cada columna nombrada exista y no se repita, que cada fila tenga tantos valores como columnas, y que cada valor sea del tipo de su columna. Las columnas que no se nombran tienen que admitir `NULL`. Los valores solo pueden ser constantes: una columna o una subconsulta en `VALUES` es un error.
* El `UPDATE` verifica las columnas asignadas (no pueden repetirse) y el tipo de cada valor, que sí puede usar columnas de la tabla (`SET edad = edad + 1`).
* `UPDATE` y `DELETE` verifican que la condición de `WHERE` sea booleana.
* Un valor se puede guardar en una columna si es del mismo tipo, o si es un `INT` y la columna `FLOAT`. Un `FLOAT` no se guarda en una columna `INT`. `NULL` solo va en columnas que lo admiten, y un texto no puede pasar del largo del `VARCHAR`.

### SELECT

* **Tablas y alias.** Cada tabla de `FROM` y `JOIN` tiene que existir, y no puede haber dos con el mismo nombre (hay que usar alias). Un `ON` ve las tablas de su izquierda y la que se une, pero no las de más adelante.
* **Columnas.** `columna` se busca en las tablas de la consulta; si está en más de una, es ambigua y hay que escribir `tabla.columna`. `tabla.*` y `*` se expanden a las columnas de las tablas.
* **`ORDER BY`** puede usar los alias del `SELECT` (`ORDER BY inscritos`), y solo ahí. Si un alias se llama igual que una columna, gana el alias.
* **Condiciones.** `WHERE`, `HAVING` y `ON` tienen que ser booleanas. `AND`, `OR` y `NOT` necesitan operandos booleanos.
* **Agregaciones.** `COUNT(*)` y `COUNT(x)` dan `INT`; `SUM` de un `INT` es `INT` y de un `FLOAT` es `FLOAT`; `AVG` es `FLOAT`; `MIN` y `MAX` conservan el tipo de su argumento. `SUM` y `AVG` solo aceptan números, y `MIN` y `MAX` no aceptan `BOOLEAN`. No se pueden usar en `WHERE` (el mensaje sugiere `HAVING`) ni anidadas.
* **`GROUP BY`.** Con `GROUP BY`, con agregaciones o con `HAVING`, una columna del `SELECT`, del `HAVING` o del `ORDER BY` tiene que aparecer en el `GROUP BY` o usarse dentro de una agregación. `SELECT *` no se puede combinar con eso.

### Tipos de las expresiones

* La aritmética (`+ - * /`) solo acepta `INT` y `FLOAT`. El resultado es `FLOAT` si algún operando lo es; `INT / INT` es una división entera.
* Dos valores se comparan si son números (`INT` con `FLOAT` vale), si son del mismo tipo, o si alguno es `NULL`. Un `BOOLEAN` solo se compara con `=` y `<>`.
* **Fechas.** Un texto entre comillas que se compara con una columna `DATE`, o se guarda en una, se interpreta como fecha y tiene que ser una fecha real en formato `AAAA-MM-DD` (`'2024-02-29'` vale, `'2023-02-29'` y `'2023-1-5'` no). Esto solo pasa con **literales**: un texto que viene de una columna `VARCHAR` no se convierte. `DATE '...'` también se valida.

### Subconsultas

* Una subconsulta puede ver las columnas de la consulta que la contiene (subconsultas **correlacionadas**, a cualquier profundidad); si un nombre está en las dos, gana la consulta más cercana.
* `IN` necesita que la subconsulta devuelva una sola columna, de un tipo comparable con el del lado izquierdo. `EXISTS` acepta cualquier cantidad de columnas.
* Una subconsulta usada como valor (`edad > (SELECT AVG(edad) FROM t)`) tiene que devolver una sola columna.
* **Solo se permiten en la cláusula `WHERE`** (de `SELECT`, `UPDATE` o `DELETE`); en otro lugar es un error.
* Que una subconsulta usada como valor devuelva **más de un registro** no se puede saber antes de ejecutar: eso lo verifica el ejecutor.

## Errores sin cascadas

Una expresión con un error pasa a tener tipo desconocido y no genera más errores por su culpa: `WHERE nmbre = 1 AND edad = 'x'` da exactamente dos errores, uno por cada problema. Si una tabla no existe, tampoco se reportan sus columnas. En un `INSERT` con una columna mal escrita no se avisa de que «falten» columnas. Los errores salen ordenados por su posición en el texto.

## Lo que deja anotado para el ejecutor

El análisis completa el AST con lo que el ejecutor necesitaría volver a calcular:

| Dónde | Qué |
| ----- | --- |
| Cada expresión | `sql_type`: su tipo (`INT`, `FLOAT`, `VARCHAR`, `BOOLEAN`, `DATE` o `NULL`) |
| Cada `ColumnRef` | `binding`: tabla, columna, profundidad (0 es esta consulta, 1 la que la contiene…) y tipo. En un `ORDER BY` que usa un alias, `source` vale `-1` y `column` es la posición en el resultado |
| Cada `Select` | `sources` (las tablas resueltas) y `output` (las columnas del resultado: nombre y tipo) |
| `Insert`, `Update`, `Delete` | `schema`: la tabla del catálogo; en `Insert`, `target_indexes`: la posición de cada columna destino |
| Texto usado como fecha | el literal pasa a ser de tipo `DATE` |

## Pruebas

`python tests/sql/run_tests.py` incluye tres grupos para esta fase:

* **`tests/sql/semantic/ok/` y `error/`**: scripts que deben analizar sin errores, y scripts que deben dar exactamente los errores de su `.err` (tipo, línea, columna y fragmento del mensaje). Un script puede empezar con `-- db: universidad` para partir del esquema de `tests/sql/fixtures/universidad`. Las ubicaciones esperadas se calcularon desde el texto, no desde la salida del analizador.
* **`tests/sql/semantic_cases.py`**: casos con el resultado escrito a mano: tipos de las expresiones, nombres de las columnas de salida, resolución de columnas y correlación, conversión de fechas, efectos de los `CREATE` y `DROP`, ausencia de cascadas, y el formato de `metadata.txt` (ida y vuelta, escrito a mano con comentarios y saltos de línea de Windows, y trece clases de error con su línea).
* Una prueba de robustez: el analizador recorre sin fallar todos los scripts válidos del repositorio, con y sin esquema.

# AST del intérprete SQL

El árbol sintáctico que produce el parser (`python sql.py archivo.sql --tree`) refleja la gramática: tiene una capa por cada nivel de precedencia (`expr → orExpr → andExpr → …`) y cada token de puntuación. El **AST** guarda solo lo que hace falta para analizar y ejecutar una sentencia. El análisis semántico y el ejecutor trabajan sobre el AST, nunca sobre el árbol sintáctico.

```
python sql.py -e "SELECT nombre FROM estudiantes WHERE edad >= 18;" --ast
```

```
Script
  Select
    items:
      SelectExpr
        ColumnRef nombre
    from:
      TableRef estudiantes
    where:
      BinaryOp >=
        ColumnRef edad
        Literal INT 18
```

Las líneas que terminan en `:` (`items:`, `from:`, `where:`…) solo agrupan hijos para que se lea qué es cada cosa; no son nodos. Con `--positions` cada nodo muestra dónde empieza (`[línea:columna]`).

## Cómo se usa

```python
from sqlengine.frontend import parse
from sqlengine.ast_builder import build_ast, format_ast

result = parse(texto)
if result.ok:
    script = build_ast(result)      # Script con una sentencia por cada sentencia del texto
    print(format_ast(script))
```

`build_ast` se niega a trabajar con un texto que tiene errores léxicos o sintácticos.

## Nodos (`sqlengine/ast.py`)

Todos los nodos tienen `line` y `column` (0-based, como los errores). Esa ubicación no cuenta al comparar nodos con `==`.

### Sentencias

| Nodo | Campos |
| ---- | ------ |
| `Script` | `statements` |
| `CreateTable` | `name`, `columns` (lista de `ColumnDef`) |
| `ColumnDef` | `name`, `type` (`DataType`), `primary_key`, `not_null`, `unique` |
| `DataType` | `name` (`INT`, `FLOAT`, `BOOLEAN`, `DATE`, `VARCHAR`), `length` (solo `VARCHAR`) |
| `DropTable` | `name` |
| `CreateIndex` | `name`, `table`, `column_name` |
| `DropIndex` | `name` |
| `Insert` | `table`, `columns` (o `None`), `rows` (lista de `Row`) |
| `Row` | `values` |
| `Update` | `table`, `assignments` (lista de `Assignment`), `where` |
| `Assignment` | `column_name`, `value` |
| `Delete` | `table`, `where` |
| `Select` | `items`, `from_table`, `joins`, `where`, `group_by`, `having`, `order_by` |

### Piezas de una consulta

| Nodo | Campos |
| ---- | ------ |
| `Star` | `table` (`*` o `t.*`) |
| `SelectExpr` | `expr`, `alias` |
| `TableRef` | `name`, `alias` (y `effective_name`: el alias si hay, si no el nombre) |
| `Join` | `table` (`TableRef`), `on` |
| `OrderItem` | `expr`, `descending` |

### Expresiones

| Nodo | Campos |
| ---- | ------ |
| `Literal` | `type` (`INT`, `FLOAT`, `VARCHAR`, `BOOLEAN`, `DATE`, `NULL`), `value` |
| `ColumnRef` | `name`, `table` (o `None`) |
| `UnaryOp` | `op` (`-` o `NOT`), `operand` |
| `BinaryOp` | `op` (`+ - * /`, `= <> < <= > >=`, `AND OR`), `left`, `right` |
| `IsNull` | `expr`, `negated` |
| `InList` | `expr`, `values`, `negated` |
| `InSubquery` | `expr`, `query`, `negated` |
| `Exists` | `query`, `negated` |
| `Subquery` | `query` (subconsulta escalar usada como valor) |
| `Aggregate` | `func` (`COUNT SUM AVG MIN MAX`), `arg` (`None` es `COUNT(*)`) |

## Decisiones

* Los paréntesis no generan nodo: solo agrupan.
* Las cadenas de operadores se encadenan hacia la izquierda: `1 - 2 - 3` es `(1 - 2) - 3`. `AND` va más fuerte que `OR`, y `NOT` más fuerte que `AND`.
* `!=` se guarda como `<>`.
* `-5` y `-2.5` son literales negativos; `+x` es simplemente `x`. `-x` es un `UnaryOp`.
* `NOT EXISTS (...)` es un solo nodo `Exists` con `negated=True`; `NOT IN` es `negated=True` en `InList` o `InSubquery`.
* Un texto con `'` repetida (`'O''Brien'`) se guarda ya sin duplicar: `O'Brien`.
* `DATE '2024-01-15'` es un literal de tipo `DATE`. Un texto entre comillas sin `DATE` es `VARCHAR`; convertirlo a fecha cuando la columna es `DATE` lo decide el análisis semántico, que conoce los tipos.
* Los nombres conservan las mayúsculas con que se escribieron. Compararlos sin distinguir mayúsculas es trabajo del análisis semántico.
* La posición de un operador binario es donde empieza su operando izquierdo; la de un literal negativo, el `-`.

## Pruebas

`python tests/sql/run_tests.py` incluye dos grupos para el AST:

* **Casos con resultado escrito a mano** (`tests/sql/ast_cases.py`): precedencia, asociatividad, literales, `NOT EXISTS`, las variantes de `IN`, ubicación de los nodos y más. El resultado esperado no sale del propio constructor.
* **Archivos de referencia** (`tests/sql/ast/*.sql` con su `.ast`): el AST completo de scripts pequeños. `--update` los regenera; conviene revisar el cambio antes de aceptarlo.

Además, cada script válido de `tests/sql/ok/` debe producir un AST con tantas sentencias como el árbol sintáctico.

"""
semantic.py — Análisis semántico de SQL.

Recibe el AST y el catálogo (el esquema de la base de datos) y verifica, antes de ejecutar nada:

  * tablas, columnas e índices que existen (y los que ya existen cuando no deben)
  * referencias ambiguas o inválidas (una columna que está en dos tablas, un alias que no existe)
  * tipos: comparaciones, aritmética, condiciones booleanas, funciones de agregación
  * valores de INSERT y UPDATE: cantidad, tipo, largo de VARCHAR, NULL, fechas
  * GROUP BY: una columna fuera de GROUP BY solo puede usarse dentro de una agregación
  * subconsultas: una subconsulta usada como valor o en IN debe devolver una sola columna

Cada error indica el problema y su ubicación (línea y columna del nombre o la expresión).

    result = analyze_script(script, catalog)
    result.errors            # lista de SqlError semánticos, ordenados por posición
    result.catalog           # el esquema después de aplicar los CREATE/DROP del script

Además deja anotado el AST para el ejecutor: el tipo de cada expresión (`sql_type`), a qué columna se
resolvió cada ColumnRef (`binding`), las tablas y columnas de salida de cada Select, y la tabla de
cada Insert, Update y Delete.

Lo que NO se puede saber antes de ejecutar (y por eso lo verifica el ejecutor): que una subconsulta
escalar devuelva más de un registro, y las violaciones de PRIMARY KEY, UNIQUE o NOT NULL por los datos.
"""

import dataclasses
import difflib
from dataclasses import dataclass
from typing import Any, List, Optional

from sqlengine import ast as A
from sqlengine import types as T
from sqlengine.catalog import apply_ddl
from sqlengine.errors import SqlError, SEMANTIC


@dataclass
class ColumnBinding:
    """A qué columna se resolvió un ColumnRef."""
    source: int         # posición de la tabla en FROM/JOIN (-1: una columna de salida, en ORDER BY)
    column: int         # posición de la columna en la tabla (o en el resultado, si source es -1)
    depth: int          # 0: esta consulta; 1: la que la contiene; 2: la de más afuera...
    name: str
    type: str
    table: str          # nombre con el que se refiere a la tabla (alias o nombre)


@dataclass
class Source:
    """Una tabla de FROM o JOIN dentro de una consulta."""
    name: str                   # nombre efectivo: el alias, o el nombre de la tabla
    table: Any                  # la Table del catálogo, o None si no existe (ya se reportó)


class Scope:
    """Las tablas visibles en un punto de una consulta; las subconsultas ven también las de afuera."""

    def __init__(self, sources, parent=None, constant=False):
        self.sources = sources
        self.parent = parent
        self.constant = constant        # True en VALUES: ahí no se puede usar ninguna columna
        self.aliases = {}               # alias del SELECT -> (posición en el resultado, tipo), para ORDER BY

    @property
    def has_unknown(self):
        return any(s.table is None for s in self.sources)

    def find_source(self, name):
        """(profundidad, posición, Source) de una tabla o alias, buscando desde esta consulta hacia afuera."""
        scope, depth = self, 0
        while scope is not None:
            for i, source in enumerate(scope.sources):
                if source.name.lower() == name.lower():
                    return depth, i, source
            scope, depth = scope.parent, depth + 1
        return None

    def visible_names(self):
        names, scope = [], self
        while scope is not None:
            names.extend(s.name for s in scope.sources)
            scope = scope.parent
        return names


class Ctx:
    """Qué se permite en el lugar de la expresión que se está analizando."""

    def __init__(self, clause, aggregates=False, subqueries=False, in_aggregate=False, use_aliases=False):
        self.clause = clause
        self.aggregates = aggregates
        self.subqueries = subqueries
        self.in_aggregate = in_aggregate
        self.use_aliases = use_aliases          # ORDER BY puede usar los alias del SELECT

    def inside_aggregate(self):
        return Ctx(self.clause, self.aggregates, self.subqueries, True, self.use_aliases)


@dataclass
class SemanticResult:
    errors: List[SqlError]
    catalog: Any

    @property
    def ok(self):
        return not self.errors


def analyze_script(script, catalog):
    """
    Analiza un script sentencia por sentencia. Cada CREATE/DROP sin errores se aplica a una copia del
    catálogo, así las sentencias siguientes ven las tablas e índices que el script va creando.
    """
    working = catalog.copy()
    analyzer = SemanticAnalyzer(working)
    for statement in script.statements:
        before = len(analyzer.errors)
        analyzer.analyze_statement(statement)
        if len(analyzer.errors) == before:
            apply_ddl(working, statement)
    return SemanticResult(analyzer.sorted_errors(), working)


def _suggest(name, candidates):
    close = difflib.get_close_matches(name.lower(), [c.lower() for c in candidates], n=1, cutoff=0.6)
    if not close:
        return ""
    original = next(c for c in candidates if c.lower() == close[0])
    return f" ¿Quisiste decir '{original}'?"


class SemanticAnalyzer:

    def __init__(self, catalog):
        self.catalog = catalog
        self.errors = []

    # ── errores ───────────────────────────────────────────

    def error(self, message, where):
        """`where` es un nodo o un Name: cualquier cosa con línea y columna."""
        self.errors.append(SqlError(SEMANTIC, message, where.line, where.column))

    def sorted_errors(self):
        unique = {}
        for e in self.errors:
            unique.setdefault((e.line, e.column, e.message), e)
        return sorted(unique.values(), key=lambda e: (e.line, e.column))

    # ── sentencias ────────────────────────────────────────

    def analyze_statement(self, statement):
        getattr(self, "check_" + type(statement).__name__)(statement)

    def _require_table(self, name):
        table = self.catalog.table(name)
        if table is None:
            self.error(f"La tabla '{name}' no existe." + _suggest(name, [t.name for t in self.catalog.tables]), name)
        return table

    def check_CreateTable(self, s):
        if self.catalog.has_table(s.name):
            self.error(f"La tabla '{s.name}' ya existe", s.name)
        seen, primary_keys = {}, 0
        for column in s.columns:
            key = column.name.lower()
            if key in seen:
                self.error(f"La columna '{column.name}' está repetida en CREATE TABLE (ya se definió en la línea {seen[key].line})", column.name)
            seen.setdefault(key, column.name)
            if column.type.name == "VARCHAR" and column.type.length < 1:
                self.error("VARCHAR necesita un largo mayor que cero", column.type)
            if column.primary_key:
                primary_keys += 1
                if primary_keys == 2:
                    self.error("Una tabla solo puede tener una columna PRIMARY KEY", column.name)

    def check_DropTable(self, s):
        self._require_table(s.name)

    def check_CreateIndex(self, s):
        table = self._require_table(s.table)
        existing = self.catalog.find_index(s.name)
        if existing is not None:
            self.error(f"Ya existe un índice llamado '{s.name}' (sobre {existing.table}.{existing.column})", s.name)
        if table is None:
            return
        found = table.find_column(s.column_name)
        if found is None:
            self.error(f"La columna '{s.column_name}' no existe en la tabla '{table.name}'." + _suggest(s.column_name, table.column_names), s.column_name)
            return
        duplicate = self.catalog.index_on(table.name, found[1].name)
        if duplicate is not None and existing is None:
            self.error(f"La columna '{table.name}.{found[1].name}' ya tiene un índice ('{duplicate.name}')", s.column_name)

    def check_DropIndex(self, s):
        if self.catalog.find_index(s.name) is None:
            names = [i.name for t in self.catalog.tables for i in t.indexes]
            self.error(f"El índice '{s.name}' no existe." + _suggest(s.name, names), s.name)

    # ── INSERT, UPDATE, DELETE ────────────────────────────

    def check_Insert(self, s):
        table = self._require_table(s.table)
        if table is None:
            return
        s.schema = table
        if s.columns:
            targets, seen = [], set()
            for name in s.columns:
                found = table.find_column(name)
                if found is None:
                    self.error(f"La columna '{name}' no existe en la tabla '{table.name}'." + _suggest(name, table.column_names), name)
                elif name.lower() in seen:
                    self.error(f"La columna '{name}' está repetida en el INSERT", name)
                seen.add(name.lower())
                targets.append(found)
        else:
            targets = list(enumerate(table.columns))
        s.target_indexes = [t[0] if t else None for t in targets]

        scope, ctx = Scope([], constant=True), Ctx("VALUES")
        for number, row in enumerate(s.rows, 1):
            for value in row.values:
                self._expr(value, scope, ctx)
            if len(row.values) != len(targets):
                expected = (f"el INSERT nombra {len(targets)} columna(s)" if s.columns
                            else f"la tabla '{table.name}' tiene {len(targets)} columna(s)")
                self.error(f"La fila {number} tiene {len(row.values)} valor(es) pero {expected}", row)
                continue
            for value, target in zip(row.values, targets):
                if target is not None:
                    self._check_assignable(value, target[1])

        if None in targets:                 # una columna del INSERT no existe: no se sabe cuáles «faltan»
            return
        listed = {t[1].name.lower() for t in targets}
        for column in table.columns:
            if column.name.lower() not in listed and not column.nullable:
                self.error(f"La columna '{column.name}' no admite NULL y el INSERT no le da un valor", s.table)

    def check_Update(self, s):
        table = self._require_table(s.table)
        if table is None:
            return
        s.schema = table
        scope, seen = Scope([Source(table.name, table)]), set()
        for assignment in s.assignments:
            name = assignment.column_name
            found = table.find_column(name)
            if found is None:
                self.error(f"La columna '{name}' no existe en la tabla '{table.name}'." + _suggest(name, table.column_names), name)
            elif name.lower() in seen:
                self.error(f"La columna '{name}' se asigna más de una vez en el UPDATE", name)
            seen.add(name.lower())
            self._expr(assignment.value, scope, Ctx("SET"))
            if found is not None:
                self._check_assignable(assignment.value, found[1])
        if s.where is not None:
            self._condition(s.where, scope, Ctx("WHERE", subqueries=True))

    def check_Delete(self, s):
        table = self._require_table(s.table)
        if table is None:
            return
        s.schema = table
        if s.where is not None:
            self._condition(s.where, Scope([Source(table.name, table)]), Ctx("WHERE", subqueries=True))

    def _check_assignable(self, expr, column):
        """El valor de `expr` tiene que poder guardarse en `column` (tipo, NULL, largo de VARCHAR)."""
        t = expr.sql_type
        if column.type == T.DATE and t == T.VARCHAR:
            t = self._as_date(expr)                       # '2024-01-15' se interpreta como fecha
        if t == T.UNKNOWN:
            return
        if t == T.NULL:
            if not column.nullable:
                self.error(f"La columna '{column.name}' no admite NULL", expr)
            return
        if not T.assignable(column.type, t):
            self.error(f"No se puede guardar un valor de tipo {t} en la columna '{column.name}' ({column.type_text})", expr)
        elif (column.type == T.VARCHAR and isinstance(expr, A.Literal) and expr.type == T.VARCHAR
              and column.length is not None and len(expr.value) > column.length):
            self.error(f"El texto tiene {len(expr.value)} caracteres y la columna '{column.name}' admite {column.length} ({column.type_text})", expr)

    def _as_date(self, expr):
        """Un texto entre comillas usado donde se espera una fecha pasa a ser un literal DATE."""
        if isinstance(expr, A.Literal) and expr.type == T.VARCHAR:
            if T.parse_date(expr.value) is None:
                self.error(f"Fecha no válida: '{expr.value}'. El formato es AAAA-MM-DD", expr)
                expr.sql_type = T.UNKNOWN
                return T.UNKNOWN
            expr.type = T.DATE
            expr.sql_type = T.DATE
            return T.DATE
        return T.VARCHAR

    # ── SELECT ────────────────────────────────────────────

    def check_Select(self, s):
        self._select(s, None)

    def _select(self, s, parent):
        """Analiza una consulta y devuelve sus columnas de salida: [(nombre, tipo)]."""
        sources, seen = [], set()
        for ref in [s.from_table] + [j.table for j in s.joins]:
            table = self._require_table(ref.name)
            label = ref.alias or ref.name
            if label.lower() in seen:
                self.error(f"El nombre '{label}' se repite en FROM; usa un alias distinto para cada tabla", label)
            seen.add(label.lower())
            sources.append(Source(str(label), table))

        for i, join in enumerate(s.joins):                 # un ON ve las tablas de su izquierda y la que se une
            self._condition(join.on, Scope(sources[: i + 2], parent), Ctx("ON"))

        scope = Scope(sources, parent)
        if s.where is not None:
            self._condition(s.where, scope, Ctx("WHERE", subqueries=True))
        for expr in s.group_by:
            self._expr(expr, scope, Ctx("GROUP BY"))

        output, select_exprs, stars = [], [], []
        for item in s.items:
            if isinstance(item, A.Star):
                stars.append(item)
                output.extend(self._expand_star(item, sources))
            else:
                t = self._expr(item.expr, scope, Ctx("SELECT", aggregates=True))
                if item.alias:
                    scope.aliases[item.alias.lower()] = (len(output), t)
                output.append((str(item.alias) if item.alias else self._default_name(item.expr), t))
                select_exprs.append(item.expr)

        if s.having is not None:
            self._condition(s.having, scope, Ctx("HAVING", aggregates=True))
        for order in s.order_by:
            self._expr(order.expr, scope, Ctx("ORDER BY", aggregates=True, use_aliases=True))

        self._check_grouping(s, select_exprs, stars)
        s.sources = [(src.name, src.table) for src in sources]
        s.output = output
        return output

    def _expand_star(self, item, sources):
        if item.table is None:
            return [(c.name, c.type) for src in sources if src.table for c in src.table.columns]
        for src in sources:
            if src.name.lower() == item.table.lower():
                return [(c.name, c.type) for c in src.table.columns] if src.table else []
        self.error(f"La tabla '{item.table}' no aparece en la cláusula FROM." + _suggest(item.table, [s.name for s in sources]), item.table)
        return []

    @staticmethod
    def _default_name(expr):
        return str(expr.name) if isinstance(expr, A.ColumnRef) else render_expression(expr)

    # ── GROUP BY ──────────────────────────────────────────

    def _check_grouping(self, s, select_exprs, stars):
        """Con GROUP BY o agregaciones, una columna fuera de GROUP BY solo se puede usar dentro de una agregación."""
        others = ([s.having] if s.having is not None else []) + [o.expr for o in s.order_by]
        grouped = (bool(s.group_by) or s.having is not None
                   or any(_has_aggregate(e) for e in select_exprs + others))
        if not grouped:
            return
        for star in stars:
            self.error("SELECT * no se puede usar junto con GROUP BY o funciones de agregación", star)
        for expr in select_exprs + others:
            self._must_be_grouped(expr, s.group_by)

    def _must_be_grouped(self, expr, groups):
        if any(_equivalent(expr, g) for g in groups) or isinstance(expr, A.Aggregate):
            return
        if isinstance(expr, A.ColumnRef):
            b = expr.binding
            if b is not None and b.depth == 0 and b.source >= 0:
                self.error(f"La columna '{expr.name}' debe aparecer en GROUP BY o usarse dentro de una función de agregación", expr)
            return
        for child in _children(expr):
            self._must_be_grouped(child, groups)

    # ── expresiones ───────────────────────────────────────

    def _expr(self, e, scope, ctx):
        t = getattr(self, "_x_" + type(e).__name__)(e, scope, ctx)
        e.sql_type = t
        return t

    def _condition(self, e, scope, ctx):
        t = self._expr(e, scope, ctx)
        if t not in (T.BOOLEAN, T.UNKNOWN):
            self.error(f"La condición de {ctx.clause} debe ser booleana pero es de tipo {t}", e)

    def _x_Literal(self, e, scope, ctx):
        if e.type == T.DATE and T.parse_date(e.value) is None:
            self.error(f"Fecha no válida: '{e.value}'. El formato es AAAA-MM-DD", e)
            return T.UNKNOWN
        return e.type

    def _x_ColumnRef(self, e, scope, ctx):
        if scope.constant:
            self.error(f"No se pueden usar columnas en {ctx.clause}: '{e.name}'. Aquí solo valen valores constantes", e)
            return T.UNKNOWN
        if e.table is not None:
            found = scope.find_source(e.table)
            if found is None:
                self.error(f"La tabla o alias '{e.table}' no existe en esta consulta." + _suggest(e.table, scope.visible_names()), e.table)
                return T.UNKNOWN
            depth, source_index, source = found
            if source.table is None:
                return T.UNKNOWN
            column = source.table.find_column(e.name)
            if column is None:
                self.error(f"La columna '{e.name}' no existe en la tabla '{source.name}'." + _suggest(e.name, source.table.column_names), e.name)
                return T.UNKNOWN
            return self._bind(e, source_index, column, depth, source.name)

        if ctx.use_aliases and e.name.lower() in scope.aliases:             # ORDER BY puede usar los alias del SELECT
            position, t = scope.aliases[e.name.lower()]
            e.binding = ColumnBinding(-1, position, 0, str(e.name), t, "")
            return t

        level, depth = scope, 0
        while level is not None:
            matches = []
            for i, source in enumerate(level.sources):
                column = source.table.find_column(e.name) if source.table else None
                if column is not None:
                    matches.append((i, column, source))
            if len(matches) > 1:
                where = " y ".join(f"{m[2].name}" for m in matches)
                self.error(f"La columna '{e.name}' es ambigua: existe en {where}. Escribe tabla.{e.name}", e)
                return T.UNKNOWN
            if matches:
                i, column, source = matches[0]
                return self._bind(e, i, column, depth, source.name)
            if level.has_unknown:
                return T.UNKNOWN                                           # una tabla no existe: no se sabe dónde estaría
            level, depth = level.parent, depth + 1

        every = [c.name for src in scope.sources if src.table for c in src.table.columns]
        where = (f"la tabla '{scope.sources[0].name}'" if len(scope.sources) == 1
                 else "ninguna de las tablas de la consulta (" + ", ".join(s.name for s in scope.sources) + ")")
        self.error(f"La columna '{e.name}' no existe en {where}." + _suggest(e.name, every), e)
        return T.UNKNOWN

    def _bind(self, ref, source_index, found, depth, source_name):
        index, column = found
        ref.binding = ColumnBinding(source_index, index, depth, column.name, column.type, source_name)
        return column.type

    def _x_UnaryOp(self, e, scope, ctx):
        t = self._expr(e.operand, scope, ctx)
        if e.op == "NOT":
            if t not in (T.BOOLEAN, T.UNKNOWN):
                self.error(f"NOT necesita una condición booleana pero recibe {t}", e)
            return T.BOOLEAN
        if t == T.UNKNOWN or t == T.NULL:
            return t
        if not T.is_numeric(t):
            self.error(f"El operador '-' necesita un número pero recibe {t}", e)
            return T.UNKNOWN
        return t

    def _x_BinaryOp(self, e, scope, ctx):
        lt, rt = self._expr(e.left, scope, ctx), self._expr(e.right, scope, ctx)
        if e.op in A.BinaryOp.LOGICAL:
            for side, operand, t in (("izquierdo", e.left, lt), ("derecho", e.right, rt)):
                if t not in (T.BOOLEAN, T.UNKNOWN):
                    self.error(f"{e.op} necesita condiciones booleanas pero el lado {side} es de tipo {t}", operand)
            return T.BOOLEAN
        if e.op in A.BinaryOp.COMPARISON:
            return self._compare(e, lt, rt)
        if T.UNKNOWN in (lt, rt):
            return T.UNKNOWN
        if not all(T.is_numeric(t) or t == T.NULL for t in (lt, rt)):
            self.error(f"El operador '{e.op}' necesita números pero recibe {lt} y {rt}", e)
            return T.UNKNOWN
        if lt == T.NULL and rt == T.NULL:
            return T.NULL
        return T.promote(lt if lt != T.NULL else rt, rt if rt != T.NULL else lt)

    def _compare(self, e, lt, rt):
        if lt == T.DATE and rt == T.VARCHAR:               # una fecha escrita como texto
            rt = self._as_date(e.right)
        elif rt == T.DATE and lt == T.VARCHAR:
            lt = self._as_date(e.left)
        if T.UNKNOWN not in (lt, rt) and not T.comparable(lt, rt, e.op):
            if lt == rt == T.BOOLEAN:
                self.error(f"Un valor BOOLEAN solo se puede comparar con = o <>, no con '{e.op}'", e)
            else:
                self.error(f"No se puede comparar {lt} con {rt} (operador '{e.op}')", e)
        return T.BOOLEAN

    def _x_IsNull(self, e, scope, ctx):
        self._expr(e.expr, scope, ctx)
        return T.BOOLEAN

    def _x_InList(self, e, scope, ctx):
        lt = self._expr(e.expr, scope, ctx)
        for value in e.values:
            vt = self._expr(value, scope, ctx)
            if lt == T.DATE and vt == T.VARCHAR:
                vt = self._as_date(value)
            if T.UNKNOWN not in (lt, vt) and not T.comparable(lt, vt):
                self.error(f"El valor de tipo {vt} no se puede comparar con {lt}", value)
        return T.BOOLEAN

    def _subquery_allowed(self, e, ctx):
        if ctx.subqueries:
            return True
        self.error(f"Las subconsultas solo se permiten en la cláusula WHERE (aquí está en {ctx.clause})", e)
        return False

    def _x_InSubquery(self, e, scope, ctx):
        if not self._subquery_allowed(e, ctx):
            return T.BOOLEAN
        lt = self._expr(e.expr, scope, ctx)
        output = self._select(e.query, scope)
        if len(output) != 1:
            self.error(f"La subconsulta de IN debe devolver una sola columna pero devuelve {len(output)}", e.query)
        elif T.UNKNOWN not in (lt, output[0][1]) and not T.comparable(lt, output[0][1]):
            self.error(f"No se puede comparar {lt} con {output[0][1]}, que es lo que devuelve la subconsulta", e.query)
        return T.BOOLEAN

    def _x_Exists(self, e, scope, ctx):
        if self._subquery_allowed(e, ctx):
            self._select(e.query, scope)
        return T.BOOLEAN

    def _x_Subquery(self, e, scope, ctx):
        if not self._subquery_allowed(e, ctx):
            return T.UNKNOWN
        output = self._select(e.query, scope)
        if len(output) != 1:
            self.error(f"Una subconsulta usada como valor debe devolver una sola columna pero devuelve {len(output)}", e.query)
            return T.UNKNOWN
        return output[0][1]

    def _x_Aggregate(self, e, scope, ctx):
        if not ctx.aggregates:
            hint = " Para filtrar por el resultado de una agregación usa HAVING." if ctx.clause == "WHERE" else ""
            self.error(f"La función {e.func} no se puede usar en {ctx.clause}.{hint}", e)
            return T.UNKNOWN
        if ctx.in_aggregate:
            self.error("Una función de agregación no puede contener otra función de agregación", e)
            return T.UNKNOWN
        if e.arg is None:                                   # COUNT(*)
            return T.INT
        t = self._expr(e.arg, scope, ctx.inside_aggregate())
        if e.func == "COUNT" or t == T.UNKNOWN:
            return T.INT if e.func == "COUNT" else T.UNKNOWN
        if e.func in ("SUM", "AVG"):
            if not T.is_numeric(t):
                self.error(f"{e.func} necesita un argumento numérico pero recibe {t}", e.arg)
                return T.UNKNOWN
            return T.INT if (e.func == "SUM" and t == T.INT) else T.FLOAT
        if t in (T.BOOLEAN, T.NULL):                        # MIN y MAX
            self.error(f"{e.func} no se puede aplicar a un valor de tipo {t}", e.arg)
            return T.UNKNOWN
        return t


# ── utilidades sobre el AST ───────────────────────────────

def _children(node):
    """Los nodos hijos de una expresión. No entra a las subconsultas: son otra consulta."""
    for f in dataclasses.fields(node):
        if not f.compare:
            continue
        value = getattr(node, f.name)
        for item in (value if isinstance(value, list) else [value]):
            if isinstance(item, A.Node) and not isinstance(item, A.Select):
                yield item


def _has_aggregate(node):
    return isinstance(node, A.Aggregate) or any(_has_aggregate(c) for c in _children(node))


def _equivalent(a, b):
    """¿Son la misma expresión? Dos referencias a columna lo son si se resolvieron a la misma columna."""
    if type(a) is not type(b):
        return False
    if isinstance(a, A.ColumnRef):
        x, y = a.binding, b.binding
        return x is not None and y is not None and (x.source, x.column, x.depth) == (y.source, y.column, y.depth)
    for f in dataclasses.fields(a):
        if not f.compare:
            continue
        va, vb = getattr(a, f.name), getattr(b, f.name)
        if isinstance(va, A.Node):
            if not _equivalent(va, vb):
                return False
        elif isinstance(va, list):
            if len(va) != len(vb) or not all(_equivalent(x, y) if isinstance(x, A.Node) else x == y for x, y in zip(va, vb)):
                return False
        elif va != vb:
            return False
    return True


_PRECEDENCE = {"OR": 1, "AND": 2, "=": 3, "<>": 3, "<": 3, "<=": 3, ">": 3, ">=": 3, "+": 4, "-": 4, "*": 5, "/": 5}


def render_expression(e):
    """Una expresión como texto SQL; sirve de nombre a las columnas calculadas (`COUNT(*)`, `edad * 2`)."""
    if isinstance(e, A.Literal):
        if e.type == "NULL":
            return "NULL"
        if e.type == "BOOLEAN":
            return "TRUE" if e.value else "FALSE"
        if e.type == "VARCHAR":
            return "'" + str(e.value).replace("'", "''") + "'"
        if e.type == "DATE":
            return f"DATE '{e.value}'"
        return str(e.value)
    if isinstance(e, A.ColumnRef):
        return f"{e.table}.{e.name}" if e.table else str(e.name)
    if isinstance(e, A.UnaryOp):
        inner = render_expression(e.operand)
        return f"NOT {inner}" if e.op == "NOT" else f"-{inner}"
    if isinstance(e, A.BinaryOp):
        prec = _PRECEDENCE[e.op]

        def side(child, right):
            text = render_expression(child)
            child_prec = _PRECEDENCE.get(child.op, 9) if isinstance(child, A.BinaryOp) else 9
            return f"({text})" if child_prec < prec or (right and child_prec == prec and e.op in "-/") else text

        return f"{side(e.left, False)} {e.op} {side(e.right, True)}"
    if isinstance(e, A.IsNull):
        return f"{render_expression(e.expr)} IS {'NOT ' if e.negated else ''}NULL"
    if isinstance(e, A.InList):
        return f"{render_expression(e.expr)} {'NOT ' if e.negated else ''}IN ({', '.join(render_expression(v) for v in e.values)})"
    if isinstance(e, A.InSubquery):
        return f"{render_expression(e.expr)} {'NOT ' if e.negated else ''}IN (subconsulta)"
    if isinstance(e, A.Exists):
        return f"{'NOT ' if e.negated else ''}EXISTS (subconsulta)"
    if isinstance(e, A.Subquery):
        return "(subconsulta)"
    if isinstance(e, A.Aggregate):
        return f"{e.func}(*)" if e.arg is None else f"{e.func}({render_expression(e.arg)})"
    return type(e).__name__

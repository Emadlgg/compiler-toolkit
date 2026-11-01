"""Motor de consultas SQL: JOIN, filtros, agrupaciones y ordenamiento sobre CSV."""
import csv
import os
import tempfile
from sqlengine import ast
from sqlengine.evaluator import decode, encode, evaluate
from sqlengine.storage import StorageError
from sqlengine.indexes import IndexManager


class QueryEngine:
    def __init__(self, storage):
        self.storage = storage

    def _table_rows(self, name):
        table = self.storage.catalog.table(name)
        if table is None:
            raise StorageError(f"La tabla '{name}' no existe")
        return table, self.storage.rows(name)

    @staticmethod
    def _context(table, record):
        return {col.name.lower(): decode(value, col) for col, value in zip(table.columns, record)}

    def _write(self, table, rows):
        path = self.storage._path(table.name)
        fd, temp = tempfile.mkstemp(prefix='.sql_', suffix='.csv', dir=self.storage.directory)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(table.column_names)
                writer.writerows(rows)
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    def _source(self, ref):
        table, records = self._table_rows(ref.name)
        alias = ref.effective_name.lower()
        contexts = []
        for record in records:
            values = self._context(table, record)
            contexts.append({f'{alias}.{key}': value for key, value in values.items()})
        return table, alias, contexts

    def _resolve(self, expr, row):
        if isinstance(expr, ast.ColumnRef):
            key = expr.name.lower()
            # El analizador semantico ya resolvio el origen de la columna.
            # En una subconsulta correlacionada pueden coexistir varios "id";
            # buscar solo por el sufijo produciria una falsa ambiguedad.
            binding = getattr(expr, 'binding', None)
            if binding is not None and binding.source >= 0:
                qualified = f'{binding.table.lower()}.{binding.name.lower()}'
                if qualified not in row:
                    raise StorageError(f'Columna desconocida: {qualified}')
                return row[qualified]
            if expr.table:
                qualified = f'{expr.table.lower()}.{key}'
                if qualified not in row:
                    raise StorageError(f'Columna desconocida: {qualified}')
                return row[qualified]
            matches = [value for name, value in row.items() if name.endswith('.' + key)]
            if len(matches) != 1:
                raise StorageError(f'Columna inexistente o ambigua: {expr.name}')
            return matches[0]
        if isinstance(expr, ast.InSubquery):
            value = self._resolve(expr.expr, row)
            headers, records = self.select(expr.query, outer=row)
            if len(headers) != 1:
                raise StorageError('IN requiere subconsulta de una columna')
            choices = [record[0] for record in records]
            if value is None:
                return None
            found = True if value in choices else None if None in choices else False
            return None if found is None else (not found if expr.negated else found)
        if isinstance(expr, ast.Exists):
            _, records = self.select(expr.query, outer=row)
            return (not bool(records)) if expr.negated else bool(records)
        if isinstance(expr, ast.Subquery):
            headers, records = self.select(expr.query, outer=row)
            if len(headers) != 1 or len(records) > 1:
                raise StorageError('Subconsulta escalar debe devolver una columna y maximo una fila')
            return records[0][0] if records else None
        if isinstance(expr, ast.Aggregate):
            raise StorageError('La agregacion requiere un grupo de registros')
        if isinstance(expr, ast.Literal):
            return evaluate(expr, {})
        if isinstance(expr, ast.UnaryOp):
            return evaluate(ast.UnaryOp(expr.op, ast.Literal('NULL' if (v := self._resolve(expr.operand, row)) is None else ('BOOLEAN' if isinstance(v, bool) else 'FLOAT' if isinstance(v, float) else 'INT' if isinstance(v, int) else 'VARCHAR'), v)), {})
        if isinstance(expr, ast.IsNull):
            result = self._resolve(expr.expr, row) is None
            return not result if expr.negated else result
        if isinstance(expr, ast.InList):
            val = self._resolve(expr.expr, row)
            choices = [self._resolve(x, row) for x in expr.values]
            if val is None:
                return None
            found = True if val in choices else None if None in choices else False
            return None if found is None else (not found if expr.negated else found)
        if isinstance(expr, ast.BinaryOp):
            left = self._resolve(expr.left, row)
            right = self._resolve(expr.right, row)
            # Reuse the SQL three-valued logic already implemented in evaluator.py.
            return evaluate(ast.BinaryOp(expr.op, ast.Literal('NULL', None) if left is None else ast.Literal('BOOLEAN' if isinstance(left, bool) else 'FLOAT' if isinstance(left, float) else 'INT' if isinstance(left, int) else 'VARCHAR', left), ast.Literal('NULL', None) if right is None else ast.Literal('BOOLEAN' if isinstance(right, bool) else 'FLOAT' if isinstance(right, float) else 'INT' if isinstance(right, int) else 'VARCHAR', right)), {})
        raise StorageError(f'Expresion no soportada: {type(expr).__name__}')

    def _group_value(self, expr, rows):
        if isinstance(expr, ast.Aggregate):
            values = [self._resolve(expr.arg, row) for row in rows] if expr.arg is not None else []
            valid = [value for value in values if value is not None]
            func = expr.func.upper()
            if func == 'COUNT':
                return len(rows) if expr.arg is None else len(valid)
            if func == 'SUM':
                return sum(valid) if valid else None
            if func == 'AVG':
                return sum(valid) / len(valid) if valid else None
            if func == 'MIN':
                return min(valid) if valid else None
            if func == 'MAX':
                return max(valid) if valid else None
            raise StorageError(f'Agregacion desconocida: {func}')
        if isinstance(expr, ast.BinaryOp):
            a, b = self._group_value(expr.left, rows), self._group_value(expr.right, rows)
            return evaluate(ast.BinaryOp(expr.op, ast.Literal('NULL', None) if a is None else ast.Literal('BOOLEAN' if isinstance(a, bool) else 'FLOAT' if isinstance(a, float) else 'INT' if isinstance(a, int) else 'VARCHAR', a), ast.Literal('NULL', None) if b is None else ast.Literal('BOOLEAN' if isinstance(b, bool) else 'FLOAT' if isinstance(b, float) else 'INT' if isinstance(b, int) else 'VARCHAR', b)), {})
        if isinstance(expr, ast.UnaryOp):
            value = self._group_value(expr.operand, rows)
            if value is None:
                return None
            return not value if expr.op == 'NOT' else -value
        if isinstance(expr, ast.IsNull):
            result = self._group_value(expr.expr, rows) is None
            return not result if expr.negated else result
        if not rows:
            return None
        return self._resolve(expr, rows[0])

    @staticmethod
    def _has_aggregate(expr):
        if isinstance(expr, ast.Aggregate):
            return True
        if isinstance(expr, ast.BinaryOp):
            return QueryEngine._has_aggregate(expr.left) or QueryEngine._has_aggregate(expr.right)
        if isinstance(expr, ast.UnaryOp):
            return QueryEngine._has_aggregate(expr.operand)
        return False

    def _indexed_candidates(self, stmt):
        """Devuelve posiciones CSV candidatas para WHERE columna = literal."""
        if stmt.joins or not isinstance(stmt.where, ast.BinaryOp) or stmt.where.op != '=':
            return None
        left, right = stmt.where.left, stmt.where.right
        if isinstance(right, ast.ColumnRef) and isinstance(left, ast.Literal):
            left, right = right, left
        if not isinstance(left, ast.ColumnRef) or not isinstance(right, ast.Literal):
            return None
        ref = stmt.from_table
        if left.table and left.table.lower() != ref.effective_name.lower():
            return None
        from sqlengine.evaluator import evaluate
        return IndexManager(self.storage).lookup(ref.name, left.name, evaluate(right, {}))

    def select(self, stmt, outer=None):
        sources = [stmt.from_table] + [join.table for join in stmt.joins]
        tables = []
        combined = [{}]
        candidates = self._indexed_candidates(stmt) if outer is None else None
        for index, ref in enumerate(sources):
            table, alias, records = self._source(ref)
            if index == 0 and candidates is not None:
                records = [records[i] for i in candidates if 0 <= i < len(records)]
            if any(alias == existing_alias for _, existing_alias in tables):
                raise StorageError(f'Alias de tabla duplicado: {alias}')
            tables.append((table, alias))
            joined = []
            for base in combined:
                for record in records:
                    candidate = {**(outer or {}), **base, **record}
                    if index == 0 or self._resolve(stmt.joins[index - 1].on, candidate) is True:
                        joined.append(candidate)
            combined = joined
        filtered = [row for row in combined if stmt.where is None or self._resolve(stmt.where, row) is True]
        selected = []
        for item in stmt.items:
            if isinstance(item, ast.Star):
                matched = [(table, alias) for table, alias in tables if item.table is None or item.table.lower() == alias]
                if not matched:
                    raise StorageError(f'Tabla desconocida en SELECT: {item.table}')
                for table, alias in matched:
                    for col in table.columns:
                        selected.append((col.name, ast.ColumnRef(col.name, alias)))
            elif isinstance(item, ast.SelectExpr):
                expr = item.expr
                name = item.alias or (expr.name if isinstance(expr, ast.ColumnRef) else expr.label())
                selected.append((name, expr))
            else:
                raise StorageError(f'Elemento SELECT no soportado: {type(item).__name__}')
        grouped = bool(stmt.group_by or stmt.having or any(self._has_aggregate(expr) for _, expr in selected))
        grouped = grouped or any(self._has_aggregate(order.expr) for order in stmt.order_by)
        if grouped:
            groups = {}
            for row in filtered:
                key = tuple(self._resolve(expr, row) for expr in stmt.group_by)
                groups.setdefault(key, []).append(row)
            if not stmt.group_by and not groups:
                groups[()] = []
            entries = []
            for rows in groups.values():
                if stmt.having is not None and self._group_value(stmt.having, rows) is not True:
                    continue
                values = [self._group_value(expr, rows) for _, expr in selected]
                entries.append((rows, values))
            for order in reversed(stmt.order_by):
                entries.sort(key=lambda entry: self._sort_key(self._order_value(order.expr, entry[0], selected, entry[1], grouped=True)), reverse=order.descending)
        else:
            entries = [(row, [self._resolve(expr, row) for _, expr in selected]) for row in filtered]
            for order in reversed(stmt.order_by):
                entries.sort(key=lambda entry: self._sort_key(self._order_value(order.expr, entry[0], selected, entry[1], grouped=False)), reverse=order.descending)
        return [name for name, _ in selected], [values for _, values in entries]

    @staticmethod
    def _sort_key(value):
        return (value is None, value if value is not None else 0)

    def _order_value(self, expr, context, selected, values, grouped):
        if isinstance(expr, ast.ColumnRef) and not expr.table:
            matches = [value for (name, _), value in zip(selected, values) if name.lower() == expr.name.lower()]
            if len(matches) == 1:
                return matches[0]
        return self._group_value(expr, context) if grouped else self._resolve(expr, context)

    def update(self, stmt):
        table, records = self._table_rows(stmt.table)
        changed, result = 0, []
        for record in records:
            context = self._context(table, record)
            new = list(record)
            if stmt.where is None or evaluate(stmt.where, context) is True:
                for assignment in stmt.assignments:
                    found = table.find_column(assignment.column_name)
                    if found is None:
                        raise StorageError(f'Columna desconocida: {assignment.column_name}')
                    index, column = found
                    new[index] = encode(evaluate(assignment.value, context), column)
                changed += 1
            result.append(new)
        self._validate_unique(table, result)
        self._write(table, result)
        return changed

    def delete(self, stmt):
        table, records = self._table_rows(stmt.table)
        remaining = [record for record in records if stmt.where is not None and evaluate(stmt.where, self._context(table, record)) is not True]
        self._write(table, remaining)
        return len(records) - len(remaining)

    @staticmethod
    def _validate_unique(table, rows):
        for index, col in enumerate(table.columns):
            if not col.must_be_unique:
                continue
            values = [record[index] for record in rows if record[index] != '']
            if len(values) != len(set(values)):
                raise StorageError(f"Valor duplicado en columna UNIQUE/PRIMARY KEY '{col.name}'")

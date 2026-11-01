"""Evaluacion de expresiones SQL sobre una fila tipada."""
from datetime import date
from sqlengine import ast
from sqlengine.storage import StorageError


# Codificacion compatible con los CSV anteriores:
# campo vacio = NULL; \E = VARCHAR vacio; \V... = VARCHAR que empieza con \.
EMPTY_TEXT = r'\E'
ESCAPED_TEXT = r'\V'

def decode(value, column):
    if value == '':
        return None
    if column.type == 'VARCHAR':
        if value == EMPTY_TEXT:
            return ''
        if value.startswith(ESCAPED_TEXT):
            return value[len(ESCAPED_TEXT):]
        return value
    if column.type == 'INT':
        return int(value)
    if column.type == 'FLOAT':
        return float(value)
    if column.type == 'BOOLEAN':
        return value.upper() == 'TRUE'
    if column.type == 'DATE':
        return date.fromisoformat(value)
    return value


def encode(value, column):
    if value is None:
        if not column.nullable:
            raise StorageError(f"La columna '{column.name}' no admite NULL")
        return ''
    if column.type == 'INT':
        if isinstance(value, bool) or not isinstance(value, int):
            raise StorageError(f"Se esperaba INT en '{column.name}'")
        return str(value)
    if column.type == 'FLOAT':
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise StorageError(f"Se esperaba FLOAT en '{column.name}'")
        return str(float(value))
    if column.type == 'BOOLEAN':
        if not isinstance(value, bool):
            raise StorageError(f"Se esperaba BOOLEAN en '{column.name}'")
        return 'TRUE' if value else 'FALSE'
    if column.type == 'DATE':
        if isinstance(value, date):
            return value.isoformat()
        try:
            return date.fromisoformat(value).isoformat()
        except (ValueError, TypeError):
            raise StorageError(f"Fecha invalida en '{column.name}'")
    if column.type == 'VARCHAR':
        if not isinstance(value, str) or len(value) > column.length:
            raise StorageError(f"Valor incompatible con VARCHAR({column.length}) en '{column.name}'")
        return EMPTY_TEXT if value == '' else ESCAPED_TEXT + value if value.startswith('\\') else value
    raise StorageError(f'Tipo desconocido: {column.type}')


def evaluate(expr, row):
    if isinstance(expr, ast.Literal):
        return date.fromisoformat(expr.value) if expr.type == 'DATE' and expr.value is not None else expr.value
    if isinstance(expr, ast.ColumnRef):
        key = expr.name.lower()
        if key not in row:
            raise StorageError(f"Columna desconocida: {expr.name}")
        return row[key]
    if isinstance(expr, ast.UnaryOp):
        value = evaluate(expr.operand, row)
        if expr.op == 'NOT':
            return None if value is None else not value
        if expr.op == '-':
            return None if value is None else -value
    if isinstance(expr, ast.IsNull):
        result = evaluate(expr.expr, row) is None
        return not result if expr.negated else result
    if isinstance(expr, ast.InList):
        value = evaluate(expr.expr, row)
        choices = [evaluate(x, row) for x in expr.values]
        if value is None:
            return None
        result = True if value in choices else (None if None in choices else False)
        return None if result is None else (not result if expr.negated else result)
    if isinstance(expr, ast.BinaryOp):
        left, right = evaluate(expr.left, row), evaluate(expr.right, row)
        op = expr.op.upper()
        if op == 'AND':
            if left is False or right is False:
                return False
            return None if left is None or right is None else bool(left and right)
        if op == 'OR':
            if left is True or right is True:
                return True
            return None if left is None or right is None else bool(left or right)
        if left is None or right is None:
            return None
        try:
            return {
                '=': lambda: left == right, '<>': lambda: left != right,
                '<': lambda: left < right, '<=': lambda: left <= right,
                '>': lambda: left > right, '>=': lambda: left >= right,
                '+': lambda: left + right, '-': lambda: left - right,
                '*': lambda: left * right, '/': lambda: left / right,
            }[op]()
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as error:
            raise StorageError(f'Error evaluando {op}: {error}') from error
    raise StorageError(f'Expresion no soportada por el ejecutor: {type(expr).__name__}')

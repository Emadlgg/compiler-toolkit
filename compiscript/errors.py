"""
errors.py — Clases de error semántico para Compiscript.
"""


class SemanticError:
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line    = line
        self.column  = column

    def __str__(self):
        if self.line:
            return f"[Línea {self.line}:{self.column}] Error semántico: {self.message}"
        return f"Error semántico: {self.message}"


class UndeclaredVariableError(SemanticError):
    def __init__(self, name, line=None, col=None):
        super().__init__(f"Variable '{name}' no declarada", line, col)

class RedeclarationError(SemanticError):
    def __init__(self, name, line=None, col=None):
        super().__init__(f"'{name}' ya está declarado en este ámbito", line, col)

class TypeMismatchError(SemanticError):
    def __init__(self, expected, got, line=None, col=None):
        super().__init__(f"Tipo incompatible: se esperaba '{expected}', se obtuvo '{got}'", line, col)

class InvalidOperationError(SemanticError):
    def __init__(self, op, type1, type2=None, line=None, col=None):
        if type2:
            super().__init__(f"Operación '{op}' no válida entre '{type1}' y '{type2}'", line, col)
        else:
            super().__init__(f"Operación '{op}' no válida para tipo '{type1}'", line, col)

class ReturnOutsideFunctionError(SemanticError):
    def __init__(self, line=None, col=None):
        super().__init__("'return' fuera de una función", line, col)

class BreakOutsideLoopError(SemanticError):
    def __init__(self, line=None, col=None):
        super().__init__("'break' fuera de un bucle", line, col)

class ContinueOutsideLoopError(SemanticError):
    def __init__(self, line=None, col=None):
        super().__init__("'continue' fuera de un bucle", line, col)

class NotCallableError(SemanticError):
    def __init__(self, name, line=None, col=None):
        super().__init__(f"'{name}' no es una función", line, col)

class ArgumentCountError(SemanticError):
    def __init__(self, name, expected, got, line=None, col=None):
        super().__init__(f"La función '{name}' espera {expected} argumentos, se dieron {got}", line, col)

class ReturnTypeMismatchError(SemanticError):
    def __init__(self, func, expected, got, line=None, col=None):
        super().__init__(f"Función '{func}' debe retornar '{expected}', no '{got}'", line, col)

class UndeclaredClassError(SemanticError):
    def __init__(self, name, line=None, col=None):
        super().__init__(f"Clase '{name}' no declarada", line, col)

class AttributeNotFoundError(SemanticError):
    def __init__(self, cls, attr, line=None, col=None):
        super().__init__(f"La clase '{cls}' no tiene atributo o método '{attr}'", line, col)

class ThisOutsideClassError(SemanticError):
    def __init__(self, line=None, col=None):
        super().__init__("'this' fuera de una clase", line, col)

class ConstNotInitializedError(SemanticError):
    def __init__(self, name, line=None, col=None):
        super().__init__(f"La constante '{name}' debe inicializarse en su declaración", line, col)

class NonBooleanConditionError(SemanticError):
    def __init__(self, stmt, got, line=None, col=None):
        super().__init__(f"La condición de '{stmt}' debe ser boolean, se obtuvo '{got}'", line, col)

class DeadCodeError(SemanticError):
    def __init__(self, line=None, col=None):
        super().__init__("Código muerto: instrucciones después de return/break/continue", line, col)
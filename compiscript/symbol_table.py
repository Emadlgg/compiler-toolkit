"""
symbol_table.py — Tabla de símbolos con scopes anidados para Compiscript.

Estructura:
  SymbolTable
    └── Scope (global)
          ├── symbols: {nombre: Symbol}
          └── children: [Scope (función), Scope (clase), Scope (bloque)]
"""


# ── Tipos del sistema ─────────────────────────────────────

class Type:
    INTEGER  = "integer"
    STRING   = "string"
    BOOLEAN  = "boolean"
    NULL     = "null"
    VOID     = "void"
    ANY      = "any"       # para inferencia cuando no se conoce el tipo
    UNKNOWN  = "unknown"   # para errores

    @staticmethod
    def is_numeric(t):
        return t in (Type.INTEGER,)

    @staticmethod
    def is_boolean(t):
        return t == Type.BOOLEAN

    @staticmethod
    def is_compatible(t1, t2):
        if t1 == Type.ANY or t2 == Type.ANY:
            return True
        if t1 == Type.NULL or t2 == Type.NULL:
            return True
        return t1 == t2


# ── Símbolo ───────────────────────────────────────────────

class Symbol:
    def __init__(self, name, kind, type_=None, value=None,
                 params=None, return_type=None, class_name=None):
        self.name        = name
        self.kind        = kind          # variable | const | function | class | parameter
        self.type        = type_ or Type.ANY
        self.value       = value         # para constantes
        self.params      = params or []  # [(nombre, tipo)] para funciones
        self.return_type = return_type   # tipo de retorno para funciones
        self.class_name  = class_name    # para métodos y atributos de clase

    def __repr__(self):
        if self.kind == "function":
            params = ", ".join(f"{n}:{t}" for n, t in self.params)
            return f"function {self.name}({params}) → {self.return_type}"
        if self.kind == "class":
            return f"class {self.name}"
        return f"{self.kind} {self.name}: {self.type}"


# ── Scope (ámbito) ────────────────────────────────────────

class Scope:
    def __init__(self, name, parent=None, kind="block"):
        self.name     = name    # global | function:X | class:X | block
        self.kind     = kind    # global | function | class | block | loop
        self.parent   = parent
        self.symbols  = {}      # {nombre: Symbol}
        self.children = []      # scopes hijos

        if parent:
            parent.children.append(self)

    def define(self, symbol):
        """Declara un símbolo en este scope."""
        self.symbols[symbol.name] = symbol

    def lookup_local(self, name):
        """Busca solo en este scope."""
        return self.symbols.get(name)

    def lookup(self, name):
        """Busca en este scope y en todos los padres."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def is_defined_local(self, name):
        return name in self.symbols

    def is_in_function(self):
        """Verifica si estamos dentro de una función."""
        scope = self
        while scope:
            if scope.kind == "function":
                return True
            scope = scope.parent
        return False

    def is_in_loop(self):
        """Verifica si estamos dentro de un bucle."""
        scope = self
        while scope:
            if scope.kind == "loop":
                return True
            if scope.kind == "function":
                return False  # salimos de la función sin encontrar loop
            scope = scope.parent
        return False

    def is_in_class(self):
        """Verifica si estamos dentro de una clase."""
        scope = self
        while scope:
            if scope.kind == "class":
                return True
            scope = scope.parent
        return False

    def get_current_function(self):
        """Retorna el símbolo de la función actual."""
        scope = self
        while scope:
            if scope.kind == "function" and scope.function_symbol:
                return scope.function_symbol
            scope = scope.parent
        return None

    def get_current_class(self):
        """Retorna el nombre de la clase actual."""
        scope = self
        while scope:
            if scope.kind == "class":
                return scope.name.replace("class:", "")
            scope = scope.parent
        return None

    def summary(self):
        """Resumen del scope para mostrar en la GUI."""
        lines = [f"Scope: {self.name} ({self.kind})"]
        for name, sym in self.symbols.items():
            lines.append(f"  {sym}")
        return "\n".join(lines)

    def __repr__(self):
        return f"Scope({self.name}, {len(self.symbols)} símbolos)"


# ── Tabla de símbolos principal ───────────────────────────

class SymbolTable:
    def __init__(self):
        self.global_scope  = Scope("global", parent=None, kind="global")
        self.current_scope = self.global_scope
        self.all_scopes    = [self.global_scope]
        self._register_builtins()

    def _register_builtins(self):
        """Registra funciones y tipos built-in de Compiscript."""
        builtins = [
            Symbol("print",   "function", params=[("value", Type.ANY)], return_type=Type.VOID),
            Symbol("integer", "class",    type_=Type.INTEGER),
            Symbol("string",  "class",    type_=Type.STRING),
            Symbol("boolean", "class",    type_=Type.BOOLEAN),
        ]
        for sym in builtins:
            self.global_scope.define(sym)

    # ── Manejo de scopes ──────────────────────────────────

    def enter_scope(self, name, kind="block"):
        """Crea y entra a un nuevo scope."""
        scope = Scope(name, parent=self.current_scope, kind=kind)
        scope.function_symbol = None  # se setea al entrar a función
        self.current_scope = scope
        self.all_scopes.append(scope)
        return scope

    def exit_scope(self):
        """Sale del scope actual y vuelve al padre."""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    # ── Definir símbolos ──────────────────────────────────

    def define(self, symbol):
        """Declara un símbolo en el scope actual."""
        self.current_scope.define(symbol)

    def define_variable(self, name, type_=None, line=None):
        sym = Symbol(name, "variable", type_=type_)
        sym.line = line
        self.current_scope.define(sym)
        return sym

    def define_const(self, name, type_=None, value=None, line=None):
        sym = Symbol(name, "const", type_=type_, value=value)
        sym.line = line
        self.current_scope.define(sym)
        return sym

    def define_function(self, name, params=None, return_type=None, line=None):
        sym = Symbol(name, "function", params=params or [],
                     return_type=return_type or Type.VOID)
        sym.line = line
        self.current_scope.define(sym)
        return sym

    def define_class(self, name, line=None):
        sym = Symbol(name, "class", type_=name)
        sym.line = line
        sym.attributes = {}   # {nombre: Symbol}
        sym.methods    = {}   # {nombre: Symbol}
        sym.parent_class = None
        self.current_scope.define(sym)
        return sym

    # ── Buscar símbolos ───────────────────────────────────

    def lookup(self, name):
        return self.current_scope.lookup(name)

    def lookup_local(self, name):
        return self.current_scope.lookup_local(name)

    def is_defined_local(self, name):
        return self.current_scope.is_defined_local(name)

    # ── Estado del scope ──────────────────────────────────

    def is_in_function(self):
        return self.current_scope.is_in_function()

    def is_in_loop(self):
        return self.current_scope.is_in_loop()

    def is_in_class(self):
        return self.current_scope.is_in_class()

    def get_current_function(self):
        return self.current_scope.get_current_function()

    def get_current_class(self):
        return self.current_scope.get_current_class()

    # ── Reporte ───────────────────────────────────────────

    def full_report(self):
        """Genera el reporte completo de todos los scopes."""
        lines = ["══ TABLA DE SÍMBOLOS ══\n"]
        self._report_scope(self.global_scope, lines, indent=0)
        return "\n".join(lines)

    def _report_scope(self, scope, lines, indent):
        prefix = "  " * indent
        lines.append(f"{prefix}┌─ {scope.name} ({scope.kind})")
        for name, sym in scope.symbols.items():
            lines.append(f"{prefix}│  {sym}")
        for child in scope.children:
            self._report_scope(child, lines, indent + 1)
        lines.append(f"{prefix}└─")
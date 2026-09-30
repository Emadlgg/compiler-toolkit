"""
symbol_table.py — Tabla de símbolos con scopes anidados para Compiscript.

Estructura:
  SymbolTable
    └── Scope (global)
          ├── symbols: {nombre: Symbol}
          └── children: [Scope (función), Scope (clase), Scope (bloque)]

Extensión para generación de código intermedio
----------------------------------------------
Cada símbolo guarda ahora la información que necesita el generador de TAC:

  storage   dónde vive:
              global    área de datos globales          (global+offset)
              local     variable local de una función   (fp+offset)
              param     parámetro de una función        (fp+offset)
              field     atributo de un objeto           (obj+offset)
              function  función declarada               (label)
              method    método de una clase             (label)
              class     clase
              builtin   función/tipo predefinido
  offset    desplazamiento en bytes dentro de su área
  size      tamaño en bytes (todo valor ocupa una palabra: WORD)
  label     etiqueta de código de funciones y métodos
  depth     nivel de anidamiento léxico del ámbito donde se declaró
            (global = 0). Sirve para calcular cuántos access links
            hay que seguir para llegar a una variable.

Registro de activación (por función), de dirección baja a alta:

  fp+0   valor de retorno
  fp+4   dirección de retorno
  fp+8   enlace de control (fp del llamador)
  fp+12  enlace de acceso  (fp del ámbito léxico que define la función)
  fp+16  parámetros (en métodos, `this` es el primero)
         variables locales
         (los temporales los añade el generador al final)
"""

WORD = 4                     # bytes por valor (enteros, booleanos y referencias)
FRAME_HEADER = 4 * WORD      # valor de retorno, dir. retorno, control link, access link


# ── Tipos del sistema ─────────────────────────────────────

class Type:
    INTEGER  = "integer"
    STRING   = "string"
    BOOLEAN  = "boolean"
    NULL     = "null"
    VOID     = "void"
    ANY      = "any"       # para inferencia cuando no se conoce el tipo
    UNKNOWN  = "unknown"   # para errores

    ARRAY_PREFIX = "array:"   # los arreglos se representan como "array:<elemento>"

    @staticmethod
    def is_numeric(t):
        return t in (Type.INTEGER,)

    @staticmethod
    def is_boolean(t):
        return t == Type.BOOLEAN

    @staticmethod
    def is_array(t):
        return isinstance(t, str) and t.startswith(Type.ARRAY_PREFIX)

    @staticmethod
    def array_of(element):
        return f"{Type.ARRAY_PREFIX}{element}"

    @staticmethod
    def element_type(t):
        """Tipo de los elementos de un arreglo ('array:integer' -> 'integer')."""
        if Type.is_array(t):
            return t[len(Type.ARRAY_PREFIX):]
        return Type.ANY

    @staticmethod
    def size_of(t):
        """
        Tamaño en bytes de un valor de tipo t. Enteros y booleanos ocupan una
        palabra; cadenas, arreglos y objetos se guardan por referencia, así
        que también ocupan una palabra.
        """
        return WORD

    @staticmethod
    def is_compatible(t1, t2):
        if t1 == Type.ANY or t2 == Type.ANY:
            return True
        if t1 == Type.NULL or t2 == Type.NULL:
            return True
        if Type.is_array(t1) and Type.is_array(t2):
            return Type.is_compatible(Type.element_type(t1), Type.element_type(t2))
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

        # Información para generación de código
        self.storage     = None          # global | local | param | field | function | method | class | builtin
        self.offset      = None          # desplazamiento en bytes
        self.size        = Type.size_of(self.type)
        self.label       = None          # etiqueta de funciones y métodos
        self.depth       = 0             # nivel léxico del ámbito donde se declara
        self.scope_name  = None          # nombre del scope que lo contiene
        self.frame_size  = 0             # funciones: tamaño del registro (sin temporales)

    def layout(self):
        """Ubicación del símbolo en memoria, en texto corto para reportes."""
        if self.storage == "global":
            return f"global+{self.offset}  ({self.size}B)"
        if self.storage in ("local", "param"):
            return f"fp+{self.offset}  ({self.size}B)"
        if self.storage == "field":
            return f"obj+{self.offset}  ({self.size}B)"
        if self.storage in ("function", "method"):
            return f"label={self.label}  frame={self.frame_size}B"
        if self.storage == "class":
            return f"objeto={self.size}B"
        return ""

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
        self.kind     = kind    # global | function | class | block | loop | switch
        self.parent   = parent
        self.symbols  = {}      # {nombre: Symbol}
        self.children = []      # scopes hijos

        self.function_symbol = None   # se asigna al entrar a una función
        self.class_symbol    = None   # se asigna al entrar a una clase

        # Layout de memoria. Los scopes de bloque no tienen área propia:
        # reservan espacio en el "dueño" (la función o el global que los contiene).
        if parent is None:
            self.depth = 0
        elif kind == "function":
            self.depth = parent.depth + 1
        else:
            self.depth = parent.depth
        self.owner = self if (parent is None or kind in ("global", "function", "class")) else parent.owner

        self.next_offset  = FRAME_HEADER if kind == "function" else 0
        self.max_offset   = self.next_offset
        self.frame_size   = 0
        self._saved_offset = None

        if parent:
            parent.children.append(self)

    def define(self, symbol):
        """Declara un símbolo en este scope y le asigna su ubicación."""
        self.symbols[symbol.name] = symbol
        if symbol.storage is None:
            self._allocate(symbol)

    def _allocate(self, sym):
        sym.depth      = self.depth
        sym.scope_name = self.name

        if sym.kind in ("variable", "const", "parameter"):
            if self.kind == "class":
                # atributo: desplazamiento dentro del objeto
                sym.storage = "field"
                sym.offset  = self.next_offset
                self.next_offset += sym.size
                sym.class_name = sym.class_name or self.name.replace("class:", "")
                if self.class_symbol is not None:
                    self.class_symbol.attributes[sym.name] = sym
                return
            owner = self.owner
            if owner.kind == "global":
                sym.storage = "global"
            else:
                sym.storage = "param" if sym.kind == "parameter" else "local"
            sym.offset = owner.next_offset
            owner.next_offset += sym.size
            owner.max_offset = max(owner.max_offset, owner.next_offset)

        elif sym.kind == "function":
            if self.kind == "class":
                sym.storage = "method"
                sym.class_name = sym.class_name or self.name.replace("class:", "")
                if self.class_symbol is not None:
                    self.class_symbol.methods[sym.name] = sym
            else:
                sym.storage = "function"

        elif sym.kind == "class":
            sym.storage = "class"

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
        """Verifica si estamos dentro de un bucle (para 'continue')."""
        scope = self
        while scope:
            if scope.kind == "loop":
                return True
            if scope.kind == "function":
                return False  # salimos de la función sin encontrar loop
            scope = scope.parent
        return False

    def is_in_breakable(self):
        """Verifica si estamos dentro de un bucle o un switch (para 'break')."""
        scope = self
        while scope:
            if scope.kind in ("loop", "switch"):
                return True
            if scope.kind == "function":
                return False
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
        self._labels       = set()
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
            sym.storage = "builtin"
            if sym.kind == "function":
                sym.label = sym.name
                self._labels.add(sym.name)
            self.global_scope.define(sym)

    # ── Manejo de scopes ──────────────────────────────────

    def enter_scope(self, name, kind="block"):
        """Crea y entra a un nuevo scope."""
        scope = Scope(name, parent=self.current_scope, kind=kind)
        # los bloques reservan espacio en la función que los contiene y lo
        # devuelven al salir, así bloques hermanos reutilizan los mismos slots
        if scope.owner is not scope and scope.owner.kind == "function":
            scope._saved_offset = scope.owner.next_offset
        self.current_scope = scope
        self.all_scopes.append(scope)
        return scope

    def exit_scope(self):
        """Sale del scope actual y vuelve al padre."""
        scope = self.current_scope
        owner = scope.owner

        if scope is not owner and owner.kind == "function":
            owner.max_offset = max(owner.max_offset, owner.next_offset)
            owner.next_offset = scope._saved_offset

        if scope.kind == "function":
            scope.frame_size = max(scope.max_offset, scope.next_offset)
            if scope.function_symbol is not None:
                scope.function_symbol.frame_size = scope.frame_size
        elif scope.kind == "class":
            if scope.class_symbol is not None:
                scope.class_symbol.size = scope.next_offset

        if scope.parent:
            self.current_scope = scope.parent

    # ── Definir símbolos ──────────────────────────────────

    def _make_label(self, name):
        """Etiqueta única para una función o método declarado en el scope actual."""
        scope = self.current_scope
        if scope.kind == "class":
            base = f"{scope.name.replace('class:', '')}_{name}"
        else:
            outer = scope.get_current_function()
            base = f"{outer.label}_{name}" if outer is not None and outer.label else name
        label, n = base, 1
        while label in self._labels:
            n += 1
            label = f"{base}_{n}"
        self._labels.add(label)
        return label

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

    def define_param(self, name, type_=None, line=None):
        """Parámetro de la función cuyo scope está activo."""
        sym = Symbol(name, "parameter", type_=type_)
        sym.line = line
        self.current_scope.define(sym)
        return sym

    def define_function(self, name, params=None, return_type=None, line=None):
        sym = Symbol(name, "function", params=params or [],
                     return_type=return_type or Type.VOID)
        sym.line = line
        sym.label = self._make_label(name)
        self.current_scope.define(sym)
        return sym

    def define_class(self, name, line=None):
        sym = Symbol(name, "class", type_=name)
        sym.line = line
        sym.attributes = {}   # {nombre: Symbol}
        sym.methods    = {}   # {nombre: Symbol}
        sym.parent_class = None
        sym.size = 0          # tamaño del objeto; se completa al cerrar la clase
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

    def is_in_breakable(self):
        return self.current_scope.is_in_breakable()

    def is_in_class(self):
        return self.current_scope.is_in_class()

    def get_current_function(self):
        return self.current_scope.get_current_function()

    def get_current_class(self):
        return self.current_scope.get_current_class()

    # ── Layout ────────────────────────────────────────────

    def global_size(self):
        """Bytes de datos globales."""
        return max(self.global_scope.max_offset, self.global_scope.next_offset)

    # ── Reporte ───────────────────────────────────────────

    def full_report(self):
        """Genera el reporte completo de todos los scopes."""
        lines = ["══ TABLA DE SÍMBOLOS ══\n"]
        self._report_scope(self.global_scope, lines, indent=0)
        return "\n".join(lines)

    def _report_scope(self, scope, lines, indent):
        prefix = "  " * indent
        extra = ""
        if scope.kind == "global":
            extra = f"  datos={self.global_size()}B"
        elif scope.kind == "function":
            extra = f"  nivel={scope.depth}  frame={scope.frame_size}B"
        elif scope.kind == "class":
            size = scope.class_symbol.size if scope.class_symbol else scope.next_offset
            extra = f"  objeto={size}B"
        lines.append(f"{prefix}┌─ {scope.name} ({scope.kind}){extra}")
        for name, sym in scope.symbols.items():
            where = sym.layout()
            suffix = f"    [{where}]" if where else ""
            lines.append(f"{prefix}│  {sym}{suffix}")
        for child in scope.children:
            self._report_scope(child, lines, indent + 1)
        lines.append(f"{prefix}└─")
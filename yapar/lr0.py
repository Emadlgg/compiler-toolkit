"""
lr0.py — Construcción del autómata LR(0).

Conceptos:
  - Item LR(0): producción con un punto que indica el progreso del parser
    Ej: expr → expr • PLUS term
  - Conjunto de items (estado): grupo de items que representan un estado del autómata
  - Closure: expande un conjunto de items agregando items de producciones apuntadas
  - GOTO: transición de un estado a otro consumiendo un símbolo
"""


# --------------------------------------------------
# Item LR(0)
# --------------------------------------------------
class LR0Item:
    def __init__(self, head, body, dot=0):
        """
        head: nombre de la producción (str)
        body: lista de símbolos de la regla (list)
        dot:  posición del punto (int)
        """
        self.head = head
        self.body = body
        self.dot  = dot

    @property
    def completed(self):
        """El punto está al final → se puede reducir."""
        return self.dot >= len(self.body)

    @property
    def next_symbol(self):
        """Símbolo después del punto. None si está al final."""
        if self.completed:
            return None
        return self.body[self.dot]

    def advance(self):
        """Retorna un nuevo item con el punto avanzado una posición."""
        return LR0Item(self.head, self.body, self.dot + 1)

    def __eq__(self, other):
        return (self.head == other.head and
                self.body == other.body and
                self.dot  == other.dot)

    def __hash__(self):
        return hash((self.head, tuple(self.body), self.dot))

    def __repr__(self):
        body_with_dot = list(self.body)
        body_with_dot.insert(self.dot, "•")
        return f"{self.head} → {' '.join(body_with_dot)}"


# --------------------------------------------------
# Autómata LR(0)
# --------------------------------------------------
class LR0Automaton:
    def __init__(self, productions, prod_order, terminals):
        """
        productions: dict { nombre: [ [símbolo, ...], ... ] }
        prod_order:  lista de no-terminales en orden (el primero es el inicio)
        terminals:   set de terminales
        """
        self.productions = productions
        self.prod_order  = prod_order
        self.terminals   = terminals
        self.start       = prod_order[0]

        # Augmentar la gramática: S' → S
        self.aug_start = self.start + "'"
        self.aug_productions = {self.aug_start: [[self.start]]}
        self.aug_productions.update(productions)

        # Resultados
        self.states      = []        # lista de frozensets de LR0Items
        self.transitions = {}        # { (state_idx, symbol): state_idx }
        self.state_index = {}        # { frozenset: idx }

    # --------------------------------------------------
    # Closure de un conjunto de items
    # --------------------------------------------------
    def closure(self, items):
        """
        Dado un conjunto de items, expande agregando items de las
        producciones apuntadas por el punto.
        """
        closure_set = set(items)
        queue = list(items)

        while queue:
            item = queue.pop()

            if item.completed:
                continue

            symbol = item.next_symbol

            # Si el símbolo después del punto es un no-terminal
            if symbol in self.aug_productions:
                for rule in self.aug_productions[symbol]:
                    # Manejar producciones vacías
                    body = rule if rule and rule != ["ε"] else []
                    new_item = LR0Item(symbol, body, 0)

                    if new_item not in closure_set:
                        closure_set.add(new_item)
                        queue.append(new_item)

        return frozenset(closure_set)

    # --------------------------------------------------
    # GOTO: transición de un estado por un símbolo
    # --------------------------------------------------
    def goto(self, state_items, symbol):
        """
        Avanza todos los items del estado que tienen 'symbol' después del punto.
        Retorna el closure del resultado.
        """
        moved = set()

        for item in state_items:
            if not item.completed and item.next_symbol == symbol:
                moved.add(item.advance())

        if not moved:
            return None

        return self.closure(moved)

    # --------------------------------------------------
    # Construcción principal del autómata
    # --------------------------------------------------
    def build(self):
        """
        Construye todos los estados y transiciones del autómata LR(0).
        """
        # Estado inicial: closure del item aumentado S' → • S
        initial_item  = LR0Item(self.aug_start, [self.start], 0)
        initial_state = self.closure({initial_item})

        self.states.append(initial_state)
        self.state_index[initial_state] = 0

        queue = [initial_state]

        while queue:
            current_state = queue.pop(0)
            current_idx   = self.state_index[current_state]

            # Obtener todos los símbolos después del punto en este estado
            symbols = set()
            for item in current_state:
                if not item.completed:
                    symbols.add(item.next_symbol)

            for symbol in symbols:
                next_state = self.goto(current_state, symbol)

                if next_state is None:
                    continue

                # Si el estado no existe, agregarlo
                if next_state not in self.state_index:
                    idx = len(self.states)
                    self.states.append(next_state)
                    self.state_index[next_state] = idx
                    queue.append(next_state)

                next_idx = self.state_index[next_state]
                self.transitions[(current_idx, symbol)] = next_idx

        return self

    # --------------------------------------------------
    # Pretty print
    # --------------------------------------------------
    def print_automaton(self):
        print(f"=== AUTOMATA LR(0) ===")
        print(f"Simbolo inicial aumentado: {self.aug_start} → {self.start}\n")

        for i, state in enumerate(self.states):
            print(f"Estado {i}:")
            for item in sorted(state, key=lambda x: (x.head, x.dot)):
                print(f"  {item}")

            # Mostrar transiciones desde este estado
            trans = {sym: dst for (src, sym), dst in self.transitions.items()
                     if src == i}
            if trans:
                for sym, dst in sorted(trans.items()):
                    print(f"  GOTO({sym}) → Estado {dst}")
            print()

    # --------------------------------------------------
    # Acceso a items de un estado
    # --------------------------------------------------
    def get_state(self, idx):
        return self.states[idx]

    def get_transitions_from(self, state_idx):
        return {sym: dst for (src, sym), dst in self.transitions.items()
                if src == state_idx}
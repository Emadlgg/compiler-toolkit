"""
lalr_table.py — Construcción de la tabla de parsing LALR.

Proceso:
  1. Construir items LR(1): cada item tiene un lookahead
     [A → α • β, a] significa: estamos parseando A→αβ y
     cuando reduzcamos, el siguiente token debe ser 'a'
  2. Calcular closure LR(1) — igual que LR(0) pero propagando lookaheads
  3. Construir el autómata LR(1) completo
  4. Fusionar estados con el mismo núcleo LR(0) — uniendo lookaheads
  5. Construir tabla ACTION/GOTO usando los lookaheads fusionados
"""

from yapar.first_follow import first_of_string


# --------------------------------------------------
# Item LR(1)
# --------------------------------------------------
class LR1Item:
    def __init__(self, head, body, dot, lookahead):
        self.head      = head
        self.body      = body
        self.dot       = dot
        self.lookahead = lookahead  # terminal (str)

    @property
    def completed(self):
        return self.dot >= len(self.body)

    @property
    def next_symbol(self):
        if self.completed:
            return None
        return self.body[self.dot]

    def advance(self):
        return LR1Item(self.head, self.body, self.dot + 1, self.lookahead)

    def core(self):
        """Núcleo: item sin lookahead — para fusionar estados LALR."""
        return (self.head, tuple(self.body), self.dot)

    def __eq__(self, other):
        return (self.head      == other.head and
                self.body      == other.body and
                self.dot       == other.dot  and
                self.lookahead == other.lookahead)

    def __hash__(self):
        return hash((self.head, tuple(self.body), self.dot, self.lookahead))

    def __repr__(self):
        body_with_dot = list(self.body)
        body_with_dot.insert(self.dot, "•")
        return f"[{self.head} → {' '.join(body_with_dot)}, {self.lookahead}]"


# --------------------------------------------------
# Tabla LALR
# --------------------------------------------------
class LALRTable:
    def __init__(self, automaton, first, terminals):
        """
        automaton: LR0Automaton ya construido (usamos su estructura)
        first:     dict { símbolo: set }
        terminals: set de terminales
        """
        self.automaton  = automaton
        self.first      = first
        self.terminals  = terminals

        self.aug_start      = automaton.aug_start
        self.aug_productions = automaton.aug_productions
        self.productions    = automaton.productions

        # Resultados
        self.lr1_states     = []       # lista de frozensets de LR1Items
        self.lr1_transitions = {}      # { (idx, symbol): idx }
        self.lr1_index      = {}       # { frozenset: idx }

        # Después de fusionar
        self.merged_states      = []   # lista de frozensets de LR1Items (fusionados)
        self.merged_transitions = {}
        self.merged_index       = {}

        self.action    = {}
        self.goto      = {}
        self.conflicts = []

    # --------------------------------------------------
    # Closure LR(1)
    # --------------------------------------------------
    def closure_lr1(self, items):
        closure_set = set(items)
        queue = list(items)

        while queue:
            item = queue.pop()

            if item.completed:
                continue

            symbol = item.next_symbol

            if symbol not in self.aug_productions:
                continue

            # β es lo que viene después de B en [A → α • B β, a]
            beta = item.body[item.dot + 1:]

            # FIRST(β a)
            first_beta_a = first_of_string(
                beta + [item.lookahead],
                self.first,
                self.terminals
            )

            for rule in self.aug_productions[symbol]:
                body = rule if rule and rule != ["ε"] else []

                for terminal in first_beta_a:
                    if terminal == "ε":
                        continue
                    new_item = LR1Item(symbol, body, 0, terminal)

                    if new_item not in closure_set:
                        closure_set.add(new_item)
                        queue.append(new_item)

        return frozenset(closure_set)

    # --------------------------------------------------
    # GOTO LR(1)
    # --------------------------------------------------
    def goto_lr1(self, state_items, symbol):
        moved = set()

        for item in state_items:
            if not item.completed and item.next_symbol == symbol:
                moved.add(item.advance())

        if not moved:
            return None

        return self.closure_lr1(moved)

    # --------------------------------------------------
    # Construcción del autómata LR(1)
    # --------------------------------------------------
    def build_lr1(self):
        initial_item  = LR1Item(self.aug_start, [self.automaton.start], 0, "$")
        initial_state = self.closure_lr1({initial_item})

        self.lr1_states.append(initial_state)
        self.lr1_index[initial_state] = 0

        queue = [initial_state]

        while queue:
            current = queue.pop(0)
            current_idx = self.lr1_index[current]

            symbols = set()
            for item in current:
                if not item.completed:
                    symbols.add(item.next_symbol)

            for symbol in symbols:
                next_state = self.goto_lr1(current, symbol)

                if next_state is None:
                    continue

                if next_state not in self.lr1_index:
                    idx = len(self.lr1_states)
                    self.lr1_states.append(next_state)
                    self.lr1_index[next_state] = idx
                    queue.append(next_state)

                next_idx = self.lr1_index[next_state]
                self.lr1_transitions[(current_idx, symbol)] = next_idx

    # --------------------------------------------------
    # Fusionar estados con el mismo núcleo LR(0)
    # --------------------------------------------------
    def merge_states(self):
        # Agrupar estados LR(1) por su núcleo LR(0)
        core_groups = {}

        for idx, state in enumerate(self.lr1_states):
            core = frozenset(item.core() for item in state)

            if core not in core_groups:
                core_groups[core] = []
            core_groups[core].append(idx)

        # Para cada grupo, fusionar los lookaheads
        # Mapeo: idx LR(1) → idx LALR
        lr1_to_lalr = {}
        self.merged_states = []

        for core, group in core_groups.items():
            # Fusionar todos los items del grupo uniendo lookaheads
            items_by_core = {}

            for lr1_idx in group:
                for item in self.lr1_states[lr1_idx]:
                    item_core = item.core()
                    if item_core not in items_by_core:
                        items_by_core[item_core] = set()
                    items_by_core[item_core].add(item.lookahead)

            # Crear los items fusionados (uno por núcleo, con todos los lookaheads)
            merged_items = set()
            for (head, body, dot), lookaheads in items_by_core.items():
                for la in lookaheads:
                    merged_items.add(LR1Item(head, list(body), dot, la))

            merged_frozenset = frozenset(merged_items)
            lalr_idx = len(self.merged_states)
            self.merged_states.append(merged_frozenset)
            self.merged_index[merged_frozenset] = jalr_idx = jalr_idx = lalr_idx

            for lr1_idx in group:
                lr1_to_lalr[lr1_idx] = lalr_idx

        # Remap transiciones LR(1) → LALR
        for (src, symbol), dst in self.lr1_transitions.items():
            lalr_src = lr1_to_lalr[src]
            lalr_dst = lr1_to_lalr[dst]
            self.merged_transitions[(lalr_src, symbol)] = lalr_dst

    # --------------------------------------------------
    # Construcción de la tabla ACTION/GOTO
    # --------------------------------------------------
    def build_table(self):
        for state_idx, state in enumerate(self.merged_states):
            for item in state:

                if not item.completed:
                    symbol = item.next_symbol

                    if symbol in self.terminals:
                        key = (state_idx, symbol)
                        if (state_idx, symbol) in self.merged_transitions:
                            next_state = self.merged_transitions[(state_idx, symbol)]
                            self._set_action(key, ("SHIFT", next_state), item)

                    else:
                        if (state_idx, symbol) in self.merged_transitions:
                            next_state = self.merged_transitions[(state_idx, symbol)]
                            self.goto[(state_idx, symbol)] = next_state

                else:
                    if item.head == self.aug_start:
                        self._set_action((state_idx, "$"), ("ACCEPT",), item)
                    else:
                        # REDUCE solo para el lookahead específico del item
                        key = (state_idx, item.lookahead)
                        self._set_action(
                            key,
                            ("REDUCE", item.head, tuple(item.body)),
                            item
                        )

    # --------------------------------------------------
    # Build completo
    # --------------------------------------------------
    def build(self):
        self.build_lr1()
        self.merge_states()
        self.build_table()
        return self

    # --------------------------------------------------
    # Detección de conflictos
    # --------------------------------------------------
    def _set_action(self, key, action, item):
        if key not in self.action:
            self.action[key] = action
        else:
            existing = self.action[key]
            if existing != action:
                types = {existing[0], action[0]}
                if "SHIFT" in types and "REDUCE" in types:
                    ctype = "SHIFT/REDUCE"
                elif types == {"REDUCE"}:
                    ctype = "REDUCE/REDUCE"
                else:
                    ctype = "SHIFT/SHIFT"

                self.conflicts.append({
                    "state":    key[0],
                    "symbol":   key[1],
                    "existing": existing,
                    "new":      action,
                    "type":     ctype,
                    "item":     str(item)
                })

    # --------------------------------------------------
    # Pretty print
    # --------------------------------------------------
    def print_summary(self):
        print(f"Estados LR(1):    {len(self.lr1_states)}")
        print(f"Estados LALR:     {len(self.merged_states)}")
        print(f"Entradas ACTION:  {len(self.action)}")
        print(f"Entradas GOTO:    {len(self.goto)}")
        print(f"Conflictos:       {len(self.conflicts)}")

        if self.conflicts:
            print("\n=== CONFLICTOS ===")
            for c in self.conflicts:
                print(f"  Estado {c['state']}, símbolo '{c['symbol']}': "
                      f"{c['type']} — {c['existing']} vs {c['new']}")
        else:
            print("  Gramática LALR sin conflictos.")

    def print_table(self):
        all_terminals    = sorted({sym for (_, sym) in self.action})
        all_nonterminals = sorted({sym for (_, sym) in self.goto})

        col_w = 20
        header = f"{'Estado':<8}"
        for t in all_terminals:
            header += f"{t:<{col_w}}"
        header += " | "
        for nt in all_nonterminals:
            header += f"{nt:<{col_w}}"

        print("=== TABLA LALR ===\n")
        print(header)
        print("-" * len(header))

        for state_idx in range(len(self.merged_states)):
            row = f"{state_idx:<8}"

            for t in all_terminals:
                action = self.action.get((state_idx, t), "")
                if action:
                    if action[0] == "SHIFT":
                        cell = f"S{action[1]}"
                    elif action[0] == "REDUCE":
                        body = " ".join(action[2]) if action[2] else "ε"
                        cell = f"R {action[1]}→{body}"
                    elif action[0] == "ACCEPT":
                        cell = "ACC"
                    else:
                        cell = str(action)
                else:
                    cell = ""
                row += f"{cell:<{col_w}}"

            row += " | "

            for nt in all_nonterminals:
                val = self.goto.get((state_idx, nt), "")
                row += f"{str(val):<{col_w}}"

            print(row)
"""
slr_table.py — Construcción de la tabla de parsing SLR(1).

La tabla tiene dos partes:
  - ACTION[estado][terminal]     → SHIFT n | REDUCE A→α | ACCEPT | ERROR
  - GOTO[estado][no-terminal]    → n (número de estado)

Reglas SLR(1):
  1. Si [A → α • a β] y GOTO(estado, a) = j  → ACTION[estado][a] = SHIFT j
  2. Si [A → α •] y A ≠ S'                   → ACTION[estado][a] = REDUCE A→α
                                                  para todo a ∈ FOLLOW(A)
  3. Si [S' → S •]                            → ACTION[estado][$] = ACCEPT
"""


class SLRTable:
    def __init__(self, automaton, follow, terminals):
        """
        automaton: LR0Automaton ya construido
        follow:    dict { no_terminal: set de terminales }
        terminals: set de terminales
        """
        self.automaton  = automaton
        self.follow     = follow
        self.terminals  = terminals

        self.action = {}   # { (estado, terminal): ("SHIFT", n) | ("REDUCE", head, body) | ("ACCEPT",) }
        self.goto   = {}   # { (estado, no_terminal): n }

        self.conflicts = []  # lista de conflictos detectados

    # --------------------------------------------------
    # Construcción principal
    # --------------------------------------------------
    def build(self):
        aug_start = self.automaton.aug_start

        for state_idx, state in enumerate(self.automaton.states):
            for item in state:

                # ── Caso 1: SHIFT ────────────────────────────────
                if not item.completed:
                    symbol = item.next_symbol

                    if symbol in self.terminals:
                        # Terminal después del punto → SHIFT
                        key = (state_idx, symbol)

                        if (state_idx, symbol) in self.automaton.transitions:
                            next_state = self.automaton.transitions[(state_idx, symbol)]
                            self._set_action(key, ("SHIFT", next_state), item)

                    else:
                        # No-terminal → GOTO
                        if (state_idx, symbol) in self.automaton.transitions:
                            next_state = self.automaton.transitions[(state_idx, symbol)]
                            self.goto[(state_idx, symbol)] = next_state

                # ── Caso 2: REDUCE o ACCEPT ──────────────────────
                else:
                    # Item completo
                    if item.head == aug_start:
                        # S' → S • → ACCEPT
                        key = (state_idx, "$")
                        self._set_action(key, ("ACCEPT",), item)

                    else:
                        # A → α • → REDUCE para todo terminal en FOLLOW(A)
                        follow_set = self.follow.get(item.head, set())

                        for terminal in follow_set:
                            key = (state_idx, terminal)
                            self._set_action(
                                key,
                                ("REDUCE", item.head, tuple(item.body)),
                                item
                            )

        return self

    # --------------------------------------------------
    # Agregar acción con detección de conflictos
    # --------------------------------------------------
    def _set_action(self, key, action, item):
        if key not in self.action:
            self.action[key] = action
        else:
            existing = self.action[key]
            if existing != action:
                conflict_type = self._conflict_type(existing, action)
                self.conflicts.append({
                    "state":    key[0],
                    "symbol":   key[1],
                    "existing": existing,
                    "new":      action,
                    "type":     conflict_type,
                    "item":     str(item)
                })
                # Por defecto se queda con la primera acción encontrada
                # (se puede cambiar para preferir SHIFT en conflictos S/R)

    def _conflict_type(self, a, b):
        types = {a[0], b[0]}
        if "SHIFT" in types and "REDUCE" in types:
            return "SHIFT/REDUCE"
        elif types == {"REDUCE"}:
            return "REDUCE/REDUCE"
        else:
            return "SHIFT/SHIFT"

    # --------------------------------------------------
    # Pretty print
    # --------------------------------------------------
    def print_table(self):
        # Obtener todos los terminales y no-terminales usados
        all_terminals   = sorted({sym for (_, sym) in self.action})
        all_nonterminals = sorted({sym for (_, sym) in self.goto})

        # Encabezado
        col_w = 18
        header = f"{'Estado':<8}"
        for t in all_terminals:
            header += f"{t:<{col_w}}"
        header += " | "
        for nt in all_nonterminals:
            header += f"{nt:<{col_w}}"

        print("=== TABLA SLR(1) ===\n")
        print(header)
        print("-" * len(header))

        for state_idx in range(len(self.automaton.states)):
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
                goto_val = self.goto.get((state_idx, nt), "")
                row += f"{str(goto_val):<{col_w}}"

            print(row)

        if self.conflicts:
            print(f"\n=== CONFLICTOS ({len(self.conflicts)}) ===")
            for c in self.conflicts:
                print(f"  Estado {c['state']}, símbolo '{c['symbol']}': "
                      f"{c['type']} — {c['existing']} vs {c['new']}")
        else:
            print("\n  Gramática SLR(1) sin conflictos.")

    def print_summary(self):
        n_states    = len(self.automaton.states)
        n_actions   = len(self.action)
        n_gotos     = len(self.goto)
        n_conflicts = len(self.conflicts)

        print(f"Estados:     {n_states}")
        print(f"Entradas ACTION: {n_actions}")
        print(f"Entradas GOTO:   {n_gotos}")
        print(f"Conflictos:  {n_conflicts}")
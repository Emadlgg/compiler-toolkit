"""
ll1_table.py — Construcción de la tabla de parsing LL(1).

La tabla M[A][a] indica qué producción usar cuando:
  - A es el no-terminal en el tope de la pila
  - a es el token actual de la entrada

Reglas de construcción:
  Para cada producción A → α:
    1. Para todo terminal a ∈ FIRST(α) - {ε}:
         M[A][a] = A → α
    2. Si ε ∈ FIRST(α):
         Para todo terminal b ∈ FOLLOW(A):
           M[A][b] = A → α
         Si $ ∈ FOLLOW(A):
           M[A][$] = A → α

Una gramática es LL(1) si no hay conflictos en la tabla
(cada celda tiene como máximo una producción).
"""

from yapar.first_follow import first_of_string


class LL1Table:
    def __init__(self, productions, prod_order, first, follow, terminals):
        """
        productions: dict { nombre: [ [símbolo, ...], ... ] }
        prod_order:  lista de no-terminales en orden
        first:       dict { símbolo: set }
        follow:      dict { no_terminal: set }
        terminals:   set de terminales
        """
        self.productions = productions
        self.prod_order  = prod_order
        self.first       = first
        self.follow      = follow
        self.terminals   = terminals

        self.table     = {}   # { (no_terminal, terminal): [símbolo, ...] }
        self.conflicts = []   # lista de conflictos detectados

    # --------------------------------------------------
    # Construcción principal
    # --------------------------------------------------
    def build(self):
        for non_terminal, rules in self.productions.items():
            for rule in rules:

                # FIRST(α) donde α es la regla
                body = rule if rule and rule != ["ε"] else []
                first_alpha = first_of_string(body, self.first, self.terminals)

                # Regla 1: para todo a ∈ FIRST(α) - {ε}
                for terminal in first_alpha - {"ε"}:
                    key = (non_terminal, terminal)
                    self._set_cell(key, rule)

                # Regla 2: si ε ∈ FIRST(α), usar FOLLOW(A)
                if "ε" in first_alpha:
                    follow_a = self.follow.get(non_terminal, set())

                    for terminal in follow_a:
                        key = (non_terminal, terminal)
                        self._set_cell(key, rule)

        return self

    # --------------------------------------------------
    # Insertar en la tabla con detección de conflictos
    # --------------------------------------------------
    def _set_cell(self, key, rule):
        if key not in self.table:
            self.table[key] = rule
        else:
            existing = self.table[key]
            if existing != rule:
                self.conflicts.append({
                    "non_terminal": key[0],
                    "terminal":     key[1],
                    "existing":     existing,
                    "new":          rule
                })

    # --------------------------------------------------
    # Pretty print de la tabla
    # --------------------------------------------------
    def print_table(self):
        # Obtener todos los terminales usados en la tabla
        all_terminals = sorted({t for (_, t) in self.table})

        col_w = 25
        header = f"{'No-terminal':<20}"
        for t in all_terminals:
            header += f"{t:<{col_w}}"

        print("=== TABLA LL(1) ===\n")
        print(header)
        print("-" * len(header))

        for nt in self.prod_order:
            row = f"{nt:<20}"
            for t in all_terminals:
                cell = self.table.get((nt, t))
                if cell is not None:
                    body = " ".join(cell) if cell else "ε"
                    content = f"{nt}→{body}"
                else:
                    content = ""
                row += f"{content:<{col_w}}"
            print(row)

        if self.conflicts:
            print(f"\n=== CONFLICTOS ({len(self.conflicts)}) ===")
            for c in self.conflicts:
                existing = " ".join(c['existing']) if c['existing'] else "ε"
                new      = " ".join(c['new'])      if c['new']      else "ε"
                print(f"  M[{c['non_terminal']}][{c['terminal']}]: "
                      f"{c['non_terminal']}→{existing} vs {c['non_terminal']}→{new}")
            print("\n  La gramática NO es LL(1).")
        else:
            print("\n  Gramática LL(1) sin conflictos.")

    def print_summary(self):
        print(f"No-terminales:   {len(self.productions)}")
        print(f"Terminales:      {len(self.terminals)}")
        print(f"Entradas tabla:  {len(self.table)}")
        print(f"Conflictos:      {len(self.conflicts)}")

        if not self.conflicts:
            print("  La gramática ES LL(1).")
        else:
            print("  La gramática NO es LL(1).")
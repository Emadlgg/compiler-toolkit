"""
parser_engine.py — Motor de análisis sintáctico.

Soporta tres modos:
  - SLR(1):  usa tabla SLRTable
  - LALR:    usa tabla LALRTable
  - LL(1):   usa tabla LL1Table

En todos los casos la entrada es una lista de tokens
producidos por el lexer de YALex.
"""


# --------------------------------------------------
# Resultado del análisis
# --------------------------------------------------
class ParseResult:
    def __init__(self):
        self.accepted   = False
        self.steps      = []    # pasos del análisis
        self.errors     = []    # errores encontrados
        self.derivation = []    # derivación (para LL(1))

    def add_step(self, stack, input_remaining, action):
        self.steps.append({
            "stack":  str(stack),
            "input":  str(input_remaining),
            "action": action
        })

    def add_error(self, msg):
        self.errors.append(msg)

    def __repr__(self):
        status = "ACEPTADA" if self.accepted else "RECHAZADA"
        return f"ParseResult({status}, {len(self.errors)} errores)"


# --------------------------------------------------
# Motor SLR / LALR (comparten la misma lógica)
# --------------------------------------------------
class LRParserEngine:
    def __init__(self, table, ignored=None):
        """
        table:   SLRTable o LALRTable (tienen action, goto, automaton)
        ignored: set de tokens a ignorar (ej: {'_WS'})
        """
        self.table   = table
        self.ignored = ignored or set()

    def parse(self, tokens):
        """
        tokens: lista de (token_name, lexeme) producida por tokenize()
        Retorna: ParseResult
        """
        result = ParseResult()

        # Filtrar tokens ignorados y agregar $
        filtered = [(tok, lex) for tok, lex in tokens
                    if tok not in self.ignored and not tok.startswith("_")]
        filtered.append(("$", "$"))

        # Pila de estados
        stack  = [0]
        pos    = 0

        while True:
            state       = stack[-1]
            token, lexeme = filtered[pos]

            action = self.table.action.get((state, token))

            # ── Sin acción → error ───────────────────────────────
            if action is None:
                expected = [sym for (st, sym) in self.table.action
                            if st == state]
                msg = (f"Error sintáctico en '{lexeme}' (token: {token}). "
                       f"Se esperaba: {', '.join(sorted(expected))}")
                result.add_error(msg)
                result.add_step(list(stack), filtered[pos:], f"ERROR: {msg}")

                # Recuperación de pánico: saltar token
                pos += 1
                if pos >= len(filtered):
                    break
                continue

            # ── SHIFT ────────────────────────────────────────────
            if action[0] == "SHIFT":
                next_state = action[1]
                result.add_step(
                    list(stack),
                    filtered[pos:],
                    f"SHIFT {token}='{lexeme}' → estado {next_state}"
                )
                stack.append(next_state)
                pos += 1

            # ── REDUCE ───────────────────────────────────────────
            elif action[0] == "REDUCE":
                head = action[1]
                body = action[2]

                # Pop |body| estados de la pila
                if body:
                    for _ in body:
                        stack.pop()

                # Estado tope después del pop
                top_state = stack[-1]

                # GOTO para el no-terminal reducido
                goto_state = self.table.goto.get((top_state, head))

                if goto_state is None:
                    msg = (f"Error GOTO: no hay transición desde estado "
                           f"{top_state} con '{head}'")
                    result.add_error(msg)
                    result.add_step(list(stack), filtered[pos:],
                                    f"ERROR GOTO: {msg}")
                    break

                body_str = " ".join(body) if body else "ε"
                result.add_step(
                    list(stack),
                    filtered[pos:],
                    f"REDUCE {head} → {body_str}, GOTO {goto_state}"
                )
                stack.append(goto_state)

            # ── ACCEPT ───────────────────────────────────────────
            elif action[0] == "ACCEPT":
                result.add_step(list(stack), filtered[pos:], "ACCEPT")
                result.accepted = True
                break

        return result


# --------------------------------------------------
# Motor LL(1)
# --------------------------------------------------
class LL1ParserEngine:
    def __init__(self, table, start_symbol, ignored=None):
        """
        table:        LL1Table ya construida
        start_symbol: símbolo inicial de la gramática
        ignored:      set de tokens a ignorar
        """
        self.table        = table
        self.start_symbol = start_symbol
        self.ignored      = ignored or set()

    def parse(self, tokens):
        """
        tokens: lista de (token_name, lexeme)
        Retorna: ParseResult
        """
        result = ParseResult()

        # Filtrar ignorados y agregar $
        filtered = [(tok, lex) for tok, lex in tokens
                    if tok not in self.ignored and not tok.startswith("_")]
        filtered.append(("$", "$"))

        # Pila predictiva: inicia con $ y el símbolo inicial
        stack     = ["$", self.start_symbol]
        pos       = 0
        max_steps = 10000  # límite para evitar loops infinitos
        steps     = 0

        while stack and steps < max_steps:
            steps += 1
            top           = stack[-1]
            token, lexeme = filtered[pos]

            # ── Aceptación ───────────────────────────────────────
            if top == "$" and token == "$":
                result.add_step(list(stack), filtered[pos:], "ACCEPT")
                result.accepted = True
                break

            # ── Match: tope = terminal = token actual ─────────────
            if top == token:
                result.add_step(
                    list(stack),
                    filtered[pos:],
                    f"MATCH '{lexeme}' ({token})"
                )
                stack.pop()
                pos += 1

            # ── No-terminal: consultar tabla ─────────────────────
            elif top in self.table.productions:
                rule = self.table.table.get((top, token))

                if rule is None:
                    expected = [t for (nt, t) in self.table.table if nt == top]
                    msg = (f"Error sintáctico en '{lexeme}' (token: {token}). "
                           f"'{top}' no puede derivar con este token. "
                           f"Se esperaba: {', '.join(sorted(expected))}")
                    result.add_error(msg)
                    result.add_step(list(stack), filtered[pos:],
                                    f"ERROR: {msg}")

                    # Recuperación: saltar token
                    pos += 1
                    if pos >= len(filtered):
                        break
                    continue

                # Reemplazar tope con la regla (en orden inverso)
                body_str = " ".join(rule) if rule else "ε"
                result.add_step(
                    list(stack),
                    filtered[pos:],
                    f"PREDICT {top} → {body_str}"
                )
                result.derivation.append(f"{top} → {body_str}")

                stack.pop()

                if rule and rule != ["ε"]:
                    for symbol in reversed(rule):
                        stack.append(symbol)

            # ── Terminal en tope que no coincide → error ──────────
            else:
                msg = (f"Error sintáctico en '{lexeme}' (token: {token}). "
                       f"Se esperaba: '{top}'")
                result.add_error(msg)
                result.add_step(list(stack), filtered[pos:],
                                f"ERROR: {msg}")

                # Recuperación: saltar token
                pos += 1
                if pos >= len(filtered):
                    break

        return result


# --------------------------------------------------
# Helper: imprimir resultado del análisis
# --------------------------------------------------
def print_result(result, show_steps=False):
    status = "✓ ACEPTADA" if result.accepted else "✗ RECHAZADA"
    print(f"\nResultado: {status}")

    if result.errors:
        print(f"\nErrores sintácticos ({len(result.errors)}):")
        for err in result.errors:
            print(f"  • {err}")

    if show_steps:
        print(f"\nPasos del análisis ({len(result.steps)}):")
        print(f"  {'Pila':<40} {'Entrada':<40} {'Acción'}")
        print("  " + "-" * 100)
        for step in result.steps:
            stack_str = str(step['stack'])[-38:]
            input_str = str(step['input'])[:38]
            print(f"  {stack_str:<40} {input_str:<40} {step['action']}")
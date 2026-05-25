"""
first_follow.py — Cálculo de conjuntos FIRST y FOLLOW.

Uso:
    from yapar.first_follow import compute_first, compute_follow

    first  = compute_first(productions, terminals)
    follow = compute_follow(productions, prod_order, first, terminals)
"""


# --------------------------------------------------
# Determinar si un símbolo es terminal o no-terminal
# --------------------------------------------------
def is_terminal(symbol, terminals):
    """
    Un símbolo es terminal si está en el conjunto de tokens declarados,
    o si es '$' (fin de cadena) o 'ε' (épsilon).
    Los no-terminales son los nombres de producciones (minúsculas en YAPar).
    """
    return symbol in terminals or symbol in ("$", "ε")


# --------------------------------------------------
# FIRST
# --------------------------------------------------
def compute_first(productions, terminals):
    """
    Calcula FIRST(X) para todos los símbolos X de la gramática.

    productions: dict { nombre: [ [símbolo, ...], ... ] }
    terminals:   set de terminales (tokens declarados)

    Retorna: dict { símbolo: set de terminales }
    """
    first = {}

    # Inicializar FIRST para todos los símbolos
    for terminal in terminals:
        first[terminal] = {terminal}

    first["ε"] = {"ε"}
    first["$"] = {"$"}

    for non_terminal in productions:
        first[non_terminal] = set()

    # Iterar hasta que no haya cambios
    changed = True
    while changed:
        changed = False

        for non_terminal, rules in productions.items():
            for rule in rules:

                # Producción vacía: A → ε
                if not rule or rule == ["ε"]:
                    if "ε" not in first[non_terminal]:
                        first[non_terminal].add("ε")
                        changed = True
                    continue

                # Para cada símbolo en la regla
                all_have_epsilon = True

                for symbol in rule:
                    # Asegurarse que el símbolo tiene entrada en first
                    if symbol not in first:
                        if is_terminal(symbol, terminals):
                            first[symbol] = {symbol}
                        else:
                            first[symbol] = set()

                    # Agregar FIRST(symbol) - {ε} a FIRST(non_terminal)
                    new_symbols = first[symbol] - {"ε"}
                    before = len(first[non_terminal])
                    first[non_terminal].update(new_symbols)
                    if len(first[non_terminal]) > before:
                        changed = True

                    # Si ε no está en FIRST(symbol), parar
                    if "ε" not in first[symbol]:
                        all_have_epsilon = False
                        break

                # Si todos los símbolos pueden derivar ε
                if all_have_epsilon:
                    if "ε" not in first[non_terminal]:
                        first[non_terminal].add("ε")
                        changed = True

    return first


def first_of_string(symbols, first, terminals):
    """
    Calcula FIRST de una cadena de símbolos (no solo uno).
    Útil para calcular FOLLOW y construir tablas.

    Retorna: set de terminales
    """
    result = set()

    if not symbols:
        return {"ε"}

    all_have_epsilon = True

    for symbol in symbols:
        if symbol not in first:
            if is_terminal(symbol, terminals):
                first[symbol] = {symbol}
            else:
                first[symbol] = set()

        result.update(first[symbol] - {"ε"})

        if "ε" not in first[symbol]:
            all_have_epsilon = False
            break

    if all_have_epsilon:
        result.add("ε")

    return result


# --------------------------------------------------
# FOLLOW
# --------------------------------------------------
def compute_follow(productions, prod_order, first, terminals):
    """
    Calcula FOLLOW(A) para todos los no-terminales A.

    El símbolo inicial (primera producción en prod_order) tiene $ en su FOLLOW.

    Retorna: dict { no_terminal: set de terminales }
    """
    follow = {nt: set() for nt in productions}

    # El símbolo inicial tiene $ en su FOLLOW
    if prod_order:
        start_symbol = prod_order[0]
        follow[start_symbol].add("$")

    # Iterar hasta que no haya cambios
    changed = True
    while changed:
        changed = False

        for lhs, rules in productions.items():
            for rule in rules:
                if not rule or rule == ["ε"]:
                    continue

                for i, symbol in enumerate(rule):
                    # Solo nos interesan los no-terminales
                    if is_terminal(symbol, terminals):
                        continue

                    if symbol not in follow:
                        follow[symbol] = set()

                    # β es lo que viene después de symbol en esta regla
                    beta = rule[i + 1:]

                    if beta:
                        # FIRST(β) - {ε} ⊆ FOLLOW(symbol)
                        first_beta = first_of_string(beta, first, terminals)
                        new_symbols = first_beta - {"ε"}
                        before = len(follow[symbol])
                        follow[symbol].update(new_symbols)
                        if len(follow[symbol]) > before:
                            changed = True

                        # Si ε ∈ FIRST(β), entonces FOLLOW(lhs) ⊆ FOLLOW(symbol)
                        if "ε" in first_beta:
                            before = len(follow[symbol])
                            follow[symbol].update(follow[lhs])
                            if len(follow[symbol]) > before:
                                changed = True

                    else:
                        # symbol es el último → FOLLOW(lhs) ⊆ FOLLOW(symbol)
                        before = len(follow[symbol])
                        follow[symbol].update(follow[lhs])
                        if len(follow[symbol]) > before:
                            changed = True

    return follow


# --------------------------------------------------
# Pretty print
# --------------------------------------------------
def print_first_follow(first, follow, productions):
    print("=== FIRST ===")
    for symbol in sorted(productions.keys()):
        symbols_str = ", ".join(sorted(first.get(symbol, set())))
        print(f"  FIRST({symbol}) = {{ {symbols_str} }}")

    print("\n=== FOLLOW ===")
    for symbol in sorted(productions.keys()):
        symbols_str = ", ".join(sorted(follow.get(symbol, set())))
        print(f"  FOLLOW({symbol}) = {{ {symbols_str} }}")
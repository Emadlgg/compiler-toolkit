class YAParParser:
    def __init__(self, text):
        self.text = text

    # --------------------------------------------------
    # Eliminar comentarios /* ... */
    # --------------------------------------------------
    def remove_comments(self, text):
        result = ""
        i = 0
        while i < len(text):
            if text[i:i+2] == "/*":
                end = text.find("*/", i)
                if end == -1:
                    raise Exception("Unclosed comment")
                i = end + 2
            else:
                result += text[i]
                i += 1
        return result

    # --------------------------------------------------
    # Parser principal
    # --------------------------------------------------
    def parse(self):
        """
        Retorna:
          tokens     : lista de nombres de tokens declarados con %token
          ignored    : set de tokens a ignorar (IGNORE)
          productions: dict { nombre: [ [simbolo, ...], ... ] }
                       cada valor es una lista de reglas,
                       cada regla es una lista de símbolos
        """
        text = self.remove_comments(self.text)

        tokens     = []
        ignored    = set()
        productions = {}
        prod_order  = []  # para mantener orden de definición

        # Separar sección de tokens y sección de producciones
        if "%%" not in text:
            raise Exception("Missing %% separator between tokens and productions")

        token_section, prod_section = text.split("%%", 1)

        # ── Parsear sección de tokens ────────────────────────────
        for line in token_section.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("%token"):
                # puede haber múltiples tokens en una línea
                parts = line[len("%token"):].strip().split()
                for tok in parts:
                    tok = tok.strip()
                    if tok:
                        tokens.append(tok)

            elif line.startswith("IGNORE"):
                parts = line[len("IGNORE"):].strip().split()
                for tok in parts:
                    tok = tok.strip()
                    if tok:
                        ignored.add(tok)

        # ── Parsear sección de producciones ──────────────────────
        # Formato:
        #   nombre:
        #       simbolo simbolo ...
        #     | simbolo simbolo ...
        #   ;
        current_prod = None
        current_rules = []

        for line in prod_section.splitlines():
            line = line.strip()

            if not line:
                continue

            # Fin de producción
            if line == ";":
                if current_prod is not None:
                    productions[current_prod] = current_rules
                    if current_prod not in prod_order:
                        prod_order.append(current_prod)
                current_prod = None
                current_rules = []
                continue

            # Nueva producción: termina en ':'
            if line.endswith(":") and not line.startswith("|"):
                # guardar la anterior si existe
                if current_prod is not None:
                    productions[current_prod] = current_rules
                    if current_prod not in prod_order:
                        prod_order.append(current_prod)

                current_prod = line[:-1].strip()
                current_rules = []
                continue

            # Alternativa con |
            if line.startswith("|"):
                rule_body = line[1:].strip()
                symbols = rule_body.split() if rule_body else []
                current_rules.append(symbols)
                continue

            # Primera regla de una producción (sin |)
            # Puede venir en la misma línea que el nombre: "nombre: A B C"
            if ":" in line and not line.startswith("|"):
                parts = line.split(":", 1)
                name = parts[0].strip()
                body = parts[1].strip()

                if current_prod is not None:
                    productions[current_prod] = current_rules
                    if current_prod not in prod_order:
                        prod_order.append(current_prod)

                current_prod = name
                current_rules = []

                if body:
                    symbols = body.split()
                    current_rules.append(symbols)
                continue

            # Línea con símbolos (continuación de regla actual)
            if current_prod is not None:
                symbols = line.split()
                if symbols:
                    current_rules.append(symbols)

        # Guardar última producción si no terminó con ;
        if current_prod is not None and current_rules:
            productions[current_prod] = current_rules
            if current_prod not in prod_order:
                prod_order.append(current_prod)

        return tokens, ignored, productions, prod_order


    # --------------------------------------------------
    # Helper: imprimir la gramática parseada
    # --------------------------------------------------
    def pretty_print(self, tokens, ignored, productions, prod_order):
        print("=== TOKENS ===")
        for tok in tokens:
            marker = " (IGNORED)" if tok in ignored else ""
            print(f"  {tok}{marker}")

        print("\n=== PRODUCCIONES ===")
        for name in prod_order:
            rules = productions[name]
            for i, rule in enumerate(rules):
                body = " ".join(rule) if rule else "ε"
                if i == 0:
                    print(f"  {name} → {body}")
                else:
                    print(f"  {'':>{len(name)}} | {body}")
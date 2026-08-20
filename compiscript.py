"""
compiscript.py — CLI principal para el analizador semántico de Compiscript.

Uso:
  python compiscript.py archivo.cps
  python compiscript.py archivo.cps --tree
  python compiscript.py archivo.cps --symbols
  python compiscript.py archivo.cps --all
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "compiscript", "generated"))

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker
from antlr4.error.ErrorListener import ErrorListener
from CompiscriptLexer  import CompiscriptLexer
from CompiscriptParser import CompiscriptParser

from compiscript.semantic import SemanticAnalyzer


# ── Error listener para errores sintácticos ──────────────
class SyntaxErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"[Línea {line}:{column}] Error sintáctico: {msg}")


# ── Parsear un archivo .cps ───────────────────────────────
def parse(source):
    stream = InputStream(source)
    lexer  = CompiscriptLexer(stream)
    lexer.removeErrorListeners()
    lex_errors = SyntaxErrorListener()
    lexer.addErrorListener(lex_errors)

    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    parser.removeErrorListeners()
    syn_errors = SyntaxErrorListener()
    parser.addErrorListener(syn_errors)

    tree = parser.program()

    all_errors = lex_errors.errors + syn_errors.errors
    return tree, parser, all_errors


# ── Análisis semántico ────────────────────────────────────
def analyze(tree):
    analyzer = SemanticAnalyzer()
    analyzer.visit(tree)
    return analyzer


# ── Imprimir árbol ────────────────────────────────────────
def print_tree(tree, parser, indent=0, max_depth=6):
    if indent > max_depth:
        return
    prefix = "  " * indent
    node_text = tree.getText()[:40] if hasattr(tree, "getText") else ""

    if tree.getChildCount() == 0:
        print(f"{prefix}└─ {node_text}")
        return

    rule_name = ""
    if hasattr(parser, "ruleNames"):
        try:
            rule_idx = tree.getRuleIndex()
            rule_name = parser.ruleNames[rule_idx]
        except:
            rule_name = type(tree).__name__

    print(f"{prefix}├─ {rule_name}")
    for i in range(tree.getChildCount()):
        print_tree(tree.getChild(i), parser, indent + 1, max_depth)


# ── Main ──────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Uso: python compiscript.py <archivo.cps> [--tree] [--symbols] [--all]")
        sys.exit(1)

    filepath = sys.argv[1]
    show_tree    = "--tree"    in sys.argv or "--all" in sys.argv
    show_symbols = "--symbols" in sys.argv or "--all" in sys.argv

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: archivo no encontrado: {filepath}")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  Compiscript — {os.path.basename(filepath)}")
    print(f"{'='*55}\n")

    # ── Parsear ──────────────────────────────────────────
    tree, parser, syntax_errors = parse(source)

    if syntax_errors:
        print("ERRORES SINTÁCTICOS:")
        for err in syntax_errors:
            print(f"  {err}")
        print()

    # ── Árbol sintáctico ──────────────────────────────────
    if show_tree:
        print("── ÁRBOL SINTÁCTICO ────────────────────────────")
        print_tree(tree, parser)
        print()

    # ── Análisis semántico ────────────────────────────────
    analyzer = analyze(tree)

    if analyzer.errors:
        print(f"ERRORES SEMÁNTICOS ({len(analyzer.errors)}):")
        for err in analyzer.errors:
            print(f"  • {err}")
    else:
        print("  ✓ Sin errores semánticos")

    # ── Tabla de símbolos ─────────────────────────────────
    if show_symbols:
        print()
        print(analyzer.table.full_report())

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
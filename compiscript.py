"""
compiscript.py — CLI principal para el analizador semántico de Compiscript.

Uso:
    python compiscript.py archivo.cps
    python compiscript.py archivo.cps --tree
    python compiscript.py archivo.cps --symbols
    python compiscript.py archivo.cps --all
    python compiscript.py --help
"""

import os
import sys


# ============================================================
# CONFIGURACIÓN DE IMPORTS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "compiscript", "generated")

if GENERATED_DIR not in sys.path:
    sys.path.insert(0, GENERATED_DIR)


from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser

from compiscript.semantic import SemanticAnalyzer


# ============================================================
# AYUDA DEL CLI
# ============================================================

HELP_TEXT = """
Uso:
  python compiscript.py <archivo.cps> [opciones]

Opciones:
  --tree       Mostrar árbol sintáctico
  --symbols    Mostrar tabla de símbolos
  --all        Mostrar árbol sintáctico y tabla de símbolos
  -h, --help   Mostrar esta ayuda

Ejemplos:
  python compiscript.py archivo.cps
  python compiscript.py archivo.cps --tree
  python compiscript.py archivo.cps --symbols
  python compiscript.py archivo.cps --all

Tests:
  python compiscript.py tests/compiscript/tipos/ok_tipos.cps --all
  python compiscript.py tests/compiscript/tipos/error_tipos.cps --all
""".strip()


def print_help():
    """Muestra la ayuda del programa."""
    print(HELP_TEXT)


# ============================================================
# ERROR LISTENER
# ============================================================

class SyntaxErrorListener(ErrorListener):
    """Recolecta errores léxicos y sintácticos producidos por ANTLR."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(
        self,
        recognizer,
        offendingSymbol,
        line,
        column,
        msg,
        e,
    ):
        self.errors.append(
            f"[Línea {line}:{column}] Error sintáctico: {msg}"
        )


# ============================================================
# PARSER
# ============================================================

def parse(source):
    """
    Ejecuta el lexer y parser de Compiscript.

    Retorna:
        tree:
            Árbol sintáctico generado por ANTLR.

        parser:
            Instancia del parser, utilizada también para
            obtener los nombres de las reglas.

        all_errors:
            Lista de errores léxicos y sintácticos.
    """

    # --------------------------------------------------------
    # Input
    # --------------------------------------------------------

    stream = InputStream(source)

    # --------------------------------------------------------
    # Lexer
    # --------------------------------------------------------

    lexer = CompiscriptLexer(stream)

    lexer.removeErrorListeners()

    lex_errors = SyntaxErrorListener()
    lexer.addErrorListener(lex_errors)

    # --------------------------------------------------------
    # Tokens
    # --------------------------------------------------------

    tokens = CommonTokenStream(lexer)

    # --------------------------------------------------------
    # Parser
    # --------------------------------------------------------

    parser = CompiscriptParser(tokens)

    parser.removeErrorListeners()

    syn_errors = SyntaxErrorListener()
    parser.addErrorListener(syn_errors)

    # Regla inicial de Compiscript.
    tree = parser.program()

    # --------------------------------------------------------
    # Combinar errores
    # --------------------------------------------------------

    all_errors = lex_errors.errors + syn_errors.errors

    return tree, parser, all_errors


# ============================================================
# ANÁLISIS SEMÁNTICO
# ============================================================

def analyze(tree):
    """
    Ejecuta el analizador semántico sobre el árbol generado
    por ANTLR.
    """

    analyzer = SemanticAnalyzer()

    analyzer.visit(tree)

    return analyzer


# ============================================================
# ÁRBOL SINTÁCTICO
# ============================================================

def print_tree(tree, parser, indent=0, max_depth=6):
    """
    Imprime una representación simplificada del árbol
    sintáctico.

    max_depth evita imprimir árboles excesivamente grandes.
    """

    if indent > max_depth:
        return

    prefix = "  " * indent

    # --------------------------------------------------------
    # Texto del nodo
    # --------------------------------------------------------

    if hasattr(tree, "getText"):
        node_text = tree.getText()[:40]
    else:
        node_text = ""

    # --------------------------------------------------------
    # Nodo hoja
    # --------------------------------------------------------

    if tree.getChildCount() == 0:
        print(f"{prefix}└─ {node_text}")
        return

    # --------------------------------------------------------
    # Obtener nombre de la regla
    # --------------------------------------------------------

    rule_name = ""

    if hasattr(parser, "ruleNames"):
        try:
            rule_idx = tree.getRuleIndex()
            rule_name = parser.ruleNames[rule_idx]
        except (AttributeError, IndexError):
            rule_name = type(tree).__name__

    # --------------------------------------------------------
    # Imprimir nodo
    # --------------------------------------------------------

    print(f"{prefix}├─ {rule_name}")

    # --------------------------------------------------------
    # Hijos
    # --------------------------------------------------------

    for i in range(tree.getChildCount()):
        child = tree.getChild(i)

        print_tree(
            child,
            parser,
            indent + 1,
            max_depth,
        )


# ============================================================
# VALIDACIÓN DE ARGUMENTOS
# ============================================================

def validate_arguments(args):
    """
    Valida las opciones recibidas desde la línea de comandos.

    Retorna:
        True si todos los argumentos son válidos.
        False si existe alguna opción desconocida.
    """

    valid_flags = {
        "--tree",
        "--symbols",
        "--all",
    }

    for arg in args:

        if arg.startswith("-") and arg not in valid_flags:
            print(f"Error: opción desconocida: {arg}")
            print()
            print("Usa:")
            print("  python compiscript.py --help")
            return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():
    # --------------------------------------------------------
    # Sin argumentos
    # --------------------------------------------------------

    if len(sys.argv) < 2:
        print_help()
        return 1

    # --------------------------------------------------------
    # Help
    # --------------------------------------------------------

    if sys.argv[1] in ("-h", "--help"):
        print_help()
        return 0

    # --------------------------------------------------------
    # Archivo
    # --------------------------------------------------------

    filepath = sys.argv[1]

    # --------------------------------------------------------
    # Opciones
    # --------------------------------------------------------

    args = sys.argv[2:]

    if not validate_arguments(args):
        return 1

    show_tree = (
        "--tree" in args
        or "--all" in args
    )

    show_symbols = (
        "--symbols" in args
        or "--all" in args
    )

    # --------------------------------------------------------
    # Validar extensión
    # --------------------------------------------------------

    if not filepath.lower().endswith(".cps"):
        print(
            "Advertencia: el archivo no tiene extensión .cps:"
        )
        print(f"  {filepath}")
        print()

    # --------------------------------------------------------
    # Leer archivo
    # --------------------------------------------------------

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            source = file.read()

    except FileNotFoundError:
        print(f"Error: archivo no encontrado: {filepath}")
        return 1

    except PermissionError:
        print(f"Error: no se puede leer el archivo: {filepath}")
        return 1

    except OSError as error:
        print(f"Error al leer el archivo:")
        print(f"  {error}")
        return 1

    # --------------------------------------------------------
    # Encabezado
    # --------------------------------------------------------

    print()
    print("=" * 55)
    print(f"  Compiscript — {os.path.basename(filepath)}")
    print("=" * 55)
    print()

    # ========================================================
    # PARSEO
    # ========================================================

    tree, parser, syntax_errors = parse(source)

    # --------------------------------------------------------
    # Errores sintácticos
    # --------------------------------------------------------

    if syntax_errors:
        print(
            f"ERRORES SINTÁCTICOS ({len(syntax_errors)}):"
        )

        for error in syntax_errors:
            print(f"  • {error}")

        print()

    # ========================================================
    # ÁRBOL SINTÁCTICO
    # ========================================================

    if show_tree:
        print(
            "── ÁRBOL SINTÁCTICO "
            "────────────────────────────"
        )

        print_tree(
            tree,
            parser,
        )

        print()

    # ========================================================
    # ANÁLISIS SEMÁNTICO
    # ========================================================

    analyzer = analyze(tree)

    if analyzer.errors:

        print(
            f"ERRORES SEMÁNTICOS "
            f"({len(analyzer.errors)}):"
        )

        for error in analyzer.errors:
            print(f"  • {error}")

    else:
        print("  ✓ Sin errores semánticos")

    # ========================================================
    # TABLA DE SÍMBOLOS
    # ========================================================

    if show_symbols:
        print()

        print(
            "── TABLA DE SÍMBOLOS "
            "────────────────────────────"
        )

        print()

        print(
            analyzer.table.full_report()
        )

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    print()
    print("=" * 55)
    print()

    # --------------------------------------------------------
    # Código de salida
    # --------------------------------------------------------

    if syntax_errors or analyzer.errors:
        return 1

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
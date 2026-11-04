"""
compiscript.py — CLI principal para el analizador semántico de Compiscript.

Uso:
    python compiscript.py archivo.cps
    python compiscript.py archivo.cps --tree
    python compiscript.py archivo.cps --symbols
    python compiscript.py archivo.cps --tac
    python compiscript.py archivo.cps --frames
    python compiscript.py archivo.cps --all
  python compiscript.py archivo.cps --mips --output build/programa.asm
    python compiscript.py archivo.cps --mips
    python compiscript.py archivo.cps --mips --output build/programa.asm
    python compiscript.py --help
"""

import os
import sys


# ============================================================
# CONFIGURACIÓN DE IMPORTS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

# El parser se importa por la ruta de paquete, igual que en semantic.py y en la
# GUI. Mezclar rutas crea dos copias del módulo y rompe los isinstance().
from compiscript.generated.CompiscriptLexer import CompiscriptLexer
from compiscript.generated.CompiscriptParser import CompiscriptParser

from compiscript.semantic import SemanticAnalyzer


# ============================================================
# AYUDA DEL CLI
# ============================================================

HELP_TEXT = """
Uso:
  python compiscript.py <archivo.cps> [opciones]

Opciones:
  --tree       Mostrar árbol sintáctico
  --symbols    Mostrar tabla de símbolos (con direcciones, offsets y tamaños)
  --tac        Generar y mostrar el código intermedio (TAC)
  --frames     Mostrar la organización de memoria: datos globales, clases y
               registros de activación
  --mips       Generar ensamblador MIPS a partir del TAC
  --output RUTA  Guardar el ensamblador en RUTA (requiere --mips)
  --all        Mostrar árbol sintáctico, tabla de símbolos, TAC y registros
  -h, --help   Mostrar esta ayuda

Ejemplos:
  python compiscript.py archivo.cps
  python compiscript.py archivo.cps --tree
  python compiscript.py archivo.cps --symbols
  python compiscript.py archivo.cps --tac
  python compiscript.py archivo.cps --frames
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
# CÓDIGO INTERMEDIO
# ============================================================

def generate_tac(tree, analyzer, show_tac=True, show_frames=False):
    """
    Corre el generador de código intermedio sobre un programa que ya pasó
    el análisis semántico e imprime el TAC y/o la organización de memoria.
    """

    from compiscript.codegen import CodeGenerator

    generator = CodeGenerator(analyzer)
    generator.generate(tree)

    if generator.errors:
        print(
            f"ERRORES DE GENERACIÓN "
            f"({len(generator.errors)}):"
        )

        for error in generator.errors:
            print(f"  • {error}")

        print()

    if show_tac:
        print(
            "── CÓDIGO INTERMEDIO (TAC) "
            "──────────────────────"
        )

        print()

        for line in generator.format().split("\n"):
            print(f"  {line}" if line else "")

        print()

    if show_frames:
        print(
            "── MEMORIA: REGISTROS DE ACTIVACIÓN "
            "───────────────"
        )

        print()

        for line in generator.memory_report().split("\n"):
            print(f"  {line}" if line else "")

        print()


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
    """Valida flags y argumento de --output sin confundir rutas con opciones."""
    flags = {"--tree", "--symbols", "--tac", "--frames", "--all", "--mips"}
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--output":
            if index + 1 >= len(args) or not args[index + 1].strip() or args[index + 1].startswith("--"):
                print("Error: --output requiere una ruta.")
                return False
            index += 2
            continue
        if arg not in flags:
            print(f"Error: opción desconocida: {arg}")
            return False
        index += 1
    if "--output" in args and "--mips" not in args:
        print("Error: --output requiere --mips.")
        return False
    if args.count("--output") > 1:
        print("Error: --output solo puede especificarse una vez.")
        return False
    return True


def compile_mips(tree, analyzer, output_path=None):
    """Genera TAC y MIPS; no guarda archivos si alguna fase falla."""
    from compiscript.codegen import CodeGenerator
    from compiscript.mips import MIPSGenerator, MIPSError

    intermediate = CodeGenerator(analyzer)
    intermediate.generate(tree)
    if intermediate.errors:
        raise MIPSError("Errores de TAC: " + "; ".join(map(str, intermediate.errors)))
    assembler = MIPSGenerator(intermediate.instructions, intermediate.records, analyzer.table)
    asm = assembler.generate()
    if output_path is not None:
        from pathlib import Path
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(asm, encoding="utf-8")
    return asm


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

    wants_mips = "--mips" in args
    output_path = args[args.index("--output") + 1] if "--output" in args else None

    show_tree = (
        "--tree" in args
        or "--all" in args
    )

    show_symbols = (
        "--symbols" in args
        or "--all" in args
    )

    show_tac = (
        "--tac" in args
        or "--all" in args
    )

    show_frames = (
        "--frames" in args
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

    # Resolver modulos antes del parser existente. Los programas sin imports
    # siguen el mismo flujo de compilacion que en los incrementos anteriores.
    try:
        from compiscript.modules import resolve_project, ModuleError
        source = resolve_project(filepath)
    except ModuleError as error:
        print(f"Error de modulos: {error}")
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

    if analyzer.warnings:
        print()
        print(
            f"ADVERTENCIAS "
            f"({len(analyzer.warnings)}):"
        )

        for warning in analyzer.warnings:
            print(f"  • {warning}")

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

    # ========================================================
    # CÓDIGO INTERMEDIO
    # ========================================================

    if show_tac or show_frames:
        print()

        if syntax_errors or analyzer.errors:
            print("  No se genera código: corrige los errores primero.")
        else:
            generate_tac(tree, analyzer, show_tac, show_frames)

    # --------------------------------------------------------
    # GENERACIÓN MIPS
    # --------------------------------------------------------
    if wants_mips:
        if syntax_errors or analyzer.errors:
            print("  No se genera MIPS: corrige los errores primero.")
        else:
            try:
                from compiscript.mips import MIPSError
                asm = compile_mips(tree, analyzer, output_path)
            except (MIPSError, ValueError, OSError) as error:
                print(f"Error de generación MIPS: {error}")
                return 1
            if output_path:
                print(f"  MIPS guardado en: {output_path}")
            else:
                print("\n── CÓDIGO MIPS ──\n")
                print(asm)

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

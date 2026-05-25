import sys
import importlib.util

from yalex.yalex_reader import read_file
from yalex.lexer_builder import build_lexer_from_spec
from yalex.generator import generate_lexer_file
from yalex.yalex_parser import YALexParser
from yalex.lexer_builder import resolve_references
from regex.regex_parser import RegexParser
from automata.thompson import Thompson
from automata.afn import merge_afns


def load_generated_lexer(path):
    spec = importlib.util.spec_from_file_location("generated_lexer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def print_help():
    print("""
Uso:
  python yalex.py archivo.yal -o salida.py         Generar lexer
  python yalex.py archivo.yal -o salida.py --tree  Generar lexer + árboles de expresión
  python yalex.py archivo.yal -o salida.py --afd   Generar lexer + grafo del AFD
  python yalex.py archivo.yal -o salida.py --all   Generar lexer + todos los gráficos
  python yalex.py archivo.yal -run "texto"         Generar y ejecutar con texto

Flags:
  --tree    Grafica el árbol de cada expresión regular definida
  --afd     Grafica el AFD completo
  --all     Equivale a --tree --afd
  --verbose Modo verbose al usar -run
""")


def draw_trees_for_spec(spec_text, output_prefix="tree"):
    """Genera un PNG del árbol por cada definición 'let' del .yal"""
    from yalex.visualizer import draw_tree

    parser = YALexParser(spec_text)
    definitions, _ = parser.parse()
    regex_map = {name: regex for name, regex in definitions}

    print(f"\nGenerando árboles de expresión...")
    for name, regex in definitions:
        try:
            resolved = resolve_references(regex, regex_map)
            tree = RegexParser(resolved).parse()
            outfile = f"{output_prefix}_{name}"
            draw_tree(tree, outfile, title=f"Regex: {name} = {regex}")
        except Exception as e:
            print(f"  [skip] {name}: {e}")


def main():
    if len(sys.argv) < 2 or "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    input_file = sys.argv[1]

    try:
        text = read_file(input_file)
    except FileNotFoundError:
        print(f"Error: archivo no encontrado: {input_file}")
        sys.exit(1)

    # Flags de visualización
    do_tree = "--tree" in sys.argv or "--all" in sys.argv
    do_afd  = "--afd"  in sys.argv or "--all" in sys.argv

    # Construir AFD
    print(f"Procesando {input_file}...")
    afd = build_lexer_from_spec(text)
    print(f"AFD construido: {len(afd.states)} estados")

    # ── Caso 1: generar archivo ──────────────────────────────────
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        output_file = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "lexer.py"

        generate_lexer_file(afd, output_file)

        # Prefijo para archivos de gráficos (mismo nombre base)
        base = output_file.replace(".py", "")

        if do_tree:
            draw_trees_for_spec(text, output_prefix=base + "_tree")

        if do_afd:
            from yalex.visualizer import draw_afd
            yal_name = input_file.replace(".yal", "")
            draw_afd(afd, base + "_afd",
                     title=f"AFD generado desde {input_file}",
                     max_states=100)

        return

    # ── Caso 2: generar y ejecutar inmediatamente ────────────────
    if "-run" in sys.argv:
        idx = sys.argv.index("-run")
        if idx + 1 >= len(sys.argv):
            print("Error: debe proporcionar texto para -run")
            sys.exit(1)

        input_text = sys.argv[idx + 1]
        output_file = "temp_lexer.py"
        generate_lexer_file(afd, output_file)

        lexer = load_generated_lexer(output_file)
        tokens, errors = lexer.tokenize(input_text)

        print("\nTokens:")
        for tok, lex in tokens:
            print(f"  ({tok}, {repr(lex)})")

        if errors:
            print("\nErrores:")
            for e in errors:
                print(f"  {e}")
        return

    # ── Default: generar lexer.py ────────────────────────────────
    generate_lexer_file(afd, "lexer.py")


if __name__ == "__main__":
    main()
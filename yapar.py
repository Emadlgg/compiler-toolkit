"""
yapar.py — CLI principal del generador de analizadores sintácticos.

Uso:
  python yapar.py parser.yapar -l lexer.yal -i input.txt
  python yapar.py parser.yapar -l lexer.yal -i input.txt --method slr
  python yapar.py parser.yapar -l lexer.yal -i input.txt --method lalr
  python yapar.py parser.yapar -l lexer.yal -i input.txt --method ll1
  python yapar.py parser.yapar -l lexer.yal -i input.txt --all
  python yapar.py parser.yapar -l lexer.yal -i input.txt --steps
"""

import sys
import importlib.util

from yapar.yapar_parser   import YAParParser
from yapar.first_follow   import compute_first, compute_follow
from yapar.lr0            import LR0Automaton
from yapar.slr_table      import SLRTable
from yapar.lalr_table     import LALRTable
from yapar.ll1_table      import LL1Table
from yapar.parser_engine  import LRParserEngine, LL1ParserEngine, print_result
from yalex.yalex_reader   import read_file
from yalex.lexer_builder  import build_lexer_from_spec
from yalex.generator      import generate_lexer_file


def load_lexer(path):
    spec   = importlib.util.spec_from_file_location("generated_lexer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_lexer_from_yal(yal_path):
    text = read_file(yal_path)
    afd  = build_lexer_from_spec(text)
    tmp  = "temp_parser_lexer.py"
    generate_lexer_file(afd, tmp)
    return load_lexer(tmp)


def print_help():
    print("""
Uso:
  python yapar.py <archivo.yapar> -l <lexer.yal> -i <input.txt> [opciones]

Opciones:
  -l <archivo.yal>   Especificacion lexica YALex
  -i <archivo.txt>   Archivo de entrada a analizar
  --method slr       Usar SLR(1)  (default)
  --method lalr      Usar LALR
  --method ll1       Usar LL(1)
  --all              Correr los tres metodos y comparar
  --steps            Mostrar pasos del analisis
  --tables           Imprimir tablas de parseo
  --lr0              Imprimir automata LR(0)
  -h, --help         Mostrar esta ayuda
""")


def main():
    if len(sys.argv) < 2 or "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    yapar_file = sys.argv[1]

    yal_file    = None
    input_file  = None
    method      = "slr"
    run_all     = "--all"    in sys.argv
    show_steps  = "--steps"  in sys.argv
    show_tables = "--tables" in sys.argv
    show_lr0    = "--lr0"    in sys.argv

    if "-l" in sys.argv:
        idx = sys.argv.index("-l")
        if idx + 1 < len(sys.argv):
            yal_file = sys.argv[idx + 1]

    if "-i" in sys.argv:
        idx = sys.argv.index("-i")
        if idx + 1 < len(sys.argv):
            input_file = sys.argv[idx + 1]

    if "--method" in sys.argv:
        idx = sys.argv.index("--method")
        if idx + 1 < len(sys.argv):
            method = sys.argv[idx + 1].lower()

    if not yal_file:
        print("Error: debe especificar el archivo .yal con -l")
        sys.exit(1)

    if not input_file:
        print("Error: debe especificar el archivo de entrada con -i")
        sys.exit(1)

    # ── Parsear .yapar ───────────────────────────────────────────
    print(f"\nProcesando {yapar_file}...")
    try:
        yapar_text = read_file(yapar_file)
    except FileNotFoundError:
        print(f"Error: no se encontró {yapar_file}")
        sys.exit(1)

    yapar_parser = YAParParser(yapar_text)
    tokens_declared, ignored, productions, prod_order = yapar_parser.parse()
    terminals = set(tokens_declared)

    print(f"  Tokens declarados: {len(tokens_declared)}")
    print(f"  Tokens ignorados:  {ignored}")
    print(f"  Producciones:      {len(productions)}")
    print(f"  Símbolo inicial:   {prod_order[0]}")

    # ── FIRST y FOLLOW ───────────────────────────────────────────
    print("\nCalculando FIRST y FOLLOW...")
    first  = compute_first(productions, terminals)
    follow = compute_follow(productions, prod_order, first, terminals)

    # ── Autómata LR(0) ───────────────────────────────────────────
    print("Construyendo autómata LR(0)...")
    automaton = LR0Automaton(productions, prod_order, terminals).build()
    print(f"  Estados: {len(automaton.states)}")
    print(f"  Transiciones: {len(automaton.transitions)}")

    if show_lr0:
        automaton.print_automaton()

    # ── Tablas ───────────────────────────────────────────────────
    print("\nConstruyendo tablas de parseo...")
    slr_table  = SLRTable(automaton, follow, terminals).build()
    lalr_table = LALRTable(automaton, first, terminals).build()
    ll1_table  = LL1Table(productions, prod_order, first, follow, terminals).build()

    print(f"  SLR(1)  — conflictos: {len(slr_table.conflicts)}")
    print(f"  LALR    — conflictos: {len(lalr_table.conflicts)}")
    print(f"  LL(1)   — conflictos: {len(ll1_table.conflicts)}")

    if show_tables:
        print()
        slr_table.print_table()
        print()
        lalr_table.print_table()
        print()
        ll1_table.print_table()

    # ── Generar lexer ────────────────────────────────────────────
    print(f"\nGenerando lexer desde {yal_file}...")
    try:
        lexer = build_lexer_from_yal(yal_file)
    except Exception as e:
        print(f"Error al generar lexer: {e}")
        sys.exit(1)

    # ── Tokenizar ────────────────────────────────────────────────
    try:
        source = read_file(input_file)
    except FileNotFoundError:
        print(f"Error: no se encontró {input_file}")
        sys.exit(1)

    print(f"Tokenizando {input_file}...")
    token_list, lex_errors = lexer.tokenize(source)

    if lex_errors:
        print(f"  Errores léxicos: {len(lex_errors)}")
        for err in lex_errors:
            print(f"    {err}")
    else:
        print(f"  Tokens: {len(token_list)} — sin errores léxicos")

    filtered_tokens = [(tok, lex) for tok, lex in token_list
                       if tok not in ignored and not tok.startswith("_")]

    # ── Análisis sintáctico ──────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  ANÁLISIS SINTÁCTICO")
    print(f"{'='*55}")

    methods_to_run = ["slr", "lalr", "ll1"] if run_all else [method]

    for m in methods_to_run:
        print(f"\n--- Método: {m.upper()} ---")

        if m == "slr":
            if slr_table.conflicts:
                print(f"  Advertencia: {len(slr_table.conflicts)} conflictos SLR")
            engine = LRParserEngine(slr_table, ignored)
            result = engine.parse(filtered_tokens)

        elif m == "lalr":
            if lalr_table.conflicts:
                print(f"  Advertencia: {len(lalr_table.conflicts)} conflictos LALR")
            engine = LRParserEngine(lalr_table, ignored)
            result = engine.parse(filtered_tokens)

        elif m == "ll1":
            if ll1_table.conflicts:
                print(f"  Advertencia: {len(ll1_table.conflicts)} conflictos LL(1)")
            engine = LL1ParserEngine(ll1_table, prod_order[0], ignored)
            result = engine.parse(filtered_tokens)

        else:
            print(f"  Método desconocido: {m}")
            continue

        print_result(result, show_steps=show_steps)

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
"""
sql.py — Línea de comandos del intérprete SQL.

Uso:
    python sql.py archivo.sql
    python sql.py archivo.sql --tokens
    python sql.py archivo.sql --tree
    python sql.py archivo.sql --ast
    python sql.py archivo.sql --db carpeta_de_la_base
    python sql.py archivo.sql --schema
    python sql.py -e "SELECT nombre FROM estudiantes WHERE edad >= 18;" --tree

Opciones:
    -e, --execute SQL   analizar el texto dado en vez de un archivo
    --tokens            mostrar la tabla de tokens
    --tree              mostrar el árbol sintáctico (sin las capas de precedencia)
    --tree-full         mostrar el árbol sintáctico completo
    --ast               mostrar el AST (árbol de sintaxis abstracta)
    --positions         con --ast, mostrar la línea y columna de cada nodo
    --db CARPETA        carpeta de la base de datos: se lee su metadata.txt para el análisis semántico
                        (sin ella, se parte de una base vacía y el script debe crear sus tablas)
    --schema            mostrar el esquema que queda después de aplicar los CREATE/DROP del script
    -h, --help          mostrar esta ayuda

Termina con código 1 si hay errores léxicos, sintácticos o semánticos.
"""

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlengine.frontend import parse, format_tokens, format_tree
from sqlengine.ast_builder import build_ast, format_ast
from sqlengine.catalog import Catalog
from sqlengine.metadata import MetadataError, format_metadata, load_catalog
from sqlengine.semantic import analyze_script

LINE = "=" * 55


def main(argv=None):
    ap = argparse.ArgumentParser(description="Intérprete SQL con almacenamiento en archivos")
    ap.add_argument("file", nargs="?", help="archivo .sql")
    ap.add_argument("-e", "--execute", metavar="SQL", help="texto SQL a analizar")
    ap.add_argument("--tokens", action="store_true", help="mostrar los tokens")
    ap.add_argument("--tree", action="store_true", help="mostrar el árbol sintáctico")
    ap.add_argument("--tree-full", action="store_true", help="mostrar el árbol sintáctico completo")
    ap.add_argument("--ast", action="store_true", help="mostrar el AST")
    ap.add_argument("--positions", action="store_true", help="con --ast, mostrar línea y columna de cada nodo")
    ap.add_argument("--db", metavar="CARPETA", help="carpeta de la base de datos (su metadata.txt)")
    ap.add_argument("--schema", action="store_true", help="mostrar el esquema resultante")
    args = ap.parse_args(argv)

    if args.execute is not None:
        text, name = args.execute, "<texto>"
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"No se pudo leer '{args.file}': {e}")
            return 2
        name = os.path.basename(args.file)
    else:
        ap.print_help()
        return 2

    result = parse(text)

    script = semantic = None
    if result.ok:
        script = build_ast(result)
        try:
            catalog = load_catalog(args.db) if args.db else Catalog()
        except MetadataError as e:
            print(f"No se pudo leer el esquema de '{args.db}': {e}")
            return 2
        semantic = analyze_script(script, catalog)

    print()
    print(LINE)
    print(f"  SQL — {name}")
    print(LINE)
    print()

    for title, errors in (("LÉXICOS", result.lexical_errors), ("SINTÁCTICOS", result.syntax_errors),
                          ("SEMÁNTICOS", semantic.errors if semantic else [])):
        if errors:
            print(f"ERRORES {title} ({len(errors)}):")
            for err in errors:
                print(f"  • {err}")
            print()

    if result.ok:
        n = len(result.statements())
        print(f"  ✓ Sin errores léxicos ni sintácticos ({n} sentencia{'s' if n != 1 else ''})")
        if semantic.ok:
            print("  ✓ Sin errores semánticos")
        print()

    if args.tokens:
        print("── TOKENS ──────────────────────────────────────")
        print()
        print(format_tokens(result))
        print()

    if args.tree or args.tree_full:
        print("── ÁRBOL SINTÁCTICO ────────────────────────────")
        print()
        print(format_tree(result, compact=not args.tree_full))
        print()

    if args.schema:
        print("── ESQUEMA ─────────────────────────────────────")
        print()
        if semantic is not None:
            print(format_metadata(semantic.catalog))
        else:
            print("  No hay esquema: corrige primero los errores léxicos y sintácticos.")
            print()

    if args.ast:
        print("── AST ─────────────────────────────────────────")
        print()
        if result.ok:
            print(format_ast(build_ast(result), positions=args.positions))
        else:
            print("  No hay AST: corrige primero los errores léxicos y sintácticos.")
        print()

    print(LINE)
    print()
    return 0 if result.ok and semantic.ok else 1


if __name__ == "__main__":
    sys.exit(main())

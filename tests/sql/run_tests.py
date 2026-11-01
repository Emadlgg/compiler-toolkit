"""
run_tests.py — Batería de pruebas del lexer, el parser, el AST y el análisis semántico de SQL.

    python tests/sql/run_tests.py            # corre todo
    python tests/sql/run_tests.py -v         # muestra cada prueba
    python tests/sql/run_tests.py --update   # reescribe los .ast esperados

Casos exitosos (tests/sql/ok/*.sql)
  * no debe haber errores léxicos ni sintácticos
  * la primera línea `-- statements: N` indica cuántas sentencias debe reconocer
  * se generan la tabla de tokens y el árbol sintáctico (completo y compacto) sin fallar
  * se construye el AST, con una sentencia por cada sentencia del texto

Casos fallidos (tests/sql/error/*.sql)
  * el archivo .err lista los errores esperados, uno por línea:  tipo línea:columna fragmento
  * deben aparecer exactamente esos errores, con esa ubicación y ese fragmento en el mensaje

Semántico (tests/sql/semantic/)
  * ok/*.sql no deben dar errores; error/*.sql deben dar exactamente los errores de su .err
  * un script puede empezar con `-- db: NOMBRE` para partir del esquema de tests/sql/fixtures/NOMBRE;
    si no, parte de una base vacía y tiene que crear sus tablas
  * semantic_cases.py: casos con el resultado escrito a mano (tipos, nombres de salida, resolución de
    columnas, subconsultas correlacionadas, efectos de los CREATE/DROP) y las pruebas de metadata.txt

AST
  * casos con el resultado escrito a mano (ast_cases.py): precedencia, asociatividad, literales,
    NOT EXISTS, ubicación de los nodos...
  * archivos de referencia (tests/sql/ast/*.sql y su .ast) con el AST completo de scripts pequeños
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from sqlengine.frontend import parse, format_tokens, format_tree
from sqlengine.ast_builder import build_ast, format_ast
import ast_cases
import semantic_cases
from sqlengine.catalog import Catalog
from sqlengine.metadata import load_catalog
from sqlengine.semantic import analyze_script


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def cases(folder):
    path = os.path.join(HERE, folder)
    return sorted(os.path.join(path, f) for f in os.listdir(path) if f.endswith(".sql"))


def run_ok(path):
    problems = []
    text = read(path)
    result = parse(text)
    for err in result.errors:
        problems.append(str(err))
    header = re.match(r"-- statements: (\d+)", text)
    if header is None:
        problems.append("falta la primera línea '-- statements: N'")
    elif int(header.group(1)) != len(result.statements()):
        problems.append(f"se esperaban {header.group(1)} sentencias y se reconocieron {len(result.statements())}")
    if not format_tokens(result) or not format_tree(result) or not format_tree(result, compact=False):
        problems.append("no se pudo mostrar la tabla de tokens o el árbol sintáctico")
    if result.ok:
        try:
            script = build_ast(result)
            if len(script.statements) != len(result.statements()):
                problems.append(f"el AST tiene {len(script.statements)} sentencias y el árbol sintáctico {len(result.statements())}")
            if not format_ast(script):
                problems.append("no se pudo mostrar el AST")
        except Exception as e:
            problems.append(f"falló al construir el AST: {type(e).__name__}: {e}")
    return problems


def catalog_for(text):
    """El catálogo de partida de un script: el de `-- db: NOMBRE` o una base vacía."""
    m = re.match(r"-- db: (\w+)", text)
    return load_catalog(os.path.join(HERE, "fixtures", m.group(1))) if m else Catalog()


def analyze(path):
    """(errores léxicos y sintácticos, errores semánticos) de un script."""
    text = read(path)
    result = parse(text)
    if not result.ok:
        return result.errors, []
    return [], analyze_script(build_ast(result), catalog_for(text)).errors


def run_semantic_ok(path):
    front, semantic = analyze(path)
    return [str(e) for e in front + semantic]


def run_semantic_error(path):
    front, semantic = analyze(path)
    if front:
        return [f"el script no analiza: {front[0]}"]
    return compare_errors(path, semantic)


def compare_errors(path, found):
    """Compara los errores encontrados con los del .err (tipo línea:columna fragmento), uno por uno."""
    problems, expected = [], []
    for line in read(path[:-4] + ".err").split("\n"):
        if not line.strip() or line.startswith("#"):
            continue
        m = re.match(r"^(\S+) (\d+):(\d+) (.+)$", line)
        if m is None:
            problems.append(f"línea mal formada en el .err: {line!r}")
            continue
        expected.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))
    if len(found) != len(expected):
        return problems + [f"se esperaban {len(expected)} errores y hubo {len(found)}:\n      " + "\n      ".join(str(e) for e in found)]
    for (kind, line, column, fragment), err in zip(expected, found):
        if (err.kind, err.line, err.column) != (kind, line, column):
            problems.append(f"se esperaba {kind} en {line}:{column} y fue {err.kind} en {err.line}:{err.column}: {err.message}")
        elif fragment not in err.message:
            problems.append(f"el mensaje no contiene {fragment!r}:\n      {err.message}")
    return problems


def run_error(path):
    problems = []
    result = parse(read(path))
    expected = []
    for line in read(path[:-4] + ".err").split("\n"):
        if not line.strip() or line.startswith("#"):
            continue
        m = re.match(r"^(\S+) (\d+):(\d+) (.+)$", line)
        if m is None:
            problems.append(f"línea mal formada en el .err: {line!r}")
            continue
        expected.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))

    found = result.errors
    if len(found) != len(expected):
        problems.append(f"se esperaban {len(expected)} errores y hubo {len(found)}:\n      " + "\n      ".join(str(e) for e in found))
        return problems
    for (kind, line, column, fragment), err in zip(expected, found):
        if (err.kind, err.line, err.column) != (kind, line, column):
            problems.append(f"se esperaba {kind} en {line}:{column} y fue {err.kind} en {err.line}:{err.column}")
        elif fragment not in err.message:
            problems.append(f"el mensaje no contiene {fragment!r}:\n      {err.message}")
    return problems


def run_ast_golden(path, update):
    result = parse(read(path))
    if not result.ok:
        return [f"el script de la prueba tiene errores: {result.errors[0]}"]
    actual = format_ast(build_ast(result)) + "\n"
    expected_path = path[:-4] + ".ast"
    if update:
        with open(expected_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(actual)
        return []
    if not os.path.exists(expected_path):
        return ["falta el archivo .ast esperado (usa --update)"]
    if read(expected_path) != actual:
        return ["el AST no coincide con el .ast esperado"]
    return []


def run_ast_case(check):
    try:
        check()
    except AssertionError as e:
        return [f"{e}" if str(e) else "no se cumplió lo esperado"]
    except Exception as e:
        return [f"{type(e).__name__}: {e}"]
    return []


def main():
    update = "--update" in sys.argv
    verbose = "-v" in sys.argv
    failures = total = 0

    def report(name, problems):
        nonlocal failures, total
        total += 1
        if problems:
            failures += 1
            print(f"  FALLA  {name}")
            for p in problems:
                print(f"    - {p}")
        elif verbose:
            print(f"  ok     {name}")

    print("Casos exitosos")
    for path in cases("ok"):
        report("ok/" + os.path.basename(path), run_ok(path))
    print("Casos fallidos")
    for path in cases("error"):
        report("error/" + os.path.basename(path), run_error(path))

    print("Semántico: casos exitosos")
    for path in cases("semantic/ok"):
        report("semantic/ok/" + os.path.basename(path), run_semantic_ok(path))
    print("Semántico: casos con errores")
    for path in cases("semantic/error"):
        report("semantic/error/" + os.path.basename(path), run_semantic_error(path))
    print("Semántico: casos con resultado escrito a mano")
    for name, check in semantic_cases.CASES:
        report("semantic/" + name, run_ast_case(check))
    print("AST: casos con resultado escrito a mano")
    for name, check in ast_cases.CASES:
        report("ast/" + name, run_ast_case(check))
    print("AST: archivos de referencia")
    for path in cases("ast"):
        report("ast/" + os.path.basename(path), run_ast_golden(path, update))

    print(f"\n{total - failures}/{total} pruebas correctas")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

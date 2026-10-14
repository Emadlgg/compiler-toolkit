"""
run_tests.py — Batería de pruebas del generador de código intermedio.

    python tests/codegen/run_tests.py            # corre todo
    python tests/codegen/run_tests.py --update   # reescribe los .tac esperados
    python tests/codegen/run_tests.py -v         # muestra el detalle de cada prueba

Casos exitosos (tests/codegen/ok/*.cps)
  * el programa no debe dar errores léxicos, sintácticos, semánticos ni de generación
  * el TAC debe coincidir con el archivo .tac esperado
  * al ejecutar el TAC en el intérprete, lo que imprime debe coincidir con el
    archivo .out (escrito a mano, independiente del generador)

Casos fallidos (tests/codegen/error/*.cps)
  * cada línea del archivo .err debe aparecer en algún mensaje de error
  * si hay errores léxicos, sintácticos o semánticos, no se debe generar TAC
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from compiscript.generated.CompiscriptLexer import CompiscriptLexer
from compiscript.generated.CompiscriptParser import CompiscriptParser
from compiscript.semantic import SemanticAnalyzer
from compiscript.codegen import CodeGenerator
from compiscript.temps import TempPool
from compiscript.tac import Temp, Goto, Return, Halt, Label, FuncBegin
from tac_vm import TacVM, VMError


class Collector(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offending, line, column, msg, e):
        self.errors.append(f"[Línea {line}:{column}] {msg}")


def compile_source(source):
    """Corre el pipeline completo y retorna un diccionario con los resultados."""
    result = {"lexical": [], "syntax": [], "semantic": [], "codegen": [], "tac": None, "generator": None}
    lexer = CompiscriptLexer(InputStream(source))
    lex_listener = Collector()
    lexer.removeErrorListeners()
    lexer.addErrorListener(lex_listener)
    parser = CompiscriptParser(CommonTokenStream(lexer))
    syn_listener = Collector()
    parser.removeErrorListeners()
    parser.addErrorListener(syn_listener)
    tree = parser.program()
    result["lexical"], result["syntax"] = lex_listener.errors, syn_listener.errors
    if lex_listener.errors or syn_listener.errors:
        return result
    analyzer = SemanticAnalyzer()
    analyzer.visit(tree)
    result["semantic"] = [str(e) for e in analyzer.errors]
    if analyzer.errors:
        return result
    generator = CodeGenerator(analyzer)
    generator.generate(tree)
    result["generator"] = generator
    result["codegen"] = [str(e) for e in generator.errors]
    result["tac"] = generator.format()
    return result


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def cases(folder):
    path = os.path.join(HERE, folder)
    return sorted(os.path.join(path, f) for f in os.listdir(path) if f.endswith(".cps"))


def run_ok(path, update):
    problems = []
    base = path[:-4]
    try:
        result = compile_source(read(path))
    except Exception as e:
        return [f"el compilador falló con una excepción: {type(e).__name__}: {e}"]
    for stage in ("lexical", "syntax", "semantic", "codegen"):
        for err in result[stage]:
            problems.append(f"error {stage}: {err}")
    if problems or result["tac"] is None:
        return problems

    if update:
        write(base + ".tac", result["tac"] + "\n")
    elif not os.path.exists(base + ".tac"):
        problems.append("falta el archivo .tac esperado (usa --update)")
    elif read(base + ".tac").rstrip("\n") != result["tac"].rstrip("\n"):
        problems.append("el TAC generado no coincide con el .tac esperado")

    problems.extend(unreachable_code(result["generator"].instructions))

    expected_path = base + ".out"
    if not os.path.exists(expected_path):
        problems.append("falta el archivo .out con la salida esperada")
        return problems
    try:
        output = TacVM(result["generator"].instructions).run()
    except Exception as e:      # VMError, o un TAC mal formado que rompe el intérprete
        problems.append(f"falló al ejecutar el TAC: {type(e).__name__}: {e}")
        return problems
    expected = read(expected_path).split("\n")
    if expected and expected[-1] == "":
        expected.pop()
    if output != expected:
        problems.append(f"salida distinta\n      esperada: {expected}\n      obtenida: {output}")
    return problems


def unreachable_code(instructions):
    """El TAC no debe tener instrucciones después de un goto/return/halt sin una etiqueta de por medio."""
    problems = []
    for prev, ins in zip(instructions, instructions[1:]):
        if isinstance(prev, (Goto, Return, Halt)) and not isinstance(ins, (Label, FuncBegin)):
            problems.append(f"código inalcanzable: {ins} después de {prev}")
    return problems


def run_error(path):
    problems = []
    result = compile_source(read(path))
    messages = result["lexical"] + result["syntax"] + result["semantic"] + result["codegen"]
    expected = [l.strip() for l in read(path[:-4] + ".err").split("\n") if l.strip() and not l.startswith("#")]
    if not messages:
        problems.append("se esperaban errores y no hubo ninguno")
    for fragment in expected:
        if not any(fragment in m for m in messages):
            problems.append(f"no apareció el error esperado: {fragment!r}\n      errores: {messages}")
    front_end_failed = result["lexical"] or result["syntax"] or result["semantic"]
    if front_end_failed and result["tac"] is not None:
        problems.append("se generó TAC a pesar de los errores previos")
    return problems


def unit_tests():
    """Pruebas directas del pool de temporales."""
    problems = []
    pool = TempPool()
    a, b = pool.new(), pool.new()
    if (a, b) != (Temp(0), Temp(1)):
        problems.append("los temporales deben numerarse desde t0")
    pool.free(b)
    pool.free(a)
    if pool.new() != Temp(0):
        problems.append("debe reutilizar el temporal libre de menor índice")
    pool.free(Temp(0))
    pool.free(Temp(0))
    if sorted(pool._free) != [0, 1]:
        problems.append("liberar dos veces el mismo temporal no debe duplicarlo")
    deep = TempPool()
    held = [deep.new() for _ in range(5)]
    for t in held:
        deep.free(t)
    for _ in range(100):
        deep.free(deep.new())
    if deep.count != 5:
        problems.append("reciclar no debe crear temporales nuevos")
    return problems


def main():
    update = "--update" in sys.argv
    verbose = "-v" in sys.argv
    failures = 0
    total = 0

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

    print("Pruebas unitarias")
    report("temps.TempPool", unit_tests())
    print("Casos exitosos")
    for path in cases("ok"):
        report("ok/" + os.path.basename(path), run_ok(path, update))
    print("Casos fallidos")
    for path in cases("error"):
        report("error/" + os.path.basename(path), run_error(path))

    print(f"\n{total - failures}/{total} pruebas correctas")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

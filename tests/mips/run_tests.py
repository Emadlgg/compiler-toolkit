"""
Bateria de pruebas del generador MIPS (extremo a extremo).

    python tests/mips/run_tests.py          # corre todo
    python tests/mips/run_tests.py -v       # detalle de cada prueba

Casos exitosos
  * tests/codegen/ok/*.cps   (los mismos programas de la fase 2)
  * tests/mips/cases/ok/*.cps
  Cada .cps se compila a .asm, se ejecuta en MARS y la salida debe coincidir
  con el .out esperado (escrito a mano, independiente del generador).

Casos fallidos  (tests/mips/cases/error/*.cps)
  Cada linea del .err debe aparecer en el log de compilacion o en la salida de
  MARS (errores de ejecucion como division por cero o indice fuera de rango).
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
from compiscript.mars import find_mars, java_available  # noqa: E402


def compile_cps(source, asm):
    r = subprocess.run([sys.executable, str(ROOT / 'compiscript.py'), str(source), '--mips',
                        '--output', str(asm)], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=120,
                       env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    return (r.stdout + r.stderr), (asm.is_file() and r.returncode == 0)


def run_mars(jar, asm):
    r = subprocess.run(['java', '-jar', str(jar), 'nc', str(asm)], capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=120)
    lines = [l for l in (r.stdout + r.stderr).splitlines()
             if not l.startswith(('MARS', 'Copyright')) and 'java.util.prefs' not in l
             and not l.startswith('INFO:') and not l.startswith('Warning in')]
    return '\n'.join(lines).strip()


def show(good, cps):
    """Una linea por prueba, con el formato que lee la pestana Pruebas CPS del IDE.
    El nombre es relativo a tests/ (codegen/ok/01_x.cps, mips/cases/error/01_y.cps)."""
    name = cps.resolve().relative_to(ROOT / 'tests').as_posix()
    print(f'  {"ok   " if good else "FALLA"}  {name}')


def main():
    jar = find_mars()
    if jar is None or not java_available():
        print('Se necesita Java y tools/Mars.jar (o la variable MARS_JAR).')
        return 2
    ok_cases = sorted((ROOT / 'tests' / 'codegen' / 'ok').glob('*.cps')) + \
               sorted((HERE / 'cases' / 'ok').glob('*.cps'))
    err_cases = sorted((HERE / 'cases' / 'error').glob('*.cps'))
    passed = failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        print('Casos exitosos')
        for cps in ok_cases:
            asm = tmp / (cps.stem + '.asm')
            log, built = compile_cps(cps, asm)
            expected = cps.with_suffix('.out').read_text(encoding='utf-8').strip()
            got = run_mars(jar, asm) if built else log.strip()
            good = built and got == expected
            passed, failed = passed + good, failed + (not good)
            show(good, cps)
            if not good:
                print('    esperado:', repr(expected)[:200])
                print('    obtenido:', repr(got)[:200])
        print('Casos fallidos')
        for cps in err_cases:
            asm = tmp / (cps.stem + '.asm')
            log, built = compile_cps(cps, asm)
            output = log + ('\n' + run_mars(jar, asm) if built else '')
            wanted = [l.strip() for l in cps.with_suffix('.err').read_text(encoding='utf-8').splitlines()
                      if l.strip() and not l.startswith('#')]
            missing = [w for w in wanted if w not in output]
            good = not missing
            passed, failed = passed + good, failed + (not good)
            show(good, cps)
            if not good:
                print('    falta en la salida:', missing)
    print(f'\n{passed}/{passed + failed} pruebas correctas')
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())

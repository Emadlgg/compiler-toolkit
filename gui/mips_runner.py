"""Integración CLI -> MIPS -> MARS para el IDE, sin dependencias de Tkinter."""
from dataclasses import dataclass
from compiscript.mars import find_mars, java_available
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class MIPSResult:
    ok: bool
    asm: str | None
    log: str
    executed: bool = False


def compile_and_run(source, output, run=False, mars_jar=None, timeout=60):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file():
        return MIPSResult(False, None, f'Archivo no encontrado: {source}')
    output.parent.mkdir(parents=True, exist_ok=True)
    # No mostrar ensamblador viejo si la compilación falla.
    if output.exists():
        output.unlink()
    command = [sys.executable, str(ROOT / 'compiscript.py'), str(source),
               '--mips', '--output', str(output)]
    child_env = os.environ.copy()
    child_env['PYTHONIOENCODING'] = 'utf-8'
    child_env['PYTHONUTF8'] = '1'
    try:
        result = subprocess.run(command, cwd=str(ROOT), env=child_env, capture_output=True,
                                text=True, encoding='utf-8', errors='replace', timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return MIPSResult(False, None, f'No se pudo ejecutar el compilador: {exc}')
    log = (result.stdout + '\n' + result.stderr).strip()
    if result.returncode or not output.is_file():
        return MIPSResult(False, None, log or 'No se generó el archivo MIPS.')
    asm = output.read_text(encoding='utf-8')
    log += f'\n\nEnsamblador: {output}'
    if not run:
        return MIPSResult(True, asm, log)
    jar = find_mars(explicit=mars_jar)
    if jar is None:
        return MIPSResult(False, asm, log + '\nMARS no encontrado. Configura MARS_JAR o coloca tools/Mars.jar.', True)
    if not java_available():
        return MIPSResult(False, asm, log + '\nJava no esta disponible en PATH.', True)
    try:
        execution = subprocess.run(['java', '-jar', str(jar), 'nc', str(output)],
                                   cwd=str(ROOT), capture_output=True, text=True,
                                   encoding='utf-8', errors='replace', timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return MIPSResult(False, asm, log + f'\nError al ejecutar MARS: {exc}', True)
    console = (execution.stdout + '\n' + execution.stderr).strip()
    # MARS puede devolver 0 aun con errores de ensamblado en algunas versiones.
    failed = execution.returncode != 0 or any(term in console.lower() for term in
              ('error in ', 'invalid command argument', 'processing terminated due to errors',
               'runtime exception', 'assemble: operation completed with errors'))
    return MIPSResult(not failed, asm, log + '\n\n--- MARS ---\n' + console, True)

"""Localizacion compartida de MARS para el IDE y las pruebas.

MARS_JAR es opcional: si no apunta a un archivo existente se intenta
la copia del proyecto en tools/Mars.jar. No descarga ni ejecuta archivos.
"""
from pathlib import Path
import os
import shutil

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_mars(explicit=None, root=None):
    """Devuelve Path absoluto del JAR o None.

    Un argumento explicito invalido no se sustituye silenciosamente por
    otro JAR: evita ejecutar uno diferente del solicitado.
    """
    if explicit is not None:
        candidate = Path(explicit).expanduser()
        return candidate.resolve() if candidate.is_file() else None
    configured = os.environ.get('MARS_JAR')
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file():
            return candidate.resolve()
    local = Path(root) if root is not None else PROJECT_ROOT
    candidate = local / 'tools' / 'Mars.jar'
    return candidate.resolve() if candidate.is_file() else None


def java_available():
    return shutil.which('java') is not None

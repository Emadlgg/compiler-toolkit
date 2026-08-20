from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent


def move(source, destination):
    src = ROOT / source
    dst = ROOT / destination

    if not src.exists():
        print(f"[SKIP] No existe: {source}")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        print(f"[SKIP] Ya existe: {destination}")
        return

    shutil.move(str(src), str(dst))
    print(f"[MOVE] {source} -> {destination}")


def delete(path):
    target = ROOT / path

    if target.exists():
        target.unlink()
        print(f"[DELETE] {path}")


def ensure_file(path):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        target.touch()
        print(f"[CREATE] {path}")


def main():
    print("\n=== Refactor del proyecto ===\n")

    # -------------------------
    # 1. Paquetes Python
    # -------------------------

    ensure_file("gui/__init__.py")
    ensure_file("compiscript/generated/__init__.py")

    # El viejo gui/init.py probablemente intentaba ser __init__.py
    old_gui_init = ROOT / "gui/init.py"
    if old_gui_init.exists():
        delete("gui/init.py")

    # -------------------------
    # 2. Ejemplos
    # -------------------------

    (ROOT / "examples/java").mkdir(parents=True, exist_ok=True)

    move(
        "ejemplo_correcto.txt",
        "examples/java/correcto.txt"
    )

    move(
        "ejemplo_errores.txt",
        "examples/java/errores.txt"
    )

    move(
        "input_java.txt",
        "examples/java/input_java.txt"
    )

    # -------------------------
    # 3. Archivos generados
    #    innecesarios de ANTLR
    # -------------------------

    generated = ROOT / "compiscript/generated"

    if generated.exists():
        for pattern in ("*.interp", "*.tokens"):
            for file in generated.glob(pattern):
                file.unlink()
                print(
                    f"[DELETE] "
                    f"{file.relative_to(ROOT)}"
                )

    # Listener no utilizado porque
    # semantic.py usa Visitor.
    listener = generated / "CompiscriptListener.py"

    if listener.exists():
        listener.unlink()
        print(
            "[DELETE] "
            "compiscript/generated/"
            "CompiscriptListener.py"
        )

    # -------------------------
    # 4. Test temporal de ANTLR
    # -------------------------

    test_antlr = ROOT / "test_antlr.py"

    if test_antlr.exists():
        print(
            "\n[REVIEW] test_antlr.py existe."
        )
        print(
            "No se eliminó automáticamente "
            "por seguridad."
        )

    print("\n=== Refactor terminado ===")
    print(
        "Ejecuta los tests antes de hacer commit.\n"
    )


if __name__ == "__main__":
    main()
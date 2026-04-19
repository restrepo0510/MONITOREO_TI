"""Preflight checks para el pipeline.

Comprueba que no existan archivos Python vacíos en el árbol `src/`.
Este script no depende de otros módulos del paquete `src` para evitar
errores de importación durante la fase de chequeo.
"""
from pathlib import Path
import sys


def check_empty_python_files(root: str = "src"):
    """Devuelve una lista de rutas (strings) a archivos .py vacíos o con sólo espacios.

    Condiciones consideradas "vacío":
    - archivo de tamaño 0
    - archivo cuyo contenido, tras hacer strip(), queda vacío
    """
    root_path = Path(root)
    if not root_path.exists():
        return []

    empties = []
    for p in sorted(root_path.rglob("*.py")):
        # Ignorar archivos __init__.py vacíos (normalmente intencionales)
        if p.name == "__init__.py":
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            # Si no se puede leer, considerarlo como fallo para llamar la atención
            empties.append(str(p))
            continue

        if len(text) == 0 or text.strip() == "":
            empties.append(str(p))

    return empties


if __name__ == "__main__":
    empties = check_empty_python_files("src")
    if empties:
        print("Archivos Python vacíos encontrados:")
        for p in empties:
            print(" -", p)
        sys.exit(1)
    else:
        print("No se encontraron archivos Python vacíos.")
        sys.exit(0)

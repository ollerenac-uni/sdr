#!/usr/bin/env python3
"""Reproduce las figuras de aliasing ejecutando las celdas publicadas.

Las celdas son autocontenidas como subsección. Así la figura versionada y el
experimento copiable no mantienen dos implementaciones que puedan divergir.
"""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUT = Path(__file__).parent
NOMBRES = [
    "aliasing-mismas-muestras.png",
    "aliasing-iq.png",
    "aliasing-mapa-frecuencias.png",
    "aliasing-cambio-sample-rate.png",
    "aliasing-limite-nyquist.png",
    "aliasing-filtrado-previo.png",
]


def generar(salida: Path = OUT) -> list[Path]:
    """Ejecuta únicamente las celdas de la subsección 4 y guarda sus figuras."""
    salida.mkdir(parents=True, exist_ok=True)
    contenido = (OUT.parent / "index.md").read_text(encoding="utf-8")
    seccion = contenido.split("### 4. Muestreo y aliasing", 1)[1]
    seccion = re.split(r"^### [5-9]\. ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    celdas = re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)
    if len(celdas) != 7:
        raise ValueError(f"Se esperaban siete celdas; se encontraron {len(celdas)}")
    paths = []
    namespace = {"__name__": "__colab__"}
    show_original = plt.show

    def guardar():
        if len(paths) >= len(NOMBRES):
            raise ValueError("Hay más figuras que nombres de salida")
        path = salida / NOMBRES[len(paths)]
        plt.gcf().savefig(path, dpi=180, facecolor="white")
        plt.close(plt.gcf())
        paths.append(path)

    try:
        plt.show = guardar
        with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
            for numero, celda in enumerate(celdas, start=1):
                exec(compile(celda, f"subseccion4-celda{numero}", "exec"), namespace)
    finally:
        plt.show = show_original
    if len(paths) != len(NOMBRES):
        raise ValueError("No se generaron todas las figuras esperadas")
    return paths


if __name__ == "__main__":
    for archivo in generar():
        print(archivo)

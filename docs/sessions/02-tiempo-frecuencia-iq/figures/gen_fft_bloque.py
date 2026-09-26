#!/usr/bin/env python3
"""Reproduce las figuras de FFT ejecutando los snippets de la subsección 5."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUT = Path(__file__).parent
NOMBRES = [
    "fft-orden-bins.png",
    "fft-bloque-leakage.png",
    "fft-zero-padding.png",
    "fft-ventanas.png",
    "fft-duracion-resolucion.png",
    "fft-tono-debil.png",
    "fft-aliasing-vs-leakage.png",
]


def generar(salida: Path = OUT) -> list[Path]:
    """Guarda una figura por experimento sin duplicar el código de Colab."""
    salida.mkdir(parents=True, exist_ok=True)
    contenido = (OUT.parent / "index.md").read_text(encoding="utf-8")
    seccion = contenido.split("### 5. Qué calcula una FFT de un bloque finito", 1)[1]
    seccion = re.split(r"^### [6-9]\. ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    celdas = re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)
    if len(celdas) != 8:
        raise ValueError(f"Se esperaban ocho celdas; se encontraron {len(celdas)}")
    paths = []
    namespace = {"__name__": "__colab__"}
    original_show = plt.show

    def guardar():
        if len(paths) >= len(NOMBRES):
            raise ValueError("Hay más figuras que nombres de salida")
        path = salida / NOMBRES[len(paths)]
        fig = plt.gcf()
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

    try:
        plt.show = guardar
        with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
            for numero, celda in enumerate(celdas, start=1):
                exec(compile(celda, f"subseccion5-celda{numero}", "exec"), namespace)
    finally:
        plt.show = original_show
        plt.close("all")
    if len(paths) != len(NOMBRES):
        raise ValueError("No se generaron todas las figuras esperadas")
    return paths


if __name__ == "__main__":
    for archivo in generar():
        print(archivo)

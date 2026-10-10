#!/usr/bin/env python3
"""Reproduce las figuras de FFT ejecutando los snippets de la subsección 5."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUT = Path(__file__).parent
NOMBRES = [
    "fft-pruebas-flechas.png",
    "fft-pruebas-espectro.png",
    "fft-tono-intermedio-flechas.png",
    "fft-orden-bins.png",
    "fft-bloque-leakage.png",
    "fft-zero-padding.png",
    "fft-tono-debil-problema.png",
    "fft-ventanas.png",
    "fft-tono-debil.png",
    "fft-duracion-resolucion.png",
    "fft-aliasing-vs-leakage.png",
]


def generar(salida: Path = OUT, solo_etapa_a: bool = False) -> list[Path]:
    """Ejecuta cada celda publicada en un espacio de variables limpio."""
    salida.mkdir(parents=True, exist_ok=True)
    contenido = (OUT.parent / "index.md").read_text(encoding="utf-8")
    seccion = contenido.split("### 5. Qué calcula una FFT de un bloque finito", 1)[1]
    seccion = re.split(r"^### [6-9]\. ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    seccion = seccion.split("#### 5.11.", 1)[0]
    celdas = re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)
    if len(celdas) != 9:
        raise ValueError(f"Se esperaban nueve celdas; se encontraron {len(celdas)}")
    nombres = NOMBRES[:5] if solo_etapa_a else NOMBRES
    if solo_etapa_a:
        celdas = celdas[:3]
    paths = []
    namespace = {"__name__": "__colab__"}
    original_show = plt.show

    def guardar():
        if len(paths) >= len(nombres):
            raise ValueError("Hay más figuras que nombres de salida")
        path = salida / nombres[len(paths)]
        fig = plt.gcf()
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

    try:
        plt.show = guardar
        with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
            for numero, celda in enumerate(celdas, start=1):
                namespace = {"__name__": "__colab__"}
                exec(compile(celda, f"subseccion5-celda{numero}", "exec"), namespace)
    finally:
        plt.show = original_show
        plt.close("all")
    if len(paths) != len(nombres):
        raise ValueError("No se generaron todas las figuras esperadas")
    return paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etapa-a", action="store_true", help="Regenerar solo los cinco PNG de 5.2–5.4")
    args = parser.parse_args()
    for archivo in generar(solo_etapa_a=args.etapa_a):
        print(archivo)

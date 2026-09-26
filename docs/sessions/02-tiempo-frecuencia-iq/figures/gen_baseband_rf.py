#!/usr/bin/env python3
"""Reproduce la subsección 6; la última figura requiere la grabación oficial."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUT = Path(__file__).parent
ROOT = OUT.parents[3]
CAPTURA = ROOT / "samples/fm_99p1MHz_2p4Msps_g30.cu8"
NOMBRES = [
    "baseband-eje-rf.png",
    "baseband-mezcla-compleja.png",
    "baseband-etiqueta-vs-mezcla.png",
    "baseband-mezclador-real-complejo.png",
    "baseband-cruce-borde.png",
    "baseband-captura-oficial.png",
]


def generar(salida: Path = OUT, captura: Path = CAPTURA, incluir_captura: bool = True) -> list[Path]:
    """Ejecuta las celdas publicadas; admite generar solo los ejemplos sintéticos."""
    if incluir_captura and not captura.is_file():
        raise FileNotFoundError(f"Falta la grabación oficial: {captura}")
    salida.mkdir(parents=True, exist_ok=True)
    contenido = (OUT.parent / "index.md").read_text(encoding="utf-8")
    seccion = contenido.split("### 6. De baseband a RF: interpretar una captura SDR", 1)[1]
    seccion = re.split(r"^## ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    celdas = re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)
    if len(celdas) != 7:
        raise ValueError(f"Se esperaban siete celdas; se encontraron {len(celdas)}")
    paths = []
    namespace = {"__name__": "__colab__", "ruta_captura": captura}
    original_show = plt.show
    esperadas = len(NOMBRES) if incluir_captura else len(NOMBRES) - 1

    def guardar():
        if len(paths) >= esperadas:
            raise ValueError("Hay más figuras que nombres de salida")
        path = salida / NOMBRES[len(paths)]
        fig = plt.gcf()
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

    try:
        plt.show = guardar
        with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
            for numero, celda in enumerate(celdas if incluir_captura else celdas[:-1], start=1):
                exec(compile(celda, f"subseccion6-celda{numero}", "exec"), namespace)
    finally:
        plt.show = original_show
        plt.close("all")
    if len(paths) != esperadas:
        raise ValueError("No se generaron todas las figuras esperadas")
    return paths


if __name__ == "__main__":
    for archivo in generar():
        print(archivo)

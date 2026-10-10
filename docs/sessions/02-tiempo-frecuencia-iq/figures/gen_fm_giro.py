#!/usr/bin/env python3
"""Reproduce la demostración FM publicada. No necesita CU8 ni produce WAV."""

from pathlib import Path
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).parent


def ejecutar():
    texto = (OUT.parent / "index.md").read_text(encoding="utf-8")
    apartado = texto.split("#### 6.5. ", 1)[1].split("#### 6.6. ", 1)[0]
    codigo = re.findall(r"```python\n(.*?)```", apartado, re.DOTALL)[0]
    entorno = {}
    exec(compile(codigo, "s02-fm-giro", "exec"), entorno)
    return entorno


def generar(salida=OUT):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    path = salida / "fm-giro-entre-muestras.png"
    original = plt.show
    try:
        plt.show = lambda: None
        with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
            ejecutar()
            plt.gcf().savefig(path, dpi=160, facecolor="white")
    finally:
        plt.show = original
        plt.close("all")
    return path


if __name__ == "__main__":
    print(generar())

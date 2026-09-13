#!/usr/bin/env python3
"""Figura del laboratorio de muestreo: 33 muestras del tono, bytes contra índice y tiempo.

    python gen_muestreo.py
"""

from __future__ import annotations

import importlib.util
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
warnings.filterwarnings(
    "ignore",
    message="Unable to import Axes3D.*",
    category=UserWarning,
    module="matplotlib.projections",
)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = Path(__file__).parent
GEN_TONO = Path(__file__).parents[4] / "samples/gen_tono.py"
BLUE, ORANGE = "#1e40af", "#c2410c"
plt.rcParams.update({"font.size": 11})


def un_milisegundo():
    spec = importlib.util.spec_from_file_location("gen_tono", GEN_TONO)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    iq = gen.tono()
    return np.arange(33), iq[0:66:2], iq[1:66:2]


def generar(salida: Path = OUT) -> Path:
    n, i, q = un_milisegundo()
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=300)
    ax.stem(n - 0.12, i, linefmt=BLUE, markerfmt="o", basefmt=" ", label="I (bytes pares)")
    ax.stem(n + 0.12, q, linefmt=ORANGE, markerfmt="s", basefmt=" ", label="Q (bytes impares)")
    ax.axhline(127.5, color="0.4", ls="--", lw=1)
    # Hueco sin tallos en n = 17..23 por encima de 108: ahí cabe la etiqueta del cero.
    ax.text(20, 131, "cero = 127.5", ha="center", va="bottom", color="0.3", fontsize=10)
    # Etiquetas en una franja fija sobre el máximo (228), no pegadas a cada tallo:
    # así no pisan los tallos vecinos; la columna sombreada las une con su pareja.
    for k in (0, 8, 16, 24):
        ax.axvspan(k - 0.45, k + 0.45, color="0.92", zorder=0)
        ax.text(k, 242, f"n={k}\n({i[k]}, {q[k]})", ha="center", va="bottom", fontsize=10)
    ax.set_xlim(-2, 34)
    ax.set_ylim(0, 290)
    ax.set_xlabel("índice de muestra n  (una línea de od)")
    ax.set_ylabel("valor del byte")
    ax.set_xticks(range(0, 33, 4))
    arriba = ax.secondary_xaxis("top", functions=(lambda x: x / 32, lambda t: t * 32))
    arriba.set_xticks([k / 32 for k in range(0, 33, 4)], [f"{k / 32:g}" for k in range(0, 33, 4)])
    arriba.set_xlabel("tiempo (ms)  =  n / 32")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=10, frameon=False)
    ruta = salida / "muestreo-un-milisegundo.png"
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


if __name__ == "__main__":
    print(generar())

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
BLUE, RED = "#1e40af", "#dc2626"  # RED como en gen_iq.py y el Time Sink
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
    # Misma x para I y Q (una línea de od = un instante); tallos desde el cero, como el Time Sink.
    mi, _, _ = ax.stem(n, i, linefmt=BLUE, markerfmt="o", basefmt=" ", bottom=127.5,
                       label="I (dirección par de od)")
    mq, _, _ = ax.stem(n, q, linefmt=RED, markerfmt="s", basefmt=" ", bottom=127.5,
                       label="Q (dirección impar de od)")
    mq.set_markerfacecolor("none")
    mq.set_markersize(8)  # el cuadrado hueco rodea al círculo cuando I == Q (n = 4, 20)
    for m in (mi, mq):
        m.set_zorder(3)  # marcadores por encima de los tallos del otro canal
    ax.axhline(127.5, color="0.4", ls="--", lw=1)
    # En n = 17..23 los dos canales están por debajo del cero: el hueco de encima es libre.
    ax.text(20, 134, "cero = 127.5", ha="center", va="bottom", color="0.3", fontsize=10)
    # Etiquetas en una franja fija sobre el máximo (228), no pegadas a cada tallo:
    # así no pisan los tallos vecinos; la columna sombreada las une con su pareja.
    for k in (0, 8, 16, 24, 32):
        ax.axvspan(k - 0.45, k + 0.45, color="0.92", zorder=0)
        ax.text(k, 242, f"n={k}\nod {2*k:07d}\n({i[k]}, {q[k]})", ha="center", va="bottom",
                fontsize=10)
    ax.set_xlim(-2.8, 34.8)
    ax.set_ylim(0, 310)
    ax.set_yticks(range(0, 251, 50))  # un byte no pasa de 255: sin marca en 300
    ax.set_xlabel("índice de muestra n  =  dirección de od / 2")
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

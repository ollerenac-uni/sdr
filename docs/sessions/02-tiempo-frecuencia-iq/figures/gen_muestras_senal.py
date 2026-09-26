#!/usr/bin/env python3
"""Genera las figuras de la subsección 1 de la sesión 2."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).parent
BLUE = "#2563eb"
ORANGE = "#c2410c"


def generar(salida: Path = OUT) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    fs, f0, N = 8000, 1000, 16
    n = np.arange(N)
    t = n / fs
    x = np.cos(2 * np.pi * f0 * t)
    t_ref = np.linspace(0, N / fs, 1000)
    x_ref = np.cos(2 * np.pi * f0 * t_ref)
    paths = []

    with plt.rc_context({"font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False}):
        fig, axes = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
        axes[0].stem(n, x, linefmt=BLUE, markerfmt="o", basefmt=" ")
        axes[0].set(xlabel="Índice de muestra n", ylabel="Amplitud",
                    title="16 muestras: el índice indica la posición en la secuencia",
                    xticks=n, xlim=(-0.4, 15.4), ylim=(-1.2, 1.2))
        axes[1].plot(t_ref * 1000, x_ref, color="0.65", lw=1.5,
                     label="Función conocida del ejemplo")
        markers, stems, _ = axes[1].stem(t * 1000, x, basefmt=" ",
                                        label="Muestras, separadas 0.125 ms")
        plt.setp(markers, color=BLUE)
        plt.setp(stems, color=BLUE)
        axes[1].axvline(N / fs * 1000, color=ORANGE, ls="--",
                       label="Fin del bloque: 2 ms (sin muestra)")
        axes[1].set(xlabel="Tiempo (ms)", ylabel="Amplitud",
                    title="Las mismas muestras: el tiempo se obtiene con t = n / fs",
                    xlim=(-0.05, 2.08), ylim=(-1.2, 1.2))
        for ax in axes:
            ax.grid(alpha=0.2)
        axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.2),
                       fontsize=9)
        path = salida / "muestras-indice-tiempo.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

        cambios = [(0.5, 1000, 0, "Amplitud: A = 0.5"),
                   (1, 2000, 0, "Frecuencia: f0 = 2 kHz"),
                   (1, 1000, np.pi / 2, "Fase: phi = pi/2 rad")]
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True,
                                 sharey=True, layout="constrained")
        for ax, (amp, freq, fase, titulo) in zip(axes, cambios):
            ax.plot(t_ref * 1000, x_ref, color="0.7", ls="--",
                    label="Referencia: A = 1, f0 = 1 kHz, phi = 0")
            y_ref = amp * np.cos(2 * np.pi * freq * t_ref + fase)
            y = amp * np.cos(2 * np.pi * freq * t + fase)
            ax.plot(t_ref * 1000, y_ref, color=BLUE, lw=1.5,
                    label="Función con el parámetro modificado")
            ax.plot(t * 1000, y, "o", color=BLUE, ms=5, label="Muestras")
            ax.set(title=titulo, ylabel="Amplitud", ylim=(-1.2, 1.2))
            ax.grid(alpha=0.2)
        axes[-1].set(xlabel="Tiempo (ms)", xlim=(0, 2))
        axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, 1.55),
                       ncol=1, fontsize=9)
        path = salida / "parametros-senoide.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for figura in generar():
        print(figura)

#!/usr/bin/env python3
"""Figuras de muestras complejas, tono I/Q y sentido de rotación."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).parent
BLUE, RED = "#2563eb", "#dc2626"


def preparar_plano(ax, limite=1.35):
    ax.axhline(0, color="0.7", lw=1)
    ax.axvline(0, color="0.7", lw=1)
    ax.set(xlabel="I (parte real)", ylabel="Q (parte imaginaria)", xlim=(-limite, limite), ylim=(-limite, limite))
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)


def generar(salida: Path = OUT) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    paths = []
    with plt.rc_context({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(7, 6), layout="constrained")
        preparar_plano(ax, 5.8)
        ax.set(xlim=(-1, 5.8), ylim=(-1, 5.8), title="Una muestra: z = 3 + 4j")
        ax.annotate("", xy=(3, 4), xytext=(0, 0), arrowprops={"arrowstyle": "->", "color": BLUE, "lw": 2.5})
        ax.plot([3, 3], [0, 4], "--", color="0.5")
        ax.plot([0, 3], [4, 4], "--", color="0.5")
        ax.plot(3, 4, "o", color=BLUE)
        ax.text(3.15, 4.15, "(I, Q) = (3, 4)", color=BLUE)
        ax.text(0.5, 2.6, "Magnitud = 5", color=BLUE, rotation=53.13)
        arco = np.linspace(0, np.angle(3 + 4j), 100)
        ax.plot(np.cos(arco), np.sin(arco), color=RED)
        ax.text(1.1, 0.45, "Fase = 53.13°", color=RED)
        path = salida / "muestra-plano-iq.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

        fs, f0, N = 8000, 1000, 16
        n = np.arange(N)
        t = n / fs
        z = np.exp(1j * 2 * np.pi * f0 * t)
        t_ref = np.linspace(0, N / fs, 1000)
        z_ref = np.exp(1j * 2 * np.pi * f0 * t_ref)
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]}, layout="constrained")
        axes[0].plot(t_ref * 1000, z_ref.real, color=BLUE, label="I: coseno")
        axes[0].plot(t * 1000, z.real, "o", color=BLUE)
        axes[0].plot(t_ref * 1000, z_ref.imag, color=RED, label="Q: seno")
        axes[0].plot(t * 1000, z.imag, "s", color=RED, mfc="white")
        axes[0].set(xlabel="Tiempo (ms)", ylabel="Amplitud", title="Dos componentes del mismo tono complejo", ylim=(-1.2, 1.2))
        axes[0].legend()
        axes[0].grid(alpha=0.2)
        preparar_plano(axes[1])
        axes[1].plot(z_ref.real, z_ref.imag, color="0.7", label="Círculo de referencia")
        axes[1].plot(z[:8].real, z[:8].imag, "o", color=BLUE)
        for k in (0, 1, 2, 4, 6):
            axes[1].text(1.12 * z[k].real, 1.12 * z[k].imag, f"n={k}", ha="center", va="center", fontsize=9)
        axes[1].annotate("", xy=(z[1].real, z[1].imag), xytext=(z[0].real, z[0].imag), arrowprops={"arrowstyle": "->", "color": BLUE, "lw": 2})
        axes[1].set_title("Una vuelta cada 1 ms; radio = 1")
        path = salida / "tono-tiempo-plano-iq.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

        fig, axes = plt.subplots(1, 2, figsize=(10, 5), layout="constrained")
        for ax, signo, color, titulo in zip(axes, (1, -1), (BLUE, RED), ("+1 kHz: giro antihorario", "−1 kHz: giro horario")):
            preparar_plano(ax)
            tono = np.exp(signo * 1j * 2 * np.pi * f0 * t[:8])
            circulo = np.exp(signo * 1j * np.linspace(0, 2 * np.pi, 200))
            ax.plot(circulo.real, circulo.imag, color="0.75")
            ax.plot(tono.real, tono.imag, "o", color=color)
            for k in (0, 1, 2, 4, 6):
                ax.text(1.12 * tono[k].real, 1.12 * tono[k].imag, f"n={k}", ha="center", va="center", fontsize=9)
            ax.annotate("", xy=(tono[1].real, tono[1].imag), xytext=(tono[0].real, tono[0].imag), arrowprops={"arrowstyle": "->", "color": color, "lw": 2})
            ax.set_title(titulo)
        path = salida / "frecuencia-sentido-giro.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for figura in generar():
        print(figura)

#!/usr/bin/env python3
"""Figuras de respaldo de la página interactiva, sin navegador ni JavaScript."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).parent
FS = 2.4e6


def generar(salida: Path = OUT) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    n = np.arange(240)
    t = n / FS
    objetivo = np.exp(1j * 2 * np.pi * 400e3 * t)
    oscilador = np.exp(-1j * 2 * np.pi * 400e3 * t)
    centrado = objetivo * oscilador
    entrada = objetivo + 0.6 * np.exp(-1j * 2 * np.pi * 600e3 * t) + 0.4
    salida_compleja = entrada * oscilador
    paths = []

    def guardar(fig, nombre):
        path = salida / nombre
        fig.savefig(path, dpi=160, facecolor="white")
        plt.close(fig)
        paths.append(path)

    with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
        circle = np.exp(1j * np.linspace(0, 2 * np.pi, 241))
        for ax, z, titulo in zip(axes, [objetivo[1], centrado[1]], ["Antes: muestra n = 1", "Después: muestra n = 1"]):
            ax.plot(circle.real, circle.imag, color="0.75", linewidth=1)
            ax.axhline(0, color="0.65", linewidth=1)
            ax.axvline(0, color="0.65", linewidth=1)
            ax.plot([0, z.real], [0, 0], color="#1565c0", linewidth=4, label="I: posición horizontal")
            ax.plot([0, 0], [0, z.imag], color="#c95608", linewidth=4, label="Q: posición vertical")
            ax.annotate("", xy=(z.real, z.imag), xytext=(0, 0), arrowprops={"arrowstyle": "->", "color": "#793bac", "lw": 2})
            ax.set(title=titulo, xlabel="I", ylabel="Q", xlim=(-1.25, 1.25), ylim=(-1.25, 1.25), aspect="equal", xticks=[-1, 0, 1], yticks=[-1, 0, 1])
            ax.text(0.03, 0.96, f"I = {z.real:.3f}; Q = {z.imag:.3f}", transform=ax.transAxes, va="top")
        guardar(fig, "mezcla-interactiva-iq.png")

        fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
        for ax, z, titulo in zip(axes, [objetivo, centrado], ["Antes: solo el objetivo", "Después: solo el objetivo"]):
            ax.plot(t[:37] * 1e6, z[:37].real, ".-", color="#1565c0", label="I")
            ax.plot(t[:37] * 1e6, z[:37].imag, ".-", color="#c95608", label="Q")
            ax.axvline(t[1] * 1e6, color="0.4", linestyle="--", label="Muestra n = 1")
            ax.set(title=titulo, xlabel="Tiempo (µs)", ylabel="Valor", ylim=(-1.2, 1.2))
            ax.grid(alpha=0.2)
            ax.legend(fontsize=8)
        guardar(fig, "mezcla-interactiva-tiempo.png")

        fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
        f = np.fft.fftshift(np.fft.fftfreq(len(n), d=1 / FS))
        for ax, z, deseado, titulo in zip(axes, [entrada, salida_compleja], [objetivo, centrado], ["Antes: tres tonos", "Después: desplazamiento −400 kHz"]):
            c = np.fft.fftshift(np.fft.fft(z)) / len(n)
            d = np.fft.fftshift(np.fft.fft(deseado)) / len(n)
            for color, mascara in [("0.55", (np.abs(c) > 1e-7) & (np.abs(d) < 1e-7)), ("#793bac", np.abs(d) > 1e-7)]:
                stem = ax.stem(f[mascara] / 1000, np.abs(c[mascara]), basefmt=" ")
                plt.setp(stem.markerline, color=color)
                plt.setp(stem.stemlines, color=color)
            ax.axvline(0, color="0.4", linestyle="--")
            ax.set(title=titulo, xlabel="Frecuencia en baseband (kHz)", ylabel="Magnitud", xlim=(-1200, 1200), ylim=(0, 1.2), xticks=[-1200, -600, 0, 600, 1200])
            ax.grid(alpha=0.2)
        guardar(fig, "mezcla-interactiva-espectro.png")
    return paths


if __name__ == "__main__":
    for archivo in generar():
        print(archivo)

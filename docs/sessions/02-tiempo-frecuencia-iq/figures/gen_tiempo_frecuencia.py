#!/usr/bin/env python3
"""Figuras de la subsección 3: tonos, suma y fase espectral."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).parent
BLUE, RED = "#2563eb", "#dc2626"


def espectro(y, fs):
    f = np.fft.fftshift(np.fft.fftfreq(len(y), d=1 / fs))
    coef = np.fft.fftshift(np.fft.fft(y)) / len(y)
    return f, coef


def dibujar_espectro(ax, f, coef, color=BLUE):
    markers, stems, _ = ax.stem(f / 1000, np.abs(coef), basefmt=" ")
    plt.setp(markers, color=color, markersize=4)
    plt.setp(stems, color=color)
    ax.set(xlabel="Frecuencia (kHz)", ylabel="Magnitud por componente", xlim=(-3, 3), ylim=(-0.04, 1.15), xticks=range(-3, 4))
    ax.grid(alpha=0.2)


def generar(salida: Path = OUT) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    fs, f0, N = 8000, 1000, 64
    t = np.arange(N) / fs
    theta = 2 * np.pi * f0 * t
    z_pos, z_neg = np.exp(1j * theta), np.exp(-1j * theta)
    x_real = np.cos(theta)
    visible = t < 0.002
    paths = []

    with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
        fig, axes = plt.subplots(3, 2, figsize=(12, 9), layout="constrained")
        casos = [(x_real, "Coseno real: amplitud 1", False), (z_pos, "Tono complejo: +1 kHz", True), (z_neg, "Tono complejo: −1 kHz", True)]
        for fila, (y, titulo, complejo) in enumerate(casos):
            axes[fila, 0].plot(t[visible] * 1000, y.real[visible], ".-", color=BLUE, label="I" if complejo else "x[n]")
            if complejo:
                axes[fila, 0].plot(t[visible] * 1000, y.imag[visible], "s-", color=RED, ms=4, mfc="white", label="Q")
            axes[fila, 0].set(title=titulo, xlabel="Tiempo (ms)", ylabel="Amplitud", ylim=(-1.2, 1.2))
            axes[fila, 0].legend(loc="upper right")
            axes[fila, 0].grid(alpha=0.2)
            f, coef = espectro(y, fs)
            dibujar_espectro(axes[fila, 1], f, coef)
            axes[fila, 1].set_title("Componentes en frecuencia del bloque de 8 ms")
            for k in np.flatnonzero(np.abs(coef) > 0.1):
                axes[fila, 1].text(f[k] / 1000, abs(coef[k]) + 0.05, f"{abs(coef[k]):g}", ha="center", color=BLUE)
        path = salida / "tonos-tiempo-espectro.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

        z1 = z_pos
        z2 = 0.5 * np.exp(-1j * 2 * np.pi * 2000 * t)
        z_suma = z1 + z2
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), layout="constrained")
        axes[0, 0].plot(t[visible] * 1000, z1.real[visible], "o-", color=BLUE, label="I del tono de +1 kHz")
        axes[0, 0].plot(t[visible] * 1000, z2.real[visible], "s-", color=RED, ms=4, label="I del tono de −2 kHz")
        axes[0, 0].set(title="Componentes antes de sumar", ylabel="Amplitud", xlabel="Tiempo (ms)")
        axes[0, 0].legend(fontsize=8)
        axes[1, 0].plot(t[visible] * 1000, z_suma.real[visible], "o-", color=BLUE, label="I de la suma")
        axes[1, 0].plot(t[visible] * 1000, z_suma.imag[visible], "s-", color=RED, ms=4, mfc="white", label="Q de la suma")
        axes[1, 0].set(title="Una sola secuencia: z1 + z2", ylabel="Amplitud", xlabel="Tiempo (ms)")
        axes[1, 0].legend(fontsize=8)
        f, C1 = espectro(z1, fs)
        _, C2 = espectro(z2, fs)
        dibujar_espectro(axes[0, 1], f, C1)
        markers, stems, _ = axes[0, 1].stem(f / 1000, np.abs(C2), basefmt=" ")
        plt.setp(markers, color=RED, marker="s", markersize=4)
        plt.setp(stems, color=RED)
        axes[0, 1].set_title("+1 kHz con magnitud 1; −2 kHz con magnitud 0.5")
        _, C_suma = espectro(z_suma, fs)
        dibujar_espectro(axes[1, 1], f, C_suma)
        axes[1, 1].set_title("El espectro de la suma conserva ambas componentes")
        for ax in axes[:, 0]:
            ax.grid(alpha=0.2)
        path = salida / "suma-tonos-tiempo-espectro.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)

        x0 = np.cos(theta)
        x90 = np.cos(theta + np.pi / 2)
        f, C0 = espectro(x0, fs)
        _, C90 = espectro(x90, fs)
        fuertes = np.abs(C0) > 0.1
        fig, axes = plt.subplots(3, 1, figsize=(10, 9), layout="constrained")
        axes[0].plot(t[visible] * 1000, x0[visible], "o-", color=BLUE, label="Fase inicial 0°")
        axes[0].plot(t[visible] * 1000, x90[visible], "s-", color=RED, ms=4, mfc="white", label="Fase inicial 90°")
        axes[0].set(title="Distintos valores en el tiempo", xlabel="Tiempo (ms)", ylabel="Amplitud")
        axes[0].legend()
        markers, stems, _ = axes[1].stem(f / 1000, np.abs(C0), basefmt=" ", label="Fase inicial 0°")
        plt.setp(markers, color=BLUE, markersize=4)
        plt.setp(stems, color=BLUE)
        axes[1].plot(f / 1000, np.abs(C90), "s", color=RED, ms=5, mfc="white", label="Fase inicial 90°")
        axes[1].set(title="Igual magnitud espectral", xlabel="Frecuencia (kHz)", ylabel="Magnitud por componente", xlim=(-2, 2), ylim=(-0.03, 0.6))
        axes[1].legend()
        axes[2].plot(f[fuertes] / 1000, np.angle(C0[fuertes], deg=True), "o", color=BLUE, ms=8, label="Fase inicial 0°")
        axes[2].plot(f[fuertes] / 1000, np.angle(C90[fuertes], deg=True), "s", color=RED, ms=7, mfc="white", label="Fase inicial 90°")
        axes[2].set(title="Distinta fase espectral: solo componentes presentes", xlabel="Frecuencia (kHz)", ylabel="Fase (grados)", xlim=(-2, 2), ylim=(-115, 115), yticks=[-90, 0, 90])
        axes[2].legend()
        for ax in axes:
            ax.grid(alpha=0.2)
        path = salida / "magnitud-fase-espectral.png"
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for figura in generar():
        print(figura)

#!/usr/bin/env python3
"""Genera las figuras didácticas de tiempo, frecuencia e IQ de la Sesión 02.

Puede ejecutarse desde cualquier directorio:

    python3 gen_time_frequency.py
    python3 gen_time_frequency.py --output-dir /tmp/figuras-s02
"""

from __future__ import annotations

import argparse
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
BLUE = "#1d4ed8"
RED = "#dc2626"
GREEN = "#047857"
AMBER = "#d97706"
PURPLE = "#7e22ce"
DARK = "#111827"
GRAY = "#6b7280"
LIGHT_BLUE = "#dbeafe"
LIGHT_AMBER = "#fef3c7"

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.facecolor": "white",
    }
)


def bin_spacing(sample_rate: float, fft_size: int) -> float:
    """Devuelve la separación entre bins de una DFT uniforme."""
    if sample_rate <= 0 or fft_size <= 0:
        raise ValueError("sample_rate y fft_size deben ser positivos")
    return sample_rate / fft_size


def save_figure(fig: plt.Figure, output_dir: Path, name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def shifted_spectrum_db(
    signal: np.ndarray,
    sample_rate: float,
    window: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Espectro centrado y normalizado al pico, en dB."""
    if window is None:
        window = np.ones(len(signal))
    spectrum = np.fft.fftshift(np.fft.fft(signal * window))
    magnitude = np.maximum(np.abs(spectrum), np.finfo(float).tiny)
    magnitude_db = 20 * np.log10(magnitude / magnitude.max())
    frequency = np.fft.fftshift(np.fft.fftfreq(len(signal), 1 / sample_rate))
    return frequency, magnitude_db


def plot_domains(output_dir: Path) -> Path:
    """Una señal, dos representaciones complementarias."""
    sample_rate = 4_000
    duration = 0.25
    t = np.arange(int(sample_rate * duration)) / sample_rate
    signal = np.cos(2 * np.pi * 120 * t) + 0.55 * np.cos(2 * np.pi * 320 * t + 0.7)
    frequency, magnitude_db = shifted_spectrum_db(signal, sample_rate, np.hanning(len(signal)))

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4), constrained_layout=True)
    axes[0].plot(t * 1e3, signal, color=BLUE, lw=1.5)
    axes[0].set_xlim(0, 35)
    axes[0].set_ylim(-1.8, 1.8)
    axes[0].set_xlabel("Tiempo (ms)")
    axes[0].set_ylabel("Amplitud")
    axes[0].set_title("Dominio del tiempo: ¿cuándo y cuánto?")
    axes[0].grid(alpha=0.2)

    keep = (frequency >= 0) & (frequency <= 600)
    axes[1].plot(frequency[keep], magnitude_db[keep], color=GREEN, lw=1.5)
    axes[1].set_ylim(-80, 5)
    axes[1].set_xlabel("Frecuencia (Hz)")
    axes[1].set_ylabel("Magnitud relativa (dB)")
    axes[1].set_title("Dominio de la frecuencia: ¿qué componentes?")
    axes[1].grid(alpha=0.2)
    for freq, level, label in ((120, 0, "120 Hz"), (320, -5.2, "320 Hz")):
        axes[1].annotate(
            label,
            xy=(freq, level),
            xytext=(freq + 42, level - 13),
            arrowprops=dict(arrowstyle="->", color=DARK),
            color=DARK,
        )

    fig.suptitle("Dos representaciones de la misma señal", fontsize=14, color=DARK)
    fig.text(
        0.5,
        -0.02,
        "Ningún gráfico es “la señal completa” por sí solo: cada vista hace visibles preguntas distintas.",
        ha="center",
        color=DARK,
    )
    return save_figure(fig, output_dir, "dominios-tiempo-frecuencia.png")


def plot_harmonics_and_clipping(output_dir: Path) -> Path:
    """Relaciona bordes, armónicos y recorte sin derivar una serie."""
    sample_rate = 8_192
    fundamental = 64
    t = np.arange(sample_rate // 8) / sample_rate
    tone = np.sin(2 * np.pi * fundamental * t)
    clipped = np.clip(2.2 * tone, -1, 1)
    square_approx = sum(
        np.sin(2 * np.pi * harmonic * fundamental * t) / harmonic
        for harmonic in (1, 3, 5, 7, 9)
    )
    square_approx *= 4 / np.pi

    fig, axes = plt.subplots(2, 2, figsize=(8.2, 5.1), constrained_layout=True)
    window = np.hanning(len(t))
    for signal, color, label, style in (
        (tone, BLUE, "Senoide", "-"),
        (clipped, RED, "Senoide recortada", "--"),
    ):
        axes[0, 0].plot(
            t * 1e3,
            signal,
            color=color,
            linestyle=style,
            lw=1.4,
            label=label,
        )
        frequency, magnitude_db = shifted_spectrum_db(signal, sample_rate, window)
        keep = (frequency >= 0) & (frequency <= 700)
        axes[0, 1].plot(
            frequency[keep],
            magnitude_db[keep],
            color=color,
            linestyle=style,
            lw=1.4,
            label=label,
        )

    axes[0, 0].set_xlim(0, 48)
    axes[0, 0].set_ylim(-1.4, 1.4)
    axes[0, 0].set_title("El recorte crea bordes")
    axes[0, 0].set_xlabel("Tiempo (ms)")
    axes[0, 0].set_ylabel("Amplitud")
    axes[0, 0].legend(frameon=False)
    axes[0, 0].grid(alpha=0.2)

    axes[0, 1].set_ylim(-75, 5)
    axes[0, 1].set_title("Los bordes aparecen como armónicos")
    axes[0, 1].set_xlabel("Frecuencia (Hz)")
    axes[0, 1].set_ylabel("Magnitud relativa (dB)")
    axes[0, 1].legend(frameon=False)
    axes[0, 1].grid(alpha=0.2)

    axes[1, 0].plot(t * 1e3, square_approx, color=PURPLE, lw=1.4)
    axes[1, 0].set_xlim(0, 48)
    axes[1, 0].set_ylim(-1.4, 1.4)
    axes[1, 0].set_title("Suma de armónicos impares: 1, 3, 5, 7 y 9")
    axes[1, 0].set_xlabel("Tiempo (ms)")
    axes[1, 0].set_ylabel("Amplitud")
    axes[1, 0].grid(alpha=0.2)

    harmonic_numbers = np.array([1, 3, 5, 7, 9])
    harmonic_levels = 20 * np.log10(1 / harmonic_numbers)
    axes[1, 1].stem(
        harmonic_numbers * fundamental,
        harmonic_levels,
        linefmt=PURPLE,
        markerfmt="o",
        basefmt=" ",
    )
    axes[1, 1].set_ylim(-25, 3)
    axes[1, 1].set_xlim(0, 700)
    axes[1, 1].set_title("Cada detalle rápido exige contenido de alta frecuencia")
    axes[1, 1].set_xlabel("Frecuencia (Hz)")
    axes[1, 1].set_ylabel("Magnitud relativa (dB)")
    axes[1, 1].grid(alpha=0.2)

    fig.suptitle("El espectro explica la forma de onda y la saturación", fontsize=14, color=DARK)
    return save_figure(fig, output_dir, "armonicos-y-recorte.png")


def plot_leakage_and_windows(output_dir: Path) -> Path:
    """Compara coherencia, fuga y la compensación de una ventana Hann."""
    sample_rate = 1_024
    size = 256
    t = np.arange(size) / sample_rate
    coherent = np.cos(2 * np.pi * 128 * t)
    off_bin = np.cos(2 * np.pi * 130 * t)

    cases = (
        (coherent, np.ones(size), "128 Hz: cae exactamente en un bin"),
        (off_bin, np.ones(size), "130 Hz: fuga con ventana rectangular"),
        (off_bin, np.hanning(size), "130 Hz: Hann reduce lóbulos laterales"),
    )

    fig = plt.figure(figsize=(8.2, 5.2), constrained_layout=True)
    grid = fig.add_gridspec(2, 2)
    spectrum_axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, 1])]
    colors = (BLUE, RED, GREEN)
    for ax, (signal, window, title), color in zip(spectrum_axes, cases, colors, strict=True):
        frequency, magnitude_db = shifted_spectrum_db(signal, sample_rate, window)
        keep = (frequency >= 70) & (frequency <= 190)
        ax.plot(frequency[keep], magnitude_db[keep], color=color, lw=1.35)
        ax.set_ylim(-70, 4)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Frecuencia (Hz)")
        ax.set_ylabel("dB")
        ax.grid(alpha=0.2)

    boundary_ax = fig.add_subplot(grid[1, 0])
    tiled = np.tile(off_bin, 3)
    index = np.arange(-size, 2 * size)
    boundary_ax.plot(index, tiled, color=AMBER, lw=1.0)
    boundary_ax.axvline(0, color=DARK, ls="--", lw=1)
    boundary_ax.axvline(size, color=DARK, ls="--", lw=1)
    boundary_ax.set_xlim(-28, size + 28)
    boundary_ax.set_ylim(-1.25, 1.25)
    boundary_ax.set_title("La DFT trata el bloque como un período")
    boundary_ax.set_xlabel("Índice de muestra")
    boundary_ax.set_ylabel("Amplitud")
    boundary_ax.annotate(
        "Los extremos pasan a ser vecinos",
        xy=(0, off_bin[0]),
        xytext=(size * 0.19, -1.12),
        arrowprops=dict(arrowstyle="->", color=DARK),
        color=DARK,
    )
    boundary_ax.grid(alpha=0.2)

    fig.suptitle(
        "Una captura finita produce fuga; la ventana cambia el compromiso",
        fontsize=14,
        color=DARK,
    )
    fig.text(
        0.5,
        -0.01,
        "Hann baja los lóbulos laterales, pero ensancha el pico: no elimina la fuga gratis.",
        ha="center",
        color=DARK,
    )
    return save_figure(fig, output_dir, "fuga-y-ventanas.png")


def plot_fft_axes(output_dir: Path) -> Path:
    """Relaciona bloque temporal, tasa, duración, bins y espectro centrado."""
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 4.7), constrained_layout=True)

    size_demo = 16
    n = np.arange(size_demo)
    axes[0].stem(n, np.sin(2 * np.pi * 3 * n / size_demo), linefmt=BLUE, markerfmt="o", basefmt=" ")
    axes[0].set_xlim(-0.8, size_demo - 0.2)
    axes[0].set_ylim(-1.3, 1.3)
    axes[0].set_xlabel("Índice $n$")
    axes[0].set_ylabel("$x[n]$")
    axes[0].set_title("Entrada: un bloque de $N$ muestras separado por $T_s=1/f_s$")
    axes[0].grid(alpha=0.2)

    bins = np.arange(-8, 8)
    levels = np.full_like(bins, 0.16, dtype=float)
    levels[bins == 3] = 1
    axes[1].stem(bins, levels, linefmt=GREEN, markerfmt="o", basefmt=" ")
    axes[1].axvline(0, color=GRAY, lw=0.8)
    axes[1].axvline(8, color=GRAY, ls="--", lw=0.8)
    axes[1].set_xlim(-8.8, 8.5)
    axes[1].set_ylim(0, 1.25)
    axes[1].set_xticks(
        [-8, 0, 7],
        ["$-f_s/2$", "0", "$+f_s/2-\\Delta f$"],
    )
    axes[1].set_yticks([])
    axes[1].set_xlabel("Frecuencia relativa a la frecuencia central")
    axes[1].set_title("Salida compleja centrada: $N$ bins separados por $\\Delta f=f_s/N$")
    axes[1].annotate(
        "un bin",
        xy=(1, 0.16),
        xytext=(2.2, 0.55),
        arrowprops=dict(arrowstyle="<->", color=DARK),
        color=DARK,
    )
    axes[1].annotate(
        "$+f_s/2$ es un límite, no otro bin",
        xy=(8, 0.03),
        xytext=(3.7, 0.78),
        arrowprops=dict(arrowstyle="->", color=GRAY),
        color=GRAY,
    )

    fig.suptitle("Cómo se construyen los ejes de una FFT", fontsize=14, color=DARK)
    fig.text(
        0.51,
        0.49,
        "$T_{captura}=N/f_s$",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=LIGHT_BLUE, edgecolor="none"),
        color=DARK,
    )
    fig.text(
        0.76,
        0.49,
        "Ejemplo: $f_s=32$ kS/s, $N=1024$ → $\\Delta f=31.25$ Hz",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=LIGHT_AMBER, edgecolor="none"),
        color=DARK,
    )
    return save_figure(fig, output_dir, "ejes-fft.png")


def plot_real_vs_complex(output_dir: Path) -> Path:
    """Contrasta la simetría real con la frecuencia con signo de IQ."""
    sample_rate = 32_000
    size = 2_048
    tone_frequency = 3_000
    t = np.arange(size) / sample_rate
    real_tone = np.cos(2 * np.pi * tone_frequency * t)
    complex_tone = np.exp(1j * 2 * np.pi * tone_frequency * t)
    window = np.hanning(size)

    fig, axes = plt.subplots(2, 2, figsize=(8.2, 5.0), constrained_layout=True)
    show = t < 2 / tone_frequency
    axes[0, 0].plot(t[show] * 1e3, real_tone[show], color=BLUE, lw=1.5)
    axes[0, 0].set_title("Señal real: un valor por instante")
    axes[0, 0].set_xlabel("Tiempo (ms)")
    axes[0, 0].set_ylabel("Amplitud")
    axes[0, 0].grid(alpha=0.2)

    axes[0, 1].plot(
        t[show] * 1e3,
        complex_tone.real[show],
        color=BLUE,
        lw=1.4,
        label="I",
    )
    axes[0, 1].plot(
        t[show] * 1e3,
        complex_tone.imag[show],
        color=RED,
        linestyle="--",
        lw=1.4,
        label="Q",
    )
    axes[0, 1].set_title("Señal compleja: $I+jQ$")
    axes[0, 1].set_xlabel("Tiempo (ms)")
    axes[0, 1].set_ylabel("Amplitud")
    axes[0, 1].legend(frameon=False)
    axes[0, 1].grid(alpha=0.2)

    for ax, signal, color, title in (
        (axes[1, 0], real_tone, BLUE, "Dos picos: $-f_0$ y $+f_0$"),
        (axes[1, 1], complex_tone, GREEN, "Un pico: el signo conserva el sentido"),
    ):
        frequency, magnitude_db = shifted_spectrum_db(signal, sample_rate, window)
        keep = np.abs(frequency) <= 7_000
        ax.plot(frequency[keep] / 1e3, magnitude_db[keep], color=color, lw=1.4)
        ax.axvline(0, color=GRAY, lw=0.7)
        ax.set_ylim(-80, 4)
        ax.set_title(title)
        ax.set_xlabel("Frecuencia relativa (kHz)")
        ax.set_ylabel("dB")
        ax.grid(alpha=0.2)

    fig.suptitle("La señal real es simétrica; IQ distingue frecuencias con signo", fontsize=14, color=DARK)
    return save_figure(fig, output_dir, "real-vs-compleja.png")


def plot_frequency_translation(output_dir: Path) -> Path:
    """Muestra cómo una exponencial compleja desplaza todo el espectro."""
    sample_rate = 32_000
    size = 4_096
    t = np.arange(size) / sample_rate
    offsets = (-5_000, -1_000, 3_500)
    source = sum(
        amplitude * np.exp(1j * 2 * np.pi * frequency * t)
        for amplitude, frequency in zip((0.45, 1.0, 0.65), offsets, strict=True)
    )
    shift = 4_000
    translated = source * np.exp(1j * 2 * np.pi * shift * t)
    window = np.hanning(size)

    fig, axes = plt.subplots(2, 1, figsize=(8.2, 4.7), sharex=True, constrained_layout=True)
    for ax, signal, color, title in (
        (axes[0], source, BLUE, "Antes: componentes en −5, −1 y +3.5 kHz"),
        (axes[1], translated, GREEN, r"Después de multiplicar por $e^{j2\pi(4\,kHz)t}$: todas se mueven +4 kHz"),
    ):
        frequency, magnitude_db = shifted_spectrum_db(signal, sample_rate, window)
        keep = np.abs(frequency) <= 11_000
        ax.plot(frequency[keep] / 1e3, magnitude_db[keep], color=color, lw=1.5)
        ax.axvline(0, color=GRAY, lw=0.7)
        ax.set_ylim(-75, 4)
        ax.set_ylabel("dB")
        ax.set_title(title)
        ax.grid(alpha=0.2)

    axes[1].set_xlabel("Frecuencia en banda base (kHz)")
    axes[0].annotate(
        "misma forma y separaciones",
        xy=(3.5, -3.8),
        xytext=(6.2, -24),
        arrowprops=dict(arrowstyle="->", color=DARK),
        color=DARK,
    )
    fig.suptitle("Traslación en frecuencia: la operación central de la sintonización digital", fontsize=14, color=DARK)
    fig.text(
        0.5,
        -0.01,
        "En RF: frecuencia absoluta = frecuencia central $f_c$ + desplazamiento de banda base.",
        ha="center",
        color=DARK,
    )
    return save_figure(fig, output_dir, "traslacion-frecuencia.png")


def generate_figures(output_dir: Path = OUT) -> tuple[Path, ...]:
    """Genera las seis figuras y devuelve sus rutas."""
    return (
        plot_domains(output_dir),
        plot_harmonics_and_clipping(output_dir),
        plot_leakage_and_windows(output_dir),
        plot_fft_axes(output_dir),
        plot_real_vs_complex(output_dir),
        plot_frequency_translation(output_dir),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUT,
        help="Directorio de salida (por defecto, el directorio del script)",
    )
    args = parser.parse_args()

    for path in generate_figures(args.output_dir):
        print("ok", path)


if __name__ == "__main__":
    main()

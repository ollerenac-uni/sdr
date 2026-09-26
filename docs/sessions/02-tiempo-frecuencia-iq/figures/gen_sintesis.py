#!/usr/bin/env python3
"""Cuatro láminas reproducibles para la síntesis visual de la sesión 02.

Solo utiliza señales sintéticas conocidas; no necesita la grabación del curso.
Uso desde la raíz: python3 docs/sessions/02-tiempo-frecuencia-iq/figures/gen_sintesis.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).parent
NOMBRES = [
    "sintesis-muestras-representaciones.png",
    "sintesis-aliasing-leakage.png",
    "sintesis-decisiones-fft.png",
    "sintesis-baseband-rf.png",
]
AZUL = "#2563eb"
NARANJA = "#ea580c"
VERDE = "#0f766e"
GRIS = "#64748b"


def espectro(z, fs, ventana=None, m=None):
    """Magnitud de tonos: conserva la escala al cambiar ventana o padding."""
    w = np.ones(len(z)) if ventana is None else np.asarray(ventana)
    m = len(z) if m is None else m
    if m < len(z) or len(w) != len(z):
        raise ValueError("No se recortan muestras y la ventana debe tener longitud N")
    f = np.fft.fftshift(np.fft.fftfreq(m, d=1 / fs))
    C = np.fft.fftshift(np.fft.fft(z * w, n=m)) / np.sum(w)
    return f, C


def hann(n):
    return 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / n)


def datos_muestras():
    fs = 8000
    n = np.arange(16)
    t = n / fs
    z = np.exp(1j * 2 * np.pi * 1000 * t)
    return {"fs": fs, "n": n, "t": t, "z": z, "complejo": espectro(z, fs), "real": espectro(z.real, fs)}


def datos_ambiguedad():
    fs = 8000
    n = np.arange(16)
    z5 = np.exp(1j * 2 * np.pi * 5000 * n / fs)
    zm3 = np.exp(-1j * 2 * np.pi * 3000 * n / fs)
    z_leak = np.exp(1j * 2 * np.pi * 1062.5 * np.arange(64) / fs)
    return {"fs": fs, "n": n, "z5": z5, "zm3": zm3, "leakage": espectro(z_leak, fs)}


def datos_fft():
    fs = 8000
    z = np.exp(1j * 2 * np.pi * 1062.5 * np.arange(64) / fs)
    pares = {}
    for n in [64, 512]:
        t = np.arange(n) / fs
        par = np.exp(1j * 2 * np.pi * 1000 * t) + np.exp(1j * 2 * np.pi * 1062.5 * t)
        pares[n] = espectro(par, fs, ventana=hann(n), m=8192)
    return {
        "fs": fs,
        "z": z,
        "sin_padding": espectro(z, fs),
        "con_padding": espectro(z, fs, m=512),
        "rectangular": espectro(z, fs, m=4096),
        "hann": espectro(z, fs, ventana=hann(64), m=4096),
        "pares": pares,
    }


def datos_rf():
    fs = 2.4e6
    fc = 99.1e6
    t = np.arange(2400) / fs
    posiciones = np.array([-600e3, 0, 400e3])
    amplitudes = np.array([0.6, 0.4, 1])
    x = sum(A * np.exp(1j * 2 * np.pi * f0 * t) for A, f0 in zip(amplitudes, posiciones))
    f_mix = -400e3
    y = x * np.exp(1j * 2 * np.pi * f_mix * t)
    return {"fs": fs, "fc": fc, "fc_nuevo": fc - f_mix, "f_mix": f_mix, "posiciones": posiciones, "amplitudes": amplitudes, "x": x, "y": y, "entrada": espectro(x, fs), "salida": espectro(y, fs)}


def tallos(ax, f, C, escala=1000, referencia=0, color=AZUL):
    """Omite residuos de punto flotante solo en tonos coherentes conocidos."""
    presentes = np.abs(C) > 1e-10
    container = ax.stem((referencia + f[presentes]) / escala, np.abs(C[presentes]), basefmt=" ")
    plt.setp(container.markerline, color=color, markersize=8)
    plt.setp(container.stemlines, color=color, linewidth=2)


def figura_muestras():
    d = datos_muestras()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    ax = axes[0, 0]
    ax.plot(d["t"] * 1000, d["z"].real, "o-", color=AZUL, label="I")
    ax.plot(d["t"] * 1000, d["z"].imag, "s-", color=NARANJA, label="Q")
    ax.axvline(2, color=GRIS, linestyle="--", label="N/fs = 2 ms")
    ax.set(title="A. Las 16 muestras en el tiempo", xlabel="Tiempo (ms)", ylabel="Valor", xlim=(-0.06, 2.08), ylim=(-1.3, 1.5), xticks=[0, 0.5, 1, 1.5, 2])
    ax.legend(fontsize=11, ncol=3, loc="upper right")
    ax = axes[0, 1]
    angulos = np.linspace(0, 2 * np.pi, 401)
    ax.plot(np.cos(angulos), np.sin(angulos), color=GRIS, alpha=0.35)
    ax.plot(d["z"][:8].real, d["z"][:8].imag, "o", color=VERDE, markersize=7)
    ax.annotate("n = 0", xy=(1, 0), xytext=(0.6, -0.4), fontsize=12, arrowprops={"arrowstyle": "->", "color": GRIS})
    ax.annotate("n = 1", xy=(np.sqrt(0.5), np.sqrt(0.5)), xytext=(0.1, 1.12), fontsize=12, arrowprops={"arrowstyle": "->", "color": GRIS})
    ax.annotate("", xy=(0.72, 0.72), xytext=(1, 0), arrowprops={"arrowstyle": "->", "color": VERDE, "connectionstyle": "arc3,rad=0.15"})
    ax.set(title="B. Una vuelta: primeras 8 muestras I/Q", xlabel="I", ylabel="Q", xlim=(-1.35, 1.35), ylim=(-1.35, 1.35), aspect="equal")
    for ax, nombre, titulo in [(axes[1, 0], "complejo", "C. FFT de I + jQ: tono complejo"), (axes[1, 1], "real", "D. FFT de solo I: coseno real")]:
        tallos(ax, *d[nombre])
        ax.set(title=titulo, xlabel="Frecuencia (kHz)", ylabel="Magnitud", xlim=(-4.2, 4.2), ylim=(-0.04, 1.15), xticks=[-4, -2, -1, 0, 1, 2, 4])
    for ax in axes.flat:
        ax.grid(alpha=0.2)
    return fig


def figura_ambiguedad():
    d = datos_ambiguedad()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), layout="constrained")
    ax = axes[0]
    ax.plot(d["n"], d["z5"].real, "o-", color=AZUL, label="I de +5 kHz")
    ax.plot(d["n"], d["zm3"].real, "s", color=AZUL, markerfacecolor="none", markersize=9, label="I de -3 kHz")
    ax.plot(d["n"], d["z5"].imag, "o-", color=NARANJA, label="Q de +5 kHz")
    ax.plot(d["n"], d["zm3"].imag, "s", color=NARANJA, markerfacecolor="none", markersize=9, label="Q de -3 kHz")
    ax.set(title="A. Aliasing: dos frecuencias originales\nLas mismas muestras a 8 kS/s", xlabel="Índice de muestra n", ylabel="Valor de I o Q", ylim=(-1.3, 1.8), xticks=[0, 4, 8, 12, 15])
    ax.legend(fontsize=10, ncol=2, loc="upper right")
    ax = axes[1]
    f, C = d["leakage"]
    ax.stem(f, np.abs(C), basefmt=" ")
    ax.axvline(1062.5, color=NARANJA, linestyle="--", label="Tono original: 1062.5 Hz")
    ax.set(title="B. Leakage: un solo tono original\nVarios bins en un bloque de 64 muestras", xlabel="Frecuencia (Hz)", ylabel="Magnitud", xlim=(250, 1875), ylim=(-0.03, 1.15), xticks=[500, 1000, 1500])
    ax.legend(fontsize=11, loc="upper right")
    for ax in axes:
        ax.grid(alpha=0.2)
    return fig


def figura_fft():
    d = datos_fft()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    f64, C64 = d["sin_padding"]
    f512, C512 = d["con_padding"]
    axes[0, 0].stem(f64, np.abs(C64), basefmt=" ")
    axes[0, 0].set(title="A. 64 datos, FFT de 64 puntos\n8 ms observados; bins cada 125 Hz", xlabel="Frecuencia (Hz)", ylabel="Magnitud", xlim=(700, 1450), ylim=(-0.03, 1.15), xticks=[750, 1000, 1250])
    axes[0, 1].plot(f512, np.abs(C512), ".-", color=AZUL, label="FFT de 512 puntos")
    axes[0, 1].plot(f64, np.abs(C64), "s", color=NARANJA, markerfacecolor="none", markersize=8, label="Bins del panel A")
    axes[0, 1].set(title="B. Los mismos 64 datos + 448 ceros\n8 ms observados; bins cada 15.625 Hz", xlabel="Frecuencia (Hz)", ylabel="Magnitud", xlim=(700, 1450), ylim=(-0.03, 1.15), xticks=[750, 1000, 1250])
    axes[0, 1].legend(fontsize=11, loc="upper right")
    ax = axes[1, 0]
    for nombre, color, etiqueta in [("rectangular", AZUL, "Rectangular"), ("hann", NARANJA, "Hann periódica")]:
        f, C = d[nombre]
        db = 20 * np.log10(np.maximum(np.abs(C), 1e-6))
        ax.plot(f, db, color=color, label=etiqueta)
    ax.set(title="C. Mismos datos, distinta ventana\nTono de 1062.5 Hz; FFT de 4096 puntos", xlabel="Frecuencia (Hz)", ylabel="dB relativos a magnitud 1", xlim=(500, 1650), ylim=(-65, 3), xticks=[500, 1000, 1500])
    ax.legend(fontsize=11, loc="lower center")
    ax = axes[1, 1]
    for n, color in [(64, AZUL), (512, NARANJA)]:
        f, C = d["pares"][n]
        ax.plot(f, np.abs(C), color=color, label=f"{n} datos: {n / d['fs'] * 1000:g} ms")
    for frecuencia in [1000, 1062.5]:
        ax.axvline(frecuencia, color=GRIS, linestyle="--", alpha=0.7)
    ax.set(title="D. Dos tonos: 1000 y 1062.5 Hz\nMás datos; Hann y FFT de 8192 en ambos", xlabel="Frecuencia (Hz)", ylabel="Magnitud", xlim=(850, 1250), ylim=(-0.03, 1.55), xticks=[900, 1000, 1100, 1200])
    ax.legend(fontsize=11, loc="upper right")
    for ax in [axes[0, 0], axes[0, 1], axes[1, 0]]:
        ax.axvline(1062.5, color=GRIS, linestyle="--", alpha=0.7)
    for ax in axes.flat:
        ax.grid(alpha=0.2)
    return fig


def figura_rf():
    d = datos_rf()
    fig, axes = plt.subplots(3, 1, figsize=(12, 8.5), layout="constrained")
    f, C = d["entrada"]
    tallos(axes[0], f, C)
    axes[0].set(title="A. Entrada en baseband: referencia RF de 99.1 MHz", xlabel="Frecuencia en baseband (kHz)", ylabel="Magnitud", xlim=(-1200, 1200), ylim=(-0.03, 1.25), xticks=[-1000, -600, -400, 0, 400, 1000])
    tallos(axes[1], f, C, escala=1e6, referencia=d["fc"])
    axes[1].set(title="B. Mismas muestras y FFT: solo se cambia el eje a RF", xlabel="Frecuencia RF (MHz)", ylabel="Magnitud", xlim=(97.9, 100.3), ylim=(-0.03, 1.25), xticks=[97.9, 98.5, 99.1, 99.5, 100.3])
    tallos(axes[2], *d["salida"], color=VERDE)
    axes[2].set(title="C. Mezcla de -400 kHz: nuevo cero RF en 99.5 MHz", xlabel="Frecuencia en baseband de la salida (kHz)", ylabel="Magnitud", xlim=(-1200, 1200), ylim=(-0.03, 1.25), xticks=[-1000, -600, -400, 0, 400, 1000])
    for ax, posiciones in [(axes[0], d["posiciones"]), (axes[2], d["posiciones"] + d["f_mix"])]:
        for posicion, amplitud, rf in zip(posiciones, d["amplitudes"], (d["fc"] + d["posiciones"]) / 1e6):
            ax.text(posicion / 1000, amplitud + 0.07, f"{rf:g} MHz", ha="center", fontsize=12)
        ax.axvline(0, color=GRIS, linestyle="--")
    axes[1].axvline(d["fc"] / 1e6, color=GRIS, linestyle="--")
    for ax in axes:
        ax.grid(alpha=0.2)
    return fig


def generar(salida: Path = OUT) -> list[Path]:
    salida.mkdir(parents=True, exist_ok=True)
    paths = []
    estilo = {"font.size": 12, "axes.titlesize": 13, "axes.spines.top": False, "axes.spines.right": False}
    with plt.rc_context(estilo):
        for nombre, construir in zip(NOMBRES, [figura_muestras, figura_ambiguedad, figura_fft, figura_rf]):
            fig = construir()
            path = salida / nombre
            fig.savefig(path, dpi=180, facecolor="white")
            plt.close(fig)
            paths.append(path)
    return paths


if __name__ == "__main__":
    for archivo in generar():
        print(archivo)

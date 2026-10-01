"""Figuras reproducibles de la sesión 3; no necesita hardware ni grabaciones."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

OUT = Path(__file__).resolve().parent
AZUL, NARANJA, VERDE = "#2563eb", "#ea580c", "#15803d"


def datos_tonos():
    fs, N, descarte = 24000, 4800, 256
    n = np.arange(N + descarte)
    x = np.exp(1j * 2 * np.pi * 1000 * n / fs) + 0.6 * np.exp(1j * 2 * np.pi * 9000 * n / fs)
    h_media = np.ones(3) / 3
    h_lp = signal.firwin(65, 3000, fs=fs)
    y_media = signal.lfilter(h_media, [1.0], x)
    y_lp = signal.lfilter(h_lp, [1.0], x)
    return fs, x[descarte:], y_media[descarte:], y_lp[descarte:], h_media, h_lp


def espectro(z, fs):
    return np.fft.fftshift(np.fft.fftfreq(len(z), 1 / fs)), np.abs(np.fft.fftshift(np.fft.fft(z)) / len(z))


def preparar_eje(ax, titulo, xlabel="Índice n", ylabel="Valor de la muestra"):
    ax.set(title=titulo, xlabel=xlabel, ylabel=ylabel)
    ax.grid(True, alpha=0.25)


def generar(salida=OUT):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    rutas = []

    def guardar(fig, nombre):
        ruta = salida / nombre
        fig.savefig(ruta, dpi=180, facecolor="white", bbox_inches="tight")
        plt.close(fig)
        rutas.append(ruta)

    with plt.rc_context({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}):
        x = np.array([0, 1, 2, 1, 0, -1, 0, 0], dtype=float)
        n = np.arange(len(x))
        retrasada = np.concatenate([np.zeros(2), x])[:len(x)]
        fig, axs = plt.subplots(1, 3, figsize=(13, 3.8), layout="constrained", sharex=True, sharey=True)
        for ax, z, titulo in zip(axs, [x, 2 * x, retrasada], ["A. Entrada x[n]", "B. Ganancia: 2x[n]", "C. Retardo: x[n − 2]"]):
            ax.stem(n, z, basefmt=" ")
            preparar_eje(ax, titulo)
            ax.set(xticks=n, ylim=(-2.6, 4.6))
        axs[0].text(0.2, 3.9, "Máximo en n = 2")
        axs[1].text(0.2, 3.9, "Mismo índice; doble valor")
        axs[2].text(0.2, 3.9, "Máximo ahora en n = 4")
        guardar(fig, "sistema-ganancia-retardo.png")

        x = np.array([0, 0, 3, 6, 3, 0, 0, 0], dtype=float)
        h = np.ones(3) / 3
        y = np.convolve(x, h, mode="full")
        fig, axs = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
        axs[0].stem(np.arange(len(x)), x, basefmt=" ")
        axs[0].scatter([2, 3, 4], x[[2, 3, 4]], s=100, facecolors="none", edgecolors=NARANJA, linewidths=2, zorder=3)
        preparar_eje(axs[0], "A. Muestras que aportan a y[4]")
        axs[0].set(xticks=np.arange(len(x)), ylim=(-0.4, 7.2))
        axs[0].text(0.1, 6.5, "Se usan x[4], x[3] y x[2]")
        axs[1].bar([0, 1, 2], [1, 2, 1], color=NARANJA)
        preparar_eje(axs[1], "B. Cada muestra multiplicada por 1/3", "Término de la suma", "Contribución")
        axs[1].set(xticks=[0, 1, 2], xticklabels=["x[4]/3", "x[3]/3", "x[2]/3"], ylim=(0, 3.2))
        axs[1].text(0, 2.7, "1 + 2 + 1 = 4")
        axs[2].stem(np.arange(len(y)), y, basefmt=" ")
        axs[2].scatter([4], [y[4]], s=100, color=NARANJA, zorder=3)
        preparar_eje(axs[2], "C. Salida del FIR")
        axs[2].set(xticks=np.arange(len(y)), ylim=(-0.4, 5.5))
        axs[2].text(4.4, 4.2, "y[4] = 4")
        guardar(fig, "fir-suma-muestras.png")

        impulso = np.zeros(8)
        impulso[0] = 1
        respuesta = signal.lfilter(h, [1.0], impulso)
        fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), layout="constrained", sharex=True)
        for ax, z, titulo in zip(axs, [impulso, respuesta], ["A. Entrada: impulso δ[n]", "B. Salida: respuesta h[n]"]):
            ax.stem(np.arange(len(z)), z, basefmt=" ")
            preparar_eje(ax, titulo)
            ax.set(xticks=np.arange(len(z)), ylim=(-0.08, 1.2))
        axs[1].text(0.4, 0.7, "Tres valores no nulos: 1/3, 1/3, 1/3")
        guardar(fig, "fir-respuesta-impulso.png")

        fs, x, y_media, y_lp, h_media, h_lp = datos_tonos()
        f, X = espectro(x, fs)
        _, Y = espectro(y_media, fs)
        f_resp = np.linspace(-fs / 2, fs / 2, 4097)
        _, H_media = signal.freqz(h_media, worN=f_resp, fs=fs)
        _, H_lp = signal.freqz(h_lp, worN=f_resp, fs=fs)
        _, ganancias = signal.freqz(h_media, worN=np.array([1000, 9000]), fs=fs)
        fig, axs = plt.subplots(1, 3, figsize=(13, 4), layout="constrained", sharex=True)
        axs[0].plot(f / 1000, X, color=AZUL)
        axs[1].plot(f_resp / 1000, np.abs(H_media), color=NARANJA)
        axs[1].scatter([1, 9], np.abs(ganancias), color="black", zorder=3)
        axs[2].plot(f / 1000, Y, color=NARANJA)
        for ax, titulo, ylabel in zip(axs, ["A. Espectro de la entrada", "B. Respuesta del filtro de 3 taps", "C. Espectro de la salida"], ["Magnitud |X| / N", "Ganancia |H(f)|", "Magnitud |Y| / N"]):
            preparar_eje(ax, titulo, "Frecuencia (kHz)", ylabel)
            ax.set(xlim=(-12, 12), ylim=(-0.02, 1.2), xticks=[-12, -9, -3, 0, 1, 3, 9, 12])
        axs[0].text(-11, 1.08, "Amplitudes: 1 y 0.6")
        axs[1].text(-11, 1.08, "|H(1 kHz)| = 0.977")
        axs[1].text(-11, 0.82, "|H(9 kHz)| = 0.138")
        axs[2].text(-11, 1.08, "Salida: 0.977 y 0.083")
        guardar(fig, "fir-respuesta-frecuencia.png")

        _, Y_lp = espectro(y_lp, fs)
        fig, axs = plt.subplots(2, 2, figsize=(12, 7), layout="constrained", sharex=True)
        axs[0, 0].plot(f_resp / 1000, np.abs(H_media), color=NARANJA)
        axs[0, 1].plot(f_resp / 1000, np.abs(H_lp), color=VERDE)
        axs[0, 1].axvline(3, color="gray", linestyle="--", alpha=0.7)
        axs[0, 1].axvline(-3, color="gray", linestyle="--", alpha=0.7)
        axs[0, 1].text(3.4, 0.65, "Cutoff nominal: ±3 kHz\n|H| ≈ 0.5 en el borde")
        for ax, valores, color in [(axs[1, 0], Y, NARANJA), (axs[1, 1], Y_lp, VERDE)]:
            ax.plot(f / 1000, X, color=AZUL, alpha=0.55, linewidth=3, label="Entrada")
            ax.plot(f / 1000, valores, color=color, label="Salida")
            ax.legend(loc="upper left")
        for ax, titulo in zip(axs.flat, ["A. Moving average: 3 taps", "B. Low-pass preparado: 65 taps", "C. Espectros con moving average", "D. Espectros con low-pass"]):
            preparar_eje(ax, titulo, "Frecuencia (kHz)", "Ganancia |H(f)|" if ax in axs[0] else "Magnitud FFT / N")
            ax.set(xlim=(-12, 12), ylim=(-0.02, 1.18), xticks=[-12, -9, -3, 0, 1, 3, 9, 12])
        axs[1, 0].text(2.3, 0.82, "Tono a 9 kHz:\n0.6 → 0.08284")
        axs[1, 1].text(2.3, 0.82, "Tono a 9 kHz:\n0.6 → 0.0002323")
        guardar(fig, "fir-comparacion-lowpass.png")

        fig, axs = plt.subplots(1, 3, figsize=(13, 3.5), layout="constrained")
        textos = [
            ("1. Entrada", "x[4] = 3\nx[3] = 6\nx[2] = 3\n\nCada una es una muestra."),
            ("2. Operación FIR", "h = [1/3, 1/3, 1/3]\n\ny[4] = (3 + 6 + 3)/3\n\nSe pondera y se suma."),
            ("3. Salida", "y[4] = 4\n\nUn valor nuevo, calculado.\nNo es una nueva adquisición.\nEl sampling rate se conserva."),
        ]
        for ax, (titulo, contenido), color in zip(axs, textos, [AZUL, NARANJA, VERDE]):
            ax.set_axis_off()
            ax.text(0.04, 0.93, titulo, va="top", fontsize=15, weight="bold", color=color)
            ax.text(0.04, 0.72, contenido, va="top", fontsize=12, linespacing=1.8, bbox={"boxstyle": "round,pad=0.8", "facecolor": color + "12", "edgecolor": color})
        guardar(fig, "sintesis-sistema-fir.png")
    return rutas


if __name__ == "__main__":
    for ruta in generar():
        print(ruta)

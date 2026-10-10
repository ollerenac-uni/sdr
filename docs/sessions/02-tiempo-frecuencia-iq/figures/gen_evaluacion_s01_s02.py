#!/usr/bin/env python3
"""Estímulos visuales originales para evaluación de S01/S02, sin clave de respuestas.

La salida debe indicarse expresamente; no se añaden figuras a la lección.
Uso: python3 docs/sessions/02-tiempo-frecuencia-iq/figures/gen_evaluacion_s01_s02.py --salida DIRECTORIO_PRIVADO
"""

import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

BLUE = "#1764ab"
ORANGE = "#c45300"
GRAY = "#475569"


def base(titulo):
    fig, ax = plt.subplots(figsize=(12.8, 7.2), layout="constrained")
    ax.set_title(titulo, pad=18)
    return fig, ax


def caja(ax, x, y, texto, ancho=0.17, alto=0.15):
    ax.add_patch(plt.Rectangle((x - ancho / 2, y - alto / 2), ancho, alto, facecolor="#edf4fc", edgecolor=BLUE, linewidth=2))
    ax.text(x, y, texto, ha="center", va="center", fontsize=18)


def flecha(ax, inicio, fin):
    ax.annotate("", xy=fin, xytext=inicio, arrowprops={"arrowstyle": "->", "lw": 2.5, "color": GRAY})


def cadena():
    fig, ax = base("Receptor Low-IF: recorrido de la señal")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    posiciones = [0.10, 0.30, 0.50, 0.70, 0.90]
    for x, texto in zip(posiciones, ["Antena", "Tuner", "ADC", "Procesamiento\ndigital", "Computador"]):
        caja(ax, x, 0.5, texto)
    for a, b in zip(posiciones[:-1], posiciones[1:]):
        flecha(ax, (a + 0.085, 0.5), (b - 0.085, 0.5))
    ax.text(0.5, 0.24, "Diagrama funcional simplificado", ha="center", color=GRAY)
    return fig


def banda():
    fig, ax = base("Intervalo nominal de una captura compleja")
    ax.axvspan(-1.2, 1.2, color=BLUE, alpha=0.18)
    ax.axhline(0, color=GRAY)
    ax.axvline(0, color=GRAY, linestyle="--")
    ax.plot(-1.2, 0, "o", color=BLUE, markersize=13)
    ax.plot(1.2, 0, "o", markerfacecolor="white", markeredgecolor=BLUE, markersize=13, markeredgewidth=2)
    ax.set(xlim=(-1.5, 1.5), ylim=(-0.1, 1), xticks=[-1.2, -0.6, 0, 0.6, 1.2], yticks=[], xlabel="Frecuencia en baseband (MHz)")
    ax.text(0, 0.6, "La zona sombreada es el intervalo representado", ha="center")
    ax.text(0, 0.4, "Punto abierto: extremo no incluido", ha="center", color=GRAY)
    return fig


def recorte():
    fig, ax = base("Entrada amplificada y salida de una etapa limitada")
    t = np.linspace(0, 2, 600)
    entrada = 1.6 * np.sin(2 * np.pi * t)
    salida = np.clip(entrada, -1, 1)
    ax.plot(t, entrada, "--", color=BLUE, linewidth=2, label="Entrada amplificada")
    ax.plot(t, salida, color=ORANGE, linewidth=4, label="Salida")
    ax.axhline(1, color=GRAY, linestyle=":")
    ax.axhline(-1, color=GRAY, linestyle=":")
    ax.set(xlabel="Tiempo (ms)", ylabel="Amplitud normalizada", ylim=(-1.9, 1.9))
    ax.legend(loc="upper right")
    ax.grid(alpha=0.2)
    return fig


def bytes_cu8():
    fig, ax = base("Fragmento de CU8: direcciones y valores decimales")
    ax.axis("off")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.add_patch(plt.Rectangle((0.06, 0.42), 0.88, 0.15, facecolor="#ffedc3", edgecolor=ORANGE))
    for y, texto in [(0.82, "Byte inicial    I       Q"), (0.67, "0000014       147     226"), (0.50, "0000016       128     228"), (0.33, "0000018       108     226")]:
        ax.text(0.5, y, texto, fontfamily="DejaVu Sans Mono", fontsize=29, ha="center", va="center")
    ax.text(0.5, 0.12, "La primera muestra del archivo tiene índice n = 0", ha="center")
    return fig


def plano_iq():
    fig, ax = base("Una muestra compleja")
    ax.axhline(0, color=GRAY)
    ax.axvline(0, color=GRAY)
    flecha(ax, (0, 0), (3, 4))
    ax.plot(3, 4, "o", color=BLUE, markersize=12)
    ax.plot([3, 3, 0], [0, 4, 4], "--", color=BLUE, alpha=0.6)
    ax.set(xlabel="I", ylabel="Q", xlim=(-1, 5), ylim=(-1, 5), xticks=np.arange(-1, 6), yticks=np.arange(-1, 6), aspect="equal")
    ax.grid(alpha=0.2)
    return fig


def giro():
    fig, ax = base("Orden de cuatro muestras consecutivas; fs = 8000 S/s")
    theta = np.linspace(0, 2 * np.pi, 300)
    z = np.exp(-1j * np.pi / 2 * np.arange(4))
    ax.plot(np.cos(theta), np.sin(theta), color="lightgray")
    ax.axhline(0, color=GRAY, alpha=0.5)
    ax.axvline(0, color=GRAY, alpha=0.5)
    for n, valor in enumerate(z):
        flecha(ax, (0, 0), (valor.real, valor.imag))
        ax.plot(valor.real, valor.imag, "o", color=BLUE, markersize=10)
        ax.text(1.22 * valor.real, 1.22 * valor.imag, f"n={n}", ha="center", va="center")
    ax.set(xlabel="I", ylabel="Q", xlim=(-1.55, 1.55), ylim=(-1.55, 1.55), aspect="equal", xticks=[-1, 0, 1], yticks=[-1, 0, 1])
    return fig


def espectro(z, fs=8000, m=None, w=None):
    w = np.ones(len(z)) if w is None else w
    m = len(z) if m is None else m
    return np.fft.fftshift(np.fft.fftfreq(m, 1 / fs)), np.fft.fftshift(np.fft.fft(z * w, m)) / w.sum()


def dos_espectros():
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.2), layout="constrained")
    n = np.arange(64)
    for ax, letra, z in zip(axes, "AB", [np.exp(2j * np.pi * 1000 * n / 8000), np.cos(2 * np.pi * 1000 * n / 8000)]):
        f, C = espectro(z)
        presentes = np.abs(C) > 1e-10
        ax.stem(f[presentes] / 1000, np.abs(C[presentes]), basefmt=" ")
        ax.set(title=f"Panel {letra}", xlabel="Frecuencia (kHz)", ylabel="Magnitud = |FFT| / N", xlim=(-2, 2), ylim=(0, 1.2), xticks=[-2, -1, 0, 1, 2], yticks=[0, 0.5, 1])
        ax.grid(alpha=0.2)
    fig.suptitle("Tonos alineados con bins; ventana rectangular", fontsize=22)
    return fig


def leakage():
    fig, ax = base("Entrada: un tono complejo de 1062.5 Hz")
    f, C = espectro(np.exp(2j * np.pi * 1062.5 * np.arange(64) / 8000))
    ax.stem(f, abs(C), basefmt=" ")
    ax.axvline(1062.5, color=ORANGE, linestyle="--", label="Frecuencia generada")
    ax.set(xlabel="Frecuencia de prueba (Hz)", ylabel="Magnitud", xlim=(250, 1875), ylim=(0, 1.05))
    ax.legend()
    ax.text(0.03, 0.92, "N = 64; fs = 8000 S/s\nVentana rectangular", transform=ax.transAxes)
    ax.grid(alpha=0.2)
    return fig


def padding():
    fig, axes = plt.subplots(2, 1, figsize=(12.8, 7.2), layout="constrained")
    for ax, letra, m in zip(axes, "AB", [64, 512]):
        ax.barh(0, 64, height=0.55, color=BLUE, label="64 muestras adquiridas")
        if m > 64:
            ax.barh(0, m - 64, left=64, height=0.55, color="white", edgecolor=ORANGE, hatch="///", label="448 ceros añadidos")
        ax.set(title=f"Panel {letra}: entrada a una FFT de {m} puntos", xlim=(0, 540), ylim=(-0.8, 1.3), xlabel="Posición en el arreglo de cálculo", yticks=[], xticks=[0, 64, 256, 512])
        ax.legend(loc="upper right", fontsize=16)
    fig.suptitle("Las muestras adquiridas tienen fs = 8000 S/s", fontsize=22)
    return fig


def ventanas():
    fig, ax = base("El mismo tono de 1 kHz; N = 64 y fs = 8000 S/s")
    z = np.exp(2j * np.pi * 1000 * np.arange(64) / 8000)
    for nombre, w, color in [("Rectangular", np.ones(64), BLUE), ("Hann", np.hanning(65)[:-1], ORANGE)]:
        f, C = espectro(z, m=16384, w=w)
        ax.plot(f, 20 * np.log10(np.maximum(abs(C), 1e-6)), label=nombre, color=color, linewidth=2.5)
    ax.set(xlabel="Frecuencia (Hz)", ylabel="Magnitud (dB respecto a 1)", xlim=(500, 1500), ylim=(-65, 4))
    ax.legend()
    ax.grid(alpha=0.2)
    return fig


def duracion():
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.2), layout="constrained")
    for ax, letra, n in zip(axes, "AB", [64, 512]):
        t = np.arange(n) / 8000
        z = np.exp(2j * np.pi * 1000 * t) + np.exp(2j * np.pi * 1062.5 * t)
        f, C = espectro(z, m=16384, w=np.hanning(n + 1)[:-1])
        ax.plot(f, abs(C), color=BLUE, linewidth=3)
        for tono in [1000, 1062.5]:
            ax.axvline(tono, color=ORANGE, linestyle="--")
        ax.set(title=f"Panel {letra}: N = {n} muestras", xlabel="Frecuencia (Hz)", ylabel="Magnitud", xlim=(900, 1160), ylim=(0, 1.5), xticks=[900, 1000, 1100])
        ax.grid(alpha=0.2)
    fig.suptitle("Ambos: fs = 8000 S/s; Hann; FFT de 16384 puntos", fontsize=21)
    return fig


def waterfall():
    fig, ax = base("Waterfall sintético: escala de color fija")
    t = np.arange(20) * 0.25
    f = np.linspace(-1000, 1000, 200, endpoint=False)
    rng = np.random.default_rng(20261010)
    potencia = 0.001 + rng.uniform(0, 0.001, (20, 200))
    mascara = ((t >= 2) & (t < 3))[:, None] & ((f >= 300) & (f < 500))[None, :]
    potencia[mascara] += 1
    im = ax.pcolormesh(np.r_[f, 1000], np.r_[t, 5], 10 * np.log10(potencia), cmap="cividis", vmin=-35, vmax=0, shading="flat")
    ax.set(xlabel="Frecuencia en baseband (Hz)", ylabel="Tiempo (s)", ylim=(5, 0), yticks=np.arange(6))
    ax.annotate("Franja señalada", xy=(500, 2.5), xytext=(-750, 1.5), color="white", arrowprops={"arrowstyle": "->", "color": "white"})
    fig.colorbar(im, ax=ax, label="Potencia relativa (dB)")
    return fig


def throttle():
    fig, ax = base("Ruta de lectura del archivo CU8")
    ax.axis("off")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    for x, nombre in [(0.16, "File Source\nByte"), (0.5, "Throttle\nByte\nTasa: ?"), (0.84, "Reconstrucción\nI/Q")]:
        caja(ax, x, 0.55, nombre, ancho=0.27, alto=0.30)
    flecha(ax, (0.295, 0.55), (0.365, 0.55))
    flecha(ax, (0.635, 0.55), (0.705, 0.55))
    ax.text(0.5, 0.2, "Salida reconstruida: 2.4 millones de muestras complejas/s", ha="center", fontsize=21)
    ax.text(0.5, 0.08, "Cada muestra compleja procede de dos bytes: I y Q", ha="center")
    return fig


def ramas():
    fig, ax = base("Dos rutas desde las mismas muestras complejas")
    ax.axis("off")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    caja(ax, 0.14, 0.5, "Muestras\nI/Q", ancho=0.20, alto=0.18)
    caja(ax, 0.61, 0.76, "FFT → magnitud", ancho=0.43, alto=0.18)
    caja(ax, 0.61, 0.27, "Selección de canal\nSecuencia compleja I/Q", ancho=0.43, alto=0.18)
    flecha(ax, (0.24, 0.5), (0.395, 0.76))
    flecha(ax, (0.24, 0.5), (0.395, 0.27))
    ax.text(0.91, 0.76, "A", ha="center", va="center", fontsize=36)
    ax.text(0.91, 0.27, "B", ha="center", va="center", fontsize=36)
    return fig


def lienzo(titulo):
    fig, ax = base(titulo)
    ax.axis("off")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    return fig, ax


def cadena_datos(titulo, textos, nota=""):
    fig, ax = lienzo(titulo)
    posiciones = np.linspace(0.17, 0.83, len(textos))
    ancho = min(0.27, 0.78 / len(textos))
    for x, texto in zip(posiciones, textos):
        caja(ax, x, 0.54, texto, ancho=ancho, alto=0.30)
    for a, b in zip(posiciones[:-1], posiciones[1:]):
        flecha(ax, (a + ancho / 2, 0.54), (b - ancho / 2, 0.54))
    if nota:
        ax.text(0.5, 0.18, nota, ha="center", va="center", fontsize=22, color=GRAY)
    return fig


def equipo_sdr():
    fig, ax = lienzo("Equipo utilizado en el curso")
    ax.plot([0.13, 0.13], [0.32, 0.74], color=BLUE, linewidth=5)
    ax.plot([0.04, 0.13, 0.22], [0.72, 0.55, 0.72], color=BLUE, linewidth=5)
    caja(ax, 0.45, 0.51, "RTL-SDR", ancho=0.23, alto=0.16)
    ax.add_patch(plt.Rectangle((0.69, 0.34), 0.27, 0.35, fill=False, edgecolor=BLUE, linewidth=4))
    ax.text(0.825, 0.515, "Computador", ha="center", fontsize=19)
    ax.plot([0.68, 0.97], [0.30, 0.30], color=BLUE, linewidth=6)
    ax.plot([0.13, 0.13, 0.335], [0.32, 0.25, 0.43], color=GRAY, linewidth=2)
    ax.plot([0.565, 0.69], [0.51, 0.51], color=GRAY, linewidth=2)
    ax.text(0.13, 0.84, "Antena", ha="center")
    ax.text(0.5, 0.08, "Antena, dongle y computador: ¿qué caracteriza al conjunto?", ha="center", color=GRAY)
    return fig


def dongle():
    fig, ax = lienzo("Dongle RTL-SDR del curso")
    ax.add_patch(plt.Rectangle((0.22, 0.32), 0.53, 0.30, facecolor="#edf4fc", edgecolor=BLUE, linewidth=4))
    ax.add_patch(plt.Rectangle((0.75, 0.40), 0.14, 0.14, facecolor="#dce2e8", edgecolor=GRAY, linewidth=3))
    ax.add_patch(plt.Rectangle((0.13, 0.42), 0.09, 0.10, facecolor="#ffe7ba", edgecolor=ORANGE, linewidth=3))
    ax.text(0.485, 0.50, "RTL-SDR", ha="center", va="center", fontsize=34, color=BLUE)
    ax.text(0.485, 0.38, "RTL2832U", ha="center", fontsize=20)
    ax.text(0.16, 0.72, "Conector\nde antena", ha="center")
    ax.text(0.82, 0.72, "USB", ha="center")
    ax.text(0.5, 0.12, "Esquema del dispositivo, no una fotografía", ha="center", color=GRAY)
    return fig


def entrada_adc():
    return cadena_datos("Entrada al ADC en la arquitectura Low-IF", ["Tuner", "Señal\n¿?", "ADC"], "¿Qué tipo de señal llega a esta etapa?")


def orden_cu8():
    fig, ax = lienzo("Dos muestras complejas guardadas en CU8")
    for k, x in enumerate(np.linspace(0.17, 0.83, 4)):
        caja(ax, x, 0.50, "?", ancho=0.18, alto=0.22)
        ax.text(x, 0.73, f"Byte {k}", ha="center")
    flecha(ax, (0.09, 0.25), (0.91, 0.25))
    ax.text(0.5, 0.13, "Orden de lectura del archivo", ha="center", color=GRAY)
    return fig


def cero_baseband():
    fig, ax = base("Captura: frecuencia central = 99.1 MHz")
    ax.axhline(0, color=GRAY, linewidth=2)
    ax.axvline(0, color=BLUE, linestyle="--", linewidth=2)
    ax.plot(0, 0, "o", color=BLUE, markersize=14)
    ax.text(0, 0.55, "RF en este punto: ?", ha="center", fontsize=25)
    ax.set(xlabel="Desplazamiento en baseband (kHz)", xlim=(-600, 600), ylim=(-0.2, 1), xticks=[-400, 0, 400], yticks=[])
    return fig


def metadatos():
    fig, ax = lienzo("Una captura y sus datos de adquisición")
    caja(ax, 0.24, 0.51, "captura.cu8\nValores I/Q", ancho=0.34, alto=0.38)
    caja(ax, 0.74, 0.51, "fs = 2.4 MS/s\nfc = 99.1 MHz", ancho=0.36, alto=0.38)
    ax.text(0.24, 0.79, "Archivo", ha="center", color=BLUE)
    ax.text(0.74, 0.79, "Metadatos", ha="center", color=BLUE)
    ax.text(0.5, 0.12, "¿Por qué se conservan ambos?", ha="center", fontsize=25)
    return fig


def ocho_bits():
    fig, ax = lienzo("Un dato de 8 bits")
    for k, x in enumerate(np.linspace(0.10, 0.90, 8)):
        caja(ax, x, 0.52, "0 / 1", ancho=0.095, alto=0.17)
        ax.text(x, 0.72, f"b{7-k}", ha="center", color=GRAY)
    ax.text(0.5, 0.22, "¿Cuántos códigos distintos se pueden formar?", ha="center", fontsize=25)
    return fig


def contar_muestras():
    fig, ax = base("Sampling rate: 32 kS/s")
    ax.axhspan(0.1, 0.75, xmin=0.0833, xmax=0.9167, color=BLUE, alpha=0.12)
    ax.annotate("", xy=(1, 0.45), xytext=(0, 0.45), arrowprops={"arrowstyle": "|-|", "lw": 3, "color": BLUE})
    ax.text(0.5, 0.60, "N = ? muestras complejas", ha="center", fontsize=25)
    ax.set(xlim=(-0.1, 1.1), ylim=(0, 1), xticks=[0, 1], yticks=[], xlabel="Tiempo (ms)")
    return fig


def duracion_archivo():
    return cadena_datos("Duración de un archivo CU8", ["Archivo\n6400 bytes", "fs\n32 kS/s", "Duración\nT = ?"], "Se pide el tiempo representado por el archivo.")


def separacion_bins():
    fig, ax = base("FFT de 1024 muestras; fs = 32 kS/s; sin padding")
    ax.stem([0, 1, 2, 3], [0.4, 0.85, 0.58, 0.25], basefmt=" ")
    ax.annotate("", xy=(2, 1.05), xytext=(1, 1.05), arrowprops={"arrowstyle": "<->", "color": ORANGE, "lw": 3})
    ax.text(1.5, 1.13, "Separación = ? Hz", ha="center", fontsize=25, color=ORANGE)
    ax.set(xlim=(-0.5, 3.5), ylim=(0, 1.5), xticks=[0, 1, 2, 3], xticklabels=["k", "k + 1", "k + 2", "k + 3"], yticks=[], xlabel="Bins consecutivos", ylabel="Magnitud ilustrativa")
    return fig


def visores():
    fig, ax = lienzo("Dos visores en el mismo flowgraph")
    caja(ax, 0.16, 0.50, "Muestras\nI/Q", ancho=0.22, alto=0.22)
    caja(ax, 0.67, 0.75, "Time Sink\nNumber of Points: cambia", ancho=0.51, alto=0.24)
    caja(ax, 0.67, 0.28, "Frequency Sink\nFFT Size: fijo", ancho=0.51, alto=0.24)
    flecha(ax, (0.27, 0.50), (0.415, 0.75))
    flecha(ax, (0.27, 0.50), (0.415, 0.28))
    ax.text(0.5, 0.06, "El sampling rate permanece fijo.", ha="center", color=GRAY)
    return fig


def tasa_decimada():
    return cadena_datos("Cambio de sampling rate", ["Entrada\n2.4 MS/s", "Decimación\nD = 8", "Salida\nfs = ?"], "¿Qué tasa queda después de decimar?")


def banda_decimada():
    fig, ax = base("Contenido de una captura antes de decimar")
    ax.axvspan(-0.5, 0.5, color=BLUE, alpha=0.13, label="Banda que cabe a la nueva tasa")
    ax.stem([-0.85, -0.22, 0.20, 0.77], [0.7, 0.85, 0.5, 0.9], basefmt=" ")
    ax.set(xlim=(-1.1, 1.1), ylim=(0, 1.4), xticks=[], yticks=[], xlabel="Frecuencia en baseband", ylabel="Magnitud ilustrativa")
    ax.legend(loc="upper center", fontsize=19)
    return fig


def etiqueta_visor():
    return cadena_datos("Ajuste del visor al leer un archivo fijo", ["Archivo\nCU8", "Frequency Sink\nCenter Frequency\ncambia", "Resultado\n¿?"], "Solo se cambia un parámetro del visor.")


def prueba_fft():
    return cadena_datos("Una prueba de frecuencia de la FFT", ["Muestras\nx[n]", "Girar\nhacia atrás", "Sumar\npunta con cola"], "¿Para qué se aplica el giro antes de sumar?")


def bloque_fftshift():
    return cadena_datos("Después de calcular la FFT", ["Coeficientes\nX[k]", "fftshift", "Resultado\n¿?"], "¿Qué hace esta operación con los coeficientes?")


def intervalo_alias():
    fig, ax = base("Tono generado: +5 kHz; sampling rate: 8 kS/s")
    ax.axvspan(-4, 4, color=BLUE, alpha=0.13)
    ax.axhline(0, color=GRAY)
    ax.stem([5], [0.85], linefmt="C1-", markerfmt="C1o", basefmt=" ")
    ax.plot(-4, 0, "o", color=BLUE, markersize=11)
    ax.plot(4, 0, "o", markerfacecolor="white", markeredgecolor=BLUE, markersize=11, markeredgewidth=2)
    ax.text(0, 0.45, "¿Qué frecuencia del intervalo\nrepresenta este tono muestreado?", ha="center", fontsize=23)
    ax.set(xlim=(-5, 6), ylim=(-0.1, 1.2), xticks=[-4, -2, 0, 2, 4, 5], yticks=[], xlabel="Frecuencia (kHz)")
    return fig


def frecuencia_rf():
    fig, ax = base("Frecuencia central de la captura: 99.1 MHz")
    ax.axhline(0, color=GRAY)
    ax.axvline(0, color=GRAY, linestyle="--")
    ax.annotate("", xy=(400, 0.45), xytext=(0, 0.45), arrowprops={"arrowstyle": "->", "lw": 3, "color": BLUE})
    ax.text(200, 0.57, "+400 kHz", ha="center", color=BLUE, fontsize=28)
    ax.plot(400, 0, "o", color=BLUE, markersize=14)
    ax.text(400, 0.86, "RF de la banda: ?", ha="center", fontsize=25)
    ax.set(xlim=(-300, 800), ylim=(-0.15, 1.15), xticks=[0, 400], yticks=[], xlabel="Desplazamiento en baseband (kHz)")
    return fig


def promedio():
    return cadena_datos("Promedio espectral de varios bloques", ["FFT de\nvarios bloques", "Valores que\nse promedian\n¿?", "Resultado\nen dB"], "Se utiliza la misma normalización en todos los bloques.")


def fm_centrada():
    fig, ax = base("Una banda FM está centrada en 0 Hz")
    ax.axvspan(-1, 1, color=BLUE, alpha=0.16)
    ax.axvline(0, color=BLUE, linestyle="--", linewidth=2)
    ax.text(0, 0.65, "Banda FM", ha="center", fontsize=30, color=BLUE)
    ax.text(0, 0.32, "I[n] = ?       Q[n] = ?", ha="center", fontsize=28)
    ax.set(xlim=(-1.6, 1.6), ylim=(0, 1), xticks=[0], xticklabels=["0 Hz"], yticks=[], xlabel="Frecuencia en baseband")
    return fig


def tipo_archivo():
    return cadena_datos("Lectura de la captura del laboratorio", ["Archivo\n.cu8", "File Source\nTipo: ?", "Bloques\nposteriores"], "El tipo de lectura debe corresponder al formato del archivo.")


def normalizacion():
    fig, ax = lienzo("Conversión de una pareja CU8")
    for y, entrada, salida in [(0.70, "I = 255", "I = ?"), (0.30, "Q = 0", "Q = ?")]:
        caja(ax, 0.13, y, entrada, ancho=0.19, alto=0.18)
        caja(ax, 0.5, y, "(u − 127.5) / 127.5", ancho=0.40, alto=0.18)
        caja(ax, 0.87, y, salida, ancho=0.19, alto=0.18)
        flecha(ax, (0.225, y), (0.30, y))
        flecha(ax, (0.70, y), (0.775, y))
    ax.text(0.5, 0.08, "Muestra compleja de salida: I + jQ", ha="center", color=GRAY)
    return fig


def resampler():
    return cadena_datos("Rational Resampler del laboratorio FM", ["Entrada\n2.4 MS/s", "Interpolación\n/ decimación\n¿?", "Salida\n192 kS/s"], "Se busca la razón entre las dos tasas.")


def tasa_audio():
    return cadena_datos("De la señal I/Q al audio", ["Entrada\n192 kS/s", "WBFM Receive\nAudio\nDecimation = 4", "Audio Sink\nTasa: ?"], "¿Qué tasa debe usar el bloque de audio?")


def discriminador():
    return cadena_datos("Una etapa de la demodulación FM", ["Canal I/Q\nseleccionado\ny centrado", "Discriminador\nFM", "Medida de\nsalida: ?"], "¿Qué mide esta etapa a partir de las muestras?")


def contraste():
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 7.2), layout="constrained")
    f = np.linspace(-1000, 1000, 160, endpoint=False)
    t = np.arange(24) * 0.125
    rng = np.random.default_rng(40)
    db = -43 + rng.uniform(-3, 3, (len(t), len(f)))
    db[:, (f > 200) & (f < 400)] += 12
    for ax, titulo, limites in zip(axes, ["Vista A", "Vista B"], [(-80, 0), (-48, -25)]):
        im = ax.pcolormesh(np.r_[f, 1000], np.r_[t, 3], db, cmap="cividis", vmin=limites[0], vmax=limites[1], shading="flat")
        ax.set(title=titulo, xlabel="Baseband (Hz)", ylabel="Tiempo (s)", ylim=(3, 0), xticks=[-1000, 0, 1000])
        fig.colorbar(im, ax=ax, label="dB", shrink=0.8)
    fig.suptitle("Waterfall sintético: mismos datos, distinto contraste", fontsize=22)
    return fig


CONSTRUCTORES = {
    "q03-cadena.png": cadena, "q07-banda.png": banda, "q08-recorte.png": recorte,
    "q13-bytes.png": bytes_cu8, "q19-plano-iq.png": plano_iq, "q20-giro.png": giro,
    "q21-espectros.png": dos_espectros, "q25-leakage.png": leakage, "q26-padding.png": padding,
    "q27-ventanas.png": ventanas, "q28-duracion.png": duracion, "q31-waterfall.png": waterfall,
    "q35-throttle.png": throttle, "q39-ramas.png": ramas,
    "q01-equipo-sdr.png": equipo_sdr, "q02-dongle.png": dongle,
    "q04-entrada-adc.png": entrada_adc, "q05-orden-cu8.png": orden_cu8,
    "q06-cero-baseband.png": cero_baseband, "q09-metadatos.png": metadatos,
    "q10-ocho-bits.png": ocho_bits, "q11-contar-muestras.png": contar_muestras,
    "q12-duracion-archivo.png": duracion_archivo, "q14-separacion-bins.png": separacion_bins,
    "q15-visores.png": visores, "q16-tasa-decimada.png": tasa_decimada,
    "q17-banda-decimada.png": banda_decimada, "q18-etiqueta-visor.png": etiqueta_visor,
    "q22-prueba-fft.png": prueba_fft, "q23-fftshift.png": bloque_fftshift,
    "q24-intervalo-alias.png": intervalo_alias, "q29-frecuencia-rf.png": frecuencia_rf,
    "q30-promedio.png": promedio, "q32-fm-centrada.png": fm_centrada,
    "q33-tipo-archivo.png": tipo_archivo, "q34-normalizacion.png": normalizacion,
    "q36-resampler.png": resampler, "q37-tasa-audio.png": tasa_audio,
    "q38-discriminador.png": discriminador, "q40-contraste.png": contraste,
}


def generar(salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    paths = []
    with plt.rc_context({"font.size": 19, "axes.titlesize": 23, "axes.spines.top": False, "axes.spines.right": False}):
        for nombre, constructor in sorted(CONSTRUCTORES.items()):
            fig = constructor()
            fig.set_dpi(125)
            fig.canvas.draw()
            # Exportación RGB directa desde el gráfico, sin transparencia.
            pixeles = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            path = salida / nombre
            Image.fromarray(pixeles).save(path)
            plt.close(fig)
            paths.append(path)
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", required=True, type=Path)
    args = parser.parse_args()
    for path in generar(args.salida):
        print(path)

"""Genera referencias calculadas para el filtro RRC y sus conexiones."""

import argparse
from pathlib import Path
import struct
import zlib

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def coeficientes_rrc(sps=4, alpha=0.35, span=8):
    """RRC centrado, con suma de coeficientes igual a sps."""
    n = np.arange(span * sps + 1)
    u = (n - span * sps / 2) / sps
    h = np.empty_like(u)
    centro = np.isclose(u, 0)
    singular = np.isclose(np.abs(u), 1 / (4 * alpha))
    resto = ~(centro | singular)
    h[centro] = 1 + alpha * (4 / np.pi - 1)
    h[singular] = alpha / np.sqrt(2) * (
        (1 + 2 / np.pi) * np.sin(np.pi / (4 * alpha))
        + (1 - 2 / np.pi) * np.cos(np.pi / (4 * alpha))
    )
    v = u[resto]
    h[resto] = (np.sin(np.pi * v * (1 - alpha))
                + 4 * alpha * v * np.cos(np.pi * v * (1 + alpha))) / (
                    np.pi * v * (1 - (4 * alpha * v) ** 2))
    return (h * sps / h.sum()).astype(np.float32)


def datos_hola(sps=4, alpha=0.35, span=8):
    cuerpo = struct.pack("!H", 4) + b"Hola"
    paquete = cuerpo + struct.pack("!I", zlib.crc32(cuerpo))
    bits = np.unpackbits(np.frombuffer(paquete, dtype=np.uint8), bitorder="big")
    simbolos = (2 * bits.astype(int) - 1).astype(np.complex64)
    taps = coeficientes_rrc(sps, alpha, span)
    impulsos = np.zeros((len(simbolos) + span) * sps, dtype=np.complex64)
    impulsos[:len(simbolos) * sps:sps] = simbolos
    rrc = np.convolve(impulsos, taps)[:len(impulsos)]
    return taps, simbolos, np.repeat(simbolos, sps), rrc


def generar_senal(salida):
    taps, simbolos, rectangular, rrc = datos_hola()
    fig, axes = plt.subplots(3, 1, figsize=(12, 9.2))
    azul, rojo = "#1565c0", "#c62828"
    ax = axes[0]
    tiempos = np.arange(len(taps)) / 4
    ax.plot(tiempos, taps, "o-", color=azul, markersize=3)
    ax.axvline(4, color="#616161", ls="--", lw=1)
    ax.annotate("Centro del pulso: 4 ms", xy=(4, taps[16]), xytext=(5, .95),
                arrowprops={"arrowstyle": "->", "color": "#616161"}, fontsize=10)
    ax.set(title="Respuesta a un símbolo +1: 33 coeficientes, intervalo de 0.25 ms",
           xlabel="Tiempo desde el comienzo del pulso (ms)", ylabel="Coeficiente h[n]",
           xlim=(-.1, 8.1), ylim=(-.3, 1.3))
    for ax, muestras, titulo in zip(axes[1:], (rectangular, rrc), (
            "Hola, pulso rectangular: 320 muestras y 80 ms",
            "Hola, pulso RRC y cierre: 352 muestras y 88 ms")):
        t = np.arange(len(muestras)) / 4
        ax.plot(t, muestras.real, "o-", color=azul, markersize=1.8, lw=.9, label="I")
        ax.plot(t, muestras.imag, color=rojo, lw=1, label="Q = 0")
        ax.set(title=titulo, xlabel="Tiempo desde el comienzo del registro (ms)",
               ylabel="Valor normalizado", xlim=(-.5, 89), ylim=(-1.85, 1.85))
        ax.legend(loc="upper right", ncol=2, fontsize=9)
    axes[2].axvspan(80, 88, color="#90a4ae", alpha=.16)
    axes[2].text(84, -1.75, "Cierre", ha="center", fontsize=9)
    for ax in axes:
        ax.grid(alpha=.2)
        ax.axhline(0, color="#888888", lw=.6, zorder=0)
    fig.suptitle("Referencia calculada: Rₛ = 1000 símbolos/s, sps = 4, α = 0.35", fontsize=13)
    fig.text(.5, .017, "El RRC incluye retardo. La zona 80–88 ms corresponde a los ceros añadidos en su entrada; la salida conserva la cola del filtro.",
             ha="center", fontsize=9)
    fig.subplots_adjust(left=.09, right=.98, top=.90, bottom=.09, hspace=.63)
    archivo = salida / "enlace-41-pulso-rrc-hola.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar_conexiones(salida):
    fig, ax = plt.subplots(figsize=(15, 6.1))
    ax.set(xlim=(0, 16.4), ylim=(0, 6.6))
    ax.axis("off")
    azul, morado, gris = "#1565c0", "#7b1fa2", "#607d8b"

    def bloque(x, y, w, h, texto, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", ec=color, fc="white", lw=1.4))
        ax.text(x + w/2, y + h/2, texto, ha="center", va="center", fontsize=8.5)

    def flecha(puntos, color, mensaje=False):
        estilo = "--" if mensaje else "-"
        for p, q in zip(puntos[:-2], puntos[1:-1]):
            ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=1.4, ls=estilo)
        ax.add_patch(FancyArrowPatch(puntos[-2], puntos[-1], arrowstyle="-|>",
                    mutation_scale=12, color=color, lw=1.4, linestyle=estilo))

    bloque(.1, 2.7, 1.9, 1.3, "Chunks to Symbols\nID: mapeador\n80 símbolos", gris)
    bloque(3.3, 4.9, 6, .8, "Rama de símbolos existente: PDU, consola y constelación\n80 símbolos; 640 bytes", gris)
    bloque(3.3, 3.6, 6, .8, "Rama rectangular existente: Repeat y adaptadores\n320 muestras; 2560 bytes; 80 ms", gris)
    bloque(2.7, 1.55, 2.25, 1.35, "Burst Shaper\nID: cierre_rrc\n0 antes; 8 después\nWindow Taps = [1.0]", azul)
    bloque(5.35, 1.55, 2.6, 1.35, "Root Raised Cosine\nFilter\nID: pulso_rrc\nInterpolation = sps", azul)
    bloque(8.35, 1.55, 2.5, 1.35, "Tagged Stream Multiply\nLength Tag\nID: longitud_rrc\nLength Scalar = sps", azul)
    bloque(11.2, 1.55, 2.3, 1.35, "Tagged Stream to PDU\nID: rrc_a_pdu\nComplex; packet_len", azul)
    bloque(14, 2.05, 2.25, .9, "QT GUI Time Sink\nID: tiempo_rrc", azul)
    bloque(14, .65, 2.25, .9, "Message Debug\nID: debug_rrc\n2816 bytes", azul)
    flecha([(2, 3.6), (2.35, 3.6), (2.35, 5.3), (3.3, 5.3)], gris)
    flecha([(2, 3.3), (2.35, 3.3), (2.35, 4), (3.3, 4)], gris)
    flecha([(2, 3), (2.35, 3), (2.35, 2.23), (2.7, 2.23)], azul)
    flecha([(4.95, 2.23), (5.35, 2.23)], azul)
    flecha([(7.95, 2.23), (8.35, 2.23)], azul)
    flecha([(10.85, 2.23), (11.2, 2.23)], azul)
    flecha([(13.5, 2.23), (13.75, 2.23), (13.75, 2.5), (14, 2.5)], morado, True)
    flecha([(13.5, 2.23), (13.75, 2.23), (13.75, 1.1), (14, 1.1)], morado, True)
    ax.text(3.82, 1.13, "80 → 88 elementos", ha="center", fontsize=9, color=azul)
    ax.text(9.6, 1.13, "packet_len: 88 → 352", ha="center", fontsize=9, color=azul)
    ax.text(.1, .25, "Ejemplo Hola, sps = 4. Línea continua: stream complejo. Línea discontinua: PDU. Las ramas anteriores se conservan.", fontsize=9)
    fig.suptitle("La rama RRC parte de los símbolos; Burst Shaper permite terminar la respuesta del filtro", fontsize=13)
    fig.subplots_adjust(left=.015, right=.995, top=.9, bottom=.035)
    archivo = salida / "enlace-42-conexion-rrc.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar(salida):
    salida.mkdir(parents=True, exist_ok=True)
    return generar_senal(salida), generar_conexiones(salida)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    for archivo in generar(parser.parse_args().salida):
        print(archivo)

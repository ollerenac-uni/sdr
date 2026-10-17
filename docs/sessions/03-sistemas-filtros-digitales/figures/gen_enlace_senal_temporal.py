"""Genera el pulso rectangular de H y la rama temporal del paso 12."""

from pathlib import Path
import argparse
import struct
import zlib

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def datos_hola(sps=4):
    cuerpo = struct.pack("!H", 4) + b"Hola"
    paquete = cuerpo + struct.pack("!I", zlib.crc32(cuerpo))
    bits = np.unpackbits(np.frombuffer(paquete, dtype=np.uint8), bitorder="big")
    simbolos = (2 * bits.astype(int) - 1).astype(np.complex64)
    muestras = np.repeat(simbolos, sps)
    return paquete, bits, simbolos, muestras


def generar_pulso(salida):
    _, bits, simbolos, muestras = datos_hola()
    assert len(simbolos) == 80 and len(muestras) == 320
    assert muestras.nbytes == 2560 and np.all(muestras.imag == 0)
    # H empieza después de los 16 bits del campo de longitud.
    assert bits[16:24].tolist() == [0, 1, 0, 0, 1, 0, 0, 0]
    simbolos_h = simbolos[16:24].real
    muestras_h = muestras[64:96].real
    tiempos = 16 + np.arange(32) / 4
    fig, axes = plt.subplots(2, 1, figsize=(11.6, 6.4), sharex=True)
    ax = axes[0]
    ax.vlines(np.arange(16, 24), 0, simbolos_h, color="#1565c0", lw=1.4)
    ax.scatter(np.arange(16, 24), simbolos_h, color="#1565c0", s=45, zorder=3)
    for k, bit in enumerate(bits[16:24]):
        ax.text(16 + k + .5, 1.32, str(bit), ha="center", fontsize=12)
    ax.set_title("H: ocho símbolos, un bit por símbolo", loc="left")
    ax.set_ylabel("I del símbolo")
    ax = axes[1]
    ax.step(np.r_[tiempos, 24], np.r_[muestras_h, muestras_h[-1]], where="post", color="#1565c0", lw=1.8)
    ax.scatter(tiempos, muestras_h, color="#1565c0", s=22, label="Muestras de I", zorder=3)
    ax.scatter(tiempos, np.zeros(32), color="#ef6c00", s=16, label="Muestras de Q = 0", zorder=3)
    ax.set_title("Pulso rectangular: cuatro muestras por símbolo", loc="left")
    ax.set(xlabel="Tiempo desde el comienzo del paquete (ms)", ylabel="Valor normalizado")
    ax.legend(loc="lower left", bbox_to_anchor=(0, -.48), ncol=2)
    for ax in axes:
        for borde in range(16, 25):
            ax.axvline(borde, color="#b0bec5", lw=.8, ls="--", zorder=0)
        ax.axhline(0, color="#888888", lw=.7, zorder=0)
        ax.set(xlim=(15.85, 24.15), ylim=(-1.6, 1.7), yticks=[-1, 0, 1], xticks=range(16, 25))
        ax.grid(axis="y", alpha=.15)
    fig.suptitle("Rₛ = 1000 símbolos/s    ·    sps = 4    ·    fₛ = 4000 muestras/s", fontsize=13)
    fig.text(.5, .02, "Fragmento de Hola: solo H. Cada intervalo de 1 ms contiene cuatro muestras separadas por 0.25 ms.", ha="center", fontsize=10)
    fig.subplots_adjust(left=.09, right=.97, top=.88, bottom=.19, hspace=.46)
    archivo = salida / "enlace-35-pulso-rectangular.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar_conexiones(salida):
    fig, ax = plt.subplots(figsize=(14.8, 5.6))
    ax.set(xlim=(0, 16), ylim=(0, 6))
    ax.axis("off")
    azul, morado, gris = "#1565c0", "#7b1fa2", "#607d8b"

    def bloque(x, y, w, h, texto, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.025", ec=color, fc="white", lw=1.5))
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=9)

    def flecha(puntos, color, mensaje=False):
        estilo = "--" if mensaje else "-"
        for p, q in zip(puntos[:-2], puntos[1:-1]):
            ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=1.6, ls=estilo)
        ax.add_patch(FancyArrowPatch(puntos[-2], puntos[-1], arrowstyle="-|>", mutation_scale=13, color=color, lw=1.6, linestyle=estilo))

    bloque(.2, 2.2, 2.1, 1.35, "Chunks to Symbols\nID: mapeador\nSalida Complex", gris)
    bloque(3.4, 4.3, 3.1, 1.1, "Tagged Stream to PDU\nexistente: 80 símbolos", gris)
    bloque(8.4, 4.75, 3.5, .85, "Constelación BPSK existente", gris)
    bloque(8.4, 3.65, 3.5, .85, "Message Debug existente\n640 bytes para Hola", gris)
    bloque(3.2, 1.6, 2.15, 1.3, "Repeat\nID: pulso_rect\nInterpolation = sps", azul)
    bloque(5.85, 1.6, 2.75, 1.3, "Tagged Stream Multiply\nLength Tag\nID: longitud_muestras\nLength Scalar = sps", azul)
    bloque(9.1, 1.6, 2.6, 1.3, "Tagged Stream to PDU\nID: muestras_a_pdu\nComplex; packet_len", azul)
    bloque(12.45, 2.15, 3.1, .95, "QT GUI Time Sink\nComplex Message", azul)
    bloque(12.45, .8, 3.1, .95, "Message Debug nuevo\n2560 bytes para Hola", azul)
    flecha([(2.3, 3), (2.7, 3), (2.7, 4.85), (3.4, 4.85)], gris)
    flecha([(6.5, 4.85), (7.4, 4.85), (7.4, 5.17), (8.4, 5.17)], morado, True)
    flecha([(6.5, 4.85), (7.4, 4.85), (7.4, 4.07), (8.4, 4.07)], morado, True)
    flecha([(2.3, 2.55), (2.7, 2.55), (2.7, 2.25), (3.2, 2.25)], azul)
    flecha([(5.35, 2.25), (5.85, 2.25)], azul)
    flecha([(8.6, 2.25), (9.1, 2.25)], azul)
    flecha([(11.7, 2.25), (12.1, 2.25), (12.1, 2.62), (12.45, 2.62)], morado, True)
    flecha([(11.7, 2.25), (12.1, 2.25), (12.1, 1.27), (12.45, 1.27)], morado, True)
    ax.text(4.9, 5.65, "Rama existente del paso 11", color=gris, ha="center", fontsize=11)
    ax.text(7.4, 1.12, "Rama nueva: 80 símbolos → 320 muestras; packet_len: 80 → 320", ha="center", color=azul, fontsize=10)
    ax.text(.2, .45, "Línea continua: stream complejo. Línea discontinua: mensaje PDU. Valores del ejemplo Hola con sps = 4.", fontsize=9)
    fig.suptitle("La nueva rama temporal sale de mapeador; los visores anteriores se conservan", fontsize=13)
    fig.subplots_adjust(left=.02, right=.99, top=.89, bottom=.03)
    archivo = salida / "enlace-36-conexion-senal-temporal.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar(salida: Path):
    salida.mkdir(parents=True, exist_ok=True)
    return generar_pulso(salida), generar_conexiones(salida)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    for archivo in generar(parser.parse_args().salida):
        print(archivo)

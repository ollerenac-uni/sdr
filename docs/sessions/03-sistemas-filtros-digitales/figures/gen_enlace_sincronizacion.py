"""Genera el formato de trama y las conexiones del detector del paso 16."""

from pathlib import Path
import struct
import zlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


SYNC = bytes.fromhex("ac dd a4 e2 f2 8c 20 fc")


def trama_hola():
    cuerpo = struct.pack(">H", 4) + b"Hola"
    paquete = cuerpo + struct.pack(">I", zlib.crc32(cuerpo))
    return SYNC + struct.pack(">HH", len(paquete), len(paquete)) + paquete


def generar_formato(salida):
    trama = trama_hola()
    colores = ["#406b91"] * 8 + ["#b65d14"] * 4 + ["#287548"] * 10
    fig, ax = plt.subplots(figsize=(13.8, 5.5))
    ax.set(xlim=(-0.2, 22.2), ylim=(0, 6.5))
    ax.axis("off")

    def caja(x, y, w, h, texto, color, tam=11):
        ax.add_patch(
            FancyBboxPatch(
                (x + 0.04, y),
                w - 0.08,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                fc="white",
                ec=color,
                lw=1.6,
            )
        )
        ax.text(
            x + w / 2,
            y + h / 2,
            texto,
            ha="center",
            va="center",
            fontsize=tam,
            color=color,
            linespacing=1.3,
        )

    ax.text(
        11,
        6.1,
        "Trama de Hola: envoltura de 12 bytes + paquete protegido de 10 bytes",
        ha="center",
        fontsize=14,
        weight="bold",
        color="#263238",
    )
    caja(0, 4.6, 8, 1.05, "Palabra de acceso\n8 bytes · 64 bits", colores[0], 12)
    caja(8, 4.6, 2, 1.05, "Longitud\n00 0a", colores[8])
    caja(10, 4.6, 2, 1.05, "Copia\n00 0a", colores[10])
    caja(
        12,
        4.6,
        10,
        1.05,
        "Paquete protegido · 10 bytes\nSe conserva su CRC",
        colores[12],
        12,
    )
    ax.text(
        17,
        4.16,
        "Contenido del paquete existente",
        ha="center",
        fontsize=11,
        weight="bold",
        color=colores[12],
    )
    caja(12, 3.0, 2, 0.85, "Long. texto\n00 04", colores[12], 10)
    caja(14, 3.0, 4, 0.85, "Hola\n4 bytes", colores[14], 11)
    caja(18, 3.0, 4, 0.85, "CRC-32\n4 bytes", colores[18], 11)
    ax.text(
        0,
        2.68,
        "Bytes transmitidos en orden MSB first; índices desde cero:",
        fontsize=10.5,
        color="#455a64",
    )
    for i, b in enumerate(trama):
        caja(i, 1.5, 1, 0.66, f"{b:02x}", colores[i], 12)
        ax.text(i + 0.5, 2.27, str(i), ha="center", fontsize=9, color="#607d8b")
    ax.text(
        11,
        1.05,
        "Longitud externa: 10 bytes de paquete. Longitud interna: 4 bytes de texto.",
        ha="center",
        fontsize=11,
        color="#263238",
    )
    ax.text(
        11,
        0.52,
        "22 bytes → 176 bits y símbolos BPSK → detector → 80 bits del paquete → 10 bytes → Hola",
        ha="center",
        fontsize=11,
        weight="bold",
        color="#287548",
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_conexiones(salida):
    fig, ax = plt.subplots(figsize=(14.5, 7.2))
    ax.set(xlim=(0, 19), ylim=(0, 8.4))
    ax.axis("off")
    azul, naranja, verde = "#406b91", "#b65d14", "#287548"
    w, h = 3.15, 1.62
    xs = [0.55, 4.0, 7.45, 10.9, 14.35]

    def bloque(x, y, titulo, contenido, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.025,rounding_size=0.10",
                fc="white",
                ec=color,
                lw=1.5,
            )
        )
        ax.text(
            x + w / 2,
            y + h - 0.3,
            titulo,
            ha="center",
            va="center",
            fontsize=10.5,
            weight="bold",
            color=color,
        )
        ax.text(
            x + w / 2,
            y + 0.57,
            contenido,
            ha="center",
            va="center",
            fontsize=10,
            linespacing=1.25,
            color="#263238",
        )

    def flecha(inicio, fin, color):
        ax.add_patch(
            FancyArrowPatch(
                inicio, fin, arrowstyle="-|>", mutation_scale=13, lw=1.5, color=color
            )
        )

    ax.text(
        9.5,
        8.0,
        "Conexiones nuevas: envolver en TX y detectar el paquete en RX",
        ha="center",
        fontsize=15,
        weight="bold",
        color="#263238",
    )
    ax.text(
        0.55,
        7.47,
        "Trama completa · preparación TX y selección RX ideal",
        fontsize=12,
        weight="bold",
        color=azul,
    )
    bloque(
        xs[0],
        5.55,
        "Construir paquete",
        "Paquete original\n10 bytes\nCRC sin cambios",
        azul,
    )
    bloque(
        xs[1],
        5.55,
        "PDU Lambda",
        "envolver_trama\nAcceso + cabecera + paquete\n22 bytes",
        naranja,
    )
    bloque(
        xs[2], 5.55, "Bytes a bits", "Trama completa\n176 valores 0/1\nMSB first", azul
    )
    bloque(
        xs[3], 5.55, "Chunks to Symbols", "a_stream → mapeador\n176 símbolos BPSK", azul
    )
    bloque(
        xs[4],
        5.55,
        "Filtros TX/RX y selección",
        "RRC TX → RRC RX\nmuestrear_rx (ideal)\n176 valores complejos",
        azul,
    )
    for a, b in zip(xs[:-1], xs[1:]):
        flecha((a + w, 6.36), (b, 6.36), azul)
    flecha((15.925, 5.55), (15.925, 3.67), azul)
    ax.text(
        16.27, 4.62, "rx_a_stream\n→ extraer_i", fontsize=10, color=azul, va="center"
    )
    ax.text(
        0.55,
        4.13,
        "RX · El detector crea la longitud; el paquete vuelve al comprobador",
        fontsize=12,
        weight="bold",
        color=verde,
    )
    bloque(xs[4], 2.05, "Binary Slicer", "decidir_bits\n176 bits de trama", azul)
    bloque(
        xs[3],
        2.05,
        "Correlate Access Code",
        "- Tag Stream · detectar_trama\nEntrega 80 bits del paquete\nNueva packet_len = 80",
        naranja,
    )
    bloque(
        xs[2],
        2.05,
        "Repack Bits",
        "empaquetar_bits\n80 bits → 10 bytes\npacket_len = 10",
        verde,
    )
    bloque(
        xs[1],
        2.05,
        "Tagged Stream to PDU",
        "paquete_rx_a_pdu\nPaquete protegido\n10 bytes",
        verde,
    )
    bloque(
        xs[0],
        2.05,
        "Comprobar y convertir",
        "Comprobar paquete\nBytes a texto UTF-8\nMessage Debug: Hola",
        verde,
    )
    for a, b in zip(xs[:0:-1], xs[-2::-1]):
        flecha((a, 2.86), (b + w, 2.86), verde)
    flecha((12.475, 2.05), (12.475, 1.45), naranja)
    ax.text(
        12.475,
        1.14,
        "Tag Debug · debug_deteccion\npacket_len = 80 bits",
        ha="center",
        va="center",
        fontsize=10,
        color=naranja,
    )
    ax.text(
        4.0,
        0.65,
        "Message Debug · debug_trama_tx: 22 bytes antes de convertir la trama en bits",
        fontsize=10,
        color=azul,
    )
    ax.text(
        9.5,
        0.18,
        "Se conserva la selección temporal ideal por PDU. El detector no utiliza las etiquetas de entrada para delimitar su salida.",
        ha="center",
        fontsize=10,
        color="#455a64",
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar(carpeta=None):
    carpeta = Path(carpeta) if carpeta is not None else Path(__file__).parent
    carpeta.mkdir(parents=True, exist_ok=True)
    archivos = [
        carpeta / "enlace-60-formato-trama.png",
        carpeta / "enlace-61-conexion-deteccion.png",
    ]
    generar_formato(archivos[0])
    generar_conexiones(archivos[1])
    return archivos


if __name__ == "__main__":
    for archivo in generar():
        print(archivo)

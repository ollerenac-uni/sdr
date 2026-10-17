"""Genera las decisiones de Hola y la rama de recuperación estándar del paquete."""

import argparse
import importlib.util
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def datos_hola():
    ruta = Path(__file__).with_name("gen_enlace_receptor.py")
    spec = importlib.util.spec_from_file_location("referencia_receptor", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    _, _, _, _, rx, indices = modulo.datos_receptor()
    amplitudes = rx[indices].real
    bits = (amplitudes >= 0).astype(np.uint8)
    paquete = np.packbits(bits, bitorder="big").tobytes()
    return amplitudes, bits, paquete


def generar_decisiones(salida):
    amplitudes, bits, paquete = datos_hola()
    azul, verde, gris = "#1565c0", "#2e7d32", "#607d8b"
    fig, axes = plt.subplots(
        2, 1, figsize=(12.2, 8.0), gridspec_kw={"height_ratios": [1, 1.1]}
    )
    ax = axes[0]
    x = np.arange(8)
    ax.vlines(x, 0, amplitudes[16:24], color=azul, lw=1.5)
    ax.scatter(x, amplitudes[16:24], color=azul, s=40)
    ax.axhline(0, color=gris, lw=1.2, ls="--", label="Umbral = 0")
    for i, (a, bit) in enumerate(zip(amplitudes[16:24], bits[16:24])):
        ax.text(
            i,
            a + (0.12 if a > 0 else -0.21),
            str(bit),
            ha="center",
            fontsize=13,
            weight="bold",
            color=verde,
        )
    ax.set(
        xticks=x,
        xticklabels=list(range(7, -1, -1)),
        xlim=(-0.6, 7.6),
        ylim=(-1.4, 1.4),
        xlabel="Posición del bit: MSB → LSB",
        ylabel="I seleccionada",
        title="Primer byte del texto: 01001000 (binario) → 0x48 → H",
    )
    ax.grid(alpha=0.2)
    ax.legend(loc="center right", fontsize=9)
    ax = axes[1]
    ax.set(xlim=(0, 10), ylim=(0, 4.1))
    ax.axis("off")
    filas = []
    for i, b in enumerate(paquete[:3]):
        filas.append(
            [
                "Longitud" if i < 2 else "Texto: H",
                f"{i}",
                " ".join(str(v) for v in bits[i * 8 : (i + 1) * 8]),
                f"{b:02x}",
            ]
        )
    tabla = ax.table(
        cellText=filas,
        colLabels=[
            "Campo",
            "Índice del byte",
            "Ocho bits consecutivos",
            "Byte hexadecimal",
        ],
        cellLoc="center",
        colWidths=[0.19, 0.17, 0.42, 0.22],
        bbox=[0, 0.51, 1, 0.42],
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(10.5)
    for (i, j), cell in tabla.get_celld().items():
        cell.set_edgecolor("#cfd8dc")
        if i == 0:
            cell.set_facecolor("#eceff1")
            cell.set_text_props(weight="bold")
    ax.text(
        5,
        1.7,
        "Paquete RX reconstruido: 10 bytes",
        ha="center",
        fontsize=11,
        weight="bold",
    )
    for i, b in enumerate(paquete):
        color = azul if i < 2 else verde if i < 6 else gris
        ax.add_patch(
            FancyBboxPatch(
                (i + 0.08, 0.75),
                0.84,
                0.62,
                boxstyle="round,pad=0.03",
                fc="white",
                ec=color,
                lw=1.4,
            )
        )
        ax.text(
            i + 0.5,
            1.06,
            f"{b:02x}",
            ha="center",
            va="center",
            fontsize=13,
            color=color,
            family="monospace",
        )
    for centro, campo, color in [
        (1, "Longitud: 2 bytes", azul),
        (4, "Texto: 4 bytes", verde),
        (8, "CRC recibido: 4 bytes", gris),
    ]:
        ax.text(centro, 0.31, campo, ha="center", fontsize=10, color=color)
    fig.suptitle(
        "Referencia calculada: decidir bits y reconstruir Hola desde el receptor RRC",
        fontsize=13,
    )
    fig.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.045, hspace=0.34)
    archivo = salida / "enlace-51-decisiones-bytes-hola.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar_conexiones(salida):
    fig, ax = plt.subplots(figsize=(15.2, 8.1))
    ax.set(xlim=(0, 15.5), ylim=(0, 8.2))
    ax.axis("off")
    azul, verde, gris = "#1565c0", "#2e7d32", "#607d8b"

    def caja(x, y, titulo, detalle, color=azul):
        w, h = 4.0, 1.25
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h, boxstyle="round,pad=0.07", fc="white", ec=color, lw=1.5
            )
        )
        ax.text(
            x + w / 2,
            y + 0.92,
            titulo,
            ha="center",
            va="center",
            fontsize=12,
            weight="bold",
            color=color,
        )
        ax.text(x + w / 2, y + 0.4, detalle, ha="center", va="center", fontsize=10)

    def flecha(a, b, mensaje=False, detalle=None):
        ax.add_patch(
            FancyArrowPatch(
                a,
                b,
                arrowstyle="-|>",
                mutation_scale=14,
                color=azul,
                lw=1.5,
                ls="--" if mensaje else "-",
            )
        )
        if detalle:
            ax.text(
                (a[0] + b[0]) / 2 - (0.32 if a[0] == b[0] else 0),
                (a[1] + b[1]) / 2 + 0.16,
                detalle,
                ha="right" if a[0] == b[0] else "center",
                fontsize=9,
                color=gris,
            )

    izquierda, centro, derecha = 0.4, 5.7, 11.0
    alto, medio, bajo = 5.9, 3.45, 1.0
    caja(
        izquierda, alto, "muestrear_rx", "80 símbolos c32\nSelección del paso 14", verde
    )
    caja(centro, alto, "rx_a_stream", "PDU to Tagged Stream: Complex\npacket_len = 80")
    caja(derecha, alto, "extraer_i", "Complex To Real\n80 elementos float")
    flecha((4.4, 6.525), (5.7, 6.525), True, "PDU")
    flecha((9.7, 6.525), (11, 6.525), detalle="c32")
    caja(
        derecha,
        medio,
        "decidir_bits",
        "Binary Slicer: I < 0 → 0; I ≥ 0 → 1\n80 elementos byte, un bit cada uno",
    )
    caja(
        centro, medio, "empaquetar_bits", "Repack Bits: 1 → 8; MSB\npacket_len: 80 → 10"
    )
    caja(
        izquierda,
        medio,
        "paquete_rx_a_pdu",
        "Tagged Stream to PDU: Byte\n10 elementos u8 → debug_paquete_rx",
    )
    flecha((13, 5.9), (13, 4.7), detalle="float")
    flecha((11, 4.075), (9.7, 4.075), detalle="bits")
    flecha((5.7, 4.075), (4.4, 4.075), detalle="bytes")
    caja(
        izquierda,
        bajo,
        "Comprobar paquete",
        "epy_block_3: longitud y CRC\nSalida: 4 bytes UTF-8",
        verde,
    )
    caja(centro, bajo, "Bytes a texto UTF-8", "epy_block_1\nSalida: texto Hola", verde)
    caja(
        derecha,
        bajo,
        "Message Debug existente",
        "blocks_message_debug_0.print\nMuestra únicamente texto aceptado",
        verde,
    )
    flecha((2.4, 3.45), (2.4, 2.25), True, "PDU")
    flecha((4.4, 1.625), (5.7, 1.625), True, "PDU")
    flecha((9.7, 1.625), (11, 1.625), True, "texto")
    ax.text(
        7.7,
        7.7,
        "Se conservan las ramas TX, la señal RX completa y la constelación de símbolos seleccionados.",
        ha="center",
        fontsize=11,
        color=gris,
    )
    ax.text(
        7.7,
        0.28,
        "Línea continua: stream. Línea discontinua: mensaje. Las longitudes cuentan elementos del tipo indicado.",
        ha="center",
        fontsize=10,
        color=gris,
    )
    fig.suptitle(
        "Recuperación de Hola: desde los símbolos RX hasta el texto comprobado",
        fontsize=14,
        y=0.985,
    )
    fig.subplots_adjust(left=0.02, right=0.99, top=0.93, bottom=0.035)
    archivo = salida / "enlace-52-conexion-recuperar-paquete.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar(salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    return [generar_decisiones(salida), generar_conexiones(salida)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    for archivo in generar(args.salida):
        print(archivo)

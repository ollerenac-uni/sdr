"""Genera el mapa conceptual del enlace digital hasta el paso 15.

Ejecutar desde cualquier directorio con Python y Matplotlib disponibles.
Las cantidades corresponden a Hola, sps=4 y 33 coeficientes RRC.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def generar():
    fig, ax = plt.subplots(figsize=(16.5, 11.8))
    fig.subplots_adjust(left=0.015, right=0.985, top=0.985, bottom=0.02)
    ax.set(xlim=(0, 22), ylim=(-0.5, 15.3))
    ax.axis("off")
    colores = {
        "datos": "#234d78",
        "simbolos": "#2469a5",
        "rectangular": "#087e8b",
        "rrc": "#b65d14",
        "rx": "#77549b",
        "bytes": "#287548",
    }
    fondos = {
        "datos": "#eff5fb",
        "simbolos": "#edf5fc",
        "rectangular": "#edf8f8",
        "rrc": "#fff5eb",
        "rx": "#f4eff9",
        "bytes": "#eff8f1",
    }

    def panel(x, y, w, h, titulo, concepto):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.15",
                fc=fondos[concepto],
                ec=colores[concepto],
                lw=1.35,
                zorder=0,
            )
        )
        ax.text(
            x + 0.25,
            y + h - 0.35,
            titulo,
            fontsize=11.5,
            weight="bold",
            color=colores[concepto],
            va="center",
        )

    def bloque(x, y, w, h, titulo, texto, concepto, tam=10.5):
        color = colores[concepto]
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.025,rounding_size=0.10",
                fc="white",
                ec=color,
                lw=1.5,
                zorder=3,
            )
        )
        ax.text(
            x + w / 2,
            y + h - 0.22,
            titulo,
            ha="center",
            va="center",
            fontsize=tam + 0.2,
            weight="bold",
            color=color,
            zorder=4,
        )
        ax.text(
            x + w / 2,
            y + (h - 0.37) / 2,
            texto,
            ha="center",
            va="center",
            fontsize=tam,
            linespacing=1.25,
            color="#263238",
            zorder=4,
        )

    def flecha(puntos, color="#455a64"):
        for inicio, fin in zip(puntos[:-2], puntos[1:-1]):
            ax.plot(
                [inicio[0], fin[0]],
                [inicio[1], fin[1]],
                color=color,
                lw=1.5,
                zorder=2,
            )
        ax.add_patch(
            FancyArrowPatch(
                puntos[-2],
                puntos[-1],
                arrowstyle="-|>",
                mutation_scale=14,
                lw=1.5,
                color=color,
                shrinkA=0,
                shrinkB=1,
                zorder=2,
            )
        )

    ax.text(
        11,
        14.92,
        "Enlace digital: los caminos y los conceptos aprendidos",
        ha="center",
        fontsize=17,
        weight="bold",
        color="#263238",
    )
    panel(0.4, 12.15, 21.2, 2.22, "TX · Del texto a los símbolos", "datos")
    bloque(
        0.8,
        12.5,
        4.7,
        1.16,
        "1 · Texto y UTF-8 · paso 5",
        "QT GUI Message Edit Box\nTexto a bytes UTF-8\nHola: 4 bytes",
        "datos",
    )
    bloque(
        6.1,
        12.5,
        4.7,
        1.16,
        "2 · Paquete · paso 7",
        "Construir paquete\nLongitud + texto + CRC\n2 + 4 + 4 = 10 bytes",
        "datos",
    )
    bloque(
        11.4,
        12.5,
        4.7,
        1.16,
        "3 · Bits · paso 10",
        "Bytes a bits\nMSB first\n10 bytes → 80 bits",
        "datos",
    )
    bloque(
        16.7,
        12.5,
        4.5,
        1.16,
        "4 · BPSK · paso 11",
        "PDU to Tagged Stream →\nChunks to Symbols · mapeador\n80 símbolos: 0 → −1; 1 → +1",
        "datos",
        tam=10,
    )
    for x in (5.5, 10.8, 16.1):
        flecha([(x, 13.08), (x + 0.6, 13.08)])

    panel(0.4, 6.65, 6.7, 4.8, "A · Observar símbolos · paso 11", "simbolos")
    panel(7.45, 6.65, 6.7, 4.8, "B · Pulso rectangular · paso 12", "rectangular")
    panel(14.5, 6.65, 7.1, 4.8, "C · Pulso RRC · paso 13", "rrc")

    # Una bifurcación conceptual: las tres ramas reciben los mismos símbolos.
    ax.plot([6.8, 21.35], [11.85, 11.85], color="#455a64", lw=1.5, zorder=2)
    ax.plot([18.95, 18.95], [12.5, 11.85], color="#455a64", lw=1.5, zorder=2)
    for lateral, centro in ((6.8, 3.75), (13.85, 10.8), (21.35, 18.05)):
        ax.scatter(lateral, 11.85, s=15, color="#455a64", zorder=3)
        flecha([(lateral, 11.85), (lateral, 10.78), (centro, 10.78), (centro, 10.55)])

    bloque(
        0.95,
        9.35,
        5.6,
        1.2,
        "Reunir los símbolos",
        "Tagged Stream to PDU\n80 símbolos complejos",
        "simbolos",
    )
    bloque(
        0.95,
        7.55,
        5.6,
        1.2,
        "Constelación TX",
        "QT GUI Constellation Sink\nDos posiciones: (−1, 0) y (+1, 0)",
        "simbolos",
    )
    flecha([(3.75, 9.35), (3.75, 8.75)], colores["simbolos"])
    ax.text(
        3.75,
        7.03,
        "Esta rama termina en el visor.",
        ha="center",
        fontsize=10,
        color=colores["simbolos"],
    )

    bloque(
        8.0,
        9.35,
        5.6,
        1.2,
        "Repeat · pulso_rect",
        "Repite cada símbolo 4 veces\n80 × 4 = 320 muestras",
        "rectangular",
    )
    bloque(
        8.0,
        7.85,
        5.6,
        1.2,
        "Actualizar la longitud",
        "Tagged Stream Multiply Length Tag\nlongitud_muestras: packet_len = 320",
        "rectangular",
        tam=10,
    )
    bloque(
        8.0,
        6.88,
        5.6,
        0.72,
        "Observación rectangular",
        "muestras_a_pdu → tiempo_bpsk + debug",
        "rectangular",
        tam=9.7,
    )
    flecha([(10.8, 9.35), (10.8, 9.05)], colores["rectangular"])
    flecha([(10.8, 7.85), (10.8, 7.6)], colores["rectangular"])

    bloque(
        15.05,
        9.35,
        6.0,
        1.2,
        "Burst Shaper · cierre_rrc",
        "Añade 8 ceros al final de los símbolos\n80 + 8 = 88 elementos",
        "rrc",
    )
    bloque(
        15.05,
        7.85,
        6.0,
        1.2,
        "Root Raised Cosine Filter · pulso_rrc",
        "Interpola y forma los pulsos RRC\n88 × 4 = 352 muestras",
        "rrc",
        tam=10,
    )
    bloque(15.05, 6.88, 3.3, 0.72, "longitud_rrc", "packet_len = 352", "rrc", tam=10)
    bloque(18.85, 6.88, 2.2, 0.72, "Visores TX", "rrc_a_pdu → RRC TX", "rrc", tam=8.5)
    flecha([(18.05, 9.35), (18.05, 9.05)], colores["rrc"])
    flecha([(18.05, 7.85), (18.05, 7.7), (16.7, 7.7), (16.7, 7.6)], colores["rrc"])
    flecha([(18.35, 7.24), (18.85, 7.24)], colores["rrc"])

    ax.plot([0.5, 15.7], [6.22, 6.22], color="#607d8b", lw=1.3, ls="--")
    ax.text(
        0.8,
        6.30,
        "FIN TX / INICIO RX · enlace ideal de muestras I/Q · sin conversión a RF",
        fontsize=11,
        weight="bold",
        color="#455a64",
    )
    flecha([(16.7, 6.88), (16.7, 6.1), (18.55, 6.1), (18.55, 4.98)], colores["rrc"])

    panel(
        0.4,
        3.20,
        21.2,
        2.52,
        "RX · Filtro adaptado y selección de símbolos · paso 14",
        "rx",
    )
    bloque(
        15.55,
        3.58,
        6.0,
        1.4,
        "Burst Shaper · cierre_rx",
        "Añade 32 ceros a las muestras TX\n352 + 32 = 384 muestras\nCierre del ensayo receptor",
        "rx",
    )
    bloque(
        8.30,
        3.58,
        6.0,
        1.4,
        "Root Raised Cosine Filter · filtro_rx",
        "Matched filter · Decimation = 1\n384 muestras a 4000 muestras/s\nDos RRC en cascada ≈ raised cosine",
        "rx",
        tam=10,
    )
    bloque(
        1.05,
        3.58,
        6.0,
        1.4,
        "Seleccionar los instantes de símbolo",
        "Tagged Stream to PDU · rx_a_pdu\nPDU Lambda · muestrear_rx\nx[32:352:4] → 80 símbolos",
        "rx",
        tam=10,
    )
    flecha([(15.55, 4.28), (14.30, 4.28)], colores["rx"])
    flecha([(8.30, 4.28), (7.05, 4.28)], colores["rx"])

    panel(
        0.4,
        0.40,
        21.2,
        2.43,
        "RX · Decisiones, bytes y comprobación · paso 15",
        "bytes",
    )
    bloque(
        0.95,
        0.76,
        4.45,
        1.42,
        "De símbolos a I",
        "PDU to Tagged Stream\nComplex To Real\n80 valores reales",
        "bytes",
    )
    bloque(
        6.20,
        0.76,
        4.45,
        1.42,
        "Decidir los bits",
        "Binary Slicer\nI < 0 → 0; I ≥ 0 → 1\n80 bits",
        "bytes",
    )
    bloque(
        11.45,
        0.76,
        4.45,
        1.42,
        "Reconstruir el paquete",
        "Repack Bits · MSB first\nTagged Stream to PDU\n80 bits → 10 bytes",
        "bytes",
    )
    bloque(
        16.70,
        0.76,
        4.45,
        1.42,
        "Comprobar y recuperar texto",
        "Comprobar paquete · longitud y CRC\nBytes a texto UTF-8 → Message Debug\n4 bytes de texto → Hola",
        "bytes",
        tam=9.2,
    )
    flecha(
        [(4.05, 3.58), (4.05, 3.02), (0.2, 3.02), (0.2, 1.47), (0.95, 1.47)],
        colores["rx"],
    )
    for x in (5.4, 10.65, 15.9):
        flecha([(x, 1.47), (x + 0.8, 1.47)], colores["bytes"])

    ax.text(
        11,
        -0.02,
        "Referencia: Hola · sps = 4 · symbol_rate = 1000 símbolos/s · samp_rate = 4000 muestras/s · RRC: α = 0.35, 33 coeficientes",
        ha="center",
        fontsize=9.4,
        color="#455a64",
    )
    ax.text(
        11,
        -0.29,
        "Bloques agrupados por función. Los visores observan representaciones; la rama RRC alimenta el receptor. Los ceros de cierre no son bits del mensaje.",
        ha="center",
        fontsize=9.4,
        color="#455a64",
    )
    salida = Path(__file__).parent / "enlace-53-mapa-conceptos.png"
    fig.savefig(salida, dpi=160, facecolor="white")
    fig.savefig(salida.with_suffix(".svg"), facecolor="white")
    svg = salida.with_suffix(".svg")
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)
    return salida


if __name__ == "__main__":
    print(generar())

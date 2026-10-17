"""Genera referencias del receptor RRC y la selección ideal de símbolos."""

import argparse
import importlib.util
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def datos_receptor(sps=4, alpha=0.35, span=8):
    ruta = Path(__file__).with_name("gen_enlace_rrc.py")
    spec = importlib.util.spec_from_file_location("referencia_rrc", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    h_tx, simbolos, _, tx = modulo.datos_hola(sps, alpha, span)
    h_rx = modulo.coeficientes_rrc(sps, alpha, span) / sps
    cierre = span * sps
    entrada = np.concatenate([tx, np.zeros(cierre, dtype=np.complex64)])
    rx = np.convolve(entrada, h_rx)[: len(entrada)]
    indices = np.arange(cierre, len(rx) - cierre, sps)
    return h_tx, h_rx, simbolos, tx, rx, indices


def generar_senal(salida):
    h_tx, h_rx, simbolos, tx, rx, indices = datos_receptor()
    conjunto = np.convolve(h_tx, h_rx)
    fig, axes = plt.subplots(3, 1, figsize=(12, 9.5))
    azul, rojo, verde = "#1565c0", "#c62828", "#2e7d32"
    ax = axes[0]
    t = np.arange(len(conjunto)) / 4
    ax.plot(t, conjunto, color=azul, lw=1.2)
    ax.plot(t[::4], conjunto[::4], "o", color=verde, ms=4)
    ax.axvline(8, color="#616161", ls="--", lw=1)
    ax.annotate(
        "Retardo total: 8 ms",
        xy=(8, conjunto[32]),
        xytext=(10, 0.85),
        arrowprops={"arrowstyle": "->", "color": "#616161"},
        fontsize=10,
    )
    ax.set(
        title="Respuesta conjunta de los dos RRC: 65 coeficientes, centro en 32 muestras",
        xlabel="Tiempo desde el comienzo de la respuesta (ms)",
        ylabel="Coeficiente conjunto",
        xlim=(-0.1, 16.1),
        ylim=(-0.25, 1.15),
    )
    ax = axes[1]
    t = np.arange(len(rx)) / 4
    ax.plot(t, rx.real, color=azul, lw=1, label="I completa")
    ax.plot(t, rx.imag, color=rojo, lw=1, label="Q = 0")
    ax.plot(
        t[indices],
        rx.real[indices],
        "o",
        color=verde,
        ms=3.4,
        label="Una muestra por símbolo",
    )
    ax.axvspan(0, 8, color="#90a4ae", alpha=0.16)
    ax.axvspan(88, 96, color="#90a4ae", alpha=0.16)
    ax.set(
        title="Hola en el receptor: 384 muestras; selección de 80 elementos desde 8 ms",
        xlabel="Tiempo desde el comienzo del registro (ms)",
        ylabel="Amplitud",
        xlim=(-0.5, 97),
        ylim=(-2, 2),
    )
    ax.legend(loc="upper right", ncol=3, fontsize=9)
    ax = axes[2]
    d = rx[indices]
    ax.scatter(
        d.real, d.imag, color=verde, s=18, alpha=0.6, label="80 muestras seleccionadas"
    )
    ax.plot([-1, 1], [0, 0], "+", color="#212121", ms=12, label="Símbolos originales")
    ax.set(
        title="Constelación después del filtro y de la selección",
        xlabel="I: componente real",
        ylabel="Q: componente imaginaria",
        xlim=(-1.5, 1.5),
        ylim=(-0.2, 0.2),
    )
    ax.legend(loc="upper center", ncol=2, fontsize=9)
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.axhline(0, color="#888888", lw=0.6, zorder=0)
    fig.suptitle(
        "Referencia calculada: Rₛ = 1000 símbolos/s, sps = 4, α = 0.35", fontsize=13
    )
    fig.text(
        0.5,
        0.016,
        "Los filtros finitos dejan diferencias pequeñas en amplitud. La selección usa límites de paquete y retardo conocidos.",
        ha="center",
        fontsize=9,
    )
    fig.subplots_adjust(left=0.095, right=0.98, top=0.91, bottom=0.09, hspace=0.63)
    archivo = salida / "enlace-45-receptor-ideal-hola.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar_conexiones(salida):
    fig, ax = plt.subplots(figsize=(15.5, 6.3))
    ax.set(xlim=(0, 16), ylim=(0, 6.4))
    ax.axis("off")
    azul, gris, verde = "#1565c0", "#607d8b", "#2e7d32"

    def caja(x, y, w, h, titulo, detalle, color=azul):
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h, boxstyle="round,pad=0.08", fc="white", ec=color, lw=1.5
            )
        )
        ax.text(
            x + w / 2,
            y + h * 0.70,
            titulo,
            ha="center",
            va="center",
            fontsize=11,
            weight="bold",
            color=color,
        )
        ax.text(x + w / 2, y + h * 0.31, detalle, ha="center", va="center", fontsize=9)

    def flecha(a, b, mensaje=False, color=azul):
        ax.add_patch(
            FancyArrowPatch(
                a,
                b,
                arrowstyle="-|>",
                mutation_scale=13,
                lw=1.4,
                color=color,
                ls="--" if mensaje else "-",
            )
        )

    caja(0.25, 2.3, 2.4, 1.2, "longitud_rrc", "TX: 352 muestras\npacket_len = 352")
    caja(
        3.15,
        4.7,
        3.9,
        1,
        "Visores TX existentes",
        "rrc_a_pdu → tiempo_rrc / debug_rrc",
        gris,
    )
    flecha((2.65, 3.12), (3.15, 5.05), color=gris)
    caja(3.15, 2.3, 2.4, 1.2, "cierre_rx", "+32 ceros complejos\npacket_len = 384")
    caja(6.05, 2.3, 2.5, 1.2, "filtro_rx", "RRC: Gain 1\n33 taps; decimación 1")
    caja(9.05, 2.3, 2.4, 1.2, "rx_a_pdu", "384 elementos c32\n3072 bytes; 96 ms")
    flecha((2.65, 2.9), (3.15, 2.9))
    flecha((5.55, 2.9), (6.05, 2.9))
    flecha((8.55, 2.9), (9.05, 2.9))
    caja(12.1, 4.65, 3.5, 1.1, "Registro completo RX", "tiempo_rx / debug_rx")
    flecha((11.45, 3.1), (12.1, 5.05), True)
    caja(
        12.1,
        2.1,
        3.5,
        1.6,
        "muestrear_rx",
        "PDU Lambda\nx[32:352:4]\n80 elementos c32",
        verde,
    )
    flecha((11.45, 2.9), (12.1, 2.9), True)
    caja(
        10.4,
        0.2,
        5.2,
        1.05,
        "Símbolos recuperados",
        "constelacion_rx / debug_simbolos_rx\n80 elementos; 640 bytes",
        verde,
    )
    flecha((13.85, 2.1), (13.3, 1.25), True, verde)
    ax.text(6.5, 1.6, "Stream: 4000 muestras/s", ha="center", fontsize=10, color=azul)
    ax.text(
        4.4,
        0.55,
        "Línea continua: stream complejo\nLínea discontinua: mensaje PDU",
        ha="center",
        fontsize=10,
        color=gris,
    )
    ax.set_title(
        "Receptor ideal para Hola: cierre, filtro adaptado y selección por paquete",
        fontsize=14,
        pad=13,
    )
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.05, top=0.88)
    archivo = salida / "enlace-46-conexion-receptor-ideal.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


def generar(salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    return [generar_senal(salida), generar_conexiones(salida)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    for archivo in generar(args.salida):
        print(archivo)

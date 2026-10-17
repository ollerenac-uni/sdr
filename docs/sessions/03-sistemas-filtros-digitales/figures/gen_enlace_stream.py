"""Genera las referencias del receptor sin etiquetas del paso 17."""

import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


def modulo_local(nombre):
    ruta = Path(__file__).with_name(nombre + ".py")
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def datos_stream():
    """Referencia causal: trama de Hola, ambos RRC y selección global."""
    trama = modulo_local("gen_enlace_sincronizacion").trama_hola()
    h_tx = modulo_local("gen_enlace_rrc").coeficientes_rrc()
    bits = np.unpackbits(np.frombuffer(trama, dtype=np.uint8), bitorder="big")
    simbolos = (2 * bits.astype(int) - 1).astype(np.complex64)
    impulsos = np.zeros((len(simbolos) + 8) * 4, dtype=np.complex64)
    impulsos[: len(simbolos) * 4 : 4] = simbolos
    tx = np.convolve(impulsos, h_tx)[: len(impulsos)]
    entrada_rx = np.concatenate((tx, np.zeros(32, dtype=np.complex64)))
    rx = np.convolve(entrada_rx, h_tx / 4)[: len(entrada_rx)]
    indices = np.arange(0, len(rx), 4)
    return rx, rx[indices], indices


def generar_conexiones(salida):
    fig, ax = plt.subplots(figsize=(14, 7.6))
    ax.set(xlim=(0, 20), ylim=(0, 10))
    ax.axis("off")
    azul, naranja, verde = "#406b91", "#b65d14", "#287548"
    gris = "#607d8b"
    w, h = 3.25, 1.5

    def caja(x, y, titulo, texto, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.03,rounding_size=0.08",
                fc="white",
                ec=color,
                lw=1.6,
            )
        )
        ax.text(
            x + w / 2,
            y + 1.12,
            titulo,
            ha="center",
            va="center",
            fontsize=11,
            color=color,
            weight="bold",
        )
        ax.text(
            x + w / 2,
            y + 0.47,
            texto,
            ha="center",
            va="center",
            fontsize=10,
            color="#263238",
            linespacing=1.4,
        )

    def flecha(a, b, color=azul):
        ax.add_patch(
            FancyArrowPatch(
                a,
                b,
                arrowstyle="-|>",
                mutation_scale=14,
                lw=1.6,
                color=color,
            )
        )

    ax.text(
        10,
        9.6,
        "Paso 17: el receptor recibe muestras sin límites de paquete",
        ha="center",
        fontsize=15,
        weight="bold",
        color="#263238",
    )
    ax.axvspan(0.2, 7.8, ymin=0.58, ymax=0.89, color=azul, alpha=0.06)
    ax.axvspan(8.1, 19.8, ymin=0.58, ymax=0.89, color=verde, alpha=0.06)
    ax.text(
        0.65, 8.55, "Generación TX de la ráfaga", fontsize=12, color=azul, weight="bold"
    )
    ax.text(
        8.55,
        8.55,
        "Recepción: fase y tasas conocidas",
        fontsize=12,
        color=verde,
        weight="bold",
    )
    xs = [0.65, 4.45, 8.55, 12.35, 16.15]
    caja(xs[0], 6.4, "RRC TX", "pulso_rrc\n→ longitud_rrc", azul)
    caja(xs[1], 6.4, "Burst Shaper", "cierre_rx\nAñade 32 ceros complejos", azul)
    caja(xs[2], 6.4, "Tag Gate", "sin_etiquetas\nPropagate Tags = No", naranja)
    caja(xs[3], 6.4, "RRC RX", "filtro_rx\nDecimation = 1", verde)
    caja(
        xs[4], 6.4, "Keep M in N", "muestrear_stream\nM = 1 · N = 4 · offset = 0", verde
    )
    for x, siguiente in zip(xs[:-1], xs[1:]):
        flecha((x + w, 7.15), (siguiente, 7.15))
    ax.plot([8.05, 8.05], [5.85, 8.7], "--", color=naranja, lw=1.3)
    ax.text(
        8.05, 5.5, "Frontera: solo muestras", color=naranja, ha="center", fontsize=10
    )
    flecha((17.775, 6.4), (17.775, 4.45), verde)
    caja(xs[4], 2.9, "Decisiones", "extraer_i\n→ decidir_bits", verde)
    caja(
        xs[3],
        2.9,
        "Detector de trama",
        "detectar_trama\nNueva packet_len = 80",
        naranja,
    )
    caja(xs[2], 2.9, "Reconstrucción", "empaquetar_bits\n→ paquete_rx_a_pdu", verde)
    caja(xs[1], 2.9, "Validación y texto", "Comprobar paquete\n→ UTF-8 → Hola", verde)
    for derecha, izquierda in zip(xs[:0:-1], xs[-2:0:-1]):
        flecha((derecha, 3.65), (izquierda + w, 3.65), verde)
    ax.text(
        14,
        5.4,
        "tiempo_rx observa el filtro.\nconstelacion_rx observa el selector.",
        ha="center",
        va="center",
        color=gris,
        fontsize=10,
        linespacing=1.5,
    )
    ax.text(
        0.65,
        4.25,
        "Tag Debug antes del filtro:\nsin etiquetas de entrada.",
        color=gris,
        fontsize=10,
        linespacing=1.5,
    )
    ax.text(
        10,
        2.1,
        "Hola: 768 muestras RX → 192 valores seleccionados → 80 bits detectados → paquete de 10 bytes",
        ha="center",
        fontsize=11,
        color=verde,
        weight="bold",
    )
    ax.text(
        10,
        1.35,
        "Se deshabilitan rx_a_pdu, muestrear_rx y rx_a_stream. Los visores RX usan entradas de stream.",
        ha="center",
        fontsize=10,
        color=gris,
    )
    ax.text(
        10,
        0.7,
        "Keep M in N conserva transitorios. El detector busca el acceso; el CRC valida el paquete reconstruido.",
        ha="center",
        fontsize=10,
        color=gris,
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_muestras(salida):
    rx, sel, indices = datos_stream()
    fig, axes = plt.subplots(2, 1, figsize=(13, 8))
    azul, rojo = "#1565c0", "#c62828"
    ax = axes[0]
    t = np.arange(len(rx)) / 4
    ax.plot(t, rx.real, color=azul, lw=0.8, label="I: 768 muestras RX")
    ax.plot(
        indices / 4,
        sel.real,
        "o",
        color=azul,
        ms=3,
        label="Selección: índices 0, 4, 8, …",
    )
    ax.plot(t, rx.imag, color=rojo, lw=1, label="Q = 0")
    ax.set(
        title="Señal RX completa: una trama y sus transitorios",
        xlabel="Tiempo desde el comienzo del registro (ms)",
        ylabel="Valor normalizado",
        xlim=(-1, 193),
        ylim=(-1.85, 1.85),
    )
    ax.legend(loc="upper right", fontsize=9, ncol=3)
    ax = axes[1]
    ax.plot(
        np.arange(len(sel)),
        sel.real,
        ".-",
        color=azul,
        ms=5,
        lw=0.7,
        label="I: 192 valores seleccionados",
    )
    ax.plot(np.arange(len(sel)), sel.imag, color=rojo, lw=1, label="Q = 0")
    regiones = [
        (0, 8, "Arranque", "#90a4ae"),
        (8, 72, "Acceso: 64", "#406b91"),
        (72, 104, "Cabecera: 32", "#b65d14"),
        (104, 184, "Paquete: 80", "#287548"),
        (184, 192, "Cierre", "#90a4ae"),
    ]
    for inicio, fin, texto, color in regiones:
        ax.axvspan(inicio - 0.5, fin - 0.5, color=color, alpha=0.10)
        ax.axvline(inicio - 0.5, color=color, lw=0.7, alpha=0.6)
        ax.text(
            (inicio + fin - 1) / 2,
            1.48,
            texto,
            ha="center",
            va="center",
            color=color,
            fontsize=9,
            rotation=90 if fin - inicio == 8 else 0,
        )
    ax.set(
        title="Selección global: la trama ocupa 176 posiciones; el detector entrega solo 80 bits",
        xlabel="Índice del valor seleccionado, desde cero",
        ylabel="Valor normalizado",
        xlim=(-2, 194),
        ylim=(-1.55, 1.85),
    )
    ax.legend(loc="lower right", fontsize=9, ncol=2)
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.axhline(0, color="#888888", lw=0.6, zorder=0)
    fig.suptitle(
        "Referencia calculada de Hola · sps = 4 · Rₛ = 1000 símbolos/s · α = 0.35",
        fontsize=14,
    )
    fig.text(
        0.5,
        0.02,
        "La selección conserva ocho valores antes de la trama y ocho después. No usa su longitud para recortar el registro.",
        ha="center",
        fontsize=10,
        color="#455a64",
    )
    fig.subplots_adjust(left=0.075, right=0.98, top=0.90, bottom=0.10, hspace=0.44)
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar(salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    archivos = [
        salida / "enlace-68-conexion-receptor-stream.png",
        salida / "enlace-69-muestras-stream-hola.png",
    ]
    generar_conexiones(archivos[0])
    generar_muestras(archivos[1])
    return archivos


if __name__ == "__main__":
    for archivo in generar(Path(__file__).parent):
        print(archivo)

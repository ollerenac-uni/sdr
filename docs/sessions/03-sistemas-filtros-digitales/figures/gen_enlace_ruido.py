"""Referencias reproducibles para la suma de ruido y sus observadores."""

import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


def modulo_local(nombre):
    spec = importlib.util.spec_from_file_location(
        nombre, Path(__file__).with_name(nombre + ".py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def datos_hola():
    h = modulo_local("gen_enlace_rrc").coeficientes_rrc()
    trama = modulo_local("gen_enlace_sincronizacion").trama_hola()
    bits = np.unpackbits(np.frombuffer(trama, dtype=np.uint8), bitorder="big")
    simbolos = (2 * bits.astype(int) - 1).astype(np.complex64)
    u = np.zeros((len(simbolos) + 8) * 4, dtype=np.complex64)
    u[: len(simbolos) * 4 : 4] = simbolos
    x = np.concatenate((np.convolve(u, h)[: len(u)], np.zeros(32, dtype=np.complex64)))
    return x, h / 4, len(simbolos)


def potencia_hola():
    x, _, _ = datos_hola()
    return float(np.mean(np.abs(x) ** 2))


def generar_conexiones(salida):
    fig, ax = plt.subplots(figsize=(14.5, 7.5))
    ax.set(xlim=(0, 20), ylim=(0, 10))
    ax.axis("off")
    azul, naranja, verde, gris = "#406b91", "#b65d14", "#287548", "#607d8b"

    def caja(x, y, w, h, titulo, texto, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.025,rounding_size=0.08",
                fc="white",
                ec=color,
                lw=1.6,
            )
        )
        ax.text(
            x + w / 2,
            y + h - 0.3,
            titulo,
            ha="center",
            va="center",
            fontsize=11,
            color=color,
            weight="bold",
        )
        ax.text(
            x + w / 2,
            y + 0.5,
            texto,
            ha="center",
            va="center",
            fontsize=10,
            color="#263238",
            linespacing=1.35,
        )

    def flecha(a, b, color=azul, mensaje=False):
        ax.add_patch(
            FancyArrowPatch(
                a,
                b,
                arrowstyle="-|>",
                mutation_scale=14,
                lw=1.5,
                color=color,
                linestyle="--" if mensaje else "-",
            )
        )

    ax.text(
        10,
        9.5,
        "Paso 18: sumar ruido antes del filtro y contar los resultados",
        fontsize=15,
        ha="center",
        weight="bold",
        color="#263238",
    )
    xs = [0.5, 4.4, 8.3, 12.2, 16.1]
    caja(xs[0], 7.05, 3.2, 1.5, "Generación TX", "RRC y cierre\n→ cierre_rx", azul)
    caja(
        xs[1],
        7.05,
        3.2,
        1.5,
        "Tag Gate",
        "sin_etiquetas\nSin etiquetas de entrada",
        azul,
    )
    caja(xs[2], 7.05, 3.2, 1.5, "Add", "sumar_ruido\nr[n] = x[n] + w[n]", naranja)
    caja(
        xs[3],
        7.05,
        3.2,
        1.5,
        "Filtro y selección",
        "filtro_rx\n→ muestrear_stream",
        verde,
    )
    caja(
        xs[4],
        7.05,
        3.2,
        1.5,
        "Recuperación RX",
        "Decisión → detector\n→ paquete → texto",
        verde,
    )
    for x, siguiente in zip(xs[:-1], xs[1:]):
        flecha((x + 3.2, 7.8), (siguiente, 7.8))
    caja(
        8.3,
        4.2,
        3.2,
        1.5,
        "Noise Source",
        "ruido · Complex Gaussian\nAmplitud a · semilla fija",
        naranja,
    )
    flecha((9.9, 5.7), (9.9, 7.05), naranja)
    ax.text(10.12, 6.3, "in1", fontsize=10, color=naranja)
    ax.text(7.82, 8.02, "in0", fontsize=10, color=azul)
    ax.text(
        0.5,
        5.7,
        "Las tres ramas de observación TX\nse conservan antes de sumar el ruido.",
        fontsize=10.5,
        color=gris,
        linespacing=1.5,
    )
    ax.text(
        12.5,
        5.5,
        "El detector guarda sus etiquetas.\nLos visores RX observan la señal con ruido.",
        fontsize=10.5,
        color=gris,
        linespacing=1.5,
    )
    caja(
        0.5,
        1.3,
        5.3,
        1.7,
        "Eventos TX",
        "envolver_trama → debug_trama_tx.store\nTX: tramas transmitidas",
        azul,
    )
    caja(
        7.3,
        1.3,
        5.3,
        1.7,
        "Eventos RX",
        "paquete → debug_paquete_rx.store\ntexto → blocks_message_debug_0.store",
        verde,
    )
    caja(
        14.1,
        1.3,
        5.3,
        1.7,
        "Resumen al cerrar Qt",
        "TX · DET · RX · OK\nRECH · SIN_PDU · SIN_TEXTO",
        naranja,
    )
    flecha((12.6, 2.15), (14.1, 2.15), gris, True)
    ax.plot([3.15, 3.15, 16.75], [1.3, 0.85, 0.85], "--", color=gris, lw=1.2)
    flecha((16.75, 0.85), (16.75, 1.3), gris, True)
    ax.text(
        10,
        0.4,
        "Los puertos store son observadores. No transfieren datos originales a las decisiones del receptor.",
        ha="center",
        fontsize=10,
        color=gris,
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_referencia(salida):
    x, h, n_simbolos = datos_hola()
    rng = np.random.default_rng(42)
    w = (rng.standard_normal(len(x)) + 1j * rng.standard_normal(len(x))) / np.sqrt(2)
    r = x + w
    y0 = np.convolve(x, h)[: len(x)]
    y1 = np.convolve(r, h)[: len(r)]
    indices = 32 + np.arange(n_simbolos) * 4
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 9))
    azul, naranja, morado = "#1565c0", "#c16e00", "#7b1fa2"
    ax = axes[0]
    t = np.arange(256) / 4
    ax.plot(t, x[:256].real, color=azul, lw=1.4, label="I limpia")
    ax.plot(t, r[:256].real, color=naranja, alpha=0.8, lw=0.7, label="I con ruido")
    ax.plot(t, r[:256].imag, color=morado, alpha=0.7, lw=0.7, label="Q con ruido")
    ax.set(
        title="Antes del RRC RX: ventana de 64 ms, amplitud de ruido a = 1",
        xlabel="Tiempo desde el comienzo del registro (ms)",
        ylabel="Valor normalizado",
        xlim=(0, 64),
        ylim=(-3.4, 3.4),
    )
    ax.legend(loc="upper right", ncol=3, fontsize=9)
    ax = axes[1]
    ax.scatter(
        y1[indices].real,
        y1[indices].imag,
        s=20,
        color=naranja,
        alpha=0.7,
        label="Después del RRC y selección, a = 1",
    )
    ax.scatter(
        y0[indices].real,
        y0[indices].imag,
        s=30,
        color=azul,
        label="Selección sin ruido, a = 0",
        zorder=3,
    )
    ax.set(
        title="176 posiciones de trama seleccionadas para comparar la referencia",
        xlabel="I: componente real",
        ylabel="Q: componente imaginaria",
        xlim=(-2.4, 2.4),
        ylim=(-1.7, 1.7),
    )
    ax.legend(loc="upper center", fontsize=9)
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.axhline(0, color="#888888", lw=0.6, zorder=0)
    axes[1].axvline(0, color="#888888", lw=0.6, zorder=0)
    fig.suptitle(
        "Referencia calculada de Hola · sps = 4 · α = 0.35 · ruido complejo gaussiano",
        fontsize=14,
    )
    fig.text(
        0.5,
        0.04,
        f"Registro limpio de 768 muestras: Pₓ ≈ {potencia_hola():.6f}. Para a = 1, potencia de ruido esperada P_w = 1.",
        ha="center",
        fontsize=10,
        color="#455a64",
    )
    fig.text(
        0.5,
        0.017,
        "La figura usa NumPy con semilla 42. No reproduce la secuencia exacta del generador de GNU Radio.",
        ha="center",
        fontsize=9,
        color="#455a64",
    )
    fig.subplots_adjust(left=0.085, right=0.98, top=0.90, bottom=0.12, hspace=0.43)
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar(salida):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    archivos = [
        salida / "enlace-74-conexion-ruido.png",
        salida / "enlace-75-referencia-ruido.png",
    ]
    generar_conexiones(archivos[0])
    generar_referencia(archivos[1])
    return archivos


if __name__ == "__main__":
    for archivo in generar(Path(__file__).parent):
        print(archivo)

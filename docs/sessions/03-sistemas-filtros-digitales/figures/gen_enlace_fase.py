"""Conexiones y constelaciones reproducibles del Costas Loop de GNU Radio."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


def datos_referencia(python_gr=None):
    """Ejecuta el lazo real sobre las muestras RRC de la referencia Hola."""
    ruta = Path(__file__).with_name("gen_enlace_ruido.py")
    spec = importlib.util.spec_from_file_location("referencia_ruido", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    x, h, _ = mod.datos_hola()
    trama = mod.modulo_local("gen_enlace_sincronizacion").trama_hola()
    bits = np.unpackbits(np.frombuffer(trama, dtype=np.uint8), bitorder="big")
    limpia = np.convolve(x, h)[: len(x)][::4]
    grcc = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
    python_gr = python_gr or os.environ.get(
        "PYTHON_GR", str(Path(grcc).parent / "python3")
    )
    programa = """
import sys,json,numpy as np
from gnuradio import blocks,digital,gr
rows=json.load(sys.stdin);result={}
for grados,row in rows.items():
    x=np.asarray(row[0])+1j*np.asarray(row[1]);t=gr.top_block()
    s=blocks.vector_source_c(x.tolist(),False);loop=digital.costas_loop_cc(.0628,2,False);v=blocks.vector_sink_c()
    t.connect(s,loop,v);t.run();y=np.asarray(v.data())
    result[grados]=[y.real.tolist(),y.imag.tolist()]
print(json.dumps(result))
"""
    entradas = {g: limpia * np.exp(1j * np.deg2rad(g)) for g in [60, 120]}
    payload = {g: [v.real.tolist(), v.imag.tolist()] for g, v in entradas.items()}
    r = subprocess.run(
        [python_gr, "-c", programa],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    salidas = json.loads(r.stdout)
    return {
        g: (v, np.array(salidas[str(g)][0]) + 1j * np.array(salidas[str(g)][1]), bits)
        for g, v in entradas.items()
    }


def generar_conexion(salida):
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set(xlim=(0, 20), ylim=(0, 10))
    ax.axis("off")
    azul, naranja, verde = "#1565a3", "#ad5812", "#287548"

    def caja(x, y, w, h, titulo, texto, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.08",
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
            linespacing=1.4,
        )

    def flecha(a, b, color=azul):
        ax.add_patch(
            FancyArrowPatch(
                a, b, arrowstyle="-|>", mutation_scale=14, lw=1.5, color=color
            )
        )

    ax.text(
        10,
        9.6,
        "Paso 19: fase constante del canal y estimación desde las muestras",
        ha="center",
        fontsize=15,
        weight="bold",
    )
    cajas = [
        (0.35, "Tag Gate", "sin_etiquetas\nSin delimitación TX", azul),
        (4.3, "Multiply Const", "rotar_fase\nFactor exp(jθ)", naranja),
        (8.25, "Add", "sumar_ruido\nRuido desactivado", naranja),
        (12.2, "RRC RX", "filtro_rx\n4000 muestras/s", verde),
        (16.15, "Keep M in N", "muestrear_stream\n1000 valores/s", verde),
    ]
    for x, titulo, texto, color in cajas:
        caja(x, 7.0, 3.45, 1.6, titulo, texto, color)
    for a, b in zip(cajas[:-1], cajas[1:]):
        flecha((a[0] + 3.45, 7.8), (b[0], 7.8))
    caja(
        12.2,
        3.9,
        3.45,
        1.6,
        "Costas Loop",
        "recuperar_fase\nOrder 2 · BW 0.0628",
        verde,
    )
    ax.plot([17.87, 17.87, 13.92], [7, 6, 6], color=verde, lw=1.5)
    flecha((13.92, 6), (13.92, 5.5), verde)
    caja(
        7.1,
        3.9,
        3.8,
        1.6,
        "Decisión y protocolo",
        "extraer_i → decidir_bits\n→ detector → paquete → texto",
        verde,
    )
    flecha((12.2, 4.7), (10.9, 4.7), verde)
    caja(
        16.15,
        3.9,
        3.45,
        1.6,
        "Antes del lazo",
        "constelacion_rx\nMuestras rotadas",
        azul,
    )
    flecha((17.87, 6), (17.87, 5.5), azul)
    caja(
        12.2,
        1.1,
        3.45,
        1.6,
        "Después del lazo",
        "constelacion_fase\nMuestras corregidas",
        verde,
    )
    flecha((13.92, 3.9), (13.92, 2.7), verde)
    ax.text(
        0.35,
        5.2,
        "Canal: θ constante, configurado en grados.\nLa multiplicación conserva magnitud.\nNo se cambia frecuencia ni reloj.",
        fontsize=11,
        color=naranja,
        linespacing=1.5,
    )
    ax.text(
        0.35,
        2.2,
        "El receptor estima fase desde las muestras.\nNo recibe θ ni referencias TX.\nLa ambigüedad BPSK de 180° permanece.",
        fontsize=11,
        color=verde,
        linespacing=1.5,
    )
    ax.text(
        10,
        0.3,
        "Los contadores y los observadores TX del paso 18 se conservan.",
        ha="center",
        fontsize=10,
        color="#546e7a",
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_constelaciones(salida, datos):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    colores = ["#1565c0", "#c16e00"]
    for fila, grados in enumerate([60, 120]):
        pre, post, bits = datos[grados]
        for col, (nombre, valores) in enumerate(
            [("Antes de Costas", pre), ("Después de Costas", post)]
        ):
            ax = axes[fila, col]
            ventana = valores[100:184]
            for bit in [0, 1]:
                puntos = ventana[bits[92:] == bit]
                ax.scatter(
                    puntos.real,
                    puntos.imag,
                    s=32,
                    color=colores[bit],
                    alpha=0.8,
                    label=f"Bit TX {bit}",
                )
            ax.axhline(0, color="#78909c", lw=0.7)
            ax.axvline(0, color="#78909c", lw=0.7)
            ax.set(
                title=f"{nombre} · canal {grados}°",
                xlabel="I normalizada",
                ylabel="Q normalizada",
                xlim=(-1.35, 1.35),
                ylim=(-1.35, 1.35),
            )
            ax.set_aspect("equal")
            ax.grid(alpha=0.25)
            ax.legend(loc="upper right", fontsize=9)
            if col == 1:
                mensaje = (
                    "Correspondencia conservada"
                    if grados == 60
                    else "Correspondencia invertida"
                )
                ax.text(0, -1.12, mensaje, ha="center", fontsize=10, color="#263238")
    fig.suptitle(
        "Mismas posiciones de datos: la alineación no resuelve la inversión BPSK",
        fontsize=14,
    )
    fig.text(
        0.5,
        0.018,
        "Referencia: primer Hola, índices 100–183 del lazo; bloque GNU Radio real, sin ruido.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar(salida, python_gr=None, datos=None):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    paths = [
        salida / "enlace-79-conexion-fase.png",
        salida / "enlace-80-referencia-fase.png",
    ]
    generar_conexion(paths[0])
    generar_constelaciones(
        paths[1], datos if datos is not None else datos_referencia(python_gr)
    )
    return paths


if __name__ == "__main__":
    for path in generar(Path(__file__).parent):
        print(path)

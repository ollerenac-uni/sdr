"""Figuras reproducibles de las dos hipótesis estándar de polaridad BPSK."""

import importlib.util
import json
from pathlib import Path
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


def datos_hola_invertidos(python_gr=None):
    ruta = Path(__file__).with_name("gen_enlace_fase.py")
    spec = importlib.util.spec_from_file_location("referencia_fase", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    datos = m.datos_referencia(python_gr)
    raw = (datos[120][1][8:184].real >= 0).astype(np.uint8)
    ruta = Path(__file__).with_name("gen_enlace_sincronizacion.py")
    spec = importlib.util.spec_from_file_location("referencia_trama", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    original = mod.trama_hola()
    python_gr = python_gr or str(Path.home() / "radioconda/bin/python3")
    programa = """
import sys,json
from gnuradio import blocks,digital,gr
t=gr.top_block();s=blocks.vector_source_b(json.load(sys.stdin),False);m=digital.map_bb([1,0]);v=blocks.vector_sink_b()
t.connect(s,m,v);t.run();print(json.dumps(list(v.data())))
"""
    r = subprocess.run(
        [python_gr, "-c", programa],
        input=json.dumps(raw.tolist()),
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    mapped = np.asarray(json.loads(r.stdout), dtype=np.uint8)
    recibida = np.packbits(raw, bitorder="big").tobytes()
    corregida = np.packbits(mapped, bitorder="big").tobytes()
    assert corregida == original and recibida == bytes(b ^ 255 for b in original)
    return original, recibida, corregida


def generar_conexion(salida):
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.set(xlim=(0, 24), ylim=(0, 12))
    ax.axis("off")
    azul, naranja, verde, gris = "#1565a3", "#b25d14", "#287548", "#607d8b"

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
            y + 0.48,
            texto,
            ha="center",
            va="center",
            fontsize=9.5,
            color="#263238",
            linespacing=1.35,
        )

    def flecha(a, b, color=azul, mensaje=False):
        ax.add_patch(
            FancyArrowPatch(
                a,
                b,
                arrowstyle="-|>",
                mutation_scale=13,
                lw=1.5,
                color=color,
                linestyle="--" if mensaje else "-",
            )
        )

    ax.text(
        12,
        11.3,
        "Paso 20: resolver la polaridad desde el acceso recibido",
        ha="center",
        fontsize=15,
        weight="bold",
    )
    caja(
        0.3,
        5.7,
        2.9,
        1.7,
        "Binary Slicer",
        "decidir_bits\nBytes con valores 0 o 1",
        azul,
    )
    caja(7.4, 7.9, 3.1, 1.6, "Detector normal", "detectar_trama\nMismo sync_bits", azul)
    caja(11.2, 7.9, 3.1, 1.6, "Repack Bits", "empaquetar_bits\n1 → 8 · MSB", azul)
    caja(15, 7.9, 3.1, 1.6, "Stream → PDU", "paquete_rx_a_pdu\nCandidato normal", azul)
    ax.plot([3.2, 3.6, 3.6], [6.55, 6.55, 8.7], color=azul, lw=1.5)
    flecha((3.6, 8.7), (7.4, 8.7), azul)
    for x1, x2 in [(10.5, 11.2), (14.3, 15)]:
        flecha((x1, 8.7), (x2, 8.7), azul)
    caja(4.0, 3.6, 2.7, 1.6, "Map", "invertir_bits\n[1, 0]", naranja)
    caja(
        7.4,
        3.6,
        3.1,
        1.6,
        "Detector invertida",
        "detectar_invertida\nMismo sync_bits",
        naranja,
    )
    caja(
        11.2, 3.6, 3.1, 1.6, "Repack Bits", "empaquetar_invertida\n1 → 8 · MSB", naranja
    )
    caja(
        15, 3.6, 3.1, 1.6, "Stream → PDU", "pdu_invertida\nCandidato corregido", naranja
    )
    ax.plot([3.2, 3.6], [6.55, 6.55], color=naranja, lw=1.5)
    ax.plot([3.6, 3.6], [6.55, 4.4], color=naranja, lw=1.5)
    flecha((3.6, 4.4), (4.0, 4.4), naranja)
    for x1, x2 in [(6.7, 7.4), (10.5, 11.2), (14.3, 15)]:
        flecha((x1, 4.4), (x2, 4.4), naranja)
    caja(
        19.2,
        5.5,
        4.35,
        2.1,
        "Comprobar paquete",
        "Longitud y CRC existentes\n→ UTF-8 → texto",
        verde,
    )
    ax.plot([18.1, 18.65, 18.65], [8.7, 8.7, 6.9], color=azul, lw=1.5, linestyle="--")
    flecha((18.65, 6.9), (19.2, 6.9), azul, True)
    ax.plot(
        [18.1, 18.65, 18.65], [4.4, 4.4, 6.2], color=naranja, lw=1.5, linestyle="--"
    )
    flecha((18.65, 6.2), (19.2, 6.2), naranja, True)
    ax.text(
        8.95,
        7.2,
        "debug_deteccion\nDET normal",
        ha="center",
        va="center",
        fontsize=10,
        color=azul,
    )
    ax.text(
        8.95,
        2.8,
        "debug_invertida\nDET invertida",
        ha="center",
        va="center",
        fontsize=10,
        color=naranja,
    )
    ax.text(
        0.3,
        1.7,
        "Ambas rutas conservan\nla secuencia recibida.\nMap solo cambia 0 ↔ 1.",
        fontsize=10.5,
        color=gris,
        linespacing=1.5,
    )
    ax.text(
        15,
        1.7,
        "Línea continua: stream con un productor por entrada.\nLínea discontinua: mensajes PDU hacia el mismo destino.\nLos visores existentes cuentan todos los candidatos y textos.",
        ha="center",
        fontsize=10.5,
        color=gris,
        linespacing=1.5,
    )
    ax.text(
        12,
        0.45,
        "El ángulo del canal no se entrega al receptor. El acceso y el CRC permiten comprobar los candidatos.",
        ha="center",
        fontsize=10,
        color=verde,
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_bytes(salida, datos):
    fig, ax = plt.subplots(figsize=(15, 5.3))
    ax.axis("off")

    def grupos(frame):
        valores = [frame[:8], frame[8:12], frame[12:14], frame[14:18], frame[18:22]]
        out = []
        for v in valores:
            words = [f"{x:02x}" for x in v]
            out.append(
                " ".join(words[:4]) + "\n" + " ".join(words[4:])
                if len(words) > 4
                else " ".join(words)
            )
        return out

    filas = [
        ["Trama TX\n(referencia)"] + grupos(datos[0]),
        ["Decisiones RX 120°\n(agrupadas)"] + grupos(datos[1]),
        ["Después de Map\n(agrupadas)"] + grupos(datos[2]),
    ]
    table = ax.table(
        cellText=filas,
        colLabels=[
            "Origen",
            "Acceso\n8 bytes",
            "Longitud externa\n4 bytes",
            "Longitud del texto\n2 bytes",
            "Texto Hola\n4 bytes",
            "CRC\n4 bytes",
        ],
        colWidths=[0.2, 0.2, 0.15, 0.15, 0.15, 0.15],
        cellLoc="center",
        bbox=[0, 0.16, 1, 0.73],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    colors = ["#e8f1fb", "#fce8e6", "#e8f4ea"]
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#90a4ae")
        cell.set_linewidth(0.7)
        cell.set_facecolor("#e9edef" if row == 0 else colors[row - 1])
        if row == 0 or col == 0:
            cell.set_text_props(weight="bold")
        elif row > 0:
            cell.set_text_props(fontfamily="monospace")
    fig.suptitle(
        "Inversión completa de la trama y restauración mediante Map [1, 0]",
        fontsize=14,
        y=0.97,
    )
    ax.text(
        0.5,
        0.07,
        "Costas Loop y Map reales, sin ruido. La agrupación en bytes se utiliza solo para interpretar la referencia.",
        ha="center",
        fontsize=10,
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        0.015,
        "El bloque Map recibe bits individuales de valor 0 o 1; el detector interpreta después la cabecera corregida.",
        ha="center",
        fontsize=10,
        transform=ax.transAxes,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar(salida, python_gr=None):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    files = [
        salida / "enlace-84-conexion-polaridad.png",
        salida / "enlace-85-bytes-polaridad.png",
    ]
    generar_conexion(files[0])
    generar_bytes(files[1], datos_hola_invertidos(python_gr))
    return files


if __name__ == "__main__":
    for p in generar(Path(__file__).parent):
        print(p)

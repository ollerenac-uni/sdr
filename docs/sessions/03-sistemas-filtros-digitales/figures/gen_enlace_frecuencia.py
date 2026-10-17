"""Conexiones y referencia de frecuencia con Rotator, RRC y Costas reales."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


def datos_referencia(python_gr=None):
    ruta = Path(__file__).with_name("gen_enlace_ruido.py")
    spec = importlib.util.spec_from_file_location("referencia_ruido", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    x, h, _ = mod.datos_hola()
    trama = mod.modulo_local("gen_enlace_sincronizacion").trama_hola()
    bits = np.unpackbits(np.frombuffer(trama, dtype=np.uint8), bitorder="big")
    python_gr = python_gr or os.environ.get(
        "PYTHON_GR", str(Path.home() / "radioconda/bin/python3")
    )
    programa = """
import json,sys,numpy as np
from gnuradio import blocks,digital,filter,gr
p=json.load(sys.stdin);x=np.array(p['re'])+1j*np.array(p['im']);out={}
for hz in (0,10,-10):
    t=gr.top_block();s=blocks.vector_source_c(x.tolist(),False)
    r=blocks.rotator_cc(2*np.pi*hz/4000,False)
    fir=filter.fir_filter_ccf(1,p['h']);keep=blocks.keep_m_in_n(gr.sizeof_gr_complex,1,4,0)
    loop=digital.costas_loop_cc(.0628,2,False)
    esc=blocks.multiply_const_ff(1000/(2*np.pi))
    pre=blocks.vector_sink_c();post=blocks.vector_sink_c();f=blocks.vector_sink_f()
    t.connect(s,r,fir,keep,loop,post);t.connect(keep,pre);t.connect((loop,1),esc,f)
    t.run();a=np.asarray(pre.data());z=np.asarray(post.data())
    out[hz]=dict(pre_re=a.real.tolist(),pre_im=a.imag.tolist(),post_re=z.real.tolist(),post_im=z.imag.tolist(),hz=list(f.data()))
print(json.dumps(out))
"""
    resultado = subprocess.run(
        [python_gr, "-c", programa],
        input=json.dumps(
            {"re": x.real.tolist(), "im": x.imag.tolist(), "h": h.tolist()}
        ),
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return {
        int(hz): {
            "pre": np.asarray(d["pre_re"]) + 1j * np.asarray(d["pre_im"]),
            "post": np.asarray(d["post_re"]) + 1j * np.asarray(d["post_im"]),
            "hz": np.asarray(d["hz"]),
            "bits": bits,
        }
        for hz, d in json.loads(resultado.stdout).items()
    }


def generar_conexion(salida):
    fig, ax = plt.subplots(figsize=(15, 7.7))
    ax.set(xlim=(0, 23), ylim=(0, 11))
    ax.axis("off")
    azul, naranja, verde, gris = "#1565a3", "#b25d14", "#287548", "#546e7a"

    def caja(x, y, w, titulo, texto, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                1.65,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                fc="white",
                ec=color,
                lw=1.5,
            )
        )
        ax.text(
            x + w / 2,
            y + 1.3,
            titulo,
            ha="center",
            va="center",
            fontsize=11,
            color=color,
            weight="bold",
        )
        ax.text(
            x + w / 2,
            y + 0.57,
            texto,
            ha="center",
            va="center",
            fontsize=9.5,
            color="#263238",
            linespacing=1.35,
        )

    def flecha(a, b, color=azul):
        ax.add_patch(
            FancyArrowPatch(
                a, b, arrowstyle="-|>", mutation_scale=14, lw=1.5, color=color
            )
        )

    ax.text(
        11.5,
        10.4,
        "Paso 21: frecuencia del canal y estimación desde las muestras",
        ha="center",
        fontsize=15,
        weight="bold",
    )
    cajas = [
        (0.4, 3.4, "Multiply Const", "rotar_fase\nFase inicial: 0°", gris),
        (4.7, 3.4, "Rotator", "desajustar_frecuencia\n2π Δf / samp_rate", naranja),
        (9, 3.4, "Add", "sumar_ruido\nRuido: 0", naranja),
        (13.3, 3.4, "RRC RX", "filtro_rx\n4000 muestras/s", verde),
        (17.6, 4.2, "Keep M in N", "muestrear_stream\n1000 valores/s", azul),
    ]
    for x, w, titulo, texto, color in cajas:
        caja(x, 7.4, w, titulo, texto, color)
    for a, b in zip(cajas[:-1], cajas[1:]):
        flecha((a[0] + a[1], 8.2), (b[0], 8.2))
    ax.text(
        0.4,
        9.35,
        "Desde Tag Gate: muestras sin delimitación TX",
        color=gris,
        fontsize=10,
    )
    caja(17.6, 4.3, 4.2, "Costas Loop", "recuperar_fase\nOrder 2 · BW 0.0628", verde)
    flecha((19.7, 7.4), (19.7, 5.95), azul)
    caja(
        12.3,
        4.3,
        4.2,
        "Decisión y protocolo",
        "extraer_i → decidir_bits\nDos polaridades → CRC → texto",
        verde,
    )
    flecha((17.6, 5.1), (16.5, 5.1), verde)
    ax.text(17.05, 5.55, "Complex", ha="center", fontsize=8.5, color=verde)
    caja(
        17.6,
        1.1,
        4.2,
        "Multiply Const · Float",
        "frecuencia_a_hz\nsymbol_rate / (2π)",
        azul,
    )
    flecha((19.7, 4.3), (19.7, 2.75), azul)
    ax.text(20, 3.4, "frequency\nrad/muestra", fontsize=9.5, color=azul)
    caja(
        12.3,
        1.1,
        4.2,
        "QT GUI Time Sink",
        "frecuencia_estimada\n192 valores · eje vertical: Hz",
        azul,
    )
    flecha((17.6, 1.9), (16.5, 1.9), azul)
    ax.text(16.95, 2.3, "Hz", ha="center", fontsize=9.5, color=azul)
    ax.text(
        0.4,
        5.35,
        "Canal: 4000 muestras/s.\nA +10 Hz, la fase aumenta 0.9° por muestra.\nCostas recibe una muestra por símbolo.",
        fontsize=11,
        color=naranja,
        linespacing=1.5,
    )
    ax.text(
        0.4,
        2.45,
        "La salida compleja sigue hacia las dos rutas de bits.\nLa salida Float solo permite observar la estimación.\nEl receptor no recibe el desajuste configurado.",
        fontsize=11,
        color=verde,
        linespacing=1.5,
    )
    ax.text(
        11.5,
        0.3,
        "Se conservan los visores complejos anteriores y los contadores del paso 20.",
        ha="center",
        fontsize=10,
        color=gris,
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_referencia(salida, datos):
    fig = plt.figure(figsize=(13.5, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=(1, 0.9), hspace=0.4, wspace=0.25)
    izquierda, derecha, inferior = (
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, :]),
    )
    d = datos[10]
    for ax, campo, titulo in [
        (izquierda, "pre", "Antes de Costas: +10 Hz"),
        (derecha, "post", "Después de Costas: mismos instantes"),
    ]:
        z = d[campo][100:184]
        for bit, color in [(0, "#1565a3"), (1, "#cf6b17")]:
            m = d["bits"][92:176] == bit
            ax.scatter(z.real[m], z.imag[m], s=22, color=color, label=f"Bit TX {bit}")
        ax.set(
            xlim=(-1.5, 1.5),
            ylim=(-1.5, 1.5),
            xlabel="I (normalizado)",
            ylabel="Q (normalizado)",
            title=titulo,
        )
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.25)
        ax.axhline(0, color="#90a4ae", lw=0.7)
        ax.axvline(0, color="#90a4ae", lw=0.7)
        ax.legend(loc="upper right", fontsize=9)
    for hz, color in [(0, "#546e7a"), (10, "#1565a3"), (-10, "#cf6b17")]:
        f = datos[hz]["hz"]
        inferior.plot(
            np.arange(len(f)),
            f,
            color=color,
            lw=1.6,
            label=f"Estimación RX, canal {hz:+d} Hz",
        )
        inferior.axhline(hz, color=color, lw=1, ls="--", alpha=0.6)
    inferior.axvspan(0, 8, color="#90a4ae", alpha=0.12)
    inferior.axvspan(184, 192, color="#90a4ae", alpha=0.12)
    inferior.axvline(100, color="#607d8b", lw=0.8, ls=":")
    inferior.set(
        xlim=(0, 192),
        ylim=(-16, 16),
        xlabel="Tiempo de muestras procesadas (ms)",
        ylabel="Frecuencia estimada (Hz)",
        title="Primer Hola: adquisición, seguimiento y cierre",
    )
    inferior.grid(alpha=0.25)
    inferior.legend(loc="lower right", fontsize=9)
    fig.suptitle(
        "Desajuste de frecuencia y recuperación con bloques GNU Radio reales",
        fontsize=15,
        y=0.97,
    )
    fig.text(
        0.5,
        0.025,
        "Constelaciones: índices 100–183. Curvas: 192 valores a 1000 valores/s. Líneas discontinuas: referencias de evaluación.",
        ha="center",
        fontsize=9.5,
        color="#455a64",
    )
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.12, top=0.9)
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar(salida, python_gr=None, datos=None):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    datos = datos if datos is not None else datos_referencia(python_gr)
    archivos = [
        salida / "enlace-90-conexion-frecuencia.png",
        salida / "enlace-91-referencia-frecuencia.png",
    ]
    generar_conexion(archivos[0])
    generar_referencia(archivos[1], datos)
    return archivos


if __name__ == "__main__":
    for archivo in generar(Path(__file__).parent):
        print(archivo)

"""Reproduce el desajuste temporal con Delay, RRC y selección de GNU Radio."""

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
    spec = importlib.util.spec_from_file_location("referencia_ruido_tiempo", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    x, h, _ = mod.datos_hola()
    python_gr = python_gr or os.environ.get(
        "PYTHON_GR", str(Path.home() / "radioconda/bin/python3")
    )
    programa = """
import json,sys,numpy as np
from gnuradio import blocks,digital,filter,gr
p=json.load(sys.stdin);x=np.array(p['re'])+1j*np.array(p['im']);out=[]
for d,o in ((0,0),(2,0),(2,2)):
    t=gr.top_block();s=blocks.vector_source_c(x.tolist(),False)
    delay=blocks.delay(gr.sizeof_gr_complex,d)
    fir=filter.fir_filter_ccf(1,p['h'])
    keep=blocks.keep_m_in_n(gr.sizeof_gr_complex,1,4,o)
    loop=digital.costas_loop_cc(.0628,2,False)
    full=blocks.vector_sink_c();pre=blocks.vector_sink_c();post=blocks.vector_sink_c()
    t.connect(s,delay,fir,keep,loop,post);t.connect(fir,full);t.connect(keep,pre)
    t.run();v=np.asarray(full.data());a=np.asarray(pre.data());z=np.asarray(post.data())
    assert np.allclose(a,z,atol=3e-6)
    out.append(dict(retardo=d,offset=o,senal=v.real.tolist(),seleccion=a.real.tolist()))
print(json.dumps(out))
"""
    resultado = subprocess.run(
        [python_gr, "-c", programa],
        input=json.dumps({"re": x.real.tolist(), "im": x.imag.tolist(), "h": h.tolist()}),
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return {
        (d["retardo"], d["offset"]): {
            **d,
            "senal": np.asarray(d["senal"]),
            "seleccion": np.asarray(d["seleccion"]),
        }
        for d in json.loads(resultado.stdout)
    }


def generar_conexion(salida):
    fig, ax = plt.subplots(figsize=(15, 6.8))
    ax.set(xlim=(0, 23), ylim=(0, 10))
    ax.axis("off")
    azul, naranja, verde, gris = "#1565a3", "#b25d14", "#287548", "#546e7a"

    def caja(x, y, w, titulo, texto, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, 1.65, boxstyle="round,pad=0.02,rounding_size=0.08",
                fc="white", ec=color, lw=1.5,
            )
        )
        ax.text(x + w / 2, y + 1.28, titulo, ha="center", va="center", fontsize=11,
                color=color, weight="bold")
        ax.text(x + w / 2, y + 0.53, texto, ha="center", va="center", fontsize=9.5,
                color="#263238", linespacing=1.35)

    def flecha(a, b, color=azul):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14,
                                    lw=1.5, color=color))

    ax.text(11.5, 9.25, "Paso 22: desplazar la señal y observar qué muestras conserva el receptor",
            ha="center", fontsize=15, weight="bold")
    cajas = [
        (0.4, 3.5, "Canal anterior", "Fase: 0°\nFrecuencia: 0 Hz", gris),
        (4.8, 3.5, "Delay · Complex", "retardar_canal\nd = retardo_muestras", naranja),
        (9.2, 3.5, "Add", "sumar_ruido\nRuido: 0", gris),
        (13.6, 3.5, "RRC RX", "filtro_rx\n4000 muestras/s", verde),
        (18.0, 4.5, "Keep M in N", "M = 1 · N = sps\no = offset_muestreo", azul),
    ]
    for x, w, titulo, texto, color in cajas:
        caja(x, 6.9, w, titulo, texto, color)
    for a, b in zip(cajas[:-1], cajas[1:]):
        flecha((a[0] + a[1], 7.72), (b[0], 7.72))
    caja(18, 3.5, 4.5, "Costas Loop", "Fase y frecuencia\n1000 valores/s", verde)
    flecha((20.25, 6.9), (20.25, 5.15))
    caja(12.2, 3.5, 4.7, "Protocolo y texto", "Dos polaridades\nLongitud → CRC → UTF-8", verde)
    flecha((18, 4.32), (16.9, 4.32), verde)
    ax.text(0.4, 5.1, "Parámetros independientes", color="#263238", fontsize=12, weight="bold")
    ax.text(0.4, 4.35, "d: retardo del canal, en muestras.", color=naranja, fontsize=11)
    ax.text(0.4, 3.7, "o: posición seleccionada dentro de cada grupo.", color=azul, fontsize=11)
    ax.text(0.4, 2.85, "Con sps = 4, d = 2 desplaza medio símbolo.\nCostas no cambia los instantes de selección.",
            color=gris, fontsize=11, linespacing=1.5)
    ax.text(11.5, 1.3, "Control diagnóstico: el operador fija o = 2 para el canal d = 2.\nEl receptor todavía no estima el instante de muestreo.",
            ha="center", color=azul, fontsize=12, linespacing=1.5)
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_referencia(salida, datos=None):
    datos = datos if datos is not None else datos_referencia()
    fig, axs = plt.subplots(3, 2, figsize=(14, 10.3), gridspec_kw={"width_ratios": [2.5, 1]})
    azul, naranja = "#1565a3", "#b25d14"
    nombres = ["Referencia: d = 0, o = 0", "Medio símbolo: d = 2, o = 0",
               "Control manual: d = 2, o = 2"]
    for fila, ((d, o), nombre) in enumerate(zip(((0, 0), (2, 0), (2, 2)), nombres)):
        row = datos[d, o]
        senal, seleccion = row["senal"], row["seleccion"]
        idx = np.arange(32, 32 + 49)
        elegidos = 32 + o + np.arange(12) * 4
        ax = axs[fila, 0]
        ax.plot((idx - 32) / 4, senal[idx], color=azul, lw=1.7, label="Salida del filtro RX")
        ax.scatter((elegidos - 32) / 4, senal[elegidos], color=naranja, s=31, zorder=4,
                   label="Muestras conservadas")
        for nivel in (-1, 1):
            ax.axhline(nivel, color="#87959e", ls="--", lw=0.7, alpha=0.65)
        ax.set(title=nombre, xlim=(-0.15, 12), ylim=(-2, 2), ylabel="I (amplitud)",
               xlabel="Tiempo / T desde el inicio nominal de la trama")
        ax.set_xticks(np.arange(13))
        ax.grid(alpha=0.22)
        if fila == 0:
            ax.legend(loc="lower left", fontsize=8.5)
        ax = axs[fila, 1]
        trama = seleccion[8:184]
        ax.scatter(trama, np.zeros_like(trama), color=azul, s=20, alpha=0.65)
        ax.axhline(0, color="#87959e", lw=0.5)
        ax.set(xlim=(-2, 2), ylim=(-2, 2), xlabel="I", ylabel="Q",
               title="Selección: 176 valores de trama")
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.22)
    fig.suptitle("Retardo constante: forma temporal e instantes seleccionados\nHola · 4000 muestras/s · 1000 símbolos/s · RRC α = 0.35 · sin ruido",
                 fontsize=14, weight="bold", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=2)
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    carpeta = Path(__file__).parent
    generar_conexion(carpeta / "enlace-92-conexion-tiempo.png")
    generar_referencia(carpeta / "enlace-93-referencia-tiempo.png")

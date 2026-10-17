"""Figuras de adquisición y seguimiento con bloques reales de GNU Radio."""

import json
import os
from pathlib import Path
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np


AZUL, NARANJA, VERDE = "#1565a3", "#b25d14", "#287548"


def datos_referencia(python_gr=None):
    python_gr = python_gr or os.environ.get(
        "PYTHON_GR", str(Path.home() / "radioconda/bin/python3")
    )
    programa = r"""
import json,struct,zlib,numpy as np
from gnuradio import blocks,digital,filter,gr
from gnuradio.filter import firdes
access=bytes.fromhex('ac dd a4 e2 f2 8c 20 fc')
code=np.unpackbits(np.frombuffer(access,dtype=np.uint8),bitorder='big')
hx=firdes.root_raised_cosine(4,4000,1000,.35,33)
hr=firdes.root_raised_cosine(1,4000,1000,.35,33)
def caso(text,d,ppm,canal):
 b=text.encode();p=struct.pack('>H',len(b))+b;p+=struct.pack('>I',zlib.crc32(p))
 frame=access+struct.pack('>HH',len(p),len(p))+p
 bits=np.unpackbits(np.frombuffer(frame,dtype=np.uint8),bitorder='big')
 # Misma forma de onda que el FIR interpolador, con los cierres existentes.
 up=np.zeros((len(bits)+8)*4,dtype=complex);up[:len(bits)*4:4]=2*bits.astype(int)-1
 x=np.r_[np.convolve(up,hx)[:len(up)],np.zeros(32)]
 t=gr.top_block();src=blocks.vector_source_c(x.tolist(),False)
 delay=blocks.delay(gr.sizeof_gr_complex,d);fir=filter.fir_filter_ccf(1,hr)
 res=filter.mmse_resampler_cc(0,1/(1+ppm*1e-6))
 sync=digital.symbol_sync_cc(digital.TED_GARDNER,4,.08,1,.5,.05,1,digital.constellation_bpsk().base(),digital.IR_MMSE_8TAP,128,[])
 loop=digital.costas_loop_cc(.0628,2,False);keep=blocks.keep_m_in_n(gr.sizeof_gr_complex,1,4,0)
 fixed,z,post=[blocks.vector_sink_c() for _ in range(3)];period=blocks.vector_sink_f();null=blocks.null_sink(4)
 t.connect(src,delay)
 if canal:t.connect(delay,res,fir)
 else:t.connect(delay,fir)
 t.connect(fir,keep,fixed);t.connect(fir,sync,z);t.connect(sync,loop,post)
 t.connect((sync,1),(null,0));t.connect((sync,2),(null,1));t.connect((sync,3),period);t.run()
 a=np.asarray(post.data());received=(a.real>=0).astype(np.uint8);found=[]
 for inv in (0,1):
  bb=received^inv
  for i in range(len(bb)-96):
   if np.array_equal(bb[i:i+64],code):
    n,k=struct.unpack('>HH',np.packbits(bb[i+64:i+96]).tobytes())
    if n==k and i+96+8*n<=len(bb):found.append(np.packbits(bb[i+96:i+96+8*n]).tobytes())
 return dict(ppm=ppm,retardo=d,fijo=np.asarray(fixed.data()).real.tolist(),
  recuperado=np.asarray(z.data()).real.tolist(),periodo=list(period.data()),ok=found==[p])
print(json.dumps(dict(adquisicion=caso('Hola',2,0,False),
 seguimiento=[caso('SDR '*199+'SDR',0,ppm,True) for ppm in (0,1000,-1000)])))
"""
    r = subprocess.run(
        [python_gr, "-c", programa],
        capture_output=True,
        text=True,
        check=True,
        timeout=25,
    )
    return json.loads(r.stdout)


def generar_conexion(salida):
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.set(xlim=(0, 24), ylim=(0, 12))
    ax.axis("off")

    def caja(x, y, w, titulo, texto, color=AZUL):
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, 1.8, boxstyle="round,pad=0.03", fc="white", ec=color, lw=1.6
            )
        )
        ax.text(
            x + w / 2,
            y + 1.35,
            titulo,
            ha="center",
            color=color,
            fontsize=11,
            weight="bold",
        )
        ax.text(
            x + w / 2,
            y + 0.6,
            texto,
            ha="center",
            va="center",
            fontsize=10,
            linespacing=1.35,
        )

    def flecha(a, b, color=AZUL):
        ax.add_patch(
            FancyArrowPatch(
                a, b, arrowstyle="-|>", mutation_scale=14, lw=1.5, color=color
            )
        )

    caja(0.4, 8.6, 3.8, "Delay", "retardar_canal\nretardo inicial", NARANJA)
    caja(5, 8.6, 5, "Fractional Resampler", "desajustar_reloj\nsolo ensayo B", NARANJA)
    caja(11, 8.6, 4.2, "Add", "sumar_ruido\nruido cero", NARANJA)
    caja(16.2, 8.6, 4.2, "RRC RX", "filtro_rx\nsps nominal = 4", VERDE)
    for a, b in [
        ((4.2, 9.5), (5, 9.5)),
        ((10, 9.5), (11, 9.5)),
        ((15.2, 9.5), (16.2, 9.5)),
    ]:
        flecha(a, b, NARANJA)
    caja(
        16.2, 5, 4.2, "Symbol Sync", "sincronizar_simbolos\nGardner · salida 1/símbolo"
    )
    flecha((18.3, 8.6), (18.3, 6.8))
    caja(
        9,
        5,
        5.2,
        "Costas y protocolo",
        "Fase → dos polaridades\nLongitud → CRC → texto",
        VERDE,
    )
    flecha((16.2, 5.9), (14.2, 5.9), VERDE)
    ax.text(
        8.7,
        7.3,
        "Salida compleja → constelación anterior a Costas",
        color=AZUL,
        fontsize=10,
    )
    caja(0.4, 1, 6, "QT GUI Time Sink", "T_avg · Float\nTemporizacion · pestaña 3")
    caja(8, 1, 6.2, "Null Sink · Float", "error → entrada 0\nT_inst → entrada 1")
    flecha((16.2, 5.2), (11.1, 2.8))
    flecha((16.2, 5), (3.4, 2.8))
    ax.text(
        0.4,
        5.8,
        "Ensayo A: conexión directa Delay → Add.\nEnsayo B: remuestreador del canal activo.",
        fontsize=11,
        linespacing=1.6,
    )
    ax.text(
        0.4,
        4.1,
        "Keep M in N permanece deshabilitado.\nEl receptor solo conoce sps nominal.",
        fontsize=11,
        linespacing=1.6,
        color=VERDE,
    )
    ax.text(
        12,
        11.3,
        "Paso 23: recuperación temporal y diagnóstico del período estimado",
        ha="center",
        fontsize=15,
        weight="bold",
    )
    fig.tight_layout()
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_adquisicion(salida, datos=None):
    datos = datos if datos is not None else datos_referencia()
    r = datos["adquisicion"]
    fig, axs = plt.subplots(
        1, 3, figsize=(15, 4.6), gridspec_kw={"width_ratios": [1, 1, 1.65]}
    )
    for ax, key, title, color in zip(
        axs[:2],
        ("fijo", "recuperado"),
        ("Selector fijo · offset 0", "Symbol Sync · Gardner"),
        (NARANJA, AZUL),
    ):
        y = np.asarray(r[key])
        ax.scatter(y, np.zeros_like(y), s=18, alpha=0.65, color=color)
        ax.set(xlim=(-2, 2), ylim=(-2, 2), xlabel="I", ylabel="Q", title=title)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.22)
    axs[2].plot(r["periodo"], color=AZUL, label="T_avg RX")
    axs[2].axhline(4, color="#566573", ls="--", label="Referencia: 4")
    axs[2].set(
        xlabel="Índice de salida del sincronizador",
        ylabel="Muestras / símbolo",
        title="Adquisición del primer Hola",
        ylim=(3.94, 4.06),
    )
    axs[2].legend(fontsize=9)
    axs[2].grid(alpha=0.22)
    fig.suptitle(
        "Retardo: 2 muestras · relojes iguales · sin ruido, fase ni desajuste de frecuencia",
        fontsize=13,
        weight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


def generar_seguimiento(salida, datos=None):
    datos = datos if datos is not None else datos_referencia()
    fig, axs = plt.subplots(2, 1, figsize=(13, 7))
    for r, color in zip(datos["seguimiento"], (AZUL, NARANJA, VERDE)):
        y = np.asarray(r["periodo"])
        p = 4 * (1 + r["ppm"] * 1e-6)
        etiqueta = f"{r['ppm']:+d} ppm · referencia {p:.3f}"
        axs[0].plot(y, color=color, lw=0.8, alpha=0.8, label=etiqueta)
        # Promedio móvil solo para la figura; no alimenta el sincronizador.
        promedio = np.convolve(y, np.ones(256) / 256, mode="valid")
        indices = np.arange(255, len(y))
        ventana = (indices >= len(y) - 2048) & (indices < len(y) - 16)
        axs[1].plot(
            indices[ventana], promedio[ventana], color=color, lw=1.4, label=etiqueta
        )
        for ax in axs:
            ax.axhline(p, color=color, ls="--", lw=0.9, alpha=0.7)
            ax.grid(alpha=0.22)
            ax.set_ylabel("Muestras / símbolo")
    axs[0].set(
        ylim=(3.94, 4.06),
        title="T_avg directo: adquisición y paquete completo",
        xlabel="Índice de salida del sincronizador",
    )
    axs[0].legend(loc="upper right", fontsize=9)
    axs[1].set(
        ylim=(3.993, 4.007),
        xlabel="Índice de salida del sincronizador",
        title="Tramo final: promedio móvil de 256 valores de T_avg",
    )
    fig.suptitle(
        "Un mismo Symbol Sync · texto de 799 bytes · sps nominal = 4 · sin ruido",
        fontsize=14,
        weight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(salida, dpi=160, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    carpeta = Path(__file__).parent
    datos = datos_referencia()
    assert datos["adquisicion"]["ok"] and all(r["ok"] for r in datos["seguimiento"])
    generar_conexion(carpeta / "enlace-100-conexion-reloj.png")
    generar_adquisicion(carpeta / "enlace-101-adquisicion-reloj.png", datos)
    generar_seguimiento(carpeta / "enlace-102-seguimiento-reloj.png", datos)

#!/usr/bin/env python3
"""Reproduce las vistas de la captura oficial, sin escribir audio.

Las primeras dos figuras ejecutan las celdas independientes de la lección.
La vista previa de S04 calcula la mezcla fuera de las celdas obligatorias.
"""

from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).parent
CAPTURA = OUT.parents[3] / "samples/fm_99p1MHz_2p4Msps_g30.cu8"
NOMBRES = ["captura-promedio-rf.png", "captura-waterfall.png", "captura-adelanto-seleccion.png"]


def celda(apartado):
    texto = (OUT.parent / "index.md").read_text(encoding="utf-8")
    bloque = texto.split(f"#### {apartado}. ", 1)[1]
    bloque = re.split(r"^#### ", bloque, maxsplit=1, flags=re.MULTILINE)[0]
    return re.findall(r"```python\n(.*?)```", bloque, re.DOTALL)[0]


def ejecutar(apartado, captura):
    entorno = {"__name__": "__colab__", "ruta_captura": Path(captura)}
    exec(compile(celda(apartado), f"s02-{apartado}", "exec"), entorno)
    return entorno


def datos_adelanto(captura):
    fs, N, bloques = 2400000, 4096, 200
    raw = np.fromfile(captura, dtype=np.uint8, count=2 * N * bloques)
    if raw.size != 2 * N * bloques:
        raise ValueError("Se necesitan 200 bloques completos de 4096 muestras I/Q")
    if Path(captura).stat().st_size % 2:
        raise ValueError("El archivo CU8 debe contener pares completos I/Q")
    v = (raw.astype(np.float32) - 127.5) / 127.5
    z = v[0::2] + 1j * v[1::2]
    y = z * np.exp(1j * 2 * np.pi * 1e6 * np.arange(z.size) / fs)
    w = np.hanning(N + 1)[:-1]
    potencias = []
    for datos in (z, y):
        X = np.fft.fftshift(np.fft.fft(datos.reshape(bloques, N) * w, axis=1), axes=1)
        potencias.append((np.abs(X) ** 2 / w.sum() ** 2).mean(axis=0))
    referencia = max(potencias[0].max(), np.finfo(float).tiny)
    db = 10 * np.log10(np.maximum(np.asarray(potencias) / referencia, 1e-12))
    f = np.fft.fftshift(np.fft.fftfreq(N, 1 / fs)) / 1e6
    return {"fs": fs, "z": z, "y": y, "f": f, "db": db}


def figura_adelanto(captura):
    d = datos_adelanto(captura)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), layout="constrained")
    for ax, valores, objetivo, titulo in zip(axes, d["db"], [-1, 0], ["A. Entrada: objetivo en −1 MHz", "B. Después de centrar: objetivo en 0 MHz"]):
        ax.plot(d["f"], valores, color="tab:blue", linewidth=0.8)
        ax.axvspan(objetivo - 0.1, objetivo + 0.1, color="tab:orange", alpha=0.18, label="Región de referencia, no filtro aplicado")
        ax.axvline(objetivo, color="tab:orange", linestyle="--", label="Centro de la banda objetivo")
        ax.set(title=titulo, xlabel="Frecuencia en baseband (MHz)", ylabel="Potencia relativa (dB)", xlim=(-1.2, 1.2), ylim=(-65, 14))
        ax.grid(alpha=0.2)
        ax.legend(loc="upper right")
    return fig


def generar(salida=OUT, captura=CAPTURA):
    salida, captura = Path(salida), Path(captura)
    if not captura.is_file():
        raise FileNotFoundError(f"Falta la grabación: {captura}")
    salida.mkdir(parents=True, exist_ok=True)
    paths = []
    original = plt.show

    def guardar():
        path = salida / NOMBRES[len(paths)]
        plt.gcf().savefig(path, dpi=160, facecolor="white")
        plt.close("all")
        paths.append(path)

    try:
        plt.show = guardar
        with plt.rc_context({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
            ejecutar("6.2", captura)
            ejecutar("6.3", captura)
            figura_adelanto(captura)
            guardar()
    finally:
        plt.show = original
        plt.close("all")
    return paths


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captura", type=Path, default=CAPTURA)
    parser.add_argument("--salida", type=Path, default=OUT)
    args = parser.parse_args()
    for path in generar(args.salida, args.captura):
        print(path)

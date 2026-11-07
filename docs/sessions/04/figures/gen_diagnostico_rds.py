#!/usr/bin/env python3
"""Dibuja el barrido medido y compara dos multiplex; no necesita las grabaciones I/Q."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


BASE = Path(__file__).resolve().parent


def generar():
    datos = json.loads((BASE / "diagnostico-rds-datos.json").read_text())
    filas = datos["barrido"]["resultados"]
    frecuencias = np.array([r["frecuencia_mhz"] for r in filas])
    tiempos = np.array([r["observacion_real_s"] for r in filas])
    grupos = np.array([r["grupos_validos"] for r in filas])
    bits = np.array([r["bits_consumidos"] for r in filas])
    fig, ax = plt.subplots(2, 1, figsize=(11, 5.8), sharex=True, layout="constrained")
    ax[0].stem(frecuencias, grupos / tiempos, basefmt=" ", linefmt="#1167b1", markerfmt=".")
    ax[0].set_ylabel("Grupos válidos/s")
    ax[0].set_title("Barrido en Lima: grupos válidos y flujo de bits son medidas distintas")
    ax[1].plot(frecuencias, bits, ".", color="#1167b1", ms=3)
    ax[1].axhline(1187.5 * np.median(tiempos), ls="--", lw=1, color="#b55d00",
                  label="Referencia nominal para una ventana de 2.2 s")
    ax[1].set_ylabel("Bits consumidos por ventana")
    ax[1].set_ylim(0, max(bits) * 1.15)
    ax[1].set_xlabel("Frecuencia sintonizada (MHz)")
    ax[1].legend(loc="lower right")
    for a in ax:
        a.axvspan(87, 88, color="0.90")
        a.set_xlim(87, 108)
        a.grid(alpha=0.25)
    ax[0].text(87.1, ax[0].get_ylim()[1] * .9, "Margen\nexplorado", fontsize=8)
    fig.savefig(BASE / "19-barrido-rds.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True, layout="constrained")
    for a, espectro in zip(ax, datos["espectros"]):
        a.plot(np.array(espectro["frecuencias_hz"]) / 1000,
               espectro["densidad_relativa_db"], color="#1167b1", lw=1)
        a.axvspan(54.625, 59.375, color="#dbeafe", alpha=.6)
        a.axvline(57, color="#b55d00", ls="--", lw=1)
        a.set_ylabel("PSD relativa (dB)")
        a.set_title("%.1f MHz — %d grupos válidos durante %.1f s" % (
            espectro["frecuencia_mhz"], espectro["grupos_validos"], espectro["observacion_real_s"]))
        a.set_xlim(50, 65)
        a.set_ylim(-25, 3)
        a.grid(alpha=.25)
    ax[-1].set_xlabel("Frecuencia del multiplex después de Quadrature Demod (kHz)")
    fig.suptitle("La presencia de energía cerca de 57 kHz requiere una comprobación de datos")
    fig.savefig(BASE / "20-espectros-rds.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    generar()

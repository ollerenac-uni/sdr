"""Grafica la magnitud del archivo SigMF de la práctica."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    carpeta = Path(__file__).resolve().parent
    archivo = carpeta.parents[3] / "output/lorawan-iq/correcto.sigmf-data"
    metadatos = json.loads(archivo.with_suffix(".sigmf-meta").read_text(encoding="utf-8"))
    tasa = metadatos["global"]["core:sample_rate"]
    magnitud = np.abs(np.fromfile(archivo, dtype="<c8"))
    activas = np.flatnonzero(magnitud)
    inicio = activas[0] * 1_000 / tasa
    fin = (activas[-1] + 1) * 1_000 / tasa
    duracion = magnitud.size * 1_000 / tasa
    tiempo = np.arange(magnitud.size) * 1_000 / tasa

    figura, eje = plt.subplots(figsize=(10, 3), layout="constrained")
    eje.axvspan(0, inicio, color="#edf2f7")
    eje.axvspan(fin, duracion, color="#edf2f7")
    eje.plot(tiempo, magnitud, color="#2563a6", linewidth=1.6)
    eje.text(inicio / 2, 0.45, "Ceros", ha="center", color="#41576c")
    eje.text((inicio + fin) / 2, 1.15, f"Paquete LoRa · {fin - inicio:.3f} ms",
             ha="center", color="#18334e", fontweight="bold")
    eje.text((fin + duracion) / 2, 0.45, "Ceros de cierre", ha="center", color="#41576c")
    marcas = (0, inicio, fin, duracion)
    eje.set_xticks(marcas, labels=["0", *(f"{marca:.3f}" for marca in marcas[1:])])
    eje.set(xlim=(0, duracion), ylim=(-0.08, 1.38), yticks=(0, 1),
            xlabel="Tiempo desde el inicio del archivo (ms)", ylabel="Magnitud de I/Q")
    eje.spines[["top", "right"]].set_visible(False)

    figura.savefig(carpeta / "registro-iq-lora.png", dpi=160)
    plt.close(figura)


if __name__ == "__main__":
    main()

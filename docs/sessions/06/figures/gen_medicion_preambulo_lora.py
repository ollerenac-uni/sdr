"""Marca las referencias de medición sobre el preámbulo del archivo de práctica."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    carpeta = Path(__file__).resolve().parent
    archivo = carpeta.parents[3] / "output/lorawan-iq/correcto.sigmf-data"
    meta = json.loads(archivo.with_suffix(".sigmf-meta").read_text(encoding="utf-8"))
    tasa = meta["global"]["core:sample_rate"]
    iq = np.fromfile(archivo, dtype="<c8")
    inicio = int(np.flatnonzero(iq)[0])
    muestras_por_simbolo = tasa * 2**7 // 125_000
    preambulo = iq[inicio:inicio + 8 * muestras_por_simbolo]
    periodo_ms = muestras_por_simbolo * 1_000 / tasa
    inicio_ms = inicio * 1_000 / tasa
    izquierda = inicio_ms + periodo_ms
    derecha = izquierda + 4 * periodo_ms

    ventana, salto = 128, 16
    # Los bordes de la primera y última columna rodean el centro de cada FFT.
    margen_ms = (ventana - salto) / 2 * 1_000 / tasa
    figura, eje = plt.subplots(figsize=(10, 3.3), layout="constrained")
    eje.specgram(
        preambulo, NFFT=ventana, Fs=tasa / 1_000, noverlap=ventana - salto,
        xextent=(inicio_ms + margen_ms, inicio_ms + 8 * periodo_ms - margen_ms),
        cmap="magma", vmin=-37, vmax=-6,
    )
    for limite in (-62.5, 62.5):
        eje.axhline(limite, color="#83ecd8", linestyle="--", linewidth=1.1)
    for numero in range(5):
        eje.axvline(
            izquierda + numero * periodo_ms, color="white",
            linestyle="-" if numero in (0, 4) else ":", linewidth=1,
        )
    eje.annotate(
        "", xy=(derecha, 90), xytext=(izquierda, 90),
        arrowprops={"arrowstyle": "<->", "color": "white", "linewidth": 1.4},
    )
    eje.text(
        (izquierda + derecha) / 2, 102, f"4 símbolos · {derecha - izquierda:.3f} ms",
        color="white", ha="center", fontsize=11,
    )
    eje.set(
        xlim=(izquierda - 0.55, derecha + 0.55), ylim=(-92, 125),
        xlabel="Tiempo desde el inicio del archivo (ms)", ylabel="Frecuencia relativa (kHz)",
        xticks=[izquierda + n * periodo_ms for n in range(5)], yticks=(-62.5, 0, 62.5),
    )
    figura.savefig(carpeta / "medicion-preambulo-lora.png", dpi=160)
    plt.close(figura)


if __name__ == "__main__":
    main()

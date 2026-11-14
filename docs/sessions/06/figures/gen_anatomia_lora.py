"""Anota el espectrograma del paquete generado por verificar_lorawan_iq.py."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    figuras = Path(__file__).resolve().parent
    raiz = figuras.parents[3]
    archivo = raiz / "output/lorawan-iq/correcto.sigmf-data"
    metadatos = json.loads(archivo.with_suffix(".sigmf-meta").read_text())
    tasa = metadatos["global"]["core:sample_rate"]
    iq = np.fromfile(archivo, dtype="<c8")
    activas = np.flatnonzero(np.abs(iq) > 0.5)
    inicio, fin = int(activas[0]), int(activas[-1]) + 1

    # Ocho upchirps, dos símbolos de sync word y 2.25 downchirps.
    # En SF7, la cabecera ocupa el primer bloque entrelazado (8 símbolos).
    # Los 44 grupos de 4 bits del payload y CRC ocupan 7 bloques de 5 símbolos.
    # El penúltimo bloque lleva 5 grupos del payload y 2 del CRC.
    # El último bloque lleva los 2 grupos restantes del CRC y relleno.
    duracion_simbolo = 1_000 * 2**7 / 125_000
    inicio_paquete = inicio * 1_000 / tasa
    inicio_cabecera = inicio_paquete + 12.25 * duracion_simbolo
    inicio_payload = inicio_cabecera + 8 * duracion_simbolo
    inicio_crc = inicio_payload + 25 * duracion_simbolo
    fin_payload = inicio_crc + 5 * duracion_simbolo
    fin_paquete = inicio_payload + 35 * duracion_simbolo
    if fin != round(fin_paquete * tasa / 1_000):
        raise ValueError("La duración del archivo de práctica no coincide con la estructura anotada.")

    ventana, salto, longitud_fft = 112, 16, 512
    muestras = iq[inicio:fin]
    muestras = np.pad(muestras, (ventana // 2, ventana // 2))
    segmentos = np.lib.stride_tricks.sliding_window_view(muestras, ventana)[::salto]
    espectro = np.fft.fftshift(
        np.fft.fft(segmentos * np.hanning(ventana), n=longitud_fft, axis=1), axes=1
    )
    amplitud = np.abs(espectro)
    nivel_db = 20 * np.log10(np.maximum(amplitud / amplitud.max(), 1e-6))
    tiempo = inicio_paquete + np.arange(len(segmentos)) * salto / tasa * 1_000
    frecuencia = np.fft.fftshift(np.fft.fftfreq(longitud_fft, 1 / tasa)) / 1_000
    banda_visible = np.abs(frecuencia) < 110

    figura, eje = plt.subplots(figsize=(12, 3.8), layout="constrained")
    eje.set_facecolor(plt.get_cmap("magma")(0.0))
    eje.pcolormesh(
        tiempo, frecuencia[banda_visible], nivel_db[:, banda_visible].T,
        shading="nearest", cmap="magma", vmin=-32, vmax=0, rasterized=True,
    )
    eje.set(
        xlim=(inicio_paquete, fin_paquete), ylim=(-138, 79),
        xlabel="Tiempo desde el inicio del archivo (ms)",
        ylabel="Frecuencia relativa (kHz)",
        yticks=(-62.5, 0, 62.5),
    )
    for limite in (inicio_cabecera, inicio_payload):
        eje.axvline(limite, color="white", linestyle="--", linewidth=1, alpha=0.9)
    for limite in (inicio_crc, fin_payload):
        eje.vlines(limite, -76, 79, color="white", linestyle=":", linewidth=1, alpha=0.7)

    marcas = (inicio_paquete, inicio_cabecera, inicio_payload, inicio_crc, fin_payload, fin_paquete)
    eje.set_xticks(marcas, labels=[f"{marca:.3f}" for marca in marcas], fontsize=9)

    transformacion = eje.get_xaxis_transform()
    eje.plot(
        [inicio_cabecera, inicio_cabecera, fin_paquete, fin_paquete],
        [1.181, 1.2, 1.2, 1.181], transform=transformacion,
        color="#41576c", linewidth=1, clip_on=False,
    )
    eje.text(
        (inicio_cabecera + fin_paquete) / 2, 1.213, "Después del preámbulo · 43 símbolos",
        transform=transformacion, ha="center", va="bottom", fontsize=10, color="#18334e",
    )

    for izquierda, derecha, titulo, cantidad in (
        (inicio_paquete, inicio_cabecera, "Preámbulo", "12.25 períodos"),
        (inicio_cabecera, inicio_payload, "Cabecera", "8 símbolos"),
        (inicio_payload, fin_paquete, "Payload y CRC", "35 símbolos"),
    ):
        centro = (izquierda + derecha) / 2
        eje.text(
            centro, 1.09, titulo, transform=eje.get_xaxis_transform(),
            ha="center", va="bottom", fontsize=11, fontweight="bold",
        )
        eje.text(
            centro, 1.025, cantidad, transform=eje.get_xaxis_transform(),
            ha="center", va="bottom", fontsize=9,
        )

    altura = -91
    for izquierda, derecha, texto, color in (
        (inicio_payload, inicio_crc, "Solo payload\n25 símbolos", "#a5cbff"),
        (inicio_crc, fin_payload, "Payload y CRC\n5 símbolos", "#ffe0a0"),
        (fin_payload, fin_paquete, "CRC y relleno\n5 símbolos", "#a0f5e9"),
    ):
        eje.plot(
            [izquierda, izquierda, derecha, derecha],
            [altura + 6, altura, altura, altura + 6], color=color, linewidth=1.4,
            clip_on=False,
        )
        eje.text(
            (izquierda + derecha) / 2, altura - 4, texto, color=color,
            ha="center", va="top", fontsize=9,
        )
    figura.savefig(figuras / "anatomia-paquete-lora.png", dpi=180)
    plt.close(figura)


if __name__ == "__main__":
    main()

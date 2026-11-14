"""Compara el FRMPayload de las dos muestras verificadas de la práctica."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    carpeta = Path(__file__).resolve().parent
    informe = carpeta.parents[3] / "gnuradio/samples/lorawan-didactico/verificacion.json"
    casos = json.loads(informe.read_text(encoding="utf-8"))["casos"]
    tramas = {
        caso["caso"]: bytes.fromhex(caso["lora_phy"]["payload_hex"]) for caso in casos
    }
    original = tramas["correcto"]
    alterada = tramas["contenido_alterado"]
    if len(original) != 20 or len(alterada) != 20 or original[5] & 0x0F or alterada[5] & 0x0F:
        raise ValueError("La figura corresponde a las dos tramas de 20 bytes sin FOpts.")

    figura, eje = plt.subplots(figsize=(8.0, 2.25), layout="constrained")
    eje.set(xlim=(-0.4, 9.65), ylim=(0, 3.1))
    eje.axis("off")
    eje.text(0, 2.58, "Byte en la trama", va="center", color="#41576c", fontsize=11)

    for posicion in range(10, 17):
        x = posicion - 7
        eje.text(x, 2.58, str(posicion), ha="center", va="center", color="#41576c")
        distinto = original[posicion - 1] != alterada[posicion - 1]
        tinta = "#983b1a" if distinto else "#562483"
        fondo = "#fff0df" if distinto else "#eee5f8"
        for y, trama in ((1.62, original), (0.62, alterada)):
            eje.text(
                x, y, f"{trama[posicion - 1]:02x}",
                ha="center", va="center", fontfamily="monospace", fontsize=15,
                color=tinta, bbox={"boxstyle": "round,pad=0.36", "facecolor": fondo,
                                   "edgecolor": tinta if distinto else "none"},
            )

    eje.text(0, 1.62, "Trama original", va="center", fontsize=12, color="#18334e")
    eje.text(0, 0.62, "Trama de prueba", va="center", fontsize=12, color="#18334e")
    figura.savefig(carpeta / "comparacion-crc-mic.png", dpi=160)
    plt.close(figura)


if __name__ == "__main__":
    main()

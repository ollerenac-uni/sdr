"""Dibuja el PHYPayload recuperado de la muestra de la práctica."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def main():
    carpeta = Path(__file__).resolve().parent
    informe = carpeta.parents[3] / "gnuradio/samples/lorawan-didactico/verificacion.json"
    casos = json.loads(informe.read_text(encoding="utf-8"))["casos"]
    caso = next(caso for caso in casos if caso["caso"] == "correcto")
    datos = bytes.fromhex(caso["lora_phy"]["payload_hex"])
    if len(datos) != 20 or datos[5] & 0x0F:
        raise ValueError("La figura corresponde a la trama de 20 bytes sin FOpts.")

    figura, eje = plt.subplots(figsize=(12, 2.6), layout="constrained")
    eje.set(xlim=(-0.2, len(datos) + 0.2), ylim=(0, 3.6))
    eje.axis("off")

    for izquierda, derecha, nombre, altura in (
        (0, 20, "PHYPayload", 3.06),
        (1, 16, "MACPayload", 2.49),
        (1, 8, "FHDR", 1.92),
    ):
        eje.plot(
            [izquierda, izquierda, derecha, derecha],
            [altura - 0.11, altura, altura, altura - 0.11],
            color="#577087", linewidth=1.15,
        )
        eje.text((izquierda + derecha) / 2, altura + 0.05, nombre,
                 ha="center", va="bottom", color="#18334e", fontsize=11)

    for izquierda, derecha, nombre, fondo, tinta in (
        (0, 1, "MHDR", "#edf2f7", "#18334e"),
        (1, 5, "DevAddr", "#edf2f7", "#18334e"),
        (5, 6, "FCtrl", "#edf2f7", "#18334e"),
        (6, 8, "FCnt", "#edf2f7", "#18334e"),
        (8, 9, "FPort", "#edf2f7", "#18334e"),
        (9, 16, "FRMPayload · mensaje cifrado", "#ece1f9", "#562483"),
        (16, 20, "MIC", "#def2eb", "#11624d"),
    ):
        eje.add_patch(Rectangle((izquierda, 0.57), derecha - izquierda, 0.9,
                                facecolor=fondo, edgecolor=tinta, linewidth=1))
        eje.text((izquierda + derecha) / 2, 1.57, nombre, ha="center",
                 va="bottom", color=tinta, fontsize=10, fontweight="bold")
        for indice in range(izquierda, derecha):
            eje.text(indice + 0.5, 1.02, f"{datos[indice]:02x}", ha="center",
                     va="center", color=tinta, fontsize=14, family="monospace")

    for indice in range(len(datos)):
        eje.text(indice + 0.5, 0.27, str(indice + 1), ha="center",
                 va="center", color="#41576c", fontsize=10)

    figura.savefig(carpeta / "anatomia-trama-lorawan.png", dpi=160)
    plt.close(figura)


if __name__ == "__main__":
    main()

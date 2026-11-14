"""Dibuja dos barridos LoRa ideales a igual ancho de banda."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    ancho_hz = 125_000
    borde_khz = ancho_hz / 2_000
    duracion_sf7_ms = 1_000 * 2**7 / ancho_hz
    ventana_ms = 2 * duracion_sf7_ms

    figura, paneles = plt.subplots(
        2, 1, sharex=True, sharey=True, figsize=(8.8, 4.1), layout="constrained"
    )
    figura.suptitle(f"Misma banda de {ancho_hz / 1_000:g} kHz", fontsize=16, fontweight="bold")
    figura.supylabel("Frecuencia relativa al centro (kHz)", fontsize=12)

    for eje, sf, simbolos, color in zip(
        paneles, (7, 8), (2, 1), ("#2563a6", "#7951a4")
    ):
        duracion_ms = 1_000 * 2**sf / ancho_hz
        unidad = "símbolos" if simbolos == 2 else "símbolo"
        eje.set_title(f"SF{sf} · {simbolos} {unidad}", loc="left", color=color, fontweight="bold")
        for indice in range(simbolos):
            eje.plot(
                [indice * duracion_ms, (indice + 1) * duracion_ms],
                [-borde_khz, borde_khz], color=color, linewidth=3,
            )
        eje.set(xlim=(-0.03, ventana_ms + 0.03), ylim=(-78, 78))
        eje.set_yticks([-borde_khz, borde_khz], labels=[f"−{borde_khz:g}", f"+{borde_khz:g}"])
        eje.grid(color="#d7dfe7", linestyle="--")
        eje.spines[["top", "right"]].set_visible(False)

    paneles[-1].set_xticks([0, duracion_sf7_ms, ventana_ms])
    paneles[-1].set_xlabel("Tiempo (ms)", fontsize=12)
    salida = Path(__file__).with_name("comparacion-sf.png")
    figura.savefig(salida, dpi=160)
    plt.close(figura)


if __name__ == "__main__":
    main()

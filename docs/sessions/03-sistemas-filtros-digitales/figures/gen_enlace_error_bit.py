"""Compara el paquete intacto de Hola con una alteración de un bit sin cambiar el CRC."""

from pathlib import Path
import argparse
import struct
import zlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar(salida: Path) -> Path:
    salida.mkdir(parents=True, exist_ok=True)
    datos = b"Hola"
    contenido = struct.pack("!H", len(datos)) + datos
    original = contenido + struct.pack("!I", zlib.crc32(contenido))
    alterado = bytearray(original)
    alterado[2] ^= 0x01
    assert sum(bin(a ^ b).count("1") for a, b in zip(original, alterado)) == 1
    assert original[-4:] == alterado[-4:]
    assert zlib.crc32(alterado[:-4]) != int.from_bytes(alterado[-4:], "big")

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.set(xlim=(-2.6, 10.15), ylim=(-1.35, 3.0))
    ax.set_axis_off()
    for centro, titulo in [(1, "Longitud"), (4, "Texto"), (8, "CRC recibido")]:
        ax.text(centro, 2.48, titulo, ha="center", fontsize=14, weight="bold")
    for y, paquete, etiqueta in [(1.4, original, "Paquetes 1 y 3\nSin cambios"), (0.15, alterado, "Paquete 2\nUn bit alterado")]:
        ax.text(-0.25, y + 0.4, etiqueta, ha="right", va="center", fontsize=12)
        for i, byte in enumerate(paquete):
            cambio = paquete is alterado and i == 2
            fondo = "#ffe0dc" if cambio else ("#e5f0fa" if i < 2 else "#e5f3e8" if i < 6 else "#fff0da")
            ax.add_patch(Rectangle((i, y), 1, 0.8, facecolor=fondo, edgecolor="#bd332b" if cambio else "#53616c", linewidth=2 if cambio else 1))
            ax.text(i + 0.5, y + 0.4, f"{byte:02x}", ha="center", va="center", family="monospace", fontsize=17, color="#a8231e" if cambio else "#20272b")
    ax.text(4, -0.4, f"Primer byte del texto: {original[2]:08b} → {alterado[2]:08b}", ha="center", fontsize=14, family="monospace")
    ax.text(4, -0.91, "Cambia H por I · La longitud y el CRC recibido no cambian", ha="center", fontsize=12)
    ax.set_title("Un bit cambia después de calcular el CRC", fontsize=17, pad=10)
    fig.subplots_adjust(left=0.03, right=0.97, top=0.84, bottom=0.05)
    archivo = salida / "enlace-22-error-un-bit.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(generar(args.salida))

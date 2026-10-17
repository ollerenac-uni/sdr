"""Muestra el formato del paquete y calcula el ejemplo de Hola."""

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
    datos = "Hola".encode("utf-8")
    cabecera = struct.pack("!H", len(datos))
    crc = struct.pack("!I", zlib.crc32(cabecera + datos))
    campos = [cabecera, datos, crc]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.set(xlim=(-0.2, 10.2), ylim=(-0.7, 3.1))
    ax.set_axis_off()
    titulos = ["Longitud", "Texto UTF-8", "CRC-32"]
    colores = ["#e5f0fa", "#e5f3e8", "#fff0da"]
    inicio = 0
    for titulo, campo, color in zip(titulos, campos, colores):
        ancho = len(campo)
        centro = inicio + ancho / 2
        ax.add_patch(Rectangle((inicio, 0.55), ancho, 1.25, facecolor=color, edgecolor="#3d5263", linewidth=1.6))
        ax.text(centro, 2.42, titulo, ha="center", fontsize=15, weight="bold")
        ax.text(centro, 2.0, f"{ancho} bytes", ha="center", fontsize=13)
        ax.text(centro, 1.33, campo.hex(" "), ha="center", va="center", fontsize=16, family="monospace")
        significado = ["Valor: 4", "Hola", "Calculado sobre longitud + texto"][titulos.index(titulo)]
        ax.text(centro, 0.86, significado, ha="center", va="center", fontsize=10.5)
        inicio += ancho
    ax.plot([0, 0, 6, 6], [0.33, 0.15, 0.15, 0.33], color="#3d5263", linewidth=1.5)
    ax.text(3, -0.02, "Estos 6 bytes entran al cálculo del CRC", ha="center", va="top", fontsize=12)
    ax.text(5, -0.53, f"Total: {sum(map(len, campos))} bytes · Sin secuencia de sincronización todavía", ha="center", fontsize=12)
    ax.set_title("Ejemplo: paquete del texto Hola", fontsize=17, pad=12)
    fig.subplots_adjust(left=0.035, right=0.965, top=0.84, bottom=0.1)
    archivo = salida / "enlace-15-formato-paquete.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(generar(args.salida))

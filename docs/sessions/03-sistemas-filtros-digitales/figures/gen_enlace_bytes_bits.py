"""Representa los primeros bytes del paquete de Hola mediante bits MSB first."""

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
    texto = b"Hola"
    cuerpo = struct.pack("!H", len(texto)) + texto
    paquete = cuerpo + struct.pack("!I", zlib.crc32(cuerpo))
    bits = [(byte >> posicion) & 1 for byte in paquete for posicion in range(7, -1, -1)]
    assert len(paquete) == 10 and len(bits) == 80
    assert paquete[:3] == bytes.fromhex("00 04 48")
    assert [f"{byte:08b}" for byte in paquete[:3]] == ["00000000", "00000100", "01001000"]
    assert (2 + len("SDR".encode("utf-8")) + 4) * 8 == 72
    fig, ax = plt.subplots(figsize=(13, 4.4))
    ax.set(xlim=(-3.1, 15.1), ylim=(-0.95, 4.45))
    ax.set_axis_off()
    ax.text(-1.8, 3.7, "Byte (hex)", ha="center", fontsize=13, weight="bold")
    ax.text(3.85, 3.7, "Bits: del mayor al menor peso", ha="center", fontsize=13, weight="bold")
    ax.text(11.5, 3.7, "Salida: elementos u8 (hex)", ha="center", fontsize=13, weight="bold")
    for columna, posicion in enumerate(range(7, -1, -1)):
        ax.text(columna * 0.9 + 0.4, 3.28, str(posicion), ha="center", fontsize=11, color="#566573")
    for fila, byte in enumerate(paquete[:3]):
        y = 2.35 - fila
        valores = [(byte >> posicion) & 1 for posicion in range(7, -1, -1)]
        color = "#e5f0fa" if fila < 2 else "#e5f3e8"
        ax.text(-1.8, y + 0.35, f"{byte:02x}", ha="center", va="center", fontsize=20, family="monospace")
        ax.annotate("", xy=(-0.12, y + 0.35), xytext=(-1.1, y + 0.35), arrowprops={"arrowstyle": "->", "color": "#455a64"})
        for columna, bit in enumerate(valores):
            x = columna * 0.9
            ax.add_patch(Rectangle((x, y), 0.8, 0.7, facecolor="#ffd98a" if bit else color, edgecolor="#455a64"))
            ax.text(x + 0.4, y + 0.35, str(bit), ha="center", va="center", fontsize=18, family="monospace")
        ax.text(11.5, y + 0.35, " ".join(f"{b:02x}" for b in valores), ha="center", va="center", fontsize=12.5, family="monospace")
    ax.text(6, -0.48, f"Paquete completo de Hola: {len(paquete)} bytes → {len(bits)} valores binarios", ha="center", fontsize=14)
    ax.set_title("El contenido se conserva; cambia su representación", fontsize=17, pad=12)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.86, bottom=0.06)
    archivo = salida / "enlace-27-bytes-bits.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(generar(args.salida))

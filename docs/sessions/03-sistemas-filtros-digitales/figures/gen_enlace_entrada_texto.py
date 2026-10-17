"""Esquema del primer bloque del enlace; no representa una captura de GRC."""

from pathlib import Path
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle


def generar(salida: Path) -> Path:
    salida.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax in axes:
        ax.set(xlim=(0, 10), ylim=(0, 6))
        ax.set_axis_off()
    azul = "#245a81"
    naranja = "#ad5d00"
    a, b = axes
    a.set_title("En el editor GRC", fontsize=16, pad=12)
    a.add_patch(FancyBboxPatch((1.5, 1.5), 7, 3.4, boxstyle="round,pad=0.12", facecolor="#eef5fa", edgecolor=azul, linewidth=1.8))
    a.text(5, 4.25, "QT GUI Message Edit Box", ha="center", fontsize=13, weight="bold", color=azul)
    a.text(5, 3.25, "ID: mensaje_a\nType: String", ha="center", va="center", fontsize=13, linespacing=1.7)
    a.plot([1.5, 8.5], [2.2, 2.2], "s", ms=9, color=naranja)
    a.text(0.95, 2.2, "val", ha="right", va="center", color=naranja, fontsize=13)
    a.text(9.0, 2.2, "msg", ha="left", va="center", color=naranja, fontsize=13)
    a.text(5, 0.65, "Puertos de mensajes, sin conectar", ha="center", fontsize=12)
    b.set_title("Al ejecutar: ejemplo con texto escrito", fontsize=15, pad=12)
    b.add_patch(FancyBboxPatch((0.5, 1.5), 9, 3.4, boxstyle="round,pad=0.12", facecolor="#f8f9fa", edgecolor="#7a8793", linewidth=1.5))
    b.text(5, 4.35, "Enlace digital de mensajes", ha="center", fontsize=13, color=azul)
    b.text(1.0, 3.4, "Mensaje de A", va="center", fontsize=12)
    b.add_patch(Rectangle((1, 2.3), 8, 0.7, facecolor="white", edgecolor=azul, linewidth=1.3))
    b.text(1.3, 2.65, "Hola", va="center", fontsize=14)
    b.text(5, 0.65, "Todavía no hay un destino para msg", ha="center", fontsize=12)
    fig.subplots_adjust(left=0.03, right=0.97, top=0.86, bottom=0.1, wspace=0.16)
    archivo = salida / "enlace-01-entrada-texto.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(generar(args.salida))

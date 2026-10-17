"""Muestra el mapeo BPSK y los ocho símbolos correspondientes al byte H."""

from pathlib import Path
import argparse
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generar(salida: Path) -> Path:
    salida.mkdir(parents=True, exist_ok=True)
    bits = np.unpackbits(np.frombuffer(b"H", dtype=np.uint8), bitorder="big")
    simbolos = 2 * bits.astype(int) - 1
    assert bits.tolist() == [0, 1, 0, 0, 1, 0, 0, 0]
    assert simbolos.tolist() == [-1, 1, -1, -1, 1, -1, -1, -1]
    assert np.angle(np.array([-1 + 0j, 1 + 0j]), deg=True).tolist() == [180, 0]
    assert np.abs(np.array([-1 + 0j, 1 + 0j])).tolist() == [1, 1]
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), gridspec_kw={"width_ratios": [1, 1.4]})
    ax = axes[0]
    ax.axhline(0, color="#888888", linewidth=0.8)
    ax.axvline(0, color="#888888", linewidth=0.8)
    ax.scatter([-1, 1], [0, 0], s=110, color="#1565c0", zorder=3)
    ax.text(-1, 0.23, "bit 0\n−1 + j0", ha="center", fontsize=12)
    ax.text(1, 0.23, "bit 1\n+1 + j0", ha="center", fontsize=12)
    ax.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), xlabel="I (parte real)", ylabel="Q (parte imaginaria)", title="Dos estados posibles")
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax = axes[1]
    posiciones = np.arange(8)
    ax.vlines(posiciones, 0, simbolos, color="#1565c0", linewidth=1.4)
    ax.scatter(posiciones, simbolos, color="#1565c0", s=45, label="I del símbolo", zorder=3)
    ax.scatter(posiciones, np.zeros(8), color="#ef6c00", s=32, label="Q del símbolo = 0", zorder=3)
    for posicion, bit in zip(posiciones, bits):
        ax.text(posicion, 1.3, str(bit), ha="center", fontsize=12)
    ax.set(xlim=(-0.5, 7.5), ylim=(-1.5, 1.65), xticks=posiciones, yticks=[-1, 0, 1], xlabel="Posición dentro del byte H (no es tiempo)", ylabel="Valor normalizado", title="Ejemplo: bits de H, de izquierda a derecha")
    ax.grid(alpha=0.2)
    ax.legend(loc="lower center", fontsize=9, ncol=2, bbox_to_anchor=(0.5, -0.38))
    fig.subplots_adjust(left=0.065, right=0.98, top=0.85, bottom=0.26, wspace=0.35)
    archivo = salida / "enlace-31-mapeo-bpsk.png"
    fig.savefig(archivo, dpi=160, facecolor="white")
    plt.close(fig)
    return archivo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(generar(args.salida))

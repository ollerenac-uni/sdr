#!/usr/bin/env python3
"""Figuras didácticas de arquitecturas de recepción para la Sesión 01.

Las ilustraciones son originales y reproducibles. Puede ejecutarse desde
cualquier directorio:

    python gen_architecture_figures.py
    python gen_architecture_figures.py --output-dir /tmp/figuras-sdr
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
warnings.filterwarnings(
    "ignore",
    message="Unable to import Axes3D.*",
    category=UserWarning,
    module="matplotlib.projections",
)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402


OUT = Path(__file__).parent
DARK = "#172033"
MUTED = "#526072"
ANALOG = "#fff3c4"
ANALOG_EDGE = "#c8860b"
DIGITAL = "#dbeafe"
DIGITAL_EDGE = "#2563a6"
SOFTWARE = "#dcfce7"
SOFTWARE_EDGE = "#168451"
BOARD = "#176b4a"
BOARD_DARK = "#0b4c35"
CHIP = "#18212f"
COPPER = "#e1b44b"
WHITE = "#ffffff"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.facecolor": "white",
    }
)


def clean_axis(ax, xlim=(0, 12), ylim=(0, 7)) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")


def box(
    ax,
    xy,
    width,
    height,
    text,
    *,
    facecolor=WHITE,
    edgecolor=DARK,
    fontsize=9,
    linewidth=1.4,
    radius=0.12,
    weight="normal",
    textcolor=DARK,
    zorder=2,
):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0.04,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        zorder=zorder,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=textcolor,
        fontweight=weight,
        zorder=zorder + 1,
    )
    return patch


def arrow(ax, start, end, *, color=DARK, linewidth=1.5, style="-") -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=linewidth,
            linestyle=style,
            color=color,
            shrinkA=2,
            shrinkB=2,
            zorder=4,
        )
    )


def antenna(ax, x, y, scale=1.0, color=DARK) -> None:
    ax.plot([x, x], [y, y + 0.52 * scale], color=color, lw=1.8)
    ax.plot([x, x - 0.22 * scale], [y, y + 0.32 * scale], color=color, lw=1.8)
    ax.plot([x, x + 0.22 * scale], [y, y + 0.32 * scale], color=color, lw=1.8)
    for radius in (0.28, 0.43):
        ax.add_patch(
            FancyArrowPatch(
                (x + radius * scale, y + 0.12 * scale),
                (x + radius * scale, y + 0.50 * scale),
                connectionstyle=f"arc3,rad={0.45 + radius / 3}",
                arrowstyle="-",
                color=color,
                lw=1.1,
            )
        )


def save_figure(fig, path: Path) -> Path:
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_conventional_vs_sdr(output_dir: Path) -> Path:
    """Compara hardware dedicado con una plataforma SDR compartida."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11.5, 5.8))
    clean_axis(left, (0, 6), (0, 7))
    clean_axis(right, (0, 6.25), (0, 7))

    left.set_title("Radio convencional", fontsize=15, color=DARK, fontweight="bold", pad=12)
    right.set_title("Radio definida por software", fontsize=15, color=DARK, fontweight="bold", pad=12)

    left.text(
        3,
        6.4,
        "Cada aplicación necesita su propia cadena física",
        ha="center",
        color=MUTED,
        fontsize=10,
    )
    rows = [("FM", "Filtro + mezclador\n+ demodulador FM", 5.1),
            ("ADS-B", "Filtro + mezclador\n+ demodulador ADS-B", 3.4),
            ("Satélite", "Filtro + mezclador\n+ demodulador LRPT", 1.7)]
    for label, hardware, y in rows:
        antenna(left, 0.42, y - 0.22, 0.75)
        box(left, (0.9, y - 0.35), 1.15, 0.75, label, facecolor=ANALOG,
            edgecolor=ANALOG_EDGE, weight="bold")
        arrow(left, (2.05, y + 0.02), (2.42, y + 0.02))
        box(left, (2.45, y - 0.55), 2.65, 1.12, hardware, facecolor=ANALOG,
            edgecolor=ANALOG_EDGE, fontsize=8.5)
    left.text(
        3,
        0.52,
        "Cambiar de estándar = cambiar circuitos",
        ha="center",
        color="#9a4f08",
        fontsize=10,
        fontweight="bold",
    )

    right.text(
        3,
        6.4,
        "El front-end y el digitalizador alimentan varias aplicaciones",
        ha="center",
        color=MUTED,
        fontsize=10,
    )
    antenna(right, 0.22, 3.18, 0.9)
    box(right, (0.72, 2.95), 1.48, 0.98, "Front-end\nanalógico", facecolor=ANALOG,
        edgecolor=ANALOG_EDGE, weight="bold")
    arrow(right, (2.20, 3.44), (2.53, 3.44))
    box(right, (2.56, 2.95), 1.10, 0.98, "ADC", facecolor=DIGITAL,
        edgecolor=DIGITAL_EDGE, weight="bold")
    right.text(2.18, 2.64, "hardware compartido", ha="center", color=MUTED, fontsize=8.5)

    branch_x = 4.00
    arrow(right, (3.66, 3.44), (branch_x, 3.44), color=SOFTWARE_EDGE)
    right.plot([branch_x, branch_x], [1.58, 5.3], color=SOFTWARE_EDGE, lw=1.5)
    for label, y in (("Receptor FM", 5.05), ("Decodificador ADS-B", 3.44),
                     ("Receptor satelital", 1.83)):
        arrow(right, (branch_x, y), (4.26, y), color=SOFTWARE_EDGE)
        box(right, (4.29, y - 0.42), 1.82, 0.84, label, facecolor=SOFTWARE,
            edgecolor=SOFTWARE_EDGE, fontsize=8.2)
    right.text(
        4.83,
        0.52,
        "Cambiar de estándar = cambiar software",
        ha="center",
        color=SOFTWARE_EDGE,
        fontsize=10,
        fontweight="bold",
    )

    fig.suptitle(
        "La diferencia no es eliminar el hardware analógico, sino hacerlo reutilizable",
        fontsize=17,
        color=DARK,
        fontweight="bold",
        y=1.01,
    )
    fig.text(
        0.5,
        0.015,
        "La frontera exacta entre hardware y software depende del equipo; el principio de reutilización permanece.",
        ha="center",
        color=MUTED,
        fontsize=9.5,
    )
    return save_figure(fig, output_dir / "radio-convencional-vs-sdr.png")


def architecture_row(ax, y, title, subtitle, blocks, links=None) -> None:
    ax.text(0.15, y + 0.62, title, fontsize=10.5, color=DARK, fontweight="bold", va="center")
    ax.text(0.15, y + 0.08, subtitle, fontsize=8.2, color=MUTED, va="center")
    x_positions = [3.45, 5.02, 6.59, 8.16, 9.73]
    for index, (label, kind) in enumerate(blocks):
        x = x_positions[index]
        palette = {
            "analog": (ANALOG, ANALOG_EDGE),
            "digital": (DIGITAL, DIGITAL_EDGE),
            "software": (SOFTWARE, SOFTWARE_EDGE),
        }[kind]
        box(ax, (x, y), 1.28, 0.92, label, facecolor=palette[0], edgecolor=palette[1],
            fontsize=7.8, weight="bold" if label == "ADC" else "normal")
        if index:
            arrow(ax, (x_positions[index - 1] + 1.28, y + 0.46), (x, y + 0.46), linewidth=1.25)
    if links:
        for label, start_index, end_index in links:
            mid = (x_positions[start_index] + x_positions[end_index] + 1.28) / 2
            ax.text(mid, y + 1.06, label, ha="center", fontsize=7.6, color=MUTED)


def plot_receiver_architectures(output_dir: Path) -> Path:
    """Contrasta muestreo directo, Zero-IF y Low-IF."""
    fig, ax = plt.subplots(figsize=(12.2, 6.7))
    clean_axis(ax, (0, 12), (0, 7.35))
    ax.set_title(
        "Tres lugares posibles para cruzar la frontera analógico–digital",
        fontsize=17,
        color=DARK,
        fontweight="bold",
        pad=12,
    )

    architecture_row(
        ax,
        5.15,
        "Muestreo directo\nde RF",
        "El ADC ve la radiofrecuencia",
        [("Filtro\nRF", "analog"), ("LNA", "analog"), ("ADC", "digital"),
         ("DDC\ndigital", "digital"), ("I/Q", "software")],
        [("RF", 1, 2), ("muestras reales", 2, 3)],
    )
    architecture_row(
        ax,
        2.95,
        "Zero-IF /\nconversión directa",
        "Dos mezcladores analógicos\nproducen I y Q",
        [("Filtro\nRF + LNA", "analog"), ("Mezclador\nI / Q", "analog"),
         ("LPF\nI / Q", "analog"), ("2 ADC", "digital"), ("I/Q", "software")],
        [("LO: 0° y 90°", 1, 2), ("dos voltajes", 2, 3)],
    )
    architecture_row(
        ax,
        0.75,
        "Low-IF",
        "Ejemplo: RTL-SDR",
        [("Filtro\nRF + LNA", "analog"), ("Tuner /\nmezclador", "analog"),
         ("ADC", "digital"), ("DDC\ndigital", "digital"), ("I/Q", "software")],
        [("IF real baja", 1, 2), ("muestras reales", 2, 3)],
    )

    for y in (4.55, 2.35):
        ax.plot([0.12, 11.85], [y, y], color="#d7dde6", lw=0.8)
    ax.text(5.15, 7.05, "analógico", color=ANALOG_EDGE, ha="center", fontweight="bold")
    ax.text(7.88, 7.05, "digital", color=DIGITAL_EDGE, ha="center", fontweight="bold")
    ax.text(10.37, 7.05, "procesamiento I/Q", color=SOFTWARE_EDGE, ha="center", fontweight="bold")
    return save_figure(fig, output_dir / "arquitecturas-receptores-sdr.png")


def chip(ax, xy, width, height, title, detail="", *, facecolor=CHIP, fontsize=8.5):
    box(ax, xy, width, height, "", facecolor=facecolor, edgecolor="#07101c", linewidth=1.2)
    pin_count = max(4, int(width * 2.6))
    for index in range(pin_count):
        px = xy[0] + (index + 0.5) * width / pin_count
        ax.plot([px, px], [xy[1] - 0.08, xy[1]], color=COPPER, lw=1)
        ax.plot([px, px], [xy[1] + height, xy[1] + height + 0.08], color=COPPER, lw=1)
    ax.text(xy[0] + width / 2, xy[1] + height * 0.62, title, ha="center", va="center",
            color=WHITE, fontsize=fontsize, fontweight="bold", zorder=5)
    if detail:
        ax.text(xy[0] + width / 2, xy[1] + height * 0.29, detail, ha="center", va="center",
                color="#cbd5e1", fontsize=7, zorder=5)


def plot_rtlsdr_v4_interior(output_dir: Path) -> Path:
    """Dibuja la cadena funcional del V4 sobre una placa esquemática."""
    fig, ax = plt.subplots(figsize=(12.0, 5.9))
    clean_axis(ax, (0, 12), (0, 6.2))
    ax.set_title(
        "RTL-SDR Blog V4: componentes principales de la cadena de recepción",
        fontsize=16,
        color=DARK,
        fontweight="bold",
        pad=12,
    )
    ax.text(
        6,
        5.72,
        "Diagrama técnico simplificado — no es una fotografía; las posiciones son esquemáticas",
        ha="center",
        color="#a13d18",
        fontsize=9.5,
        fontweight="bold",
    )

    board = FancyBboxPatch(
        (0.72, 0.72), 10.55, 4.5,
        boxstyle="round,pad=0.08,rounding_size=0.22",
        facecolor=BOARD, edgecolor=BOARD_DARK, linewidth=2.3, zorder=0,
    )
    ax.add_patch(board)

    # Conectores del extremo de RF y USB.
    ax.add_patch(FancyBboxPatch((0.18, 2.22), 0.72, 1.45, boxstyle="round,pad=0.03",
                                facecolor="#d4d9df", edgecolor="#606a75", lw=1.5, zorder=2))
    ax.text(0.54, 2.95, "SMA", rotation=90, ha="center", va="center", color=DARK,
            fontsize=8, fontweight="bold", zorder=3)
    ax.add_patch(FancyBboxPatch((11.05, 1.88), 0.82, 2.0, boxstyle="round,pad=0.03",
                                facecolor="#c6cbd1", edgecolor="#59636f", lw=1.5, zorder=2))
    ax.text(11.46, 2.88, "USB", rotation=90, ha="center", va="center", color=DARK,
            fontsize=8, fontweight="bold", zorder=3)

    box(ax, (1.16, 2.28), 1.45, 1.33, "Triplexor\n+ filtros RF", facecolor="#e5f0df",
        edgecolor="#77a45e", fontsize=8.5, weight="bold")
    ax.text(1.88, 1.84, "HF  ·  VHF  ·  UHF", ha="center", color="#d8f3dc", fontsize=7.5)
    chip(ax, (3.05, 2.15), 2.2, 1.62, "R828D", "tuner · LNA · mezclador")
    chip(ax, (6.35, 1.84), 3.18, 2.24, "RTL2832U", "ADC · DDC · controlador USB")
    box(ax, (4.12, 4.34), 1.72, 0.55, "TCXO 28.8 MHz", facecolor="#f5e6a6",
        edgecolor="#a67a12", fontsize=7.8, weight="bold")
    box(ax, (3.12, 0.98), 2.42, 0.60, "HF: upconverter 28.8 MHz", facecolor="#d8ecdf",
        edgecolor="#4e9168", fontsize=7.3)
    arrow(ax, (0.88, 2.95), (1.14, 2.95), color=COPPER, linewidth=2.0)
    arrow(ax, (2.61, 2.95), (3.03, 2.95), color=COPPER, linewidth=2.0)
    arrow(ax, (5.25, 2.95), (6.33, 2.95), color=COPPER, linewidth=2.0)
    arrow(ax, (9.53, 2.95), (11.05, 2.95), color=COPPER, linewidth=2.0)
    arrow(ax, (4.98, 4.34), (4.35, 3.79), color="#ead27a", linewidth=1.2, style="--")
    arrow(ax, (5.38, 4.34), (7.30, 4.10), color="#ead27a", linewidth=1.2, style="--")
    arrow(ax, (4.32, 1.58), (4.32, 2.13), color="#8bd0a5", linewidth=1.2, style="--")

    ax.text(0.50, 4.32, "RF", ha="center", color=WHITE, fontweight="bold")
    ax.text(5.79, 3.19, "IF real", ha="center", color="#fff2b8", fontsize=8, fontweight="bold")
    ax.text(10.27, 3.19, "I/Q + control", ha="center", color="#cfe6ff", fontsize=8,
            fontweight="bold")
    ax.text(
        6,
        0.28,
        "La cadena funcional sí corresponde al V4; el encapsulado y la ubicación exacta pueden variar entre revisiones de placa.",
        ha="center",
        color=MUTED,
        fontsize=8.7,
    )
    return save_figure(fig, output_dir / "rtl-sdr-v4-interior.png")


def generate_figures(output_dir: Path = OUT) -> tuple[Path, Path, Path]:
    """Genera las tres figuras y devuelve sus rutas."""
    output_dir.mkdir(parents=True, exist_ok=True)
    return (
        plot_conventional_vs_sdr(output_dir),
        plot_receiver_architectures(output_dir),
        plot_rtlsdr_v4_interior(output_dir),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUT,
        help="Directorio de salida (por defecto, el directorio del script)",
    )
    args = parser.parse_args()
    for path in generate_figures(args.output_dir):
        print("ok", path)


if __name__ == "__main__":
    main()

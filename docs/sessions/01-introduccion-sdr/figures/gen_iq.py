#!/usr/bin/env python3
"""Figuras didácticas sobre I/Q y el tipo complejo de GNU Radio.

Genera dos PNG a 300 DPI. Puede ejecutarse desde cualquier directorio:

    python gen_iq.py
    python gen_iq.py --output-dir /tmp/figuras-iq
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
import numpy as np  # noqa: E402


OUT = Path(__file__).parent
BLUE = "#1e40af"
RED = "#dc2626"
GREEN = "#047857"
DARK = "#111827"
GRAY = "#6b7280"
LIGHT_BLUE = "#dbeafe"
LIGHT_RED = "#fee2e2"

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.facecolor": "white",
    }
)


def quadrature_tone(
    sample_count: int = 1200,
    cycles: float = 3,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Devuelve una sinusoide compleja y sus dos componentes reales."""
    t = np.arange(sample_count) / sample_count
    phase = 2 * np.pi * cycles * t
    i_signal = np.cos(phase)
    q_signal = np.sin(phase)
    return t, i_signal, q_signal, i_signal + 1j * q_signal


def save_figure(fig: plt.Figure, path: Path) -> Path:
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_quadrature_time(output_dir: Path) -> Path:
    """Dibuja I y Q como proyecciones reales de una hélice compleja."""
    t, i_signal, q_signal, _ = quadrature_tone()
    periods = 3 * t

    fig = plt.figure(figsize=(7.2, 4.0), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=(1.55, 1), height_ratios=(1, 1))
    ax_3d = fig.add_subplot(grid[:, 0])
    ax_i = fig.add_subplot(grid[0, 1])
    ax_q = fig.add_subplot(grid[1, 1], sharex=ax_i)

    def project(time, i_value, q_value):
        """Proyección oblicua reproducible del espacio (tiempo, I, Q)."""
        return time + 0.34 * i_value, 0.20 * i_value + 0.58 * q_value

    helix_x, helix_y = project(periods, i_signal, q_signal)
    i_x, i_y = project(periods, i_signal, np.full_like(periods, -1.35))
    q_x, q_y = project(periods, np.full_like(periods, 1.35), q_signal)
    ax_3d.plot(helix_x, helix_y, color=GREEN, lw=2.2, label="$z(t)=I(t)+jQ(t)$")
    ax_3d.plot(i_x, i_y, color=BLUE, lw=1.4)
    ax_3d.plot(q_x, q_y, color=RED, lw=1.4)

    origin_x, origin_y = project(0, -1.35, -1.35)
    time_x, time_y = project(3.15, -1.35, -1.35)
    i_axis_x, i_axis_y = project(0, 1.55, -1.35)
    q_axis_x, q_axis_y = project(0, -1.35, 1.55)
    for end_x, end_y in ((time_x, time_y), (i_axis_x, i_axis_y), (q_axis_x, q_axis_y)):
        ax_3d.annotate(
            "",
            xy=(end_x, end_y),
            xytext=(origin_x, origin_y),
            arrowprops=dict(arrowstyle="->", color=DARK, lw=0.9),
        )
    ax_3d.text(time_x, time_y - 0.10, "Tiempo", ha="right", va="top")
    ax_3d.text(i_axis_x + 0.05, i_axis_y, "I", va="center")
    ax_3d.text(q_axis_x - 0.04, q_axis_y + 0.03, "Q", ha="right")
    ax_3d.text(i_x[-1], i_y[-1] - 0.10, "$I(t)$", color=BLUE, ha="right", va="top")
    ax_3d.text(q_x[-1], q_y[-1] + 0.08, "$Q(t)$", color=RED, ha="right", va="bottom")
    ax_3d.set_xlim(-0.65, 3.65)
    ax_3d.set_ylim(-1.18, 1.18)
    ax_3d.set_aspect("equal", adjustable="box")
    ax_3d.axis("off")
    ax_3d.legend(loc="upper left", frameon=False)

    ax_i.plot(periods, i_signal, color=BLUE, lw=1.8)
    ax_i.axhline(0, color=DARK, lw=0.6)
    ax_i.set_ylabel("I")
    ax_i.set_ylim(-1.25, 1.25)
    ax_i.set_title("Dos señales reales, separadas $90°$")
    ax_i.text(0.08, 0.88, "$I(t)=\\cos(2\\pi f_0t)$", color=BLUE, transform=ax_i.transAxes)
    ax_i.tick_params(labelbottom=False)

    ax_q.plot(periods, q_signal, color=RED, lw=1.8)
    ax_q.axhline(0, color=DARK, lw=0.6)
    ax_q.set_xlabel("Tiempo  $t/T$")
    ax_q.set_ylabel("Q")
    ax_q.set_ylim(-1.25, 1.25)
    ax_q.set_xticks([0, 1, 2, 3])
    ax_q.text(0.08, 0.88, "$Q(t)=\\sin(2\\pi f_0t)$", color=RED, transform=ax_q.transAxes)

    fig.suptitle(
        "Una sinusoide compleja son dos señales reales en cuadratura",
        fontsize=13,
        color=DARK,
    )
    fig.text(
        0.5,
        -0.015,
        "La curva verde no es otro voltaje: representa conjuntamente cada par $(I,Q)$ como $I+jQ$.",
        ha="center",
        color=DARK,
    )
    return save_figure(fig, output_dir / "iq-cuadratura-tiempo.png")


def draw_spectral_stem(ax, negative: float, positive: float, color: str) -> None:
    """Dibuja los coeficientes en −f₀ y +f₀ de un espectro discreto ideal."""
    ax.axhline(0, color=DARK, lw=0.8)
    ax.axvline(0, color=GRAY, lw=0.5, alpha=0.6)
    ax.vlines([-1, 1], [0, 0], [negative, positive], color=color, lw=2.5)
    ax.scatter([-1, 1], [negative, positive], color=color, s=24, zorder=3)
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-0.72, 1.18)
    ax.set_xticks([-1, 0, 1], ["$-f_0$", "0", "$+f_0$"])
    ax.set_yticks([-0.5, 0, 0.5, 1])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def plot_spectral_cancellation(output_dir: Path) -> Path:
    """Muestra cómo I+jQ elimina la copia espectral en frecuencia negativa."""
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 4.4), sharex=True, constrained_layout=True)

    draw_spectral_stem(axes[0], 0.5, 0.5, BLUE)
    axes[0].set_ylabel("$I(f)$", rotation=0, labelpad=25, color=BLUE, fontweight="bold")
    axes[0].text(-1, 0.58, "$+\\frac{1}{2}$", color=BLUE, ha="center")
    axes[0].text(1, 0.58, "$+\\frac{1}{2}$", color=BLUE, ha="center")
    axes[0].text(
        0.02,
        0.9,
        "$I(t)=\\cos(2\\pi f_0t)=\\frac{1}{2}e^{j2\\pi f_0t}+\\frac{1}{2}e^{-j2\\pi f_0t}$",
        transform=axes[0].transAxes,
        color=BLUE,
    )

    draw_spectral_stem(axes[1], -0.5, 0.5, RED)
    axes[1].set_ylabel("$jQ(f)$", rotation=0, labelpad=25, color=RED, fontweight="bold")
    axes[1].text(-1, -0.64, "$-\\frac{1}{2}$", color=RED, ha="center")
    axes[1].text(1, 0.58, "$+\\frac{1}{2}$", color=RED, ha="center")
    axes[1].text(
        0.02,
        0.9,
        "$jQ(t)=j\\sin(2\\pi f_0t)=\\frac{1}{2}e^{j2\\pi f_0t}-\\frac{1}{2}e^{-j2\\pi f_0t}$",
        transform=axes[1].transAxes,
        color=RED,
    )

    draw_spectral_stem(axes[2], 0, 1, GREEN)
    axes[2].set_ylabel("$Z(f)$", rotation=0, labelpad=25, color=GREEN, fontweight="bold")
    axes[2].text(1, 1.06, "$1$", color=GREEN, ha="center")
    axes[2].annotate(
        "$\\frac{1}{2}-\\frac{1}{2}=0$\nse cancela esta copia",
        xy=(-1, 0),
        xytext=(-0.62, 0.72),
        color=DARK,
        ha="center",
        arrowprops=dict(arrowstyle="->", color=DARK),
        bbox=dict(boxstyle="round,pad=0.25", facecolor=LIGHT_RED, edgecolor="none"),
    )
    axes[2].annotate(
        "$\\frac{1}{2}+\\frac{1}{2}=1$\nse conserva esta frecuencia",
        xy=(1, 1),
        xytext=(0.48, 0.35),
        color=DARK,
        ha="center",
        arrowprops=dict(arrowstyle="->", color=DARK),
        bbox=dict(boxstyle="round,pad=0.25", facecolor=LIGHT_BLUE, edgecolor="none"),
    )
    axes[2].set_xlabel("Frecuencia relativa a la portadora")

    fig.suptitle(
        "$Z(f)=I(f)+jQ(f)$ cancela la copia negativa, no la parte imaginaria",
        fontsize=13,
        color=DARK,
    )
    return save_figure(fig, output_dir / "iq-cancelacion-espectral.png")


def generate_figures(output_dir: Path = OUT) -> tuple[Path, Path]:
    """Genera las dos figuras y devuelve sus rutas."""
    output_dir.mkdir(parents=True, exist_ok=True)
    return (
        plot_quadrature_time(output_dir),
        plot_spectral_cancellation(output_dir),
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

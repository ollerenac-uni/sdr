"""Figuras del cierre de la Sesión 01: de las muestras al espectro y al tiempo.

Genera tres PNG a partir de la grabación oficial del curso:

- `de-muestras-a-espectro.png`: qué hace la transformada sobre un solo bloque.
- `espectrograma.png`: los 10 segundos completos como mapa frecuencia-tiempo.
- `superficie3d.png`: los mismos datos como superficie, para comparar legibilidad.

A diferencia de los demás generadores de la sesión, este necesita la grabación
`samples/fm_99p1MHz_2p4Msps_g30.cu8`, que no está en el repositorio por su tamaño
y se descarga de Drive. Sin ella el script se detiene con un mensaje claro.

Uso: python gen_espectro_tiempo.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = Path(__file__).parent
MUESTRA = OUT.parents[3] / "samples/fm_99p1MHz_2p4Msps_g30.cu8"

FS = 2.4e6  # tasa de muestreo de la grabación, muestras/s
FC = 99.1e6  # frecuencia central del tuner, Hz
N = 2048  # tamaño del bloque de la transformada
FILAS = 300  # filas del espectrograma tras promediar en el tiempo

AZUL, ROJO, VERDE, OSCURO = "#1e40af", "#dc2626", "#047857", "#111827"

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.dpi": 130,
        "savefig.facecolor": "white",
    }
)


def cargar_iq(ruta=MUESTRA, cuenta=None):
    """Lee un `.cu8` y devuelve muestras complejas normalizadas a ±1."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"Falta la grabación: {ruta}\n"
            "Descárgala de la carpeta 'samples' del curso en Drive y colócala ahí."
        )
    crudo = np.fromfile(ruta, dtype=np.uint8, count=-1 if cuenta is None else 2 * cuenta)
    i = crudo[0::2].astype(np.float32) - 127.5
    q = crudo[1::2].astype(np.float32) - 127.5
    return (i + 1j * q) / 127.5


def espectrograma(iq, n=N, filas=FILAS):
    """Devuelve (frecuencias MHz, tiempos s, potencia dB) lista para dibujar."""
    n_bloques = len(iq) // n
    bloques = iq[: n_bloques * n].reshape(n_bloques, n) * np.hanning(n)
    pot = np.abs(np.fft.fftshift(np.fft.fft(bloques, axis=1), axes=1)) ** 2
    # Promedia grupos de bloques para que la imagen quepa en pantalla.
    pot = pot[: n_bloques // filas * filas].reshape(filas, -1, n).mean(axis=1)
    db = 10 * np.log10(pot + 1e-20)
    db -= db.max()
    f = (FC + np.fft.fftshift(np.fft.fftfreq(n, 1 / FS))) / 1e6
    t = np.linspace(0, len(iq) / FS, filas)
    return f, t, db


def fig_de_muestras_a_espectro(iq):
    """Tres paneles: contra qué se compara, el bloque crudo, y el resultado."""
    bloque = iq[:N]
    n = np.arange(N)
    t_us = n / FS * 1e6
    tb_us = N / FS * 1e6

    fig, ax = plt.subplots(3, 1, figsize=(7.6, 7.6))

    for k, color in ((1, AZUL), (2, ROJO), (3, VERDE)):
        ax[0].plot(t_us, np.cos(2 * np.pi * k * n / N), color=color, lw=1.2,
                   label=f"k={k}: {k} vuelta{'s' if k > 1 else ''}")
    ax[0].axhline(0, color="#999", lw=0.6)
    ax[0].set_xlim(0, tb_us)
    ax[0].legend(ncol=3, fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.28))
    ax[0].set_ylabel("parte real")
    ax[0].set_xlabel("Tiempo dentro del bloque (µs)")
    ax[0].set_title("(a) Cada bin k es la senoide que da k vueltas enteras en el bloque",
                    fontsize=9.5)

    ax[1].plot(t_us, bloque.real, color=AZUL, lw=0.4, label="I")
    ax[1].plot(t_us, bloque.imag, color=ROJO, lw=0.4, alpha=0.7, label="Q")
    ax[1].set_xlim(0, tb_us)
    ax[1].set_ylabel("amplitud")
    ax[1].set_xlabel("Tiempo (µs)")
    ax[1].legend(fontsize=8, frameon=False, loc="upper right")
    ax[1].set_title(f"(b) El bloque real: {N} muestras, {tb_us:.0f} µs. Las emisoras están, pero invisibles",
                    fontsize=9.5)

    esp = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(bloque * np.hanning(N)))) + 1e-12)
    esp -= esp.max()
    bins = np.arange(-N // 2, N // 2)
    ax[2].plot(bins, esp, color=OSCURO, lw=0.6)
    ax[2].set_xlim(-N // 2, N // 2)
    ax[2].set_ylim(-45, 10)
    ax[2].set_xlabel("bin k")
    ax[2].set_ylabel("dB relativos")
    ax[2].set_title("(c) El resultado: una comparación por cada k, puestas en orden", fontsize=9.5)
    sec = ax[2].secondary_xaxis(
        "bottom",
        functions=(lambda b: (FC + b * FS / N) / 1e6, lambda f: (f * 1e6 - FC) / (FS / N)),
    )
    sec.set_xlabel("Frecuencia (MHz)")
    sec.spines["bottom"].set_position(("outward", 34))
    for b, etiqueta in ((-853, "98.1 MHz\nbin −853"), (0, "$f_c$ = 99.1\nbin 0"), (853, "100.1 MHz\nbin +853")):
        ax[2].annotate(etiqueta, xy=(b, 1), ha="center", va="bottom", fontsize=7.5, color=ROJO)

    fig.tight_layout(h_pad=2.6)
    fig.savefig(OUT / "de-muestras-a-espectro.png")
    plt.close(fig)


def fig_espectrograma(f, t, db):
    lo = np.percentile(db, 2)
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    m = ax.pcolormesh(f, t, db, shading="auto", cmap="magma", vmin=lo, vmax=0)
    ax.set_xlabel("Frecuencia (MHz)")
    ax.set_ylabel("Tiempo (s)")
    ax.set_title("Los 24 millones de muestras en un solo cuadro", pad=8)
    fig.colorbar(m, ax=ax, label="Potencia relativa (dB)")
    fig.tight_layout()
    fig.savefig(OUT / "espectrograma.png")
    plt.close(fig)


def fig_superficie3d(f, t, db, paso_f=6, paso_t=5):
    lo = np.percentile(db, 2)
    F, T = np.meshgrid(f[::paso_f], t[::paso_t])
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(F, T, db[::paso_t, ::paso_f], cmap="magma", linewidth=0.15,
                    edgecolor="k", antialiased=True, vmin=lo, vmax=0, rcount=60, ccount=170)
    ax.set_xlabel("Frecuencia (MHz)")
    ax.set_ylabel("Tiempo (s)")
    ax.set_zlabel("Potencia (dB)")
    ax.set_zlim(lo, 2)
    ax.view_init(elev=38, azim=-122)
    ax.set_title("Los mismos datos como superficie")
    fig.tight_layout()
    fig.savefig(OUT / "superficie3d.png")
    plt.close(fig)


def main():
    iq = cargar_iq()
    print(f"muestras leídas: {len(iq):,}  ({len(iq)/FS:.1f} s)")
    fig_de_muestras_a_espectro(iq)
    print("ok de-muestras-a-espectro.png")
    f, t, db = espectrograma(iq)
    fig_espectrograma(f, t, db)
    print("ok espectrograma.png")
    fig_superficie3d(f, t, db)
    print("ok superficie3d.png")


if __name__ == "__main__":
    main()

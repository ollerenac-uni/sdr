#!/usr/bin/env python3
"""Genera una figura reproducible de decimación para el laboratorio.

Requiere la muestra oficial en ``samples/``, distribuida por Drive y excluida
del repositorio. Ejecutar desde la raíz: ``python docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


OUT = Path(__file__).parent
MUESTRA = Path(__file__).parents[4] / "samples/fm_99p1MHz_2p4Msps_g30.cu8"
FS = 2_400_000
D = 8


def pasabajos(fs: float, corte: float, transicion: float) -> np.ndarray:
    """FIR Hamming de 193 coeficientes, equivalente al usado en el grafo."""
    ntaps = int(53 * fs / (22 * transicion)) | 1
    k = np.arange(ntaps) - ntaps // 2
    h = np.sinc(2 * corte * k / fs) * np.hamming(ntaps)
    return h / h.sum()


def decimar(x: np.ndarray, d: int, filtrar: bool) -> np.ndarray:
    """Conserva una de cada ``d`` muestras, con prefiltro opcional."""
    if filtrar:
        fs_salida = FS / d
        x = np.convolve(x, pasabajos(FS, 0.4 * fs_salida, 0.1 * fs_salida), mode="same")
    return x[::d]


def leer(segundos: float = 0.5) -> np.ndarray:
    if not MUESTRA.exists():
        raise SystemExit(f"Falta {MUESTRA}. Descárgala de la carpeta samples del curso en Drive.")
    datos = np.fromfile(MUESTRA, dtype=np.uint8, count=2 * int(FS * segundos)).astype(np.float32)
    return ((datos[0::2] - 127.5) + 1j * (datos[1::2] - 127.5)) / 127.5


def psd_db(x: np.ndarray, fs: float, nfft: int = 1024) -> tuple[np.ndarray, np.ndarray]:
    """Promedio de espectros con ventana Hann, para comparación visual estable."""
    bloques = x[: x.size // nfft * nfft].reshape(-1, nfft) * np.hanning(nfft)
    potencia = np.mean(np.abs(np.fft.fft(bloques, axis=1)) ** 2, axis=0)
    frecuencias = np.fft.fftshift(np.fft.fftfreq(nfft, 1 / fs))
    return frecuencias, 10 * np.log10(np.fft.fftshift(potencia) + 1e-12)


def panel(eje, x: np.ndarray, fs: float, color: str, titulo: str) -> None:
    frecuencias, potencia = psd_db(x, fs)
    eje.plot(frecuencias / 1e3, potencia, color=color, lw=0.8)
    eje.set_title(titulo, fontsize=10, loc="left")
    eje.set_xlabel("frecuencia relativa a 99.1 MHz (kHz)")
    eje.set_ylabel("dB")
    eje.grid(alpha=0.2)


def generar(salida: Path = OUT) -> Path:
    """Escribe la comparación original / sin filtro / con filtro."""
    salida.mkdir(parents=True, exist_ok=True)
    x = leer()
    fig, ejes = plt.subplots(3, 1, figsize=(10, 9), dpi=300)
    panel(ejes[0], x, FS, "#1e40af", "(a) Grabación original: 2.4 MS/s")
    panel(ejes[1], decimar(x, D, filtrar=False), FS / D, "#b91c1c",
          "(b) Keep 1 in 8: 300 kS/s sin filtro")
    panel(ejes[2], decimar(x, D, filtrar=True), FS / D, "#15803d",
          "(c) Decimating FIR Filter: 300 kS/s con filtro")
    fig.tight_layout()
    ruta = salida / "decimacion-con-y-sin-filtro.png"
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


if __name__ == "__main__":
    print(generar())

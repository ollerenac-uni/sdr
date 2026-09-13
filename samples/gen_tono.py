#!/usr/bin/env python3
"""Tono complejo de 1 kHz muestreado a 32 kS/s, en formato .cu8 como el del RTL-SDR.

Desde la raíz del repositorio:

    python samples/gen_tono.py

Escribe samples/tono_1kHz_32kSps.cu8: 3200 muestras, 6400 bytes, 0.1 s.
"""

from pathlib import Path

import numpy as np

FS = 32_000  # muestras por segundo
F0 = 1_000  # Hz
AMPLITUD = 100  # niveles del ADC alrededor del cero, que en .cu8 está en 127.5
DURACION = 0.1  # s
SALIDA = Path(__file__).parent / "tono_1kHz_32kSps.cu8"


def tono(fs=FS, f0=F0, amplitud=AMPLITUD, duracion=DURACION):
    """Bytes I, Q, I, Q... del tono complejo."""
    n = np.arange(round(fs * duracion))
    z = amplitud * np.exp(2j * np.pi * f0 * n / fs)
    iq = np.empty(2 * n.size, dtype=np.uint8)
    iq[0::2] = np.round(127.5 + z.real)
    iq[1::2] = np.round(127.5 + z.imag)
    return iq


if __name__ == "__main__":
    tono().tofile(SALIDA)
    print(f"{SALIDA.name}: {SALIDA.stat().st_size} bytes")

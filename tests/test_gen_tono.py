"""El tono sintético del laboratorio de muestreo: los números que la guía cita."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "samples/gen_tono.py"


def cargar():
    spec = importlib.util.spec_from_file_location("gen_tono", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestTono(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iq = cargar().tono()
        cls.i, cls.q = cls.iq[0::2], cls.iq[1::2]

    def test_son_6400_bytes_sin_signo(self):
        self.assertEqual(self.iq.dtype, np.uint8)
        self.assertEqual(self.iq.size, 6400)

    def test_un_cuarto_de_ciclo_son_8_muestras(self):
        """La guía pide encontrar los 90° en od: estos cuatro pares son los que leerá."""
        self.assertEqual((self.i[0], self.q[0]), (228, 128))
        self.assertEqual((self.i[8], self.q[8]), (128, 228))
        self.assertEqual((self.i[16], self.q[16]), (28, 128))
        self.assertEqual((self.i[24], self.q[24]), (127, 28))

    def test_la_muestra_32_empieza_otro_ciclo(self):
        """I vuelve a 228; Q sale 127 y no 128 porque 127.5 se redondea según el residuo."""
        self.assertEqual((self.i[32], self.q[32]), (228, 127))

    def test_usa_la_escala_sin_recortar(self):
        self.assertEqual((int(self.iq.min()), int(self.iq.max())), (28, 228))

    def test_fft_de_32_pone_el_tono_en_el_bin_1(self):
        d = self.iq.astype(float) - 127.5
        espectro = np.abs(np.fft.fft((d[0::2] + 1j * d[1::2])[:32]))
        self.assertEqual(int(espectro.argmax()), 1)
        self.assertGreater(espectro[1], 500 * np.delete(espectro, 1).max())


if __name__ == "__main__":
    unittest.main()

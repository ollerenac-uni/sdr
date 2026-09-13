"""Figura del calentamiento: los bytes de od dibujados contra el índice y el tiempo."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "docs/sessions/01-introduccion-sdr/figures/gen_muestreo.py"


def cargar():
    spec = importlib.util.spec_from_file_location("gen_muestreo", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestFiguraMuestreo(unittest.TestCase):
    def test_dibuja_33_muestras_para_que_se_vea_el_regreso(self):
        n, i, q = cargar().un_milisegundo()
        self.assertEqual(len(n), 33)
        self.assertEqual((i[0], q[0], i[8], q[8]), (228, 128, 128, 228))
        self.assertEqual((i[32], q[32]), (228, 127))

    def test_genera_el_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = cargar().generar(Path(tmp))
            self.assertEqual(ruta.name, "muestreo-un-milisegundo.png")
            self.assertGreater(ruta.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()

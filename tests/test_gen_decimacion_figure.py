"""Comportamiento que debe mostrar la figura reproducible de decimación."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
RUTA = ROOT / "docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py"


def cargar():
    spec = importlib.util.spec_from_file_location("gen_decimacion", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestDecimacionDeLaFigura(unittest.TestCase):
    def test_el_filtro_elimina_el_tono_que_se_plegaria(self):
        """Sin prefiltro, 400 kHz cae en 100 kHz al bajar de 2.4 MS/s a 300 kS/s."""
        g = cargar()
        n = np.arange(48_000)
        x = np.exp(2j * np.pi * 400_000 * n / g.FS)

        sin_filtro = g.decimar(x, g.D, filtrar=False)
        con_filtro = g.decimar(x, g.D, filtrar=True)
        f_sin, p_sin = g.psd_db(sin_filtro, g.FS / g.D)
        f_con, p_con = g.psd_db(con_filtro, g.FS / g.D)
        k_sin = np.argmin(np.abs(f_sin - 100_000))
        k_con = np.argmin(np.abs(f_con - 100_000))

        self.assertGreater(p_sin[k_sin] - p_con[k_con], 40)

    @unittest.skipUnless((ROOT / "samples/fm_99p1MHz_2p4Msps_g30.cu8").exists(),
                         "Falta la grabación oficial; se descarga de Drive")
    def test_genera_la_figura_de_decimacion(self):
        g = cargar()
        with tempfile.TemporaryDirectory() as temporal:
            ruta = g.generar(Path(temporal))
            self.assertEqual(ruta.name, "decimacion-con-y-sin-filtro.png")
            self.assertGreater(ruta.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()

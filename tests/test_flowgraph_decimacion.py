"""Contrato del grafo: compara descarte directo y decimación con prefiltro."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
TAPS = "firdes.low_pass(1, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)"


class TestGrafoDecimacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        grafo = yaml.safe_load((ROOT / "gnuradio-flowgraphs/decimacion.grc").read_text(encoding="utf-8"))
        cls.opciones = grafo["options"]["parameters"]
        cls.bloques = {b["name"]: b["parameters"] for b in grafo["blocks"]}
        cls.conexiones = {tuple(c) for c in grafo["connections"]}

    def test_compara_las_dos_ramas_desde_la_muestra_oficial(self):
        self.assertEqual(self.opciones["id"], "decimacion")
        self.assertEqual(self.bloques["blocks_file_source_0"]["file"],
                         "../samples/fm_99p1MHz_2p4Msps_g30.cu8")
        self.assertEqual(self.bloques["samp_rate"]["value"], "2400000")
        self.assertEqual(self.bloques["D"]["value"], "8")
        self.assertIn(("blocks_float_to_complex_0", "0", "blocks_keep_one_in_n_0", "0"), self.conexiones)
        self.assertIn(("blocks_float_to_complex_0", "0", "fir_filter_xxx_0", "0"), self.conexiones)

    def test_la_rama_filtrada_restringe_la_banda_antes_de_descartar(self):
        fir = self.bloques["fir_filter_xxx_0"]
        self.assertEqual((fir["type"], fir["decim"], fir["taps"]), ("ccf", "D", TAPS))
        self.assertEqual(self.bloques["qtgui_freq_sink_sin_filtro"]["bw"], "samp_rate/D")
        self.assertEqual(self.bloques["qtgui_freq_sink_con_filtro"]["bw"], "samp_rate/D")


if __name__ == "__main__":
    unittest.main()

"""Contrato del receptor FM: archivo CU8 reproducible y entrada Soapy opcional."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
GRAFO = ROOT / "gnuradio-flowgraphs/receptor_fm_99p1_2p048Msps.grc"


class TestReceptorFm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        grafo = yaml.safe_load(GRAFO.read_text(encoding="utf-8"))
        cls.opciones = grafo["options"]["parameters"]
        cls.bloques = {bloque["name"]: bloque for bloque in grafo["blocks"]}
        cls.conexiones = {tuple(conexion) for conexion in grafo["connections"]}

    def parametros(self, nombre):
        return self.bloques[nombre]["parameters"]

    def test_la_ruta_predeterminada_lee_cu8_a_2048_msps(self):
        self.assertEqual(self.opciones["id"], "receptor_fm_99p1_2p048Msps")
        self.assertEqual(self.parametros("samp_rate")["value"], "2048000")
        fuente = self.parametros("blocks_file_source_0")
        self.assertEqual(fuente["type"], "byte")
        self.assertEqual(fuente["file"], "../samples/fm_99p1MHz_2p048Msps_g30.cu8")
        self.assertEqual(self.bloques["blocks_file_source_0"]["states"]["state"], "enabled")
        self.assertEqual(self.parametros("blocks_throttle2_0")["samples_per_second"], "2*samp_rate")

    def test_convierte_los_bytes_iq_antes_del_resampler(self):
        self.assertEqual(self.parametros("blocks_add_const_vxx_0")["const"], "-127.5")
        self.assertEqual(self.parametros("blocks_multiply_const_vxx_0")["const"], "1/127.5")
        for puerto in ("0", "1"):
            self.assertIn(("blocks_deinterleave_0", puerto, "blocks_float_to_complex_0", puerto),
                          self.conexiones)
        self.assertIn(("blocks_float_to_complex_0", "0", "rational_resampler_xxx_0", "0"),
                      self.conexiones)

    def test_el_receptor_sigue_las_tasas_de_la_guia_oficial(self):
        resampler = self.parametros("rational_resampler_xxx_0")
        self.assertEqual((resampler["type"], resampler["interp"], resampler["decim"]),
                         ("ccc", "3", "32"))
        wbfm = self.parametros("analog_wfm_rcv_0")
        self.assertEqual((wbfm["quad_rate"], wbfm["audio_decimation"]), ("192000", "4"))
        self.assertEqual(self.parametros("audio_sink_0")["samp_rate"], "48000")

    def test_soapy_permanece_como_alternativa_desactivada(self):
        soapy = self.bloques["soapy_rtlsdr_source_0"]
        self.assertEqual(soapy["states"]["state"], "disabled")
        self.assertEqual(self.parametros("soapy_rtlsdr_source_0")["samp_rate"], "samp_rate")
        self.assertIn(("soapy_rtlsdr_source_0", "0", "rational_resampler_xxx_0", "0"),
                      self.conexiones)


if __name__ == "__main__":
    unittest.main()

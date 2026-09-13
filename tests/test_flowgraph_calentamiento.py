"""Contrato del grafo del calentamiento: la cadena de test2.grc a 32 kS/s sobre el tono."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def cargar(nombre):
    grafo = yaml.safe_load((ROOT / "gnuradio-flowgraphs" / nombre).read_text(encoding="utf-8"))
    return grafo, {b["name"]: b for b in grafo["blocks"]}, {tuple(c) for c in grafo["connections"]}


class TestCalentamiento(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafo, cls.b, cls.c = cargar("calentamiento_32k.grc")

    def p(self, nombre):
        return self.b[nombre]["parameters"]

    def test_identidad_y_tasa(self):
        self.assertEqual(self.grafo["options"]["parameters"]["id"], "calentamiento_32k")
        self.assertEqual(self.p("samp_rate")["value"], "32000")

    def test_lee_el_tono_como_bytes(self):
        fuente = self.p("blocks_file_source_0")
        self.assertEqual(fuente["file"], "../samples/tono_1kHz_32kSps.cu8")
        self.assertEqual(fuente["type"], "byte")
        self.assertEqual(fuente["repeat"], "False")
        self.assertEqual((fuente["offset"], fuente["length"]), ("0", "64"))
        self.assertEqual(self.p("blocks_throttle2_0")["samples_per_second"], "2*samp_rate")

    def test_misma_cadena_que_test2(self):
        cadena = ["blocks_file_source_0", "blocks_throttle2_0", "blocks_uchar_to_float_0",
                  "blocks_add_const_vxx_0", "blocks_multiply_const_vxx_0", "blocks_deinterleave_0"]
        for origen, destino in zip(cadena, cadena[1:]):
            self.assertIn((origen, "0", destino, "0"), self.c)
        for sumidero in ("qtgui_freq_sink_x_0", "qtgui_time_sink_x_0"):
            self.assertIn(("blocks_float_to_complex_0", "0", sumidero, "0"), self.c)

    def test_el_time_sink_muestra_un_periodo_de_bytes_crudos(self):
        """El File Source termina tras 64 bytes, así que la imagen se congela en el primer
        periodo: no hace falta disparo. Marcadores como en la Figura 1: círculo I, cuadrado Q."""
        t = self.p("qtgui_time_sink_x_0")
        self.assertEqual((t["size"], t["srate"]), ("32", "samp_rate"))
        self.assertEqual(t["tr_mode"], "qtgui.TRIG_MODE_FREE")
        self.assertEqual((t["ymin"], t["ymax"]), ("0", "256"))
        self.assertEqual((t["label1"], t["label2"]), ("I", "Q"))
        self.assertEqual((t["marker1"], t["marker2"]), ("0", "1"))

    def test_la_normalizacion_empieza_en_bypass(self):
        """La guía empieza comparando los bytes crudos con od; el alumno quita el bypass en 1.5."""
        for nombre, const in (("blocks_add_const_vxx_0", "-127.5"), ("blocks_multiply_const_vxx_0", "1/127.5")):
            with self.subTest(bloque=nombre):
                self.assertEqual(self.b[nombre]["states"]["state"], "bypassed")
                self.assertEqual(self.p(nombre)["const"], const)

    def test_el_freq_sink_da_bins_de_1_khz_sin_ensanchar_la_raya(self):
        f = self.p("qtgui_freq_sink_x_0")
        self.assertEqual((f["fftsize"], f["bw"], f["fc"]), ("32", "samp_rate", "0"))
        self.assertEqual(f["wintype"], "window.WIN_RECTANGULAR")
        self.assertEqual(f["label1"], "Espectro")

    def test_sin_hardware(self):
        """El dongle no puede muestrear a 32 kS/s: no hay fuente de hardware."""
        self.assertFalse([n for n in self.b if n.startswith("soapy_")])


if __name__ == "__main__":
    unittest.main()

"""Contrato de las fuentes alternativas del flowgraph de prueba."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
FLOWGRAPH = ROOT / "gnuradio-flowgraphs/test.grc"


class TestFlowgraphSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph = yaml.safe_load(FLOWGRAPH.read_text(encoding="utf-8"))
        cls.blocks = {block["name"]: block for block in graph["blocks"]}
        cls.connections = {tuple(connection) for connection in graph["connections"]}

    def test_recorded_complex_file_is_the_active_throttled_source(self):
        """Evita volver a interpretar una grabación .cu8 como complex64."""
        file_source = self.blocks["blocks_file_source_0"]
        throttle = self.blocks["blocks_throttle2_0"]

        self.assertEqual(file_source["states"]["state"], "enabled")
        self.assertEqual(file_source["parameters"]["type"], "complex")
        self.assertTrue(file_source["parameters"]["file"].endswith(".cfile"))
        self.assertEqual(throttle["states"]["state"], "enabled")
        self.assertEqual(throttle["parameters"]["type"], "complex")
        self.assertEqual(throttle["parameters"]["samples_per_second"], "samp_rate")

        self.assertIn(
            ("blocks_file_source_0", "0", "blocks_throttle2_0", "0"),
            self.connections,
        )
        self.assertIn(
            ("blocks_throttle2_0", "0", "qtgui_freq_sink_x_0", "0"),
            self.connections,
        )
        self.assertIn(
            ("blocks_throttle2_0", "0", "qtgui_time_sink_x_0", "0"),
            self.connections,
        )

    def test_soapy_source_remains_visible_but_disabled(self):
        """Evita que el flowgraph requiera un dongle de forma predeterminada."""
        soapy_source = self.blocks["soapy_rtlsdr_source_0"]

        self.assertEqual(soapy_source["states"]["state"], "disabled")
        self.assertIn(
            ("soapy_rtlsdr_source_0", "0", "qtgui_freq_sink_x_0", "0"),
            self.connections,
        )
        self.assertIn(
            ("soapy_rtlsdr_source_0", "0", "qtgui_time_sink_x_0", "0"),
            self.connections,
        )


if __name__ == "__main__":
    unittest.main()

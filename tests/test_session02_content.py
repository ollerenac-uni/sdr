"""Contrato pedagógico y de publicación para la Sesión 02."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SESSION_DIR = ROOT / "docs/sessions/02-tiempo-frecuencia-iq"
ARTICLE = SESSION_DIR / "index.md"
MKDOCS = ROOT / "mkdocs.yml"


class Session02ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markdown = ARTICLE.read_text(encoding="utf-8")
        cls.nav = MKDOCS.read_text(encoding="utf-8")

    def test_page_is_a_draft_session_two_and_is_in_navigation(self):
        self.assertIn('title: "Sesión 02', self.markdown)
        self.assertIn("session: 2", self.markdown)
        self.assertIn("status: draft", self.markdown)
        self.assertIn(
            "sessions/02-tiempo-frecuencia-iq/index.md",
            self.nav,
        )

    def test_practical_math_contract_is_explicit(self):
        required = (
            "dos representaciones de la misma señal",
            r"\Delta f = \frac{f_s}{N}",
            "señal real",
            "señal compleja",
            "fuga espectral",
            "traslación en frecuencia",
            "No se evalúa",
        )
        for text in required:
            with self.subTest(text=text):
                self.assertIn(text, self.markdown)

    def test_figures_are_referenced_and_generated(self):
        names = {
            "dominios-tiempo-frecuencia.png",
            "armonicos-y-recorte.png",
            "fuga-y-ventanas.png",
            "ejes-fft.png",
            "real-vs-compleja.png",
            "traslacion-frecuencia.png",
        }
        for name in names:
            with self.subTest(name=name):
                self.assertIn(f"figures/{name}", self.markdown)
                self.assertTrue((SESSION_DIR / "figures" / name).is_file())

    def test_real_capture_route_is_file_first_and_hardware_optional(self):
        self.assertIn("File Source → Throttle", self.markdown)
        self.assertIn("Soapy RTL-SDR Source", self.markdown)
        self.assertIn("desactivada (`D`)", self.markdown)
        self.assertIn("gnuradio-flowgraphs/test.grc", self.markdown)

    def test_official_data_stays_cu8_and_conversion_is_explicit(self):
        self.assertIn("dtype=np.uint8", self.markdown)
        self.assertIn("def load_cu8", self.markdown)
        self.assertIn("0/255", self.markdown)
        self.assertIn(".tofile", self.markdown)
        self.assertIn("SHA-256", self.markdown)

    def test_deferred_topics_are_named_as_out_of_scope(self):
        for topic in (
            "integrales de la transformada continua",
            "algoritmo interno de la FFT",
            "ganancia de procesamiento de la FFT",
            "convolución",
        ):
            with self.subTest(topic=topic):
                self.assertIn(topic, self.markdown)

    def test_all_embedded_python_examples_parse(self):
        blocks = re.findall(
            r"```python\n(.*?)\n```",
            self.markdown,
            flags=re.DOTALL,
        )
        self.assertGreaterEqual(len(blocks), 5)
        for number, block in enumerate(blocks, start=1):
            with self.subTest(block=number):
                compile(block, f"session02-example-{number}", "exec")


if __name__ == "__main__":
    unittest.main()

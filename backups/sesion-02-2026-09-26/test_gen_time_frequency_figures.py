"""Regresiones de las figuras de tiempo, frecuencia e IQ de la Sesión 02."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
GENERATOR = (
    ROOT
    / "docs/sessions/02-tiempo-frecuencia-iq/figures/gen_time_frequency.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_time_frequency", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TimeFrequencyFigureGeneratorTests(unittest.TestCase):
    def test_generator_writes_six_nonempty_png_files(self):
        module = load_generator()
        with tempfile.TemporaryDirectory() as tmp:
            paths = module.generate_figures(Path(tmp))

            self.assertEqual(len(paths), 6)
            self.assertEqual(
                {path.name for path in paths},
                {
                    "dominios-tiempo-frecuencia.png",
                    "armonicos-y-recorte.png",
                    "fuga-y-ventanas.png",
                    "ejes-fft.png",
                    "real-vs-compleja.png",
                    "traslacion-frecuencia.png",
                },
            )
            for path in paths:
                with self.subTest(path=path.name):
                    self.assertTrue(path.is_file())
                    self.assertGreater(path.stat().st_size, 10_000)
                    self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_course_fft_examples_have_the_expected_bin_spacing(self):
        module = load_generator()

        self.assertEqual(module.bin_spacing(32_000, 1_024), 31.25)
        self.assertAlmostEqual(module.bin_spacing(2_400_000, 4_096), 585.9375)


if __name__ == "__main__":
    unittest.main()

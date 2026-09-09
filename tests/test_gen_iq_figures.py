"""Pruebas de las figuras didácticas de señales I/Q de la Sesión 01."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "docs/sessions/01-introduccion-sdr/figures/gen_iq.py"


def load_generator():
    if not SCRIPT.exists():
        raise AssertionError(f"Falta el generador esperado: {SCRIPT}")

    spec = importlib.util.spec_from_file_location("gen_iq", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"No se pudo cargar el generador: {SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IQFigureGeneratorTests(unittest.TestCase):
    def test_i_plus_jq_cancels_the_negative_frequency_copy(self):
        """Falla si se invierte Q o si I+jQ conserva ambas copias espectrales."""
        generator = load_generator()
        _, i_signal, q_signal, complex_signal = generator.quadrature_tone(
            sample_count=1024,
            cycles=11,
        )

        np.testing.assert_allclose(complex_signal, i_signal + 1j * q_signal)
        spectrum = np.fft.fft(complex_signal)
        positive_power = abs(spectrum[11])
        negative_power = abs(spectrum[-11])

        self.assertGreater(positive_power, 1000 * max(negative_power, 1e-12))

    def test_generator_writes_both_nonempty_png_files(self):
        """Falla si una de las dos explicaciones visuales deja de generarse."""
        generator = load_generator()

        with tempfile.TemporaryDirectory() as directory:
            paths = generator.generate_figures(Path(directory))

            self.assertEqual(
                {path.name for path in paths},
                {"iq-cuadratura-tiempo.png", "iq-cancelacion-espectral.png"},
            )
            for path in paths:
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 20_000)
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

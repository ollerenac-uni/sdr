"""Pruebas de las figuras de arquitectura de la Sesión 01."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = (
    ROOT
    / "docs/sessions/01-introduccion-sdr/figures/gen_architecture_figures.py"
)


def load_generator():
    if not SCRIPT.exists():
        raise AssertionError(f"Falta el generador esperado: {SCRIPT}")

    spec = importlib.util.spec_from_file_location("gen_architecture_figures", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"No se pudo cargar el generador: {SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArchitectureFigureGeneratorTests(unittest.TestCase):
    def test_generator_writes_three_nonempty_png_files(self):
        """Falla si falta una figura o deja de producir un PNG válido."""
        generator = load_generator()

        with tempfile.TemporaryDirectory() as directory:
            paths = generator.generate_figures(Path(directory))

            self.assertEqual(
                {path.name for path in paths},
                {
                    "radio-convencional-vs-sdr.png",
                    "arquitecturas-receptores-sdr.png",
                    "rtl-sdr-v4-interior.png",
                },
            )
            for path in paths:
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 20_000)
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()

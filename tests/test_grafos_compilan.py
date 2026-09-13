"""Todo .grc del repositorio debe cargar en GNU Radio Companion.

Los tests de contrato leen el YAML y pueden pasar con un grafo que GRC no carga: un id de
bloque mal escrito (filter_fir_filter_xxx en vez de fir_filter_xxx) crea un bloque ficticio
y deja puertos sin conectar. Solo compilar lo detecta.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
GRCC = next((str(p) for p in (Path.home() / "radioconda/bin/grcc",) if p.exists()), None) or shutil.which("grcc") or ""


@unittest.skipUnless(GRCC and Path(GRCC).exists(), "grcc no disponible: instala radioconda")
class TestGrafosCompilan(unittest.TestCase):
    def test_cada_grc_compila(self):
        for grafo in sorted((ROOT / "gnuradio-flowgraphs").glob("*.grc")):
            with self.subTest(grafo=grafo.name), tempfile.TemporaryDirectory() as tmp:
                r = subprocess.run([GRCC, "-o", tmp, str(grafo)], capture_output=True, text=True, timeout=120)
                self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-800:])


if __name__ == "__main__":
    unittest.main()

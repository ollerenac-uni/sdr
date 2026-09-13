"""Lo que la guía del laboratorio de muestreo afirma, comprobado contra la realidad."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PAGINA = ROOT / "docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md"
GITHUB = "https://github.com/ollerenac-uni/sdr/blob/main/"


def texto():
    return PAGINA.read_text(encoding="utf-8")


class TestCalentamiento(unittest.TestCase):
    def test_la_salida_de_od_publicada_es_la_real(self):
        """Regla de AGENTS.md: todo comando se ejecuta antes de publicarse."""
        spec = importlib.util.spec_from_file_location("gen_tono", ROOT / "samples/gen_tono.py")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "tono.cu8"
            gen.tono().tofile(ruta)
            salida = subprocess.run(["od", "-Ad", "-tu1", "-w2", "-N64", "-v", str(ruta)],
                                    capture_output=True, text=True, check=True).stdout
        pagina = texto()
        for linea in salida.splitlines():
            self.assertIn(linea, pagina, f"La guía no muestra la línea real de od: {linea!r}")

    def test_enlaza_el_generador_y_el_grafo(self):
        pagina = texto()
        self.assertIn(GITHUB + "samples/gen_tono.py", pagina)
        self.assertIn(GITHUB + "gnuradio-flowgraphs/calentamiento_32k.grc", pagina)

    def test_cita_los_numeros_que_sostienen_el_ejercicio(self):
        pagina = texto()
        for dato in ("od -Ad -tu1 -w2 -N64 -v samples/tono_1kHz_32kSps.cu8",
                     "0.788", "31.25 Hz", "32 ms", "0000064", "WIN_RECTANGULAR"):
            self.assertIn(dato, pagina)


if __name__ == "__main__":
    unittest.main()

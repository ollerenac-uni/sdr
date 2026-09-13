"""Lo que la guía del laboratorio de muestreo afirma, comprobado contra la realidad."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PAGINA = ROOT / "docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md"
GITHUB = "https://github.com/ollerenac-uni/sdr/blob/main/"
MUESTRA = "samples/fm_99p1MHz_2p4Msps_g30.cu8"


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
            tamano = ruta.stat().st_size
            salida = subprocess.run(["od", "-Ad", "-tu1", "-w2", "-N64", "-v", str(ruta)],
                                    capture_output=True, text=True, check=True).stdout
        pagina = texto()
        bloque = re.search(r"El segundo imprime esto:\n\n```\n(.*?)```", pagina, re.S)
        self.assertIsNotNone(bloque, "No se encuentra el bloque de salida de od tras «El segundo imprime esto:»")
        self.assertEqual(bloque.group(1), salida)
        self.assertIn(f"`tono_1kHz_32kSps.cu8: {tamano} bytes`", pagina)

    def test_enlaza_el_generador_y_el_grafo(self):
        pagina = texto()
        self.assertIn(GITHUB + "samples/gen_tono.py", pagina)
        self.assertIn(GITHUB + "gnuradio-flowgraphs/calentamiento_32k.grc", pagina)

    def test_cita_los_numeros_que_sostienen_el_ejercicio(self):
        pagina = texto()
        for dato in ("od -Ad -tu1 -w2 -N64 -v samples/tono_1kHz_32kSps.cu8",
                     "0.788", "31.25 Hz", "32 ms", "0000064"):
            self.assertIn(dato, pagina)


class TestGrabacionReal(unittest.TestCase):
    def test_cita_las_cuentas_a_24_msps(self):
        pagina = texto()
        for dato in (f"wc -c < {MUESTRA}", "48000000",
                     f"od -An -tu1 -w2 -N4800 -v {MUESTRA} | wc -l",
                     "2343.75 Hz", "426.7 µs", "1171.875 Hz", "585.9 Hz"):
            self.assertIn(dato, pagina)

    @unittest.skipUnless((ROOT / MUESTRA).exists(),
                         f"Falta {MUESTRA}; se descarga de Drive")
    def test_los_comandos_publicados_dan_lo_que_dice_la_guia(self):
        for comando, esperado in ((f"wc -c < {MUESTRA}", "48000000"),
                                  (f"od -An -tu1 -w2 -N4800 -v {MUESTRA} | wc -l", "2400"),
                                  (f"od -Ad -tu1 -w2 -N4800 -v {MUESTRA} | wc -l", "2401")):
            with self.subTest(comando=comando):
                salida = subprocess.run(comando, shell=True, cwd=ROOT,
                                        capture_output=True, text=True, check=True).stdout
                self.assertEqual(salida.strip(), esperado)


if __name__ == "__main__":
    unittest.main()

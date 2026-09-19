"""Lo que la guía del laboratorio de muestreo afirma, comprobado contra la realidad."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
PAGINA = ROOT / "docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md"
GITHUB = "https://github.com/ollerenac-uni/sdr/blob/main/"
MUESTRA = "samples/fm_99p1MHz_2p4Msps_g30.cu8"


def texto():
    return PAGINA.read_text(encoding="utf-8")


def tono():
    """Bytes del tono tal como los escribe samples/gen_tono.py."""
    spec = importlib.util.spec_from_file_location("gen_tono", ROOT / "samples/gen_tono.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen.tono()


def od(*opciones, bytes_):
    """Salida de od sobre los bytes del tono, escritos en un directorio temporal."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "tono.cu8"
        bytes_.tofile(ruta)
        return subprocess.run(["od", *opciones, str(ruta)], capture_output=True, text=True, check=True).stdout


class TestCalentamiento(unittest.TestCase):
    def test_la_salida_de_od_publicada_es_la_real(self):
        """Regla de AGENTS.md: todo comando se ejecuta antes de publicarse."""
        b = tono()
        tamano = b.nbytes
        salida = od("-Ad", "-tu1", "-w2", "-N64", "-v", bytes_=b)
        pagina = texto()
        bloque = re.search(r"El segundo imprime esto:\n\n```\n(.*?)```", pagina, re.S)
        self.assertIsNotNone(bloque, "No se encuentra el bloque de salida de od tras «El segundo imprime esto:»")
        self.assertEqual(bloque.group(1), salida)
        self.assertIn(f"`tono_1kHz_32kSps.cu8: {tamano} bytes`", pagina)

    def test_la_salida_de_od_b_publicada_es_la_real(self):
        primera = od("-b", "-N32", bytes_=tono()).splitlines()[0]
        citada = "0000000 344 200 342 223"
        self.assertTrue(primera.startswith(citada), primera)
        self.assertIn(f"`{citada}`", texto())

    def test_la_salida_octal_y_decimal_publicada_es_la_real(self):
        comando = "od -Ad -to1 -tu1 -w2 -N8 samples/tono_1kHz_32kSps.cu8"
        salida = od(*comando.split()[1:-1], bytes_=tono())
        bloque = re.search(r"    ```bash\n    " + re.escape(comando) + r"\n    ```\n\n    ```\n(.*?)    ```",
                           texto(), re.S)
        self.assertIsNotNone(bloque, f"No se encuentra el bloque de salida de {comando}")
        self.assertEqual(textwrap.dedent(bloque.group(1)), salida)

    def test_las_cifras_del_espectro_de_32_muestras(self):
        """Espectros de un periodo normalizado como la cadena: FFT/N en dB, ventana rectangular."""
        b = tono().astype(float)
        z = ((b[0::2] - 127.5) + 1j * (b[1::2] - 127.5)) / 127.5
        periodos = z.reshape(-1, 32)
        db = 20 * np.log10(np.maximum(np.abs(np.fft.fft(periodos, axis=1)) / 32, 1e-12))
        khz = np.fft.fftfreq(32, 1 / 32).astype(int)
        huecos = db < -100
        pagina = texto()

        self.assertFalse(huecos[0].any())
        segundo = sorted(khz[huecos[1]])
        self.assertEqual(segundo, [-13, -9, -5, -1, 3, 7, 11, 15])
        lista = [f"−{-k}" if k < 0 else f"+{k}" for k in segundo]
        self.assertIn(", ".join(lista[:-1]) + " y " + lista[-1] + " kHz", pagina)

        sin_huecos = int((~huecos.any(axis=1)).sum())
        self.assertEqual(sin_huecos, 26)
        self.assertIn(f"{sin_huecos} de los 100", pagina)
        ceros_127 = int((b[0::2].reshape(-1, 32)[:, 8] == 127).sum())
        self.assertEqual(ceros_127, 14)
        self.assertIn(f"{ceros_127} de los 100", pagina)

        n = np.arange(32)
        amplitud = 100 / 127.5
        error = periodos[0] - amplitud * np.exp(2j * np.pi * n / 32)
        error_db = 10 * np.log10(amplitud**2 / np.mean(np.abs(error) ** 2))
        potencia = np.abs(np.fft.fft(periodos[0]) / 32) ** 2
        resto_db = 10 * np.log10(potencia[1] / (potencia.sum() - potencia[1]))
        for valor, citado in ((error_db, "47.8 dB"), (resto_db, "48.8 dB")):
            self.assertEqual(f"{valor:.1f} dB", citado)
            self.assertIn(citado, pagina)

    def test_enlaza_el_generador_y_el_grafo(self):
        pagina = texto()
        self.assertIn(GITHUB + "samples/gen_tono.py", pagina)
        self.assertIn(GITHUB + "gnuradio-flowgraphs/warmup_32k.grc", pagina)

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

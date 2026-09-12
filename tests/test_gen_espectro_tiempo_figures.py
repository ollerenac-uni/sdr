"""Pruebas del generador de figuras del cierre de la Sesión 01.

El generador es el único de la sesión que depende de la grabación oficial, que no
está en el repositorio. Las pruebas que necesitan datos se omiten si falta, pero
las que comprueban el contrato del módulo se ejecutan siempre.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "docs/sessions/01-introduccion-sdr/figures/gen_espectro_tiempo.py"
FIGURAS = ("de-muestras-a-espectro.png", "espectrograma.png", "superficie3d.png")


def load_generator():
    if not SCRIPT.exists():
        raise AssertionError(f"Falta el generador esperado: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("gen_espectro_tiempo", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"No se pudo cargar el generador: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestContratoDelModulo(unittest.TestCase):
    """No necesitan la grabación."""

    @classmethod
    def setUpClass(cls):
        cls.gen = load_generator()

    def test_los_parametros_coinciden_con_la_grabacion_del_curso(self):
        self.assertEqual(self.gen.FS, 2.4e6)
        self.assertEqual(self.gen.FC, 99.1e6)
        self.assertEqual(self.gen.N, 2048)

    def test_la_resolucion_publicada_en_la_leccion_es_la_que_calcula(self):
        """La lección afirma 853 µs de bloque y 1172 Hz de resolución."""
        tb = self.gen.N / self.gen.FS
        self.assertAlmostEqual(tb * 1e6, 853.3, places=1)
        self.assertAlmostEqual(1 / tb, 1171.9, places=1)
        self.assertAlmostEqual(1 / tb, self.gen.FS / self.gen.N, places=6)

    def test_la_emisora_de_98_1_MHz_cae_en_el_bin_anotado(self):
        """La figura etiqueta el bin −853; debe salir de la aritmética."""
        offset = 98.1e6 - self.gen.FC
        self.assertEqual(round(offset / (self.gen.FS / self.gen.N)), -853)

    def test_la_grabacion_ausente_da_un_mensaje_util(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            self.gen.cargar_iq(ruta=Path("/no/existe/muestra.cu8"))
        self.assertIn("Drive", str(ctx.exception))

    def test_el_espectrograma_devuelve_ejes_coherentes(self):
        """Sobre datos sintéticos: un tono debe caer en su bin."""
        n, filas = self.gen.N, 4
        k = 100
        muestras = np.exp(2j * np.pi * k * np.arange(n * filas * 3) / n)
        f, t, db = self.gen.espectrograma(muestras, n=n, filas=filas)
        self.assertEqual(db.shape, (filas, n))
        self.assertEqual(len(f), n)
        self.assertEqual(len(t), filas)
        self.assertEqual(int(db[0].argmax()) - n // 2, k)
        self.assertAlmostEqual(f[n // 2], self.gen.FC / 1e6, places=6)


@unittest.skipUnless(
    (ROOT / "samples/fm_99p1MHz_2p4Msps_g30.cu8").exists(),
    "Falta samples/fm_99p1MHz_2p4Msps_g30.cu8; se descarga de Drive",
)
class TestConLaGrabacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gen = load_generator()

    def test_la_grabacion_se_lee_normalizada(self):
        iq = self.gen.cargar_iq(cuenta=100_000)
        self.assertEqual(len(iq), 100_000)
        self.assertLessEqual(np.abs(iq).max(), 1.5)
        self.assertLess(abs(iq.real.mean()), 0.05, "offset DC inesperado")


class TestFigurasPublicadas(unittest.TestCase):
    def test_las_tres_figuras_estan_en_el_repositorio(self):
        """La lección las enlaza; deben existir aunque falte la grabación."""
        for nombre in FIGURAS:
            with self.subTest(figura=nombre):
                ruta = SCRIPT.parent / nombre
                self.assertTrue(ruta.exists(), f"Falta la figura {nombre}")
                self.assertGreater(ruta.stat().st_size, 10_000)

    def test_la_leccion_enlaza_las_tres(self):
        leccion = (ROOT / "docs/sessions/01-introduccion-sdr/index.md").read_text(encoding="utf-8")
        for nombre in FIGURAS:
            with self.subTest(figura=nombre):
                self.assertIn(f"figures/{nombre}", leccion)


if __name__ == "__main__":
    unittest.main()

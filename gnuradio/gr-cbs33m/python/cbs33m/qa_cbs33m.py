"""Pruebas de conversión, consumo de elementos y continuidad del oscilador."""

import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np
from gnuradio import blocks, gr


CARPETA = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "cbs33m_qa", CARPETA / "__init__.py", submodule_search_locations=[str(CARPETA)]
)
cbs33m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cbs33m
SPEC.loader.exec_module(cbs33m)


class TestBloquesCBS33M(unittest.TestCase):
    def test_conversor_conserva_todas_las_parejas(self):
        datos = np.tile(np.array([255, 0, 0, 255, 127, 128], np.uint8), 337)
        fuente = blocks.vector_source_b(datos.tolist(), False)
        conversor = cbs33m.cu8_a_c64()
        destino = blocks.vector_sink_c()
        tb = gr.top_block()
        tb.connect(fuente, conversor, destino)
        tb.run()
        esperado = (datos.astype(np.float32) - 127.5) / 127.5
        esperado = esperado[0::2] + 1j * esperado[1::2]
        np.testing.assert_allclose(destino.data(), esperado, atol=1e-7)
        self.assertEqual(len(destino.data()) * 2, len(datos))

    def test_rotador_es_independiente_de_los_lotes(self):
        entrada = np.linspace(0.1, 1, 43).astype(np.complex64) * (1 + 0.5j)
        for frecuencia in (0, 600000, -400000):
            with self.subTest(frecuencia=frecuencia):
                bloque = cbs33m.rotador_frecuencia(frecuencia, 2.4e6)
                partes = []
                inicio = 0
                for cantidad in (4, 7, 3, 29):
                    salida = np.zeros(cantidad, np.complex64)
                    self.assertEqual(
                        bloque.work([entrada[inicio:inicio + cantidad]], [salida]),
                        cantidad,
                    )
                    partes.extend(salida)
                    inicio += cantidad
                esperado = entrada * np.exp(2j * np.pi * frecuencia * np.arange(43) / 2.4e6)
                np.testing.assert_allclose(partes, esperado, atol=2e-6)

    def test_resintonia_conserva_la_fase_de_continuacion(self):
        bloque = cbs33m.rotador_frecuencia(400000, 2.4e6)
        salida = np.zeros(4, np.complex64)
        bloque.work([np.ones(4, np.complex64)], [salida])
        fase = bloque.fase
        bloque.set_frecuencia_mezcla(-600000)
        bloque.work([np.ones(4, np.complex64)], [salida])
        esperado = np.exp(1j * (fase - np.pi / 2 * np.arange(4)))
        np.testing.assert_allclose(salida, esperado, atol=1e-6)

    def test_parametros_invalidos(self):
        for escala in (0, -1, np.inf, np.nan):
            with self.subTest(escala=escala), self.assertRaises(ValueError):
                cbs33m.cu8_a_c64(escala)
        for tasa in (0, -1, np.inf, np.nan):
            with self.subTest(tasa=tasa), self.assertRaises(ValueError):
                cbs33m.rotador_frecuencia(0, tasa)
        bloque = cbs33m.rotador_frecuencia()
        with self.assertRaises(ValueError):
            bloque.set_frecuencia_mezcla(np.nan)


if __name__ == "__main__":
    unittest.main()

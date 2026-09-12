"""Contrato de los dos flowgraphs de la Sesión 01.

`test.grc` falla a propósito: declara la muestra `.cu8` como `complex64` para que
el alumno vea qué ocurre. `test2.grc` es la solución de referencia y lee el mismo
archivo byte a byte. Estos tests impiden que alguien "arregle" el primero por
descuido o rompa la cadena del segundo.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
MUESTRA = "../samples/fm_99p1MHz_2p4Msps_g30.cu8"


def cargar(nombre):
    grafo = yaml.safe_load((ROOT / "gnuradio-flowgraphs" / nombre).read_text(encoding="utf-8"))
    bloques = {b["name"]: b for b in grafo["blocks"]}
    conexiones = {tuple(c) for c in grafo["connections"]}
    return grafo, bloques, conexiones


class TestPruebaFallida(unittest.TestCase):
    """test.grc: el error es deliberado y debe conservarse."""

    @classmethod
    def setUpClass(cls):
        cls.grafo, cls.bloques, cls.conexiones = cargar("test.grc")

    def test_el_file_source_declara_complex_sobre_un_cu8(self):
        fuente = self.bloques["blocks_file_source_0"]
        self.assertEqual(fuente["states"]["state"], "enabled")
        self.assertEqual(fuente["parameters"]["type"], "complex")
        self.assertTrue(
            fuente["parameters"]["file"].endswith(".cu8"),
            "El fallo de la Parte B depende de apuntar a un .cu8 con tipo complex.",
        )

    def test_no_hay_cadena_de_conversion(self):
        """Si alguien añade la conversión aquí, la Parte B deja de fallar."""
        for bloque in ("blocks_uchar_to_float_0", "blocks_deinterleave_0"):
            self.assertNotIn(bloque, self.bloques)

    def test_el_throttle_alimenta_los_dos_sumideros(self):
        throttle = self.bloques["blocks_throttle2_0"]
        self.assertEqual(throttle["parameters"]["type"], "complex")
        self.assertIn(("blocks_file_source_0", "0", "blocks_throttle2_0", "0"), self.conexiones)
        for sumidero in ("qtgui_freq_sink_x_0", "qtgui_time_sink_x_0"):
            self.assertIn(("blocks_throttle2_0", "0", sumidero, "0"), self.conexiones)


class TestLecturaCorrecta(unittest.TestCase):
    """test2.grc: la cadena de siete bloques de la Parte C."""

    @classmethod
    def setUpClass(cls):
        cls.grafo, cls.bloques, cls.conexiones = cargar("test2.grc")

    def test_la_fuente_entrega_bytes_crudos(self):
        fuente = self.bloques["blocks_file_source_0"]
        self.assertEqual(fuente["states"]["state"], "enabled")
        self.assertEqual(fuente["parameters"]["type"], "byte")
        self.assertTrue(fuente["parameters"]["file"].endswith(".cu8"))

    def test_el_throttle_va_al_doble_por_ser_flujo_de_bytes(self):
        """Dos bytes por muestra compleja: a samp_rate se reproduce a media velocidad."""
        throttle = self.bloques["blocks_throttle2_0"]
        self.assertEqual(throttle["parameters"]["type"], "byte")
        self.assertEqual(throttle["parameters"]["samples_per_second"], "2*samp_rate")

    def test_las_constantes_centran_y_normalizan(self):
        self.assertEqual(self.bloques["blocks_add_const_vxx_0"]["parameters"]["const"], "-127.5")
        self.assertEqual(self.bloques["blocks_multiply_const_vxx_0"]["parameters"]["const"], "1/127.5")
        for nombre in ("blocks_add_const_vxx_0", "blocks_multiply_const_vxx_0", "blocks_deinterleave_0"):
            self.assertEqual(self.bloques[nombre]["parameters"]["type"], "float")

    def test_deinterleave_separa_en_dos_flujos(self):
        self.assertEqual(self.bloques["blocks_deinterleave_0"]["parameters"]["num_streams"], "2")
        for puerto in ("0", "1"):
            self.assertIn(
                ("blocks_deinterleave_0", puerto, "blocks_float_to_complex_0", puerto),
                self.conexiones,
            )

    def test_la_cadena_completa_esta_conectada_en_orden(self):
        cadena = [
            "blocks_file_source_0",
            "blocks_throttle2_0",
            "blocks_uchar_to_float_0",
            "blocks_add_const_vxx_0",
            "blocks_multiply_const_vxx_0",
            "blocks_deinterleave_0",
        ]
        for origen, destino in zip(cadena, cadena[1:]):
            self.assertIn((origen, "0", destino, "0"), self.conexiones)
        for sumidero in ("qtgui_freq_sink_x_0", "qtgui_time_sink_x_0"):
            self.assertIn(("blocks_float_to_complex_0", "0", sumidero, "0"), self.conexiones)


class TestContratoComun(unittest.TestCase):
    """Lo que ambos grafos deben cumplir para el laboratorio."""

    def test_el_dongle_queda_visible_pero_desactivado(self):
        """Ningún grafo puede exigir hardware para ejecutarse."""
        for nombre in ("test.grc", "test2.grc"):
            with self.subTest(grafo=nombre):
                _, bloques, conexiones = cargar(nombre)
                self.assertEqual(bloques["soapy_rtlsdr_source_0"]["states"]["state"], "disabled")
                for sumidero in ("qtgui_freq_sink_x_0", "qtgui_time_sink_x_0"):
                    self.assertIn(("soapy_rtlsdr_source_0", "0", sumidero, "0"), conexiones)

    def test_la_ruta_del_archivo_es_relativa(self):
        """Ruta relativa al .grc: GRC ejecuta el grafo desde la carpeta del .grc."""
        for nombre in ("test.grc", "test2.grc"):
            with self.subTest(grafo=nombre):
                _, bloques, _ = cargar(nombre)
                ruta = bloques["blocks_file_source_0"]["parameters"]["file"]
                self.assertEqual(ruta, MUESTRA)

    def test_los_identificadores_no_colisionan(self):
        """Con el mismo id, grcc genera el mismo .py y un grafo pisa al otro."""
        ids = [cargar(n)[0]["options"]["parameters"]["id"] for n in ("test.grc", "test2.grc")]
        self.assertEqual(len(set(ids)), 2, f"ids duplicados: {ids}")

    def test_el_slider_alcanza_la_frecuencia_de_la_muestra(self):
        """99.1 MHz debe ser alcanzable: con paso 2 desde 100 nunca se llega."""
        for nombre in ("test.grc", "test2.grc"):
            with self.subTest(grafo=nombre):
                _, bloques, _ = cargar(nombre)
                freq = bloques["freq"]["parameters"]
                self.assertEqual(float(freq["value"]), 99.1)
                paso = float(freq["step"])
                resto = round((99.1 - float(freq["start"])) / paso, 6)
                self.assertEqual(resto, round(resto), "99.1 no cae en la rejilla del slider")


if __name__ == "__main__":
    unittest.main()

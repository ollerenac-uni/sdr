"""Numeración de las figuras de las sesiones.

Insertar una figura en medio de una sesión desplaza a todas las posteriores y el
error no produce ningún aviso al construir el sitio. Estas pruebas lo detectan.
Regla documentada en AGENTS.md.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SESIONES = sorted(ROOT.glob("docs/sessions/*/index.md"))

PIE = re.compile(r"^\*\*Figura (\d+)\.\*\*\s*(.+)$")
IMAGEN = re.compile(r"^!\[(.*?)\]\((figures/[^)]+)\)")


def lineas(sesion):
    return sesion.read_text(encoding="utf-8").split("\n")


def pies_de(sesion):
    return [int(m.group(1)) for l in lineas(sesion) if (m := PIE.match(l))]


class TestNumeracionDeFiguras(unittest.TestCase):
    def test_hay_sesiones_que_revisar(self):
        self.assertTrue(SESIONES, "No se encontró ninguna sesión en docs/sessions/")

    def test_los_pies_van_de_uno_a_n_sin_saltos(self):
        for sesion in SESIONES:
            with self.subTest(sesion=sesion.parent.name):
                nums = pies_de(sesion)
                self.assertEqual(
                    nums,
                    list(range(1, len(nums) + 1)),
                    f"Numeración rota en {sesion.parent.name}: {nums}. "
                    "Renumera los pies posteriores tras insertar una figura (AGENTS.md).",
                )

    def test_ninguna_imagen_se_queda_sin_pie(self):
        for sesion in SESIONES:
            L = lineas(sesion)
            for i, l in enumerate(L):
                if not (m := IMAGEN.match(l)):
                    continue
                siguientes = L[i + 1 : i + 4]
                with self.subTest(sesion=sesion.parent.name, figura=m.group(2)):
                    self.assertTrue(
                        any(PIE.match(s) for s in siguientes),
                        f"{m.group(2)} en {sesion.parent.name}:{i+1} no tiene pie "
                        "'**Figura N.** …' en las tres líneas siguientes.",
                    )

    def test_las_imagenes_referenciadas_existen(self):
        for sesion in SESIONES:
            for l in lineas(sesion):
                if m := IMAGEN.match(l):
                    with self.subTest(sesion=sesion.parent.name, figura=m.group(2)):
                        self.assertTrue((sesion.parent / m.group(2)).exists(),
                                        f"Falta el archivo {m.group(2)}")

    def test_toda_imagen_lleva_texto_alternativo(self):
        for sesion in SESIONES:
            for i, l in enumerate(lineas(sesion)):
                if m := IMAGEN.match(l):
                    with self.subTest(sesion=sesion.parent.name, linea=i + 1):
                        self.assertGreater(len(m.group(1)), 20,
                                           f"Texto alternativo demasiado corto en {m.group(2)}")

    def test_las_citas_en_el_texto_apuntan_a_figuras_existentes(self):
        """Un párrafo que dice «la Figura 10» debe referirse a una que exista."""
        cita = re.compile(r"\bFigura (\d+)\b")
        for sesion in SESIONES:
            total = len(pies_de(sesion))
            for i, l in enumerate(lineas(sesion)):
                if PIE.match(l):
                    continue
                for n in map(int, cita.findall(l)):
                    with self.subTest(sesion=sesion.parent.name, linea=i + 1, cita=n):
                        self.assertLessEqual(
                            n, total,
                            f"{sesion.parent.name}:{i+1} cita la Figura {n} pero la sesión "
                            f"solo tiene {total}.",
                        )


if __name__ == "__main__":
    unittest.main()

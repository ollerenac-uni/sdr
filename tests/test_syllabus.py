"""El programa mantiene 16 sesiones de alcance acotado y los índices coinciden."""

from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]


def filas_sesiones(texto):
    return [
        [celda.strip() for celda in linea.strip().strip("|").split("|")]
        for linea in texto.splitlines()
        if re.match(r"^\| \d{2} \|", linea)
    ]


def test_syllabus_contiene_16_sesiones_y_laboratorios_numerados():
    texto = (ROOT / "docs/syllabus.md").read_text(encoding="utf-8")
    filas = filas_sesiones(texto)
    assert [int(fila[0]) for fila in filas] == list(range(1, 17))
    assert filas[0][1].startswith("**Introducción.**")
    assert "El curso comprende 16 sesiones" in texto
    assert "2 h de clase y 2 h de laboratorio" in texto
    assert "No requieren hardware SDR individual" in texto
    assert "una computadora\ncon GNU Radio" in texto
    assert "`.cu8`" in texto
    assert "El temario presenta el programa previsto" in texto
    assert "publicarán progresivamente" in texto
    for numero, fila in enumerate(filas, 1):
        assert len(fila) == 3
        assert re.match(r"\*\*.+\.\*\* Se .+\.$", fila[1])
        assert re.match(rf"\*\*Laboratorio #{numero}: .+\.\*\* Se .+\.$", fila[2])


def test_indices_mantienen_los_titulos_del_syllabus():
    filas = filas_sesiones((ROOT / "docs/syllabus.md").read_text(encoding="utf-8"))
    titulos = {fila[0]: re.search(r"\*\*(.+?)\.\*\*", fila[1]).group(1) for fila in filas}
    for ruta in ("docs/index.md", "docs/sessions/index.md"):
        texto = (ROOT / ruta).read_text(encoding="utf-8")
        filas_indice = filas_sesiones(texto)
        assert [int(fila[0]) for fila in filas_indice] == list(range(1, 17))
        titulos_indice = {fila[0]: re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", fila[1]) for fila in filas_indice}
        assert titulos_indice == titulos
        assert "syllabus.md" in texto
        assert "pre-lab" in texto


def test_alcance_prioriza_practica_guiada_y_consolidacion():
    texto = (ROOT / "docs/syllabus.md").read_text(encoding="utf-8")
    normalizado = " ".join(texto.split())
    assert "no se exige implementar desde cero todos los algoritmos de sincronización" in normalizado
    assert "pocas ideas clave y un experimento principal por sesión" in normalizado
    assert "fuera del programa obligatorio" in texto
    titulos = [re.search(r"\*\*(.+?)\.\*\*", fila[1]).group(1) for fila in filas_sesiones(texto)]
    assert titulos[6] == "Enlace digital ideal"
    assert titulos[12] == "Integración del receptor QPSK"
    assert titulos[15] == "Síntesis y demostración del enlace"
    assert not any(re.search(r"multipath|equalization|OFDM", titulo, re.IGNORECASE) for titulo in titulos)


def test_syllabus_esta_en_la_navegacion():
    config = yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert {"Syllabus": "syllabus.md"} in config["nav"]

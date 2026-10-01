"""El PDF imprimible conserva el syllabus y no divide una sesión entre páginas."""

import importlib.util
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "docs/downloads/syllabus-sdr.pdf"


def paginas_pdf(ruta):
    comando = shutil.which("pdftotext")
    if comando is None:
        pytest.skip("pdftotext no está instalado")
    resultado = subprocess.run([comando, str(ruta), "-"], check=True, capture_output=True, text=True)
    return [pagina for pagina in resultado.stdout.split("\f") if pagina.strip()]


def verificar_contenido(ruta):
    paginas = paginas_pdf(ruta)
    assert len(paginas) == 3
    for pagina, inicio in zip(paginas, (1, 6, 11)):
        assert [int(numero) for numero in re.findall(r"Sesión (\d{2}) —", pagina)] == list(range(inicio, inicio + 5))
        assert [int(numero) for numero in re.findall(r"Laboratorio #(\d+):", pagina)] == list(range(inicio, inicio + 5))
    texto_pdf = re.sub(r"\s+", "", " ".join(paginas))
    syllabus = (ROOT / "docs/syllabus.md").read_text(encoding="utf-8")
    for linea in syllabus.splitlines():
        if re.match(r"^\| \d{2} \|", linea):
            for celda in linea.strip("|").split("|")[1:]:
                tema, descripcion = re.fullmatch(r"\s*\*\*(.+?)\.\*\*\s+(.+?)\s*", celda).groups()
                for campo in (tema, descripcion):
                    assert re.sub(r"\s+", "", campo.replace("`", "")) in texto_pdf


def test_pdf_publicado_conserva_el_contenido_del_syllabus():
    assert PDF.is_file()
    assert "downloads/syllabus-sdr.pdf" in (ROOT / "docs/syllabus.md").read_text(encoding="utf-8")
    verificar_contenido(PDF)


def test_pdf_se_regenera_desde_el_markdown(tmp_path):
    pytest.importorskip("reportlab")
    spec = importlib.util.spec_from_file_location("syllabus_pdf", ROOT / "scripts/generar_syllabus_pdf.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    destino = modulo.generar_pdf(destino=tmp_path / "syllabus.pdf")
    verificar_contenido(destino)

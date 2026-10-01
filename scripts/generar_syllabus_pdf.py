"""Genera el PDF sencillo desde docs/syllabus.md, con ReportLab.

Comando local: /usr/bin/python3 scripts/generar_syllabus_pdf.py
"""

import argparse
from functools import partial
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/syllabus.md"
OUTPUT = ROOT / "docs/downloads/syllabus-sdr.pdf"
TOTAL_SESIONES = 16
SESIONES_POR_PAGINA = 4


def texto_plano(texto):
    texto = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", texto)
    return texto.replace("`", "").replace("**", "")


def leer_syllabus(ruta):
    texto = ruta.read_text(encoding="utf-8").split("---", 2)[2].strip()
    introduccion = texto.split("| Sesión |", 1)[0]
    parrafos = []
    for bloque in re.split(r"\n\s*\n", introduccion):
        bloque = " ".join(bloque.split())
        if bloque.startswith("# ") or re.fullmatch(r"\[[^\]]+\]\([^\)]+\)", bloque):
            continue
        if bloque:
            parrafos.append(texto_plano(bloque))

    sesiones = []
    for linea in texto.splitlines():
        if not re.match(r"^\| \d{2} \|", linea):
            continue
        numero, clase, laboratorio = [celda.strip() for celda in linea.strip("|").split("|")]
        campos = []
        for celda in (clase, laboratorio):
            campo = re.fullmatch(r"\*\*(.+?)\.\*\*\s+(.+)", celda)
            if campo is None:
                raise ValueError(f"Formato inesperado en la sesión {numero}: {celda}")
            campos.extend(texto_plano(valor) for valor in campo.groups())
        sesiones.append((int(numero), *campos))
    if [sesion[0] for sesion in sesiones] != list(range(1, TOTAL_SESIONES + 1)):
        raise ValueError(f"El syllabus debe contener las sesiones 1 a {TOTAL_SESIONES}, en orden.")
    return parrafos, sesiones


def numero_pagina(canvas, documento):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0] - documento.rightMargin, 12 * mm, str(documento.page))
    canvas.restoreState()


def generar_pdf(origen=SOURCE, destino=OUTPUT):
    parrafos, sesiones = leer_syllabus(origen)
    estilos = {
        "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=12),
        "sesion": ParagraphStyle("sesion", fontName="Helvetica-Bold", fontSize=11.5, leading=15, spaceAfter=4),
        "cuerpo": ParagraphStyle("cuerpo", fontName="Helvetica", fontSize=10.5, leading=14, spaceAfter=4),
        "laboratorio": ParagraphStyle("laboratorio", fontName="Helvetica-Bold", fontSize=10.5, leading=14, spaceBefore=3, spaceAfter=3),
    }
    contenido = [Paragraph("Syllabus — Radio Definida por Software", estilos["titulo"])]
    contenido.extend(Paragraph(escape(parrafo), estilos["cuerpo"]) for parrafo in parrafos)
    contenido.append(Spacer(1, 8))

    for numero, tema, descripcion, laboratorio, practica in sesiones:
        if numero > 1 and (numero - 1) % SESIONES_POR_PAGINA == 0:
            contenido.append(PageBreak())
        contenido.append(KeepTogether([
            Paragraph(escape(f"Sesión {numero:02d} — {tema}"), estilos["sesion"]),
            Paragraph(escape(f"Clase (2 h): {descripcion}"), estilos["cuerpo"]),
            Paragraph(escape(laboratorio), estilos["laboratorio"]),
            Paragraph(escape(f"Laboratorio (2 h): {practica}"), estilos["cuerpo"]),
            Spacer(1, 10),
        ]))

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento = SimpleDocTemplate(
        str(destino), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Syllabus — Radio Definida por Software", author="Curso SDR — UNI",
    )
    documento.build(contenido, onFirstPage=numero_pagina, onLaterPages=numero_pagina,
                    canvasmaker=partial(Canvas, invariant=1))
    return destino


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--output", type=Path, default=OUTPUT)
    opciones = argumentos.parse_args()
    print(generar_pdf(destino=opciones.output))

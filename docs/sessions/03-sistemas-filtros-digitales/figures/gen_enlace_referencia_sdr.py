"""Resalta funciones sobre la figura vectorial original de SDR for Engineers.

Desde la raíz del repositorio:
    /usr/bin/python3 docs/sessions/03-sistemas-filtros-digitales/figures/gen_enlace_referencia_sdr.py

Requiere PyMuPDF (módulo fitz) y rsvg-convert (librsvg). --salida permite
comprobar la reproducción fuera de docs/. El PDF fuente está versionado en sdr-reference-courses/.
Se conservan la geometría y los textos del diagrama; las capas SVG añaden
resaltados. Los títulos, la leyenda y la atribución quedan fuera del original.

Fuente: Collins, Getz, Pu y Wyglinski (2018), Software-Defined Radio for
Engineers, Artech House, figura 1.3, p. 5 (página 22 del PDF).
"""

import argparse
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import fitz


SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
CARPETA = Path(__file__).resolve().parent
RAIZ = CARPETA.parents[3]
LIBRO = RAIZ / "sdr-reference-courses/SDR4Engineers.pdf"
PAGINA = 21  # Índice desde cero; corresponde a la página impresa 5.
RECORTE = (88, 433, 373, 200)  # x, y, ancho y alto; excluye el pie del libro.
CAJAS = {
    "datos_tx": (92.33, 474.72, 133.16, 501.94),
    "modulador": (255.65, 474.72, 296.48, 501.94),
    "demodulador": (255.65, 583.60, 296.48, 610.82),
    "datos_rx": (92.33, 583.60, 133.16, 610.82),
    "muestras_tx": (298.20, 476.00, 307.60, 485.60),
    "muestras_rx": (298.20, 584.90, 307.60, 594.50),
}
VARIANTES = {
    "datos": {
        "titulo": "Data source · Entrada del mensaje",
        "detalle": "El texto y su representación binaria preparan los datos del transmisor.",
        "foco": ["datos_tx"],
        "apoyo": [],
    },
    "modulacion": {
        "titulo": "Symbol mod · Bits, símbolos y muestras",
        "detalle": "La función agrupa el mapeo BPSK y la conformación del pulso.",
        "foco": ["modulador"],
        "apoyo": [],
    },
    "recepcion": {
        "titulo": "Symbol demod · Recuperación de símbolos y bits",
        "detalle": "La función receptora reúne filtrado, sincronización y decisiones.",
        "foco": ["demodulador"],
        "apoyo": [],
    },
    "entrega": {
        "titulo": "Data sink · Entrega del mensaje recuperado",
        "detalle": "El laboratorio reconstruye el paquete y comprueba sus datos antes de entregar el texto.",
        "foco": ["datos_rx"],
        "apoyo": ["demodulador"],
    },
    "canal": {
        "titulo": "Canal simulado · Entre las interfaces de muestras S",
        "detalle": "El canal del laboratorio conecta estas interfaces digitales; no utiliza las cadenas RF.",
        "foco": ["muestras_tx", "muestras_rx"],
        "apoyo": ["modulador", "demodulador"],
    },
    "integrado": {
        "titulo": "Enlace BPSK · Datos, modulación, recepción y entrega",
        "detalle": "Se resaltan las funciones desarrolladas; las etapas analógicas y RF quedan como contexto.",
        "foco": ["datos_tx", "modulador", "demodulador", "datos_rx"],
        "apoyo": [],
    },
}


def elemento(padre, nombre, **atributos):
    return ET.SubElement(padre, f"{{{SVG}}}{nombre}", {
        clave.replace("_", "-"): str(valor) for clave, valor in atributos.items()
    })


def texto(padre, contenido, x, y, tam=18, color="#374151", peso="normal"):
    nodo = elemento(padre, "text", x=x, y=y, font_size=tam,
                    font_family="sans-serif", fill=color, font_weight=peso)
    nodo.text = contenido


def resaltar(padre, nombre, color, opacidad, ancho):
    x0, y0, x1, y1 = CAJAS[nombre]
    margen = 1.05
    elemento(padre, "rect", x=x0-margen, y=y0-margen,
             width=x1-x0+2*margen, height=y1-y0+2*margen,
             rx=0.8, fill=color, fill_opacity=opacidad,
             stroke=color, stroke_width=ancho)


def componer(original, variante):
    raiz = ET.Element(f"{{{SVG}}}svg", {
        "width": "1400", "height": "860", "viewBox": "0 0 1400 860",
        "role": "img",
    })
    elemento(raiz, "title").text = variante["titulo"]
    elemento(raiz, "desc").text = (
        "Figura 1.3 de Software-Defined Radio for Engineers, con resaltados del curso. "
        "La fila TX se lee de izquierda a derecha y la fila RX de derecha a izquierda."
    )
    elemento(raiz, "rect", width=1400, height=860, fill="white")
    texto(raiz, variante["titulo"], 40, 37, tam=28, color="#1f2937", peso="bold")
    texto(raiz, variante["detalle"], 40, 69)

    x, y, ancho, alto = RECORTE
    escala = 1330 / ancho
    definiciones = elemento(raiz, "defs")
    recorte = elemento(definiciones, "clipPath", id="recorte_diagrama",
                       clipPathUnits="userSpaceOnUse")
    elemento(recorte, "rect", x=x, y=y, width=ancho, height=alto)
    diagrama = elemento(
        raiz, "g", clip_path="url(#recorte_diagrama)",
        transform=f"matrix({escala} 0 0 {escala} {35-x*escala} {90-y*escala})",
    )
    for nodo in original:
        diagrama.append(deepcopy(nodo))
    for nombre in variante["apoyo"]:
        resaltar(diagrama, nombre, "#176c9b", 0.10, 1.20)
    for nombre in variante["foco"]:
        resaltar(diagrama, nombre, "#c66a00", 0.16, 1.65)
    for x, color, etiqueta in (
        (40, "#c66a00", "Función o interfaz estudiada"),
        (460, "#176c9b", "Función relacionada"),
    ):
        elemento(raiz, "rect", x=x, y=813, width=18, height=18,
                 fill=color, fill_opacity=0.16, stroke=color, stroke_width=2)
        texto(raiz, etiqueta, x+29, 828, tam=17)
    texto(raiz, "Sin resaltar: contexto del sistema.", 815, 828, tam=17)
    texto(raiz, "Fuente: Collins, Getz, Pu y Wyglinski (2018), figura 1.3, p. 5. © Autores. Resaltados del curso.",
          40, 851, tam=14, color="#4b5563")
    return ET.tostring(raiz, encoding="utf-8", xml_declaration=True)


def generar(salida):
    conversor = shutil.which("rsvg-convert")
    if conversor is None:
        raise RuntimeError("Se necesita rsvg-convert (librsvg) para exportar los PNG.")
    salida.mkdir(parents=True, exist_ok=True)
    with fitz.open(LIBRO) as libro:
        original = ET.fromstring(libro[PAGINA].get_svg_image(text_as_path=True))
    for nombre, variante in VARIANTES.items():
        base = salida / f"enlace-referencia-sdr-{nombre}"
        svg = componer(original, variante)
        base.with_suffix(".svg").write_bytes(svg)
        subprocess.run([
            conversor, "--format", "png", "--output", str(base.with_suffix(".png")),
            str(base.with_suffix(".svg")),
        ], check=True)
        print(base.with_suffix(".png").name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=CARPETA)
    generar(parser.parse_args().salida)

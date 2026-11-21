"""Catálogos fijos de las dos ventanas I/Q reales de ADS-B del curso."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOGOS = {
    "leccion": ROOT / "gnuradio/samples/adsb-posiciones/origen.json",
    "laboratorio": ROOT / "gnuradio/samples/adsb-laboratorio/origen.json",
}


def cargar_muestra(nombre="leccion"):
    catalogo = CATALOGOS[nombre]
    return catalogo.parent, json.loads(catalogo.read_text(encoding="utf-8"))


def ruta_captura(origen):
    for catalogo in CATALOGOS.values():
        if catalogo.exists():
            datos = json.loads(catalogo.read_text(encoding="utf-8"))
            if origen["archivo"] == datos["archivo"] and origen["sha256"] == datos["sha256"]:
                return catalogo.parent / datos["archivo"]
    raise ValueError("El informe no identifica una captura del catálogo ADS-B del curso")

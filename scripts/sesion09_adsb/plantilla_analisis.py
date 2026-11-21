"""Laboratorio 6: completar extraer_campos y conservar las evidencias del trabajo.

El preparador copia este archivo a output/adsb-laboratorio/mi_analisis.py.
Ejecutar desde la raíz del repositorio, con Radioconda activo.
"""

import argparse
from pathlib import Path
import sys

ROOT=next((p for p in Path(__file__).resolve().parents if (p/"mkdocs.yml").exists()),Path.cwd())
sys.path.insert(0,str(ROOT))
from scripts.sesion09_adsb.laboratorio import ejecutar_analisis


def extraer_campos(bits):
    """Recibe una cadena de 112 caracteres '0'/'1', MSB primero.

    Devolver un diccionario con df (int), ca (int), icao (str de seis
    dígitos hexadecimales) y tc (int) para toda trama DF17.

    Si TC está entre 9 y 18, incluir también cpr_impar (int 0/1),
    cpr_lat y cpr_lon (int de 17 bits), y altitud_ft (int o None para Q=0).

    Completar con cortes de bits o desplazamientos/máscaras propios.
    Los rangos se consultan en la sección 6 de la sesión 9.
    No llamar a interpretar/campo del curso como sustituto de esta función.
    """
    raise NotImplementedError("Completar extraer_campos(bits) con los campos de DF17 y ME de posición")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada",type=Path,default=ROOT/"output/adsb-laboratorio/mensajes.json")
    parser.add_argument("--salida",type=Path,default=ROOT/"output/adsb-laboratorio/resultado")
    args=parser.parse_args()
    try:
        r=ejecutar_analisis(extraer_campos,args.entrada,args.salida)
    except (NotImplementedError,ValueError,KeyError,OSError) as exc:
        parser.exit(1,f"Pendiente de completar o revisar: {exc}\n")
    print(f"Aeronaves con posición: {len(r['resumen']['aeronaves_con_posicion'])}")
    print(f"Posiciones CPR: {len(r['posiciones'])}")
    print("Mapa:",args.salida/"mapa.html")


if __name__=="__main__":
    main()

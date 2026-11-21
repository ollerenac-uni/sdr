"""Verifica posiciones desde I/Q ADS-B real y genera un mapa interactivo.

Ejecutar con Radioconda desde la raíz de sdr. No arma la clase ni el laboratorio.
La comparación independiente opcional usa pyModeS, sin modificar el entorno.
"""

import argparse
import csv
from datetime import datetime, timezone
from importlib.metadata import version
import json
import math
from pathlib import Path
import sys

if __package__:
    from .receptor import ROOT, crear_potencia, recuperar_tramas, recuperar_posiciones, resumen, mode_s_residue, sha256
else:
    from receptor import ROOT, crear_potencia, recuperar_tramas, recuperar_posiciones, resumen, mode_s_residue, sha256

import numpy as np


def contrastar_pymodes(tramas, posiciones, carpeta):
    sys.path.insert(0, str(carpeta.resolve()))
    import pyModeS as pms
    for f in tramas:
        if pms.crc(f["hex"]) != 0:
            raise ValueError("pyModeS no valida el CRC de una trama aceptada")
        if f.get("altitud_ft") is not None and f["altitud_ft"] != pms.adsb.altitude(f["hex"]):
            raise ValueError("La altitud no coincide con pyModeS")
        if "callsign" in f and f["callsign"] != pms.adsb.callsign(f["hex"]).replace("_", "").strip():
            raise ValueError("El indicativo no coincide con pyModeS")
        if "velocidad_kt" in f:
            v = pms.adsb.velocity(f["hex"])
            if math.floor(f["velocidad_kt"]) != v[0] or not math.isclose(f["rumbo_deg"], v[1], abs_tol=1e-9):
                raise ValueError("La velocidad/curso no coincide con pyModeS")
    for p in posiciones:
        ref = pms.adsb.position(p["hex_par"], p["hex_impar"], p["tiempo_par_s"], p["tiempo_impar_s"])
        if ref is None or max(abs(p["latitud"]-ref[0]), abs(p["longitud"]-ref[1])) > 1e-9:
            raise ValueError("La posición CPR no coincide con pyModeS")
    return {"biblioteca": "pyModeS", "version": version("pyModeS"), "crc_coincidentes": len(tramas),
            "posiciones_coincidentes": len(posiciones), "tolerancia_grados": 1e-9,
            "nota_velocidad": "Se compara tras truncar a kt enteros, como la salida de pyModeS."}


def guardar_resultados(r, salida):
    (salida / "verificacion.json").write_text(json.dumps(r, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (salida / "tramas.avr").write_text("".join(f"*{f['hex'].upper()};\n" for f in r["tramas"]))
    claves = ["icao", "callsign", "tiempo_s", "latitud", "longitud", "altitud_ft", "velocidad_kt", "rumbo_deg",
              "hex_par", "hex_impar", "tiempo_par_s", "tiempo_impar_s", "separacion_s", "metodo"]
    with (salida / "posiciones.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=claves)
        w.writeheader()
        w.writerows(r["posiciones"])
    geo = {"type": "FeatureCollection", "features": [{"type": "Feature",
           "geometry": {"type": "Point", "coordinates": [p["longitud"], p["latitud"]]},
           "properties": {k: v for k, v in p.items() if k not in ("latitud", "longitud")}}
           for p in r["posiciones"]]}
    (salida / "posiciones.geojson").write_text(json.dumps(geo, ensure_ascii=False)+"\n", encoding="utf-8")
    template = Path(__file__).with_name("mapa.html").read_text()
    contenido = json.dumps(r, ensure_ascii=False).replace("<", "\\u003c")
    vendor = Path(__file__).parent / "vendor/leaflet-1.9.4"
    recursos = {"__LEAFLET_CSS__": "leaflet.css", "__LEAFLET_JS__": "leaflet.js",
                "__LEAFLET_LICENSE__": "LICENSE"}
    for marcador, nombre in recursos.items():
        template = template.replace(marcador, (vendor / nombre).read_text(encoding="utf-8"))
    (salida / "mapa.html").write_text(template.replace("__DATA__", contenido), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=ROOT / "output/adsb-posiciones")
    parser.add_argument("--pymodes-dir", type=Path, help="Carpeta de pyModeS para comprobación independiente")
    args = parser.parse_args()
    carpeta = ROOT / "gnuradio/samples/adsb-posiciones"
    origen = json.loads((carpeta / "origen.json").read_text())
    archivo = carpeta / origen["archivo"]
    if not archivo.exists():
        parser.error("Falta la muestra: ejecutar scripts/sesion09_adsb/descargar_muestra.py")
    hash_entrada = sha256(archivo)
    if hash_entrada != origen["sha256"]:
        parser.error("La captura no coincide con el SHA-256 de origen.json")
    args.salida.mkdir(parents=True, exist_ok=True)
    potencia = args.salida / "potencia8.f32"
    print("GNU Radio: I/Q 2.4 Msps -> remuestreo 10/3 -> potencia 8 Msps...", flush=True)
    n = crear_potencia(archivo, potencia)
    print("Detectando preámbulos y recuperando bits PPM, sin corregir errores...", flush=True)
    tramas, candidatos = recuperar_tramas(potencia)
    posiciones = recuperar_posiciones(tramas)
    controles = []
    for f in tramas:
        bits = np.unpackbits(np.frombuffer(bytes.fromhex(f["hex"]), dtype=np.uint8))
        bits[40] ^= 1
        controles.append(mode_s_residue(bits) != 0)
    if not posiciones or not all(controles):
        raise SystemExit("La muestra no produjo posiciones verificables o falló el control de CRC")
    por_hex = {f["hex"]: f for f in tramas}
    parejas_validas = all(
        por_hex[p["hex_par"]]["icao"] == por_hex[p["hex_impar"]]["icao"] == p["icao"]
        and por_hex[p["hex_par"]]["cpr_impar"] == 0
        and por_hex[p["hex_impar"]]["cpr_impar"] == 1
        and p["separacion_s"] <= 10 for p in posiciones)
    if not parejas_validas:
        raise SystemExit("Se detectó una pareja CPR incompatible")
    referencia = contrastar_pymodes(tramas, posiciones, args.pymodes_dir) if args.pymodes_dir else None
    r = {"fecha_verificacion_utc": datetime.now(timezone.utc).isoformat(), "origen": origen,
         "cadena": ["File Source cf32_le", "Rational Resampler 10/3", "Complex to Mag^2",
                    "Preambulo y medias por mitad de bit", "PPM", "CRC-24 sin corrección", "CPR global"],
         "parametros": {"fs_potencia": 8000000, "muestras_potencia": n, "muestras_por_bit": 8,
                        "muestras_por_mitad": 4, "contraste_minimo": 1.5, "umbral_potencia": .0005,
                        "bits_corregidos": 0, "separacion_maxima_pareja_s": 10},
         "tiempo": "Relativo a la salida del remuestreador; incluye su retardo fijo. No es UTC original ni reloj de reproducción.",
         "resumen": resumen(tramas, posiciones), "candidatos_muestra": candidatos,
         "controles": {"captura_sha256_correcto": hash_entrada == origen["sha256"],
                       "crc_independiente_de_los_campos": all(mode_s_residue(np.unpackbits(
                           np.frombuffer(bytes.fromhex(f["hex"]), dtype=np.uint8))) == 0 for f in tramas),
                       "alteraciones_un_bit_rechazadas": sum(controles),
                       "parejas_mismo_icao_y_paridades_opuestas": parejas_validas,
                       "sin_referencia_geografica_para_decodificar": True},
         "contraste_independiente": referencia, "tramas": tramas, "posiciones": posiciones,
         "limites": ["Solo DF17 y posiciones aéreas barométricas TC9–18.",
                     "Fechas del nombre original sin zona horaria; tiempos de muestra relativos.",
                     "El mapa muestra posiciones decodificadas, no ubicaciones actuales ni posiciones interpoladas.",
                     "No se infiere velocidad a partir de distancias/tiempo del archivo; se muestra TC19.",
                     "Un CRC válido detecta errores, no autentica al emisor."]}
    guardar_resultados(r, args.salida)
    print(json.dumps(r["resumen"], ensure_ascii=False, indent=2))
    if referencia:
        print(f"Contraste independiente: {referencia['posiciones_coincidentes']} posiciones coinciden con pyModeS {referencia['version']}.")
    print("Mapa:", args.salida / "mapa.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""I/Q real -> potencia con GNU Radio -> PPM -> CRC -> posiciones CPR globales.

No corrige bits ni sintetiza mensajes. Los tiempos se calculan con índices de
muestra, nunca con el reloj de reproducción. Referencias de CPR y PPM:
https://mode-s.org/1090mhz/content/ads-b/3-airborne-position.html
https://www.faa.gov/documentLibrary/media/Order/6365.1A.pdf
"""

from collections import Counter
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.verificar_capturas_rf import mode_s_residue, sha256

FS = 8_000_000
CALLSIGN = "_ABCDEFGHIJKLMNOPQRSTUVWXYZ_____ _______________0123456789______"


def crear_potencia(archivo, salida):
    from gnuradio import blocks, filter, gr
    tb = gr.top_block("Verificación ADS-B: remuestreo y potencia")
    fuente = blocks.file_source(gr.sizeof_gr_complex, str(archivo), False)
    rr = filter.rational_resampler_ccc(interpolation=10, decimation=3)
    mag = blocks.complex_to_mag_squared()
    destino = blocks.file_sink(gr.sizeof_float, str(salida), False)
    tb.connect(fuente, rr, mag, destino)
    tb.run()
    destino.close()
    return salida.stat().st_size // 4


def campo(hexadecimal, inicio, longitud):
    """Extrae bits numerados desde cero, MSB primero, de una trama de 112 bits."""
    return (int(hexadecimal, 16) >> (112-inicio-longitud)) & ((1 << longitud)-1)


def interpretar(h, indice, calidad):
    tc = campo(h, 32, 5)
    r = {"hex": h, "muestra_8msps": int(indice), "tiempo_s": indice/FS,
         "df": campo(h, 0, 5), "icao": h[2:8], "tc": tc,
         "crc24_valido": True, "contraste_preambulo": float(calidad)}
    if 1 <= tc <= 4:
        r["callsign"] = "".join(CALLSIGN[campo(h, 40+i*6, 6)]
                                for i in range(8)).replace("_", "").strip()
    elif 9 <= tc <= 18:
        r.update(cpr_impar=campo(h, 53, 1), cpr_lat=campo(h, 54, 17),
                 cpr_lon=campo(h, 71, 17))
        alt = campo(h, 40, 12)
        # Q=1: pasos de 25 ft. No se interpreta Gillham/Q=0 con esta fórmula.
        r["altitud_ft"] = (((alt & 0xfe0) >> 1) | (alt & 0x0f))*25-1000 if alt & 0x10 else None
    elif tc == 19 and campo(h, 37, 3) in (1, 2):
        ew, ns = campo(h, 46, 10), campo(h, 57, 10)
        if ew and ns:
            escala = 4 if campo(h, 37, 3) == 2 else 1
            vx = (ew-1)*escala*(-1 if campo(h, 45, 1) else 1)
            vy = (ns-1)*escala*(-1 if campo(h, 56, 1) else 1)
            r.update(velocidad_kt=math.hypot(vx, vy), rumbo_deg=math.degrees(math.atan2(vx, vy)) % 360)
    return r


def recuperar_tramas(archivo_potencia, bloque=1 << 20, umbral=.0005, contraste=1.5):
    """Integra medias de 0.5 us en todas las fases de muestra; deduplica por ráfaga.

    Cada bloque lee 959 muestras adicionales: una trama que cruza un límite
    de procesamiento se examina completa. Solo se conservan DF17 con CRC-24
    nulo; no se cambia ningún bit para hacer coincidir el CRC.
    """
    potencia = np.memmap(archivo_potencia, dtype="<f4", mode="r")
    pulsos = (0, 8, 28, 36)
    huecos = (4, 12, 16, 20, 24, 32, 40, 44, 48, 52, 56, 60)
    filas, vistos, candidatos = [], {}, 0
    fin = max(0, len(potencia)-959)
    for base in range(0, fin, bloque):
        cantidad = min(bloque, fin-base)
        ventana = potencia[base:base+cantidad+959]
        medias = np.convolve(ventana, np.full(4, .25, np.float32), mode="valid")
        minimo = medias[:cantidad].copy()
        for p in pulsos[1:]:
            np.minimum(minimo, medias[p:p+cantidad], out=minimo)
        maximo = medias[4:4+cantidad].copy()
        for p in huecos[1:]:
            np.maximum(maximo, medias[p:p+cantidad], out=maximo)
        indices = np.flatnonzero((minimo > umbral) & (minimo > contraste*maximo))
        candidatos += len(indices)
        for local in indices:
            a = medias[local+64:local+64+112*8:8]
            b = medias[local+68:local+68+112*8:8]
            bits = (a > b).astype(np.uint8)
            if int(bits[:5].dot(2**np.arange(4, -1, -1))) != 17 or mode_s_residue(bits) != 0:
                continue
            h = np.packbits(bits).tobytes().hex()
            indice = base+int(local)
            calidad = float(minimo[local]/max(float(maximo[local]), 1e-12))
            r = interpretar(h, indice, calidad)
            anterior = vistos.get(h)
            if anterior is not None and abs(indice-filas[anterior]["muestra_8msps"]) < 16:
                if calidad > filas[anterior]["contraste_preambulo"]:
                    filas[anterior] = r
            else:
                vistos[h] = len(filas)
                filas.append(r)
    return sorted(filas, key=lambda f: f["muestra_8msps"]), candidatos


def nl(lat):
    lat = abs(lat)
    if lat > 87:
        return 1
    if lat == 87:
        return 2
    x = 1-(1-math.cos(math.pi/30))/math.cos(math.radians(lat))**2
    return int(math.floor(2*math.pi/math.acos(max(-1, min(1, x)))))


def posicion_global(a, b):
    """CPR aéreo global; requiere dos DF17 del mismo ICAO, uno par y otro impar."""
    if a["icao"] != b["icao"] or a["cpr_impar"] == b["cpr_impar"]:
        return None
    if not (9 <= a["tc"] <= 18 and 9 <= b["tc"] <= 18):
        return None
    if abs(a["tiempo_s"]-b["tiempo_s"]) > 10:
        return None
    par, impar = (a, b) if not a["cpr_impar"] else (b, a)
    ye, yo = par["cpr_lat"]/131072, impar["cpr_lat"]/131072
    xe, xo = par["cpr_lon"]/131072, impar["cpr_lon"]/131072
    j = math.floor(59*ye-60*yo+.5)
    le, lo = 6*((j % 60)+ye), (360/59)*((j % 59)+yo)
    le = le-360 if le >= 270 else le
    lo = lo-360 if lo >= 270 else lo
    if not (-90 <= le <= 90 and -90 <= lo <= 90) or nl(le) != nl(lo):
        return None
    ultimo = max((a, b), key=lambda f: f["tiempo_s"])
    lat = le if not ultimo["cpr_impar"] else lo
    zonas = nl(lat)
    ni = max(zonas-ultimo["cpr_impar"], 1)
    m = math.floor(xe*(zonas-1)-xo*zonas+.5)
    lon = (360/ni)*((m % ni)+(xe if not ultimo["cpr_impar"] else xo))
    if lon >= 180:
        lon -= 360
    return {"icao": ultimo["icao"], "tiempo_s": ultimo["tiempo_s"],
            "latitud": lat, "longitud": lon, "altitud_ft": ultimo.get("altitud_ft"),
            "hex_par": par["hex"], "hex_impar": impar["hex"],
            "tiempo_par_s": par["tiempo_s"], "tiempo_impar_s": impar["tiempo_s"],
            "separacion_s": abs(par["tiempo_s"]-impar["tiempo_s"]), "metodo": "CPR global"}


def recuperar_posiciones(tramas):
    memoria, aviones, posiciones = {}, {}, []
    for f in sorted(tramas, key=lambda r: r["tiempo_s"]):
        icao = f["icao"]
        avion = aviones.setdefault(icao, {})
        for k in ("callsign", "velocidad_kt", "rumbo_deg"):
            if k in f:
                avion[k] = f[k]
        if not 9 <= f["tc"] <= 18:
            continue
        banco = memoria.setdefault(icao, {})
        banco[f["cpr_impar"]] = f
        if 1-f["cpr_impar"] in banco:
            p = posicion_global(f, banco[1-f["cpr_impar"]])
            if p is not None:
                p.update(avion)
                posiciones.append(p)
    return posiciones


def resumen(tramas, posiciones):
    return {"tramas_df17_crc_valido": len(tramas),
            "tipos": dict(sorted(Counter(f["tc"] for f in tramas).items())),
            "aeronaves_detectadas": len({f["icao"] for f in tramas}),
            "mensajes_posicion_aerea": sum(9 <= f["tc"] <= 18 for f in tramas),
            "posiciones_cpr_global": len(posiciones),
            "aeronaves_con_posicion": sorted({p["icao"] for p in posiciones})}

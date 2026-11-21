"""Verifica y descifra el nodo experimental publicado en el PCAP real de Brno.

Reutiliza verificar_lorawan para MIC de datos y descifrado FRMPayload; añade
lectura del PCAP e incorporación OTAA de LoRaWAN 1.0.x. El PCAP contiene
paquetes ya demodulados por el sniffer, no muestras I/Q.
Requiere cryptography, disponible en el Radioconda usado para esta comprobación.
Las claves se leen de los archivos públicos del dataset; no se buscan claves.
"""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import struct

if __package__:
    from .verificar_lorawan import aes128, analizar_trama, cmac128
else:
    from verificar_lorawan import aes128, analizar_trama, cmac128


ROOT = Path(__file__).resolve().parents[2]
CARPETA = ROOT / "gnuradio/samples/lorawan-brno"
DEV_EUI = "70b3d5cee0000042"
DEV_ADDR = "01e65ddc"


def leer_claves(carpeta):
    def filas(nombre):
        with (carpeta / nombre).open(encoding="utf-8") as archivo:
            yield from csv.reader(linea for linea in archivo if not linea.startswith("#"))

    raices = {fila[0].lower(): bytes.fromhex(fila[1]) for fila in filas("root_keys_lorawan")}
    sesiones = {fila[0].lower(): tuple(bytes.fromhex(k) for k in fila[1:3])
                for fila in filas("session_keys_lorawan")}
    return raices[DEV_EUI], *sesiones[DEV_ADDR]


def leer_pcap(archivo):
    """Lee PCAP clásico con LoRaTap v1; conserva los bytes PHYPayload."""
    with archivo.open("rb") as entrada:
        cabecera = entrada.read(24)
        if len(cabecera) != 24:
            raise ValueError("PCAP incompleto")
        if cabecera[:4] == b"\xd4\xc3\xb2\xa1":
            endian = "<"
        elif cabecera[:4] == b"\xa1\xb2\xc3\xd4":
            endian = ">"
        else:
            raise ValueError("Se requiere PCAP clásico con resolución de microsegundos")
        if struct.unpack(endian + "IHHIIII", cabecera)[-1] != 270:
            raise ValueError("El enlace del PCAP debe ser LoRaTap (270)")
        numero = 0
        while cabecera_paquete := entrada.read(16):
            if len(cabecera_paquete) != 16:
                raise ValueError("Cabecera de paquete truncada")
            segundos, micros, longitud, original = struct.unpack(endian + "IIII", cabecera_paquete)
            datos = entrada.read(longitud)
            if len(datos) != longitud or longitud != original or len(datos) < 15:
                raise ValueError("Paquete incompleto")
            longitud_loratap = int.from_bytes(datos[2:4], "big")
            if datos[0] != 1 or not 15 <= longitud_loratap <= len(datos):
                raise ValueError("Esta prueba requiere una cabecera LoRaTap v1 válida")
            numero += 1
            yield {
                "numero_pcap": numero,
                "tiempo_unix": segundos + micros / 1e6,
                "frecuencia_hz": int.from_bytes(datos[4:8], "big"),
                "sf": datos[9],
                "frame": datos[longitud_loratap:],
            }


def descifrar_datos(frame, nwk, app):
    """Adapta el verificador común al formato histórico del informe de Brno."""
    datos = analizar_trama(frame, nwk, app)
    resultado = {
        "devaddr": datos["dev_addr"],
        "direccion": datos["direccion"],
        "fcnt32": datos["fcnt_32"],
        "fport": datos["fport"],
        "mic_recibido": datos["mic_recibido"],
        "mic_calculado": datos["mic_calculado"],
        "mic_valido": datos["mic_valido"],
        "phypayload_hex": datos["phy_payload_hex"],
    }
    if not datos["mic_valido"]:
        return resultado
    claro = bytes.fromhex(datos["payload_descifrado_hex"] or "")
    resultado["frmpayload_claro_hex"] = claro.hex()
    resultado["frmpayload_claro_ascii"] = claro.decode("ascii", errors="replace")
    return resultado


def verificar(archivo, carpeta_claves):
    raiz, nwk, app = leer_claves(carpeta_claves)
    conteos = Counter()
    cargas = Counter()
    ejemplos = {}
    solicitudes = []
    incorporaciones = []
    tramas_unicas = set()
    app_unicas = set()
    primer_frame = None
    for paquete in leer_pcap(archivo):
        conteos["paquetes_pcap"] += 1
        frame = paquete["frame"]
        if len(frame) == 23 and frame[0] == 0 and frame[9:17][::-1].hex() == DEV_EUI:
            if hmac.compare_digest(cmac128(raiz, frame[:-4])[:4], frame[-4:]):
                solicitudes.append(paquete)
        if len(frame) in (17, 33) and frame[0] == 0x20:
            # La red cifra Join Accept con AES decrypt; el nodo lo abre con encrypt.
            claro = aes128(raiz, frame[1:])
            if hmac.compare_digest(cmac128(raiz, frame[:1] + claro[:-4])[:4], claro[-4:]):
                if claro[6:10][::-1].hex() == DEV_ADDR:
                    previas = [p for p in solicitudes if p["tiempo_unix"] < paquete["tiempo_unix"]]
                    if previas:
                        solicitud = previas[-1]
                        material = claro[:6] + solicitud["frame"][17:19] + bytes(7)
                        nwk_derivada = aes128(raiz, b"\x01" + material)
                        app_derivada = aes128(raiz, b"\x02" + material)
                        incorporaciones.append({
                            "join_request_hex": solicitud["frame"].hex(),
                            "join_accept_hex": frame.hex(),
                            "join_accept_claro_hex": claro.hex(),
                            "mic_request_valido": True,
                            "mic_accept_valido": True,
                            "nwkskey_derivada": nwk_derivada.hex(),
                            "appskey_derivada": app_derivada.hex(),
                            "coinciden_con_claves_publicadas": nwk_derivada == nwk and app_derivada == app,
                        })
        if len(frame) < 5 or frame[1:5][::-1].hex() != DEV_ADDR:
            continue
        conteos["recepciones_del_devaddr"] += 1
        try:
            datos = descifrar_datos(frame, nwk, app)
        except ValueError:
            conteos["estructura_no_admitida"] += 1
            continue
        if not datos["mic_valido"]:
            conteos["mic_invalido"] += 1
            continue
        conteos["mic_valido"] += 1
        tramas_unicas.add(frame)
        if datos["fport"] not in (None, 0) and datos["frmpayload_claro_hex"]:
            conteos["recepciones_aplicacion_descifradas"] += 1
            app_unicas.add(frame)
            carga = datos["frmpayload_claro_hex"]
            cargas[carga] += 1
            if carga not in ejemplos:
                ejemplos[carga] = {**datos, "numero_pcap": paquete["numero_pcap"],
                                  "frecuencia_hz": paquete["frecuencia_hz"], "sf": paquete["sf"]}
            primer_frame = primer_frame or frame

    controles = {}
    if primer_frame:
        nwk_incorrecta = bytes([nwk[0] ^ 1]) + nwk[1:]
        app_incorrecta = bytes([app[0] ^ 1]) + app[1:]
        alterado = bytearray(primer_frame)
        alterado[-5] ^= 1
        rechazado = descifrar_datos(primer_frame, nwk_incorrecta, app)
        referencia = descifrar_datos(primer_frame, nwk, app)
        otra_app = descifrar_datos(primer_frame, nwk, app_incorrecta)
        controles = {
            "nwkskey_incorrecta_rechazada": not rechazado["mic_valido"],
            "sin_texto_claro_si_mic_invalido": "frmpayload_claro_hex" not in rechazado,
            "byte_alterado_rechazado": not descifrar_datos(bytes(alterado), nwk, app)["mic_valido"],
            "appskey_incorrecta_cambia_texto": otra_app["frmpayload_claro_hex"] != referencia["frmpayload_claro_hex"],
            "mic_no_autentica_appskey": otra_app["mic_valido"],
        }
    return {
        "fecha_prueba_utc": datetime.now(timezone.utc).isoformat(),
        "archivo": str(archivo.resolve().relative_to(ROOT)) if archivo.resolve().is_relative_to(ROOT) else str(archivo.resolve()),
        "sha256": hashlib.sha256(archivo.read_bytes()).hexdigest(),
        "tamano_bytes": archivo.stat().st_size,
        "entrada": "PCAP clásico, LoRaTap v1; paquetes recibidos por sniffer, sin muestras I/Q",
        "dev_eui": DEV_EUI, "dev_addr": DEV_ADDR,
        "fcnt32_bits_altos": 0,
        "claves_fuente": "https://zenodo.org/records/8090619",
        "conteos": dict(conteos),
        "tramas_mic_valido_unicas": len(tramas_unicas),
        "tramas_aplicacion_unicas": len(app_unicas),
        "incorporaciones_otaa_verificadas": incorporaciones,
        "payloads_aplicacion": [{**ejemplo, "recepciones": cargas[carga]}
                                 for carga, ejemplo in ejemplos.items()],
        "controles": controles,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", type=Path, nargs="?", default=CARPETA / "03_Brno_join.pcap")
    parser.add_argument("--claves", type=Path, default=CARPETA)
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    resultado = verificar(args.archivo, args.claves)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto + "\n", encoding="utf-8")
    print(texto)
    valido = (resultado["conteos"].get("recepciones_aplicacion_descifradas", 0) > 0
              and any(j["coinciden_con_claves_publicadas"] for j in resultado["incorporaciones_otaa_verificadas"])
              and resultado["controles"] and all(resultado["controles"].values()))
    return 0 if valido else 1


if __name__ == "__main__":
    raise SystemExit(main())

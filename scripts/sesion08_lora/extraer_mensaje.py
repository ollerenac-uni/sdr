"""Extrae el FRMPayload cifrado de los 20 bytes recuperados en la práctica.

Entrada predeterminada: salida del inspector I/Q de la sección 3.5.7.
Conserva los nombres de entrega sin necesitar GNU Radio Companion. No verifica
el MIC ni descifra; solo interpreta las posiciones del formato de datos.
"""

import argparse
from pathlib import Path


def extraer(trama):
    if len(trama) != 20:
        raise ValueError("Se esperaban 20 bytes de PHYPayload; revisar la sección 3.5.7")
    if trama[0] >> 5 not in (2, 3, 4, 5):
        raise ValueError("Se requiere una trama de datos LoRaWAN")
    longitud_opciones = trama[5] & 0x0F
    indice_puerto = 8 + longitud_opciones
    inicio = indice_puerto + 1
    fin = len(trama) - 4
    if inicio >= fin:
        raise ValueError("La trama no contiene un FRMPayload en el intervalo esperado")
    return longitud_opciones, indice_puerto, inicio, fin, trama[inicio:fin]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path,
                        default=Path("output/lorawan-iq/traza/03_phypayload.bin"))
    parser.add_argument("--salida", type=Path, default=Path("output/lorawan-iq"),
                        help="Directorio donde guardar los dos archivos de entrega")
    args = parser.parse_args()
    try:
        trama = args.entrada.read_bytes()
        opciones, puerto, inicio, fin, mensaje = extraer(trama)
    except FileNotFoundError:
        parser.error("No existe la entrada; ejecutar primero inspeccionar_lora.py --etapa phypayload")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "trama_recibida.bin").write_bytes(trama)
    (args.salida / "mensaje_cifrado.bin").write_bytes(mensaje)
    print(f"FOptsLen = {opciones}")
    print(f"FPort = {trama[puerto]} (byte {puerto + 1})")
    print(f"FRMPayload (bytes {inicio + 1} a {fin}) = {mensaje.hex(' ')}")
    print(f"Guardados {len(mensaje)} bytes en {args.salida / 'mensaje_cifrado.bin'}")
    print(f"Guardados {len(trama)} bytes en {args.salida / 'trama_recibida.bin'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

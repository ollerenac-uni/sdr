"""Descarga y prepara las capturas del catálogo de ingeniería reversa.

Usar el Python de Radioconda. Descarga prefijos de los ZIP grandes y conserva
su hash; nunca presenta un prefijo como una descarga completa. No requiere
instalar software ni modificar el entorno global. Los binarios quedan fuera
de Git por las reglas existentes de .gitignore.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import urllib.request
import zlib

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "gnuradio/samples/ingenieria-reversa"
VENDOR = ROOT / "tmp/rf-capturas/vendor/adsb"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def request(url):
    return urllib.request.urlopen(urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 CBS33M-course-capture-verifier"}),
        timeout=60)


def archive_prefix(config):
    with request(config["url"]) as source:
        header = source.read(30)
        (signature, version, flags, method, mtime, mdate, crc,
         compressed, full_size, name_size, extra_size) = struct.unpack("<IHHHHHIIIHH", header)
        if signature != 0x04034B50 or method != 8 or flags & 1:
            raise ValueError("Formato ZIP no compatible con extracción de prefijo")
        name = source.read(name_size).decode("utf-8")
        source.read(extra_size)
        if name != config["miembro"]:
            raise ValueError(f"Cambió el miembro ZIP: {name}")
        decompressor = zlib.decompressobj(-15)
        data = bytearray()
        limit = config["prefijo_bytes"]
        while len(data) < limit:
            chunk = source.read(256*1024)
            if not chunk:
                break
            data.extend(decompressor.decompress(chunk))
            if decompressor.eof:
                break
        data = bytes(data[:limit])
        if len(data) != limit or digest(data) != config["sha256_prefijo"]:
            raise ValueError("El tamaño o SHA-256 del prefijo no coincide con la captura verificada")
        if limit == full_size and zlib.crc32(data) != crc:
            raise ValueError("Falló el CRC32 del miembro completo del ZIP")
        return data


def wav_iq(data, expected_rate, expected_center):
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("La entrada no es RIFF/WAVE")
    pos = 12
    fmt = None
    center = None
    while pos+8 <= len(data):
        key = data[pos:pos+4]
        size = struct.unpack_from("<I", data, pos+4)[0]
        pos += 8
        if key == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", data, pos)
        elif key == b"auxi":
            center = struct.unpack_from("<I", data, pos+32)[0]
        elif key == b"data":
            if (fmt is None or fmt[0:3] != (1, 2, expected_rate)
                    or fmt[4:] != (4, 16) or center != expected_center):
                raise ValueError(f"No coincide PCM16 I/Q, tasa o frecuencia: {fmt}, {center}")
            # A prefix may end in the middle of a sample; keep complete I/Q pairs.
            available = min(size, len(data)-pos)
            raw = np.frombuffer(data[pos:pos+available//4*4], "<i2")
            values = raw.astype(np.float32).reshape(-1, 2)
            return ((values[:, 0] + 1j*values[:, 1])/32768).astype("<c8").tobytes()
        pos += size + size % 2
    raise ValueError("No se encontró el chunk I/Q data")


def sdriq(data, expected_rate, expected_center):
    rate, center, timestamp, bits = struct.unpack_from("<IQQI", data)
    if rate != expected_rate or center != expected_center or bits != 24:
        raise ValueError("La cabecera SDRangel no coincide con la captura verificada")
    values = np.frombuffer(data[32:32+(len(data)-32)//8*8], "<i4")
    values = values.astype(np.float32).reshape(-1, 2)
    return ((values[:, 0] + 1j*values[:, 1])/2**23).astype("<c8").tobytes()


def save_checked(path, expected_hash, producer):
    if path.exists():
        if digest(path.read_bytes()) == expected_hash:
            print(f"Ya verificado: {path.relative_to(ROOT)}", flush=True)
            return
        raise ValueError(f"Existe un archivo diferente; no se sobrescribe: {path}")
    data = producer()
    if digest(data) != expected_hash:
        raise ValueError(f"SHA-256 incorrecto para {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"Descargado/verificado: {path.relative_to(ROOT)} ({len(data)} bytes)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo", nargs="+", choices=["lacrosse", "aprs", "ais", "ble", "adsb"])
    args = parser.parse_args()
    catalog = json.loads((SAMPLES / "catalogo.json").read_text())
    for entry in catalog["capturas"]:
        if args.solo and entry["id"] not in args.solo:
            continue

        def download(entry=entry):
            config = entry["descarga"]
            if config["tipo"] == "directa":
                with request(config["url"]) as source:
                    return source.read()
            data = archive_prefix(config)
            if config["conversion"] == "wav_iq_16":
                return wav_iq(data, entry["fs"], entry["fc"])
            return sdriq(data, entry["fs"], entry["fc"])

        save_checked(SAMPLES / entry["archivo"], entry["sha256"], download)

    if not args.solo or "adsb" in args.solo:
        for block in catalog["gr_adsb"]["archivos"]:
            def download_block(block=block):
                with request(block["url"]) as source:
                    return source.read()
            save_checked(VENDOR / block["archivo"], block["sha256"], download_block)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)

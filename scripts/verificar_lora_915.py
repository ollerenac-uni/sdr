"""Decodifica la captura real de LoRa de OSU, sin GUI ni hardware SDR.

Ejecutar con el Python de Radioconda; consultar la procedencia y la descarga en
gnuradio/samples/lora-915-osu/README.md. Esta prueba verifica CRC de LoRa PHY,
no MIC ni descifrado de LoRaWAN.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from gnuradio import blocks, gr, lora_sdr
import pmt


ROOT = Path(__file__).resolve().parents[1]
CAPTURA = ROOT / "gnuradio/samples/lora-915-osu/IQ_1.sigmf-data"


def sha256_archivo(archivo):
    resumen = hashlib.sha256()
    with archivo.open("rb") as entrada:
        for parte in iter(lambda: entrada.read(1024 * 1024), b""):
            resumen.update(parte)
    return resumen.hexdigest()


def verificar(archivo, sync_word=0x34):
    archivo = archivo.resolve()
    tamano = archivo.stat().st_size
    if not tamano or tamano % 8:
        raise ValueError("La captura debe contener muestras completas I/Q float32 (8 bytes)")
    parametros = {
        "frecuencia_central_hz": 915000000,
        "tasa_muestras_sps": 1000000,
        "ancho_canal_hz": 125000,
        "sf": 7,
        "sync_word": f"0x{sync_word:02x}",
        "cabecera_explicita": True,
        "decodificacion_soft": True,
        "ldro_mode": 2,
    }
    resumen = sha256_archivo(archivo)
    tb = gr.top_block("Verificación LoRa real a 915 MHz")
    fuente = blocks.file_source(gr.sizeof_gr_complex, str(archivo), False)
    receptor = lora_sdr.lora_sdr_lora_rx(
        center_freq=parametros["frecuencia_central_hz"],
        bw=parametros["ancho_canal_hz"],
        cr=1, has_crc=True, impl_head=False, pay_len=255,
        samp_rate=parametros["tasa_muestras_sps"], sf=parametros["sf"],
        sync_word=[sync_word], soft_decoding=True, ldro_mode=2,
        print_rx=[False, False],
    )
    destino = blocks.vector_sink_b()
    mensajes = blocks.message_debug()
    tb.connect(fuente, receptor, destino)
    tb.msg_connect((receptor, "out"), (mensajes, "store"))
    tb.run()

    if archivo.stat().st_size != tamano:
        raise ValueError("La captura cambió durante la prueba; completar la descarga primero")
    datos = bytes(destino.data())
    tramas = []
    contenidos_validos = Counter()
    for tag in destino.tags():
        if pmt.symbol_to_string(tag.key) != "frame_info":
            continue
        info = pmt.to_python(tag.value)
        inicio = int(tag.offset)
        longitud = int(info["pay_len"])
        contenido = datos[inicio:inicio + longitud]
        valida = (
            info.get("crc") == 1 and info.get("crc_valid") is True
            and len(contenido) == longitud
        )
        tramas.append({
            "offset_bytes_salida": inicio,
            "longitud_bytes": longitud,
            "coding_rate": f"4/{4 + int(info['cr'])}",
            "crc_presente": bool(info["crc"]),
            "crc_valido": info.get("crc_valid"),
            "cabecera_error": info.get("err"),
        })
        if valida:
            contenidos_validos[contenido] += 1

    return {
        "fecha_prueba_utc": datetime.now(timezone.utc).isoformat(),
        "archivo": str(archivo.relative_to(ROOT)) if archivo.is_relative_to(ROOT) else str(archivo),
        "sha256": resumen,
        "tamano_bytes": tamano,
        "muestras_complejas": tamano // 8,
        "duracion_s": tamano / 8 / parametros["tasa_muestras_sps"],
        "formato": "cf32_le",
        "gnuradio_version": gr.version(),
        "python_version": sys.version.split()[0],
        "modulo_receptor": str(Path(lora_sdr.__file__).resolve()),
        "parametros": parametros,
        "bytes_recuperados": len(datos),
        "mensajes_recibidos": mensajes.num_messages(),
        "tramas_recuperadas": len(tramas),
        "paquetes_crc_validos": sum(contenidos_validos.values()),
        "tramas_con_crc_invalido": sum(t["crc_valido"] is False for t in tramas),
        "payloads_validos": [{
            "repeticiones": cantidad,
            "hex": contenido.hex(),
            "texto_ascii": contenido.decode("ascii", errors="replace"),
        } for contenido, cantidad in contenidos_validos.items()],
        "tramas": tramas,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", type=Path, nargs="?", default=CAPTURA)
    parser.add_argument("--sync-word", type=lambda valor: int(valor, 0), default=0x34)
    parser.add_argument("--salida", type=Path, help="Guardar también el informe JSON")
    args = parser.parse_args()
    if not 0 <= args.sync_word <= 255:
        parser.error("sync-word debe ser un byte, por ejemplo 0x34")
    resultado = verificar(args.archivo, args.sync_word)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto + "\n", encoding="utf-8")
    print(texto)
    return 0 if resultado["paquetes_crc_validos"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

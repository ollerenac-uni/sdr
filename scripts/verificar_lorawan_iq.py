"""Prueba LoRaWAN 1.0.x con I/Q generado por bloques de GNU Radio.

No es una captura por aire ni una prueba de conexión a una red LoRaWAN.
Modula una trama real publicada en 03_Brno_join.pcap y comprueba su recepción,
CRC, MIC y descifrado. La frecuencia de 915 MHz es una referencia de simulación.
Los datos y claves pertenecen a un nodo de prueba publicado por sus autores:
https://zenodo.org/records/8090619

Ejecutar con Radioconda, que incluye gr-lora_sdr y cryptography.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from gnuradio import blocks, gr, lora_sdr
import pmt

from verificar_lorawan import analizar_trama


TRAMA = bytes.fromhex("80dc5de60190040001dbf5a4e31239d05321687b")
NWK = bytes.fromhex("e2898779a03de59e2317b149abf00238")
APP = bytes.fromhex("59ca1ac91922887093bc7b236bd1b07f")
FS = 1000000
BW = 125000
SF = 7
FRECUENCIA = 915000000


def modular(trama):
    """Una fuente finita transporta bytes binarios, incluidos 00 y 80..ff."""
    tb = gr.top_block("LoRaWAN: generación de I/Q didáctico")
    fuente = blocks.vector_source_b(list(trama), False)
    etiquetar = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, len(trama), "packet_len")
    whitening = lora_sdr.whitening(False, True, ',', 'packet_len')
    cabecera = lora_sdr.header(False, True, 1)
    crc = lora_sdr.add_crc(True)
    hamming = lora_sdr.hamming_enc(1, SF)
    interleaver = lora_sdr.interleaver(1, SF, 2, BW)
    gray = lora_sdr.gray_demap(SF)
    modulador = lora_sdr.modulate(SF, FS, BW, [0x34], 16384, 8)
    destino = blocks.vector_sink_c()
    tb.connect(fuente, etiquetar, whitening, cabecera, crc, hamming,
               interleaver, gray, modulador, destino)
    tb.run()
    datos = np.asarray(destino.data(), dtype='<c8')
    # El cierre facilita el vaciado del receptor al procesar un archivo finito.
    return np.concatenate((np.zeros(8192, dtype='<c8'), datos,
                           np.zeros(32768, dtype='<c8')))


def recibir(archivo, sync_word=0x34):
    tb = gr.top_block("LoRaWAN: recepción de I/Q didáctico")
    fuente = blocks.file_source(gr.sizeof_gr_complex, str(archivo), False)
    receptor = lora_sdr.lora_sdr_lora_rx(
        center_freq=FRECUENCIA, bw=BW, cr=1, has_crc=True, impl_head=False,
        pay_len=len(TRAMA), samp_rate=FS, sf=SF, sync_word=[sync_word],
        soft_decoding=True, ldro_mode=2, print_rx=[False, False],
    )
    destino = blocks.vector_sink_b()
    tb.connect(fuente, receptor, destino)
    tb.run()
    datos = bytes(destino.data())
    tramas = []
    for tag in destino.tags():
        if pmt.symbol_to_string(tag.key) != 'frame_info':
            continue
        info = pmt.to_python(tag.value)
        inicio, longitud = int(tag.offset), int(info['pay_len'])
        contenido = datos[inicio:inicio + longitud]
        tramas.append({
            'payload_hex': contenido.hex(),
            'longitud_completa': len(contenido) == longitud,
            'crc_presente': info.get('crc') == 1,
            'crc_valido': info.get('crc_valid') is True,
            'cabecera_sin_error': info.get('err') == 0,
        })
    return tramas


def guardar_iq(trama, archivo):
    datos = modular(trama)
    datos.tofile(archivo)
    meta = {
        'global': {
            'core:datatype': 'cf32_le', 'core:sample_rate': FS,
            'core:version': '1.2.6',
            'core:description': 'Señal generada por GNU Radio. No es una captura por aire.',
        },
        'captures': [{'core:sample_start': 0, 'core:frequency': FRECUENCIA}],
        'annotations': [],
    }
    archivo.with_suffix('.sigmf-meta').write_text(json.dumps(meta, indent=2) + '\n')
    return {'archivo': archivo.name, 'muestras_complejas': len(datos),
            'sha256': hashlib.sha256(archivo.read_bytes()).hexdigest()}


def comprobar(salida):
    salida.mkdir(parents=True, exist_ok=True)
    alterada = bytearray(TRAMA)
    alterada[9] ^= 1  # Se conserva el MIC; LoRa Tx añade un CRC PHY nuevo.
    casos = []
    recibida_correcta = None
    archivo_correcto = None
    for nombre, trama, mic_esperado in (
        ('correcto', TRAMA, True), ('contenido_alterado', bytes(alterada), False),
    ):
        archivo = salida / f'{nombre}.sigmf-data'
        iq = guardar_iq(trama, archivo)
        recuperadas = recibir(archivo)
        if len(recuperadas) != 1:
            raise RuntimeError(f'{nombre}: se esperaba una trama y se recibieron {len(recuperadas)}')
        rx = recuperadas[0]
        if not all(rx[k] for k in ('longitud_completa', 'crc_presente', 'crc_valido', 'cabecera_sin_error')):
            raise RuntimeError(f'{nombre}: falló la recuperación física: {rx}')
        recuperada = bytes.fromhex(rx['payload_hex'])
        if recuperada != trama:
            raise RuntimeError(f'{nombre}: los bytes recibidos difieren de los enviados')
        mac = analizar_trama(recuperada, NWK, APP, 4)
        if mac['mic_valido'] != mic_esperado:
            raise RuntimeError(f'{nombre}: MIC distinto del esperado')
        if mic_esperado and mac['payload_descifrado_utf8'] != 'timeout':
            raise RuntimeError('El dato de aplicación difiere del resultado conocido')
        casos.append({'caso': nombre, 'iq': iq, 'lora_phy': rx, 'lorawan': mac})
        if nombre == 'correcto':
            recibida_correcta, archivo_correcto = recuperada, archivo

    red_incorrecta = analizar_trama(recibida_correcta, bytes(16), APP, 4)
    app_incorrecta = analizar_trama(recibida_correcta, NWK, bytes(16), 4)
    sync_incorrecto = recibir(archivo_correcto, 0x12)
    if red_incorrecta['mic_valido'] or not app_incorrecta['mic_valido']:
        raise RuntimeError('Falló el control independiente de las claves')
    if app_incorrecta['payload_descifrado_hex'] == b'timeout'.hex() or sync_incorrecto:
        raise RuntimeError('Falló el control de AppSKey o de sync word')
    return {
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'origen_iq': 'generado por GNU Radio; sin recepción ni transmisión por aire',
        'origen_trama': 'https://zenodo.org/records/8090619, 03_Brno_join.pcap, paquete 258',
        'gnuradio_version': gr.version(), 'python_version': sys.version.split()[0],
        'parametros': {'frecuencia_referencia_hz': FRECUENCIA, 'samp_rate': FS,
                       'bw': BW, 'sf': SF, 'cr': '4/5', 'sync_word': '0x34'},
        'casos': casos,
        'clave_red_incorrecta': red_incorrecta,
        'clave_aplicacion_incorrecta': app_incorrecta,
        'sync_word_0x12_tramas': len(sync_incorrecto),
        'controles_aprobados': True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, default=Path('output/lorawan-iq'))
    args = parser.parse_args()
    resultado = comprobar(args.salida)
    informe = args.salida / 'verificacion.json'
    informe.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n')
    print(f'Controles aprobados. Informe: {informe}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

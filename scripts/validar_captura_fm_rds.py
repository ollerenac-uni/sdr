#!/usr/bin/env python3
"""Valida audio mono y grupos RDS de una captura cu8 con tasas explícitas."""

import argparse
from collections import Counter
from fractions import Fraction
import json
import math
from pathlib import Path

from gnuradio import analog, blocks, cbs33m, digital, filter, gr
from gnuradio.filter import firdes
import numpy as np
import pmt
import rds
import satellites


def validar(args):
    archivo = args.archivo.resolve()
    tamano = archivo.stat().st_size
    if tamano % 2:
        raise ValueError("El archivo debe contener parejas completas I/Q")
    inicio = round(args.inicio * args.sample_rate)
    disponibles = tamano // 2 - inicio
    if disponibles <= 0:
        raise ValueError("El inicio está fuera de la captura")
    muestras = disponibles if args.duracion is None else min(
        disponibles, round(args.duracion * args.sample_rate)
    )
    tasa_canal = args.sample_rate / args.decim_canal
    tasa_rds_previa = tasa_canal / args.decim_rds
    tasa_rds = tasa_rds_previa * args.interp_rds / args.remuestreo_decim_rds
    tasa_audio = tasa_canal / args.decim_audio
    relacion = Fraction(48000 * args.decim_canal * args.decim_audio, args.sample_rate)
    if tasa_canal < 240000:
        raise ValueError("Este filtro de canal requiere al menos 240 ksps de salida")
    if tasa_audio < 36000 or min(tasa_rds, tasa_rds_previa) < 8000:
        raise ValueError("La decimación propuesta no conserva las bandas filtradas")
    if abs(args.station_freq - args.center_freq) + 110000 > args.sample_rate / 2:
        raise ValueError("El canal elegido queda fuera de la captura")

    tb = gr.top_block("Validación de captura FM/RDS")
    fuente = blocks.file_source(gr.sizeof_char, str(archivo), False, 2 * inicio, 2 * muestras)
    conversion = cbs33m.cu8_a_c64()
    rotador = cbs33m.rotador_frecuencia(args.center_freq - args.station_freq, args.sample_rate)
    canal = filter.fir_filter_ccf(
        args.decim_canal, firdes.low_pass(1, args.sample_rate, 100000, 20000)
    )
    demod = analog.quadrature_demod_cf(tasa_canal / (2 * math.pi * 75000))
    complejo = blocks.float_to_complex(1)
    tasa_rotador = args.tasa_declarada_rotador_rds or tasa_canal
    centrar_rds = cbs33m.rotador_frecuencia(-57000, tasa_rotador)
    aislar_rds = filter.fir_filter_ccf(
        args.decim_rds, firdes.low_pass(1, tasa_canal, 3000, 1000)
    )
    remuestreo_rds = filter.rational_resampler_ccc(
        interpolation=args.interp_rds, decimation=args.remuestreo_decim_rds,
        taps=[], fractional_bw=0.4,
    )
    ganancia = blocks.multiply_const_cc(args.ganancia_rds)
    normalizador = analog.agc_cc(2e-3, 0.7, 1.0, 100)
    costas = digital.costas_loop_cc(0.01, 2, False)
    rrc = filter.fir_filter_ccf(1, firdes.root_raised_cosine(1, tasa_rds, 2375, 1, 101))
    reloj = digital.symbol_sync_cc(
        digital.TED_GARDNER, tasa_rds / 2375, 0.01, 1, 1, 0.1, 1,
        digital.constellation_bpsk().base(), digital.IR_MMSE_8TAP, 128, [],
    )
    manchester = satellites.manchester_sync_cc(32)
    real = blocks.complex_to_real(1)
    slicer = digital.binary_slicer_fb()
    diferencial = digital.diff_decoder_bb(2, digital.DIFF_DIFFERENTIAL)
    decoder = rds.decoder(False, False)
    parser = rds.parser(False, False, 0)
    grupos = blocks.message_debug()
    campos = blocks.message_debug()
    audio_fir = filter.fir_filter_fff(
        args.decim_audio, firdes.low_pass(1, tasa_canal, 16000, 2000)
    )
    remuestreo = filter.rational_resampler_fff(
        interpolation=relacion.numerator, decimation=relacion.denominator,
        taps=[], fractional_bw=0.4,
    )
    deenfasis = analog.fm_deemph(fs=48000, tau=75e-6)
    audio = blocks.vector_sink_f()
    tb.connect(fuente, conversion, rotador, canal, demod)
    tb.connect(demod, complejo, centrar_rds, aislar_rds)
    if args.interp_rds == args.remuestreo_decim_rds == 1:
        tb.connect(aislar_rds, ganancia)
    else:
        tb.connect(aislar_rds, remuestreo_rds, ganancia)
    if args.agc_rds:
        tb.connect(ganancia, normalizador, costas)
    else:
        tb.connect(ganancia, costas)
    tb.connect(costas, rrc, reloj, manchester, real, slicer, diferencial, decoder)
    tb.connect(demod, audio_fir, remuestreo, deenfasis, audio)
    tb.msg_connect((decoder, "out"), (grupos, "store"))
    tb.msg_connect((decoder, "out"), (parser, "in"))
    tb.msg_connect((parser, "out"), (campos, "store"))
    tb.run()

    textos = {0: set(), 1: set(), 4: set()}
    for i in range(campos.num_messages()):
        mensaje = campos.get_message(i)
        tipo = pmt.to_long(pmt.tuple_ref(mensaje, 0))
        if tipo in textos:
            textos[tipo].add(pmt.symbol_to_string(pmt.tuple_ref(mensaje, 1)))
    tipos_grupo = Counter()
    pi = Counter()
    for i in range(grupos.num_messages()):
        contenido = pmt.cdr(grupos.get_message(i))
        datos = bytes(pmt.u8vector_elements(contenido))
        pi[f"{int.from_bytes(datos[:2], 'big'):04X}"] += 1
        tipos_grupo[f"{datos[2] >> 4}{'B' if datos[2] & 8 else 'A'}"] += 1
    datos_audio = np.asarray(audio.data(), dtype=np.float32)
    if args.audio_wav:
        import wave
        with wave.open(str(args.audio_wav), "wb") as salida:
            salida.setnchannels(1)
            salida.setsampwidth(2)
            salida.setframerate(48000)
            salida.writeframes((np.clip(datos_audio * 0.2, -1, 1) * 32767).astype('<i2').tobytes())
    return {
        "archivo": str(archivo), "formato": "cu8", "sample_rate_hz": args.sample_rate,
        "center_freq_hz": args.center_freq, "station_freq_hz": args.station_freq,
        "inicio_s": args.inicio, "duracion_procesada_s": muestras / args.sample_rate,
        "tasa_canal_hz": tasa_canal, "tasa_rds_previa_hz": tasa_rds_previa,
        "remuestreo_rds": [args.interp_rds, args.remuestreo_decim_rds],
        "tasa_declarada_rotador_rds_hz": tasa_rotador, "tasa_rds_hz": tasa_rds,
        "muestras_por_chip": tasa_rds / 2375, "tasa_audio_previa_hz": tasa_audio,
        "remuestreo_audio": [relacion.numerator, relacion.denominator],
        "ganancia_rds": args.ganancia_rds, "agc_rds": args.agc_rds,
        "grupos_validos": grupos.num_messages(),
        "pi_por_grupo": dict(pi), "tipos_grupo": dict(tipos_grupo),
        "nombres_ps": sorted(textos[1]), "radiotextos": sorted(textos[4]),
        "muestras_audio": len(datos_audio), "tasa_audio_hz": 48000,
        "audio_rms": float(np.sqrt(np.mean(datos_audio ** 2))) if len(datos_audio) else 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", type=Path)
    parser.add_argument("--sample-rate", type=int, default=2048000)
    parser.add_argument("--center-freq", type=float, required=True)
    parser.add_argument("--station-freq", type=float, required=True)
    parser.add_argument("--decim-canal", type=int, default=8)
    parser.add_argument("--decim-audio", type=int, default=4)
    parser.add_argument("--decim-rds", type=int, default=16)
    parser.add_argument("--interp-rds", type=int, default=1)
    parser.add_argument("--remuestreo-decim-rds", type=int, default=1)
    parser.add_argument("--tasa-declarada-rotador-rds", type=float)
    parser.add_argument("--ganancia-rds", type=float, default=20)
    parser.add_argument("--agc-rds", action="store_true")
    parser.add_argument("--inicio", type=float, default=0)
    parser.add_argument("--duracion", type=float)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--audio-wav", type=Path)
    args = parser.parse_args()
    if min(args.sample_rate, args.decim_canal, args.decim_audio, args.decim_rds,
           args.interp_rds, args.remuestreo_decim_rds) <= 0:
        parser.error("Las tasas y decimaciones deben ser positivas")
    if args.tasa_declarada_rotador_rds is not None and args.tasa_declarada_rotador_rds <= 0:
        parser.error("La tasa declarada del rotador debe ser positiva")
    if args.inicio < 0 or (args.duracion is not None and args.duracion <= 0):
        parser.error("El inicio debe ser no negativo y la duración positiva")
    try:
        resultado = validar(args)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.json:
        args.json.write_text(texto + "\n", encoding="utf-8")
    print(texto)
    return 0 if resultado["grupos_validos"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

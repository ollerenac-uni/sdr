#!/usr/bin/env python3
"""Comprueba la clase 4 desde una captura, sin audio físico ni GUI."""

import argparse
import json
import math
from pathlib import Path

from gnuradio import analog, blocks, cbs33m, digital, filter, gr
from gnuradio.filter import firdes
import pmt
import rds
import satellites


def verificar(archivo):
    archivo = Path(archivo)
    if archivo.stat().st_size % 2:
        raise ValueError("La captura debe contener parejas completas de bytes I/Q")
    tb = gr.top_block("Comprobación FM y RDS")
    fuente = blocks.file_source(gr.sizeof_char, str(archivo), False)
    conversor = cbs33m.cu8_a_c64()
    sintonizador = cbs33m.rotador_frecuencia(1e6, 2.4e6)
    canal = filter.fir_filter_ccf(8, firdes.low_pass(1, 2.4e6, 120e3, 30e3))
    demodulador = analog.quadrature_demod_cf(300000 / (2 * math.pi * 75000))
    complejo = blocks.float_to_complex(1)
    rotador_rds = cbs33m.rotador_frecuencia(-57000, 300000)
    filtro_rds = filter.fir_filter_ccf(25, firdes.low_pass(1, 300000, 3e3, 1e3))
    ganancia = blocks.multiply_const_cc(20)
    agc = analog.agc_cc(2e-3, 0.7, 1, 100)
    costas = digital.costas_loop_cc(0.01, 2, False)
    rrc = filter.fir_filter_ccf(1, firdes.root_raised_cosine(1, 12000, 2375, 1, 101))
    reloj = digital.symbol_sync_cc(
        digital.TED_GARDNER, 12000 / 2375, 0.01, 1, 1, 0.1, 1,
        digital.constellation_bpsk().base(), digital.IR_MMSE_8TAP, 128, [],
    )
    manchester = satellites.manchester_sync_cc(32)
    real = blocks.complex_to_real(1)
    decision = digital.binary_slicer_fb()
    diferencial = digital.diff_decoder_bb(2, digital.DIFF_DIFFERENTIAL)
    decoder = rds.decoder(False, False)
    parser = rds.parser(False, False, 0)
    grupos = blocks.message_debug()
    campos = blocks.message_debug()
    audio_fir = filter.fir_filter_fff(6, firdes.low_pass(1, 300000, 16e3, 2e3))
    remuestreo = filter.rational_resampler_fff(interpolation=24, decimation=25, taps=[], fractional_bw=0.4)
    deenfasis = analog.fm_deemph(fs=48000, tau=75e-6)
    volumen = blocks.multiply_const_ff(0.2)
    audio = blocks.vector_sink_f()
    tb.connect(fuente, conversor, sintonizador, canal, demodulador)
    tb.connect(demodulador, complejo, rotador_rds, filtro_rds, ganancia, agc,
               costas, rrc, reloj, manchester, real, decision, diferencial, decoder)
    tb.connect(demodulador, audio_fir, remuestreo, deenfasis, volumen, audio)
    tb.msg_connect((decoder, "out"), (grupos, "store"))
    tb.msg_connect((decoder, "out"), (parser, "in"))
    tb.msg_connect((parser, "out"), (campos, "store"))
    tb.run()
    mensajes = [campos.get_message(i) for i in range(campos.num_messages())]
    textos = {1: set(), 4: set()}
    for mensaje in mensajes:
        tipo = pmt.to_long(pmt.tuple_ref(mensaje, 0))
        if tipo in textos:
            textos[tipo].add(pmt.symbol_to_string(pmt.tuple_ref(mensaje, 1)))
    return {
        "archivo": str(archivo),
        "duracion_captura_s": archivo.stat().st_size / (2 * 2.4e6),
        "muestras_audio": len(audio.data()),
        "grupos_validos": grupos.num_messages(),
        "nombres_ps": sorted(textos[1]),
        "radiotextos": sorted(textos[4]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", type=Path,
                        help="Captura oficial de 2.4 Msps centrada en 99.1 MHz")
    args = parser.parse_args()
    resultado = verificar(args.archivo.resolve())
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado["grupos_validos"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Repite la rama RDS con estado inicial nuevo desde multiplex FM grabado."""

import argparse
from collections import Counter
import json
from pathlib import Path

from gnuradio import analog, blocks, cbs33m, digital, filter, gr
from gnuradio.filter import firdes
import numpy as np
import pmt
import rds
import satellites


def reproducir(archivo, duracion=None):
    with np.load(archivo) as captura:
        muestras = np.asarray(captura["muestras"], dtype=np.float32)
        tasa = float(captura["sample_rate"])
    if duracion is not None:
        muestras = muestras[:round(duracion * tasa)]
    if tasa != 300000:
        raise ValueError("Esta réplica de fm.grc requiere multiplex a 300 ksps")
    tb = gr.top_block("Repetición RDS con estado nuevo")
    fuente = blocks.vector_source_f(muestras, False)
    complejo = blocks.float_to_complex(1)
    centrar = cbs33m.rotador_frecuencia(-57000, tasa)
    aislar = filter.fir_filter_ccf(25, firdes.low_pass(1, tasa, 3000, 1000))
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
    slicer = digital.binary_slicer_fb()
    diferencial = digital.diff_decoder_bb(2, digital.DIFF_DIFFERENTIAL)
    decoder = rds.decoder(False, False)
    parser = rds.parser(False, False, 0)
    grupos = blocks.message_debug()
    campos = blocks.message_debug()
    tb.connect(fuente, complejo, centrar, aislar, ganancia, agc, costas, rrc,
               reloj, manchester, real, slicer, diferencial, decoder)
    tb.msg_connect((decoder, "out"), (grupos, "store"))
    tb.msg_connect((decoder, "out"), (parser, "in"))
    tb.msg_connect((parser, "out"), (campos, "store"))
    tb.run()
    pi = Counter()
    for i in range(grupos.num_messages()):
        datos = bytes(pmt.u8vector_elements(pmt.cdr(grupos.get_message(i))))
        pi[f"{int.from_bytes(datos[:2], 'big'):04X}"] += 1
    textos = {1: set(), 4: set()}
    for i in range(campos.num_messages()):
        mensaje = campos.get_message(i)
        tipo = pmt.to_long(pmt.tuple_ref(mensaje, 0))
        if tipo in textos:
            textos[tipo].add(pmt.symbol_to_string(pmt.tuple_ref(mensaje, 1)).strip())
    return {
        "archivo": str(archivo), "estado_inicial": "Todos los bloques son instancias nuevas.",
        "tasa_mpx_hz": tasa, "duracion_s": len(muestras) / tasa,
        "bits_consumidos": int(decoder.nitems_read(0)),
        "grupos_validos": grupos.num_messages(), "pi_por_grupo": dict(pi),
        "ps_publicados": sorted(textos[1]), "radiotextos_publicados": sorted(textos[4]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivos", nargs="+", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--duracion", type=float, help="Procesar solo este prefijo de cada grabación, en segundos.")
    args = parser.parse_args()
    if args.duracion is not None and args.duracion <= 0:
        parser.error("La duración debe ser positiva")
    resultados = [reproducir(p, args.duracion) for p in args.archivos]
    texto = json.dumps(resultados, ensure_ascii=False, indent=2)
    if args.json:
        args.json.write_text(texto + "\n", encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()

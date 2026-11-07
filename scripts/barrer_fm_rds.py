#!/usr/bin/env python3
"""Barre FM usando el fm.grc compilado y registra adquisición RDS por sintonía."""

import argparse
from collections import Counter
from datetime import datetime
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt5 import Qt
from gnuradio import blocks, gr
import numpy as np
import pmt
from scipy.signal import welch
import yaml

ROOT = Path(__file__).resolve().parents[1]


def cargar_grafo(generado):
    spec = importlib.util.spec_from_file_location("fm_barrido_generado", generado)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    # La adquisición la regula RTL-SDR Source. Evitar audio físico durante el barrido.
    modulo.audio.sink = lambda *a, **kw: blocks.null_sink(gr.sizeof_float)
    return modulo


def esperar(app, segundos):
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        app.processEvents()
        time.sleep(min(0.02, max(0, limite - time.monotonic())))


def campos_de(debug, inicio):
    campos = {0: set(), 1: set(), 4: set()}
    for i in range(inicio, debug.num_messages()):
        mensaje = debug.get_message(i)
        if not pmt.is_tuple(mensaje):
            continue
        tipo = pmt.to_long(pmt.tuple_ref(mensaje, 0))
        if tipo in campos:
            campos[tipo].add(pmt.symbol_to_string(pmt.tuple_ref(mensaje, 1)).strip())
    return campos


def espectro_mpx(datos, tasa):
    if len(datos) < 8192:
        return {}
    datos = np.asarray(datos[-round(tasa * 0.5):], dtype=np.float32)
    f, p = welch(datos, fs=tasa, nperseg=8192)
    piso = max(float(np.mean(p[(f >= 61000) & (f <= 65000)])), 1e-20)
    alas = ((f >= 54500) & (f <= 59500) & (np.abs(f - 57000) >= 300))
    centro = np.abs(f - 57000) < 150
    potencia_alas = max(float(np.mean(p[alas])), 1e-20)
    potencia_centro = max(float(np.max(p[centro])), 1e-20)
    return {
        "alas_57k_sobre_referencia_db": 10 * math.log10(potencia_alas / piso),
        "pico_central_sobre_alas_db": 10 * math.log10(potencia_centro / potencia_alas),
        "nota": "Cocientes espectrales; no son SNR calibrada ni prueba de RDS válido.",
    }


def barrer(args):
    salida = args.salida.resolve()
    salida.mkdir(parents=True, exist_ok=True)
    if args.generado is None:
        carpeta = salida / "generado"
        carpeta.mkdir(exist_ok=True)
        grafo = args.grafo.resolve()
        identificador = yaml.safe_load(grafo.read_text())["options"]["parameters"]["id"]
        subprocess.run(["grcc", "-o", str(carpeta), str(grafo)], check=True)
        generado = carpeta / f"{identificador}.py"
    else:
        generado = args.generado.resolve()
    modulo = cargar_grafo(generado)
    app = Qt.QApplication.instance() or Qt.QApplication(["barrido-fm-rds"])
    clase = args.clase or generado.stem
    tb = getattr(modulo, clase)()
    if hasattr(modulo, "snippets_main_after_init"):
        modulo.snippets_main_after_init(tb)
    if args.ganancia is not None:
        tb.rtlsdr_source_0.set_gain(args.ganancia, 0)
    if args.desplazamiento is not None:
        tb.set_desplazamiento_sintonia(args.desplazamiento)
    grupos = blocks.message_debug()
    campos = blocks.message_debug()
    mpx = blocks.vector_sink_f()
    tb.msg_connect((tb.decodificador_rds, "out"), (grupos, "store"))
    tb.msg_connect((tb.parser_rds, "out"), (campos, "store"))
    tb.connect(tb.demodulador_fm, mpx)
    if args.frecuencias:
        frecuencias = [float(f) for f in args.frecuencias.split(",")]
    else:
        pasos = round((args.fin - args.inicio) / args.paso)
        frecuencias = [round(args.inicio + i * args.paso, 6) for i in range(pasos + 1)]
    informe = {
        "inicio_local": datetime.now(ZoneInfo("America/Lima")).isoformat(),
        "ubicacion": "Lima, Perú", "gnuradio": gr.version(),
        "generado": str(generado), "ganancia_rf_solicitada_db": args.ganancia,
        "clase_grafo": clase,
        "secciones_snippet": sorted(n for n in vars(modulo) if n.startswith("snippets_")),
        "panel_frecuencia_al_iniciar": tb.panel_rds.freq.text(),
        "desplazamiento_sintonia_hz": getattr(tb, "desplazamiento_sintonia", 0),
        "asentamiento_s": args.espera, "observacion_s": args.tiempo,
        "metodo": "El mismo flowgraph permanece ejecutándose entre cambios de frecuencia.",
        "frecuencias_mhz": frecuencias, "resultados": [],
    }
    tb.start()
    tb.flowgraph_started.set()
    if hasattr(modulo, "snippets_main_after_start"):
        modulo.snippets_main_after_start(tb)
    try:
        for frecuencia in frecuencias:
            tb.set_frecuencia_emisora(frecuencia)
            esperar(app, args.espera)
            # Excluir mensajes y muestras anteriores al asentamiento del sintonizador.
            g0, c0 = grupos.num_messages(), campos.num_messages()
            bits0 = tb.decodificador_rds.nitems_read(0)
            mpx.reset()
            principio = time.monotonic()
            esperar(app, args.tiempo)
            transcurrido = time.monotonic() - principio
            g1 = grupos.num_messages()
            pi = Counter()
            tipos = Counter()
            for i in range(g0, g1):
                datos = bytes(pmt.u8vector_elements(pmt.cdr(grupos.get_message(i))))
                pi[f"{int.from_bytes(datos[:2], 'big'):04X}"] += 1
                tipos[f"{datos[2] >> 4}{'B' if datos[2] & 8 else 'A'}"] += 1
            textos = campos_de(campos, c0)
            registro = {
                "frecuencia_mhz": frecuencia,
                "grupos_validos": g1 - g0,
                "pi_por_grupo": dict(pi), "tipos_grupo": dict(tipos),
                "ps_publicados": sorted(textos[1]), "radiotextos_publicados": sorted(textos[4]),
                "bits_consumidos": int(tb.decodificador_rds.nitems_read(0) - bits0),
                "observacion_real_s": transcurrido,
                "panel_frecuencia": tb.panel_rds.freq.text(),
                "panel_ps": tb.panel_rds.station.text(),
                "panel_rt": tb.panel_rds.radiotext.text(),
                "costas_frecuencia_hz": tb.fase_rds.get_frequency() * tb.tasa_rds / (2 * math.pi),
                **espectro_mpx(mpx.data(), tb.tasa_canal),
            }
            informe["resultados"].append(registro)
            (salida / "barrido.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n")
            muestras_mpx = mpx.data()
            if not args.guardar_mpx_completo:
                muestras_mpx = muestras_mpx[-round(tb.tasa_canal * 0.5):]
            np.savez_compressed(salida / f"mpx-{len(informe['resultados']):03d}-{frecuencia:.1f}.npz",
                                muestras=np.asarray(muestras_mpx, dtype=np.float32),
                                sample_rate=tb.tasa_canal)
            print(json.dumps({k: registro[k] for k in ["frecuencia_mhz", "grupos_validos", "pi_por_grupo", "ps_publicados", "bits_consumidos"]}), flush=True)
    finally:
        tb.stop()
        tb.wait()
        if hasattr(modulo, "snippets_main_after_stop"):
            modulo.snippets_main_after_stop(tb)
        tb.close()
        app.processEvents()
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inicio", type=float, default=87)
    parser.add_argument("--fin", type=float, default=108)
    parser.add_argument("--paso", type=float, default=0.1)
    parser.add_argument("--espera", type=float, default=0.7)
    parser.add_argument("--tiempo", type=float, default=2.3)
    parser.add_argument("--frecuencias", help="Lista en MHz, separada por comas; conserva el orden y las repeticiones.")
    parser.add_argument("--ganancia", type=float)
    parser.add_argument("--desplazamiento", type=float, help="Desplazamiento de sintonía en Hz; requiere el grafo mejorado.")
    parser.add_argument("--generado", type=Path, help="Usar un fm.py ya generado para comparar versiones.")
    parser.add_argument("--grafo", type=Path, default=ROOT / "gnuradio/flowgraphs/fm.grc",
                        help="Flowgraph que se compila cuando no se especifica --generado.")
    parser.add_argument("--clase", help="Clase del Python generado; por defecto, el nombre del archivo.")
    parser.add_argument("--guardar-mpx-completo", action="store_true", help="Conservar el multiplex completo de cada observación para repetir la prueba sin USB.")
    parser.add_argument("--salida", type=Path, default=ROOT / "output/barrido-fm-rds")
    args = parser.parse_args()
    if args.paso <= 0 or args.fin < args.inicio or args.tiempo <= 0 or args.espera < 0:
        parser.error("Rango o tiempos inválidos")
    barrer(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Guía restaurada y prueba DSP del .grc, sin hardware, Qt ni dispositivo de audio.

Las variantes temporales conservan la cadena DSP del grafo publicado. Solo se
sustituyen pacing/visores/audio para poder ejecutar una entrada finita y medirla.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parents[1]
GRAFO = ROOT / "gnuradio-flowgraphs/receptor_fm_99p1_2p048Msps.grc"
GUIA = ROOT / "docs/sessions/02-tiempo-frecuencia-iq/laboratorio-receptor-fm.md"
GRCC = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
PYTHON_GR = Path(GRCC).parent / "python3"
RUTA_CU8 = {
    "blocks_file_source_0", "blocks_throttle2_0", "blocks_uchar_to_float_0",
    "blocks_add_const_vxx_0", "blocks_multiply_const_vxx_0",
    "blocks_deinterleave_0", "blocks_float_to_complex_0",
}


def leer_grafo():
    return yaml.safe_load(GRAFO.read_text(encoding="utf-8"))


def bloques(grafo):
    return {bloque["name"]: bloque for bloque in grafo["blocks"]}


@pytest.fixture(scope="module")
def runtime():
    if not Path(GRCC).is_file() or not PYTHON_GR.is_file():
        pytest.skip("GNU Radio y su intérprete no están disponibles")
    resultado = subprocess.run([str(PYTHON_GR), "-c", "from gnuradio import gr; print(gr.version())"], capture_output=True, text=True, timeout=15)
    if resultado.returncode:
        pytest.skip("El intérprete de grcc no puede importar GNU Radio")
    return GRCC, str(PYTHON_GR)


def compilar(grafo, directorio, runtime):
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / "verificacion.grc"
    ruta.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    resultado = subprocess.run([runtime[0], "-o", str(directorio), str(ruta)], capture_output=True, text=True, timeout=60)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    return directorio / (grafo["options"]["parameters"]["id"] + ".py")


def variante_headless(archivo, fs=2048000, interpolacion=3, decimacion=32):
    grafo = deepcopy(leer_grafo())
    grafo["options"]["parameters"].update(id="fm_verificacion", generate_options="no_gui")
    b = bloques(grafo)
    b["volume"].update(id="variable", parameters={"value": "0.2"})
    b["samp_rate"]["parameters"]["value"] = str(fs)
    b["blocks_file_source_0"]["parameters"].update(file=str(archivo), repeat="False", length=str(2 * fs))
    # El Copy no altera los bytes, pero evita esperar al reloj durante una prueba.
    b["blocks_throttle2_0"].update(id="blocks_copy", parameters={"type": "byte", "vlen": "1", "enabled": "True"})
    for nombre in ("qtgui_freq_sink_rf", "qtgui_freq_sink_canal"):
        b[nombre].update(id="blocks_null_sink", parameters={"type": "complex", "vlen": "1", "num_inputs": "1"})
    b["audio_sink_0"].update(id="blocks_vector_sink_x", parameters={"type": "float", "vlen": "1", "reserve_items": "48000"})
    b["rational_resampler_xxx_0"]["parameters"].update(interp=str(interpolacion), decim=str(decimacion))
    return grafo


def ejecutar_dsp(modulo, runtime):
    programa = """
import importlib.util, json, sys
import numpy as np
spec = importlib.util.spec_from_file_location('fm_prueba', sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
tb = m.fm_verificacion()
tb.run()
y = np.asarray(tb.audio_sink_0.data())
estable = y[4800:]
f = np.fft.rfftfreq(len(estable), 1 / 48000)
X = np.abs(np.fft.rfft((estable - np.mean(estable)) * np.hanning(len(estable))))
print(json.dumps({'version': m.gr.version(), 'muestras': len(y),
    'finite': bool(np.isfinite(y).all()), 'rms': float(np.sqrt(np.mean(estable**2))),
    'pico_hz': float(f[np.argmax(X)]),
    'fraccion_pico': float(np.sum(X[np.abs(f - 1000) < 10]**2) / np.sum(X**2))}))
"""
    resultado = subprocess.run([runtime[1], "-c", programa, str(modulo)], capture_output=True, text=True, timeout=60)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    datos = json.loads(resultado.stdout.strip().splitlines()[-1])
    print(datos)
    assert datos["finite"]
    return datos


def test_guia_y_navegacion_restauradas_con_fuentes_y_metadatos():
    guia = GUIA.read_text(encoding="utf-8")
    assert "status: draft" in guia
    assert "laboratorio-receptor-fm.md" in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "laboratorio-receptor-fm.md" in GUIA.with_name("index.md").read_text(encoding="utf-8")
    for expresion in ("2.048 MS/s", "2.4 MS/s", "Quadrature Rate = 192000", "Audio Decimation = 4", "audio mono", "underruns", "±76.8 kHz"):
        assert expresion in guia
    for fuente in ("rational_resampler_impl.cc", "quadrature_demod_cf_impl.cc", "wfm_rcv.py", "fm_emph.py"):
        assert fuente in guia
    assert "Complex Float32" in guia
    assert "siete bloques" in guia


def test_tasas_y_intervalos_derivados_de_parametros_del_grc():
    b = bloques(leer_grafo())
    fs = int(b["samp_rate"]["parameters"]["value"])
    L = int(b["rational_resampler_xxx_0"]["parameters"]["interp"])
    D = int(b["rational_resampler_xxx_0"]["parameters"]["decim"])
    tasa_canal = fs * L / D
    wbfm = b["analog_wfm_rcv_0"]["parameters"]
    assert 2 * fs == 4096000
    assert tasa_canal == float(wbfm["quad_rate"]) == 192000
    assert tasa_canal / int(wbfm["audio_decimation"]) == int(b["audio_sink_0"]["parameters"]["samp_rate"]) == 48000
    np.testing.assert_allclose((99.1e6 + np.array([-fs / 2, fs / 2])) / 1e6, [98.076, 100.124])
    np.testing.assert_allclose((99.1e6 + np.array([-tasa_canal / 2, tasa_canal / 2])) / 1e6, [99.004, 99.196])
    assert fs / 1024 == 2000
    assert tasa_canal / 1024 == 187.5
    assert 2400000 * 2 / 25 == tasa_canal
    assert 192000 * 0.4 == 76800
    assert 192000 / (2 * np.pi * 75000) == pytest.approx(0.4074366543152521)


@pytest.mark.parametrize("fs,L,D", [(2048000, 3, 32), (2400000, 2, 25)])
def test_cadena_grc_recupera_tono_fm_conocido(tmp_path, runtime, fs, L, D):
    # FM ideal: desviación 15 kHz, moduladora de 1 kHz, amplitud I/Q 0.8.
    t = np.arange(fs) / fs
    fase = 2 * np.pi * 15000 / fs * np.cumsum(np.sin(2 * np.pi * 1000 * t))
    z = 0.8 * np.exp(1j * fase)
    cu8 = np.empty(2 * fs, dtype=np.uint8)
    cu8[0::2] = np.rint(127.5 + 127.5 * z.real).astype(np.uint8)
    cu8[1::2] = np.rint(127.5 + 127.5 * z.imag).astype(np.uint8)
    archivo = tmp_path / "fm_sintetica.cu8"
    archivo.write_bytes(cu8.tobytes())
    modulo = compilar(variante_headless(archivo, fs, L, D), tmp_path / "compilado", runtime)
    datos = ejecutar_dsp(modulo, runtime)
    assert abs(datos["muestras"] - 48000) < 200
    assert abs(datos["pico_hz"] - 1000) < 2
    assert datos["fraccion_pico"] > 0.99
    # De-emphasis atenúa el tono: no se exige amplitud de salida igual a la entrada.
    assert 0.02 < datos["rms"] < 0.04


def test_captura_del_laboratorio_produce_audio_real_si_esta_disponible(tmp_path, runtime):
    archivo = ROOT / "samples/fm_99p1MHz_2p048Msps_g30.cu8"
    if not archivo.is_file():
        pytest.skip("La captura se distribuye fuera de Git")
    modulo = compilar(variante_headless(archivo), tmp_path / "compilado", runtime)
    datos = ejecutar_dsp(modulo, runtime)
    assert abs(datos["muestras"] - 48000) < 200
    assert datos["rms"] > 1e-5


def test_variante_soapy_compila_sin_cadena_cu8_activa(tmp_path, runtime):
    grafo = leer_grafo()
    grafo["options"]["parameters"]["id"] = "fm_soapy_verificacion"
    b = bloques(grafo)
    for nombre in RUTA_CU8:
        b[nombre]["states"]["state"] = "disabled"
    b["soapy_rtlsdr_source_0"]["states"]["state"] = "enabled"
    modulo = compilar(grafo, tmp_path / "compilado", runtime)
    codigo = modulo.read_text(encoding="utf-8")
    assert "soapy.source(" in codigo
    assert "blocks.file_source(" not in codigo
    assert "blocks.throttle(" not in codigo

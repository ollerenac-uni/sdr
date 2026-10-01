"""Compila el GRC publicado y ejecuta su cadena DSP en ambos modos, sin Qt."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

np = pytest.importorskip("numpy")
signal = pytest.importorskip("scipy.signal")
ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "docs/sessions/03-sistemas-filtros-digitales"
GRAFO = CARPETA / "filtros_sesion03.grc"
GRCC = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
PYTHON_GR = Path(GRCC).parent / "python3"


@pytest.fixture(scope="module")
def runtime():
    if not Path(GRCC).is_file() or not PYTHON_GR.is_file():
        pytest.skip("GNU Radio y su intérprete no están disponibles")
    return GRCC, str(PYTHON_GR)


def leer_grafo():
    return yaml.safe_load(GRAFO.read_text(encoding="utf-8"))


def compilar(grafo, directorio, runtime):
    directorio.mkdir(parents=True, exist_ok=True)
    archivo = directorio / "prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    resultado = subprocess.run([runtime[0], "-o", str(directorio), str(archivo)], capture_output=True, text=True, timeout=45)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    return directorio / (grafo["options"]["parameters"]["id"] + ".py")


def test_contrato_grafo_descargable_sin_hardware():
    grafo = leer_grafo()
    b = {bloque["name"]: bloque for bloque in grafo["blocks"]}
    assert grafo["options"]["parameters"]["id"] == "filtros_sesion03"
    assert b["fir"]["id"] == "fir_filter_xxx"
    assert b["fir"]["parameters"]["type"] == "ccf"
    assert b["fir"]["parameters"]["decim"] == "1"
    assert b["samp_rate"]["parameters"]["value"] == "24000"
    assert b["import_scipy"]["id"] == "import"
    assert "as dsp_signal" in b["import_scipy"]["parameters"]["imports"]
    assert b["espectros"]["parameters"]["nconnections"] == "2"
    assert b["espectros"]["parameters"]["bw"] == "samp_rate"
    assert all(b[nombre]["parameters"]["type"] == "complex" for nombre in ("tono_util", "tono_no_deseado", "suma_tonos", "ritmo", "espectros"))
    assert all("file" not in bloque["parameters"] for bloque in grafo["blocks"])
    guia = (CARPETA / "laboratorio-filtrado.md").read_text(encoding="utf-8")
    assert "[Descargar el flowgraph `filtros_sesion03.grc`](filtros_sesion03.grc)" in guia
    # El nuevo ID no pisa el .py de ningún flowgraph del curso existente.
    for archivo in (ROOT / "gnuradio-flowgraphs").glob("*.grc"):
        previo = yaml.safe_load(archivo.read_text(encoding="utf-8"))
        assert previo["options"]["parameters"]["id"] != "filtros_sesion03"


@pytest.mark.parametrize("modo", [0, 1])
def test_grafo_gui_compila_con_import_scipy_real(tmp_path, runtime, modo):
    grafo = deepcopy(leer_grafo())
    next(b for b in grafo["blocks"] if b["name"] == "modo_filtro")["parameters"]["value"] = str(modo)
    modulo = compilar(grafo, tmp_path, runtime)
    codigo = modulo.read_text(encoding="utf-8")
    assert "from scipy import signal as dsp_signal" in codigo
    assert "filter.fir_filter_ccf(1, taps)" in codigo
    assert "self.espectros" in codigo
    assert "import signal" in codigo  # Módulo de señales del SO, distinto de SciPy.


@pytest.mark.parametrize("modo", [0, 1])
def test_dsp_publicado_conserva_iq_tasa_y_frecuencias(tmp_path, runtime, modo):
    grafo = deepcopy(leer_grafo())
    grafo["options"]["parameters"].update(id="filtros_sesion03_prueba", generate_options="no_gui")
    b = {bloque["name"]: bloque for bloque in grafo["blocks"]}
    b["modo_filtro"]["parameters"]["value"] = str(modo)
    # Se conserva la suma, las fuentes y el FIR. Head limita la prueba a 5056
    # muestras y Vector Sink sustituye al visor. No se espera al reloj de Throttle.
    b["ritmo"].update(id="blocks_head", parameters={"type": "complex", "vlen": "1", "num_items": "5056"})
    b["espectros"].update(id="blocks_vector_sink_x", parameters={"type": "complex", "vlen": "1", "reserve_items": "5056"})
    grafo["connections"] = [c for c in grafo["connections"] if not (c[2] == "espectros" and c[3] == "1")]
    grafo["connections"] = [c for c in grafo["connections"] if not (c[0] == "ritmo" and c[2] == "espectros")]
    grafo["connections"].append(["fir", "0", "espectros", "0"])
    modulo = compilar(grafo, tmp_path, runtime)
    programa = """
import importlib.util, json, sys
import numpy as np
spec = importlib.util.spec_from_file_location('filtros_prueba', sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
tb = m.filtros_sesion03_prueba()
tb.run()
y = np.asarray(tb.espectros.data())
z = y[256:]
f = np.fft.fftshift(np.fft.fftfreq(len(z), 1 / 24000))
Y = np.abs(np.fft.fftshift(np.fft.fft(z)) / len(z))
indices = [np.argmin(np.abs(f - f0)) for f0 in (1000, 9000)]
print(json.dumps({'muestras': len(y), 'finito': bool(np.isfinite(y).all()),
    'frecuencias': f[indices].tolist(), 'amplitudes': Y[indices].tolist(),
    'residuo': float(np.max(np.delete(Y, indices))),
    'rms_q': float(np.sqrt(np.mean(z.imag**2)))}))
"""
    resultado = subprocess.run([runtime[1], "-c", programa, str(modulo)], capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    datos = json.loads(resultado.stdout.strip().splitlines()[-1])
    assert datos["finito"]
    assert datos["muestras"] == 5056
    np.testing.assert_allclose(datos["frecuencias"], [1000, 9000])
    h = np.ones(3)/3 if modo == 0 else signal.firwin(65, 3000, fs=24000)
    _, H = signal.freqz(h, worN=np.array([1000, 9000]), fs=24000)
    # Signal Source usa un NCO float32: se admite su pequeño error acumulado,
    # sin rebajar la comprobación del rechazo del tono de 9 kHz.
    np.testing.assert_allclose(datos["amplitudes"], np.array([1, 0.6])*np.abs(H), rtol=0.002, atol=1e-6)
    assert datos["residuo"] < 0.002
    assert datos["rms_q"] > 0.5

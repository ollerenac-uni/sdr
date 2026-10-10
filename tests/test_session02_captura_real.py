"""Celdas independientes, estimaciones de potencia y discriminador FM de S02."""

import ast
import importlib.util
from pathlib import Path
import re

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "docs/sessions/02-tiempo-frecuencia-iq"
CAPTURA = ROOT / "samples/fm_99p1MHz_2p4Msps_g30.cu8"


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, SESSION / f"figures/{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def visor():
    return cargar("gen_captura_sdr")


@pytest.fixture
def cu8(tmp_path):
    # Extremos y valores centrales: detectan una resta sobre uint8.
    pares = np.tile(np.array([[0, 255], [127, 128], [255, 0], [128, 127]], dtype=np.uint8), (204800, 1))
    ruta = tmp_path / "captura.cu8"
    ruta.write_bytes(pares.tobytes())
    return ruta, pares


def ejecutar(visor, apartado, ruta):
    original = plt.show
    try:
        plt.show = lambda: plt.close("all")
        return visor.ejecutar(apartado, ruta)
    finally:
        plt.show = original
        plt.close("all")


def test_promedio_lineal_conserva_escala_comun_y_decodifica_cu8(visor, cu8):
    ruta, pares = cu8
    d = ejecutar(visor, "6.2", ruta)
    esperado = ((pares[:, 0].astype(float) - 127.5) + 1j * (pares[:, 1].astype(float) - 127.5)) / 127.5
    np.testing.assert_allclose(d["z"].ravel(), esperado, atol=1e-7)
    assert d["z"][0, 0] == -1 + 1j
    assert d["z"].shape == (200, 4096)
    np.testing.assert_allclose(d["promedio"], d["P"].mean(axis=0))
    assert np.max(d["db"][1]) == pytest.approx(0)
    assert d["N"] / d["fs"] == pytest.approx(0.0017066666666666667)
    assert np.diff(d["f_rf"])[0] * 1e6 == pytest.approx(585.9375)
    assert d["f_rf"][0] == pytest.approx(97.9)
    assert d["f_rf"][-1] < 100.3
    assert np.isfinite(d["db"]).all()


def test_waterfall_agrupa_bloques_sin_huecos_y_no_normaliza_cada_fila(visor, cu8):
    ruta, _ = cu8
    d = ejecutar(visor, "6.3", ruta)
    assert d["filas"] == 20
    assert d["potencia"].shape == (20, 4096)
    np.testing.assert_allclose(np.diff(d["tiempo_bordes"]), 40960 / 2400000)
    assert d["tiempo_bordes"][-1] == pytest.approx(819200 / 2400000)
    esperado = 10 * np.log10(np.maximum(d["potencia"] / d["referencia"], 1e-12))
    np.testing.assert_allclose(d["db"], esperado)


@pytest.mark.parametrize("apartado", ["6.2", "6.3"])
def test_archivos_ausentes_impares_y_cortos_tienen_error_claro(visor, tmp_path, apartado):
    with pytest.raises(FileNotFoundError, match="Falta la grabación"):
        ejecutar(visor, apartado, tmp_path / "ausente.cu8")
    ruta = tmp_path / "corto.cu8"
    ruta.write_bytes(bytes([0, 127, 255]))
    with pytest.raises(ValueError, match="pares completos"):
        ejecutar(visor, apartado, ruta)
    ruta.write_bytes(bytes([0, 255]))
    with pytest.raises(ValueError, match="bloques completos"):
        ejecutar(visor, apartado, ruta)


def test_fm_recupera_mensaje_con_escala_conocida(monkeypatch):
    monkeypatch.setattr(plt, "show", lambda: plt.close("all"))
    d = cargar("gen_fm_giro").ejecutar()
    np.testing.assert_allclose(d["recuperado"], d["mensaje"][1:], atol=3e-14)
    np.testing.assert_allclose(abs(d["z"]), 1)
    assert len(d["giro"]) == len(d["z"]) - 1 == 47
    assert np.max(np.abs(d["giro"])) == pytest.approx(np.pi / 4)
    assert d["N"] / d["fs"] == 0.001
    # La misma operación mide también giros negativos.
    assert d["giro"].min() < 0 < d["giro"].max()


def test_adelanto_conserva_magnitud_y_traslada_toda_la_entrada(visor, cu8):
    d = visor.datos_adelanto(cu8[0])
    np.testing.assert_allclose(np.abs(d["y"]), np.abs(d["z"]), atol=1e-7)
    assert not np.allclose(d["y"], d["z"])
    assert d["db"].shape == (2, 4096)


def test_generadores_reproducen_png_sin_wav(visor, cu8, tmp_path):
    paths = visor.generar(tmp_path, cu8[0])
    paths.append(cargar("gen_fm_giro").generar(tmp_path))
    assert len(paths) == 4
    for path in paths:
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert not list(tmp_path.glob("*.wav"))


def test_captura_oficial_y_tiempos_si_esta_disponible(visor):
    if not CAPTURA.is_file():
        pytest.skip("Las grabaciones se distribuyen por Drive, no por Git")
    assert CAPTURA.stat().st_size == 48000000
    d = ejecutar(visor, "6.3", CAPTURA)
    assert d["filas"] == 585
    assert d["tiempo_bordes"][-1] == pytest.approx(9.984)
    assert 10 - d["tiempo_bordes"][-1] == pytest.approx(0.016)


def test_figuras_y_celdas_tienen_contrato_legible(visor):
    texto = (SESSION / "index.md").read_text(encoding="utf-8")
    seccion = texto.split("### 6. Leer una captura SDR real", 1)[1].split("## Síntesis visual", 1)[0]
    assert len(re.findall(r"```python\n", seccion)) == 3
    assert [int(n) for n in re.findall(r"\*\*Figura (\d+)\.\*\*", seccion)] == [26, 27, 28, 29]
    assert ".wav" not in seccion.lower()
    for celda in re.findall(r"```python\n(.*?)```", seccion, re.DOTALL):
        for nodo in ast.walk(ast.parse(celda)):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                if nodo.func.attr in {"plot", "set", "subplots", "annotate", "text", "legend", "pcolormesh", "bar", "axvline", "colorbar"}:
                    assert nodo.lineno == nodo.end_lineno

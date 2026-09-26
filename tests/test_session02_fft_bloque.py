"""Verificación de las celdas didácticas publicadas de FFT, ventanas y leakage."""

import ast
import importlib.util
from pathlib import Path
import re

import pytest

np = pytest.importorskip("numpy")
matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "docs/sessions/02-tiempo-frecuencia-iq"


def celdas():
    texto = (SESSION / "index.md").read_text(encoding="utf-8")
    seccion = texto.split("### 5. Qué calcula una FFT de un bloque finito", 1)[1]
    seccion = re.split(r"^### [6-9]\. ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    return re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)


@pytest.fixture(scope="module")
def experimento():
    namespace = {}
    original_show = plt.show
    plt.show = lambda: plt.close("all")
    try:
        for numero, celda in enumerate(celdas(), start=1):
            exec(compile(celda, f"subseccion5-celda{numero}", "exec"), namespace)
    finally:
        plt.show = original_show
        plt.close("all")
    return namespace


def test_ocho_celdas_y_ploteo_en_una_linea():
    assert len(celdas()) == 8
    metodos = {"plot", "stem", "set", "subplots", "annotate", "text", "legend", "axhline", "axvline", "axvspan", "grid", "show"}
    for celda in celdas():
        for nodo in ast.walk(ast.parse(celda)):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                if nodo.func.attr in metodos:
                    assert nodo.lineno == nodo.end_lineno, nodo.func.attr


def test_dft_como_suma_y_orden_de_bins(experimento):
    d = experimento
    productos = d["tono8"] * np.exp(-1j * 2 * np.pi * d["n8"] / 8)
    assert np.sum(productos) == pytest.approx(8)
    np.testing.assert_allclose(np.fft.fft(d["tono8"])[[1, 2]], [8, 0], atol=1e-12)
    np.testing.assert_array_equal(d["f_sin_ordenar"], [0, 1000, 2000, 3000, -4000, -3000, -2000, -1000])
    assert abs(d["C_sin_ordenar"][1]) == pytest.approx(1)
    assert abs(d["C_sin_ordenar"][6]) == pytest.approx(0.5)
    np.testing.assert_array_equal(d["f_ordenado"], np.arange(-4000, 4000, 1000))
    np.testing.assert_allclose(d["C_ordenado"], np.fft.fftshift(d["C_sin_ordenar"]))


def test_coherencia_y_leakage_rectangular(experimento):
    d = experimento
    assert d["T_obs"] == pytest.approx(0.008)
    f, C = d["espectro_bloque"](d["tonos"][1000], d["fs"])
    np.testing.assert_array_equal(f[np.abs(C) > 1e-10], [1000])
    assert np.max(np.abs(C)) == pytest.approx(1)
    f, C = d["espectro_bloque"](d["tonos"][1062.5], d["fs"])
    assert np.count_nonzero(np.abs(C) > 1e-10) == 64
    for frecuencia in [1000, 1125]:
        k = np.flatnonzero(f == frecuencia)[0]
        assert abs(C[k]) == pytest.approx(0.6366836927259824)
    assert np.exp(1j * 2 * np.pi * 1000 * d["T_obs"]) == pytest.approx(1)
    assert np.exp(1j * 2 * np.pi * 1062.5 * d["T_obs"]) == pytest.approx(-1)


def test_padding_conserva_datos_coeficientes_y_escala(experimento):
    d = experimento
    np.testing.assert_array_equal(d["entrada_padded"][:64], d["z_off"])
    np.testing.assert_array_equal(d["entrada_padded"][64:], 0)
    np.testing.assert_allclose(d["C512"][::8], d["C64"], atol=1e-12)
    assert np.diff(d["f64"])[0] == 125
    assert np.diff(d["f512"])[0] == 15.625
    assert d["f512"][np.argmax(np.abs(d["C512"]))] == 1062.5
    assert np.max(np.abs(d["C512"])) == pytest.approx(1)
    with pytest.raises(ValueError):
        d["espectro_bloque"](d["z_off"], 8000, nfft=32)
    with pytest.raises(ValueError):
        d["espectro_bloque"](d["z_off"], 8000, ventana=np.ones(32))


def test_hann_periodica_y_normalizacion(experimento):
    d = experimento
    np.testing.assert_allclose(d["w_hann"], np.hanning(65)[:-1], atol=1e-14)
    assert np.sum(d["w_hann"]) == pytest.approx(32)
    assert np.sum(d["w_rect"]) == 64
    for nombre, desplazamiento in [("C_rect", 125), ("C_hann", 250)]:
        C = d[nombre]
        assert np.max(np.abs(C)) == pytest.approx(1)
        for frecuencia in [1062.5 - desplazamiento, 1062.5 + desplazamiento]:
            k = np.flatnonzero(d["f_win"] == frecuencia)[0]
            assert abs(C[k]) < 1e-12
    np.testing.assert_allclose(d["magnitud_db"](np.array([1, 0.1, 0.01, 0])), [0, -20, -40, -120])


def test_mas_observacion_resuelve_el_par_no_mas_puntos(experimento):
    d = experimento
    f_corto, C_corto = d["resultados_duracion"][64]
    f_largo, C_largo = d["resultados_duracion"][512]
    np.testing.assert_array_equal(f_corto, f_largo)
    for f, C, esperados in [(f_corto, C_corto, [1031.25]), (f_largo, C_largo, [1000, 1062.5])]:
        a = np.abs(C)
        indices = np.flatnonzero((a[1:-1] > a[:-2]) & (a[1:-1] > a[2:])) + 1
        indices = indices[(f[indices] > 850) & (f[indices] < 1250) & (a[indices] > 0.2)]
        np.testing.assert_array_equal(f[indices], esperados)


def test_leakage_del_fuerte_en_frecuencia_del_debil(experimento):
    d = experimento
    esperados = {"Rectangular": (-28.86237994460845, -27.106749776681582), "Hann": (-60.480863520243425, -40.57918977771017)}
    for nombre, (solo, ambos) in esperados.items():
        f, C_fuerte, C_ambos = d["resultados_debil"][nombre]
        k = np.flatnonzero(f == d["f_debil"])[0]
        assert d["magnitud_db"](C_fuerte)[k] == pytest.approx(solo)
        assert d["magnitud_db"](C_ambos)[k] == pytest.approx(ambos)


def test_alias_limpio_y_leakage_son_casos_distintos(experimento):
    d = experimento
    z = np.exp(1j * 2 * np.pi * 5000 * np.arange(64) / 8000)
    f, C = d["espectro_bloque"](z, 8000)
    np.testing.assert_array_equal(f[np.abs(C) > 1e-10], [-3000])


def test_generador_reproduce_siete_figuras(tmp_path):
    path = SESSION / "figures/gen_fft_bloque.py"
    spec = importlib.util.spec_from_file_location("gen_fft_bloque", path)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    paths = modulo.generar(tmp_path)
    assert len(paths) == 7
    for path in paths:
        assert path.parent == tmp_path
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

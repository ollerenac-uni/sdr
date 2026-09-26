"""Comprueba los snippets publicados de aliasing y sus figuras reproducibles."""

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
    seccion = texto.split("### 4. Muestreo y aliasing", 1)[1]
    seccion = re.split(r"^### [5-9]\. ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    return re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)


@pytest.fixture(scope="module")
def experimento():
    namespace = {}
    original = plt.show
    plt.show = lambda: plt.close("all")
    try:
        for numero, celda in enumerate(celdas(), start=1):
            exec(compile(celda, f"celda-{numero}", "exec"), namespace)
    finally:
        plt.show = original
        plt.close("all")
    return namespace


def test_celdas_y_llamadas_de_ploteo_en_una_linea():
    assert len(celdas()) == 7
    for celda in celdas():
        for nodo in ast.walk(ast.parse(celda)):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                if nodo.func.attr in {"plot", "stem", "set", "subplots", "annotate", "text", "legend", "axhline", "axvline", "axvspan", "grid", "show"}:
                    assert nodo.lineno == nodo.end_lineno, nodo.func.attr


def test_equivalencia_real_y_compleja(experimento):
    d = experimento
    np.testing.assert_allclose(d["x1"], d["x9"], atol=1e-12)
    np.testing.assert_allclose(d["z5"], d["z_m3"], atol=1e-12)
    f, C = d["espectro"](d["z5"], 8000)
    assert f[np.argmax(np.abs(C))] == -3000


def test_intervalo_y_aliases(experimento):
    alias = experimento["frecuencia_alias"]
    entradas = np.array([1000, 5000, 7000, 9000, -5000, 4000, -4000, 11000, -6000])
    np.testing.assert_array_equal(alias(entradas, 8000), [1000, -3000, -1000, 1000, 3000, -4000, -4000, 3000, 2000])
    for tasa in [4000, 8000, 12000]:
        f = alias(np.arange(-50000, 50001), tasa)
        assert np.all(f >= -tasa / 2)
        assert np.all(f < tasa / 2)


@pytest.mark.parametrize("tasa,cantidad,pico", [(12000, 96, 3000), (8000, 64, 3000), (4000, 32, -1000)])
def test_cambiar_tasa_mantiene_duracion(experimento, tasa, cantidad, pico):
    assert int(round(experimento["duracion"] * tasa)) == cantidad
    t = np.arange(cantidad) / tasa
    z = np.exp(1j * 2 * np.pi * 3000 * t)
    f, C = experimento["espectro"](z, tasa)
    assert f[np.argmax(np.abs(C))] == pico
    assert abs(C[np.argmax(np.abs(C))]) == pytest.approx(1)


def test_nyquist_real_y_complejo(experimento):
    tn = experimento["tn"]
    np.testing.assert_allclose(np.cos(2 * np.pi * 4000 * tn), (-1.0) ** np.arange(9), atol=1e-12)
    np.testing.assert_allclose(np.cos(2 * np.pi * 4000 * tn + np.pi / 2), 0, atol=1e-12)
    np.testing.assert_allclose(np.abs(np.exp(1j * (2 * np.pi * 4000 * tn + np.pi / 2))), 1, atol=1e-12)


def test_filtrado_antes_de_reducir_tasa(experimento):
    d = experimento
    assert len(d["entrada"]) == 192
    assert len(d["sin_filtro"]) == len(d["con_filtro"]) == 64
    np.testing.assert_allclose(d["sin_filtro"], 1.6 * d["con_filtro"], atol=1e-12)
    for nombre, magnitud in [("sin_filtro", 1.6), ("con_filtro", 1.0)]:
        f, C = d["espectro"](d[nombre], 8000)
        presentes = np.abs(C) > 1e-10
        np.testing.assert_array_equal(f[presentes], [1000])
        np.testing.assert_allclose(np.abs(C[presentes]), [magnitud], atol=1e-12)


def test_generador_reproduce_seis_png(tmp_path):
    path = SESSION / "figures/gen_aliasing.py"
    spec = importlib.util.spec_from_file_location("gen_aliasing", path)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    paths = modulo.generar(tmp_path)
    assert len(paths) == 6
    for png in paths:
        assert png.parent == tmp_path
        assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

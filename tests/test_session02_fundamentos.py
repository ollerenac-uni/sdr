"""Ejecuta las 14 celdas publicadas de las subsecciones 1–3 y verifica sus datos."""

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
PAGINA = ROOT / "docs/sessions/02-tiempo-frecuencia-iq/index.md"


def celdas(numero):
    texto = PAGINA.read_text(encoding="utf-8").split("## Teoría", 1)[1]
    seccion = re.split(rf"^### {numero}\. ", texto, maxsplit=1, flags=re.MULTILINE)[1]
    seccion = re.split(r"^### \d+\. ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    return re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)


@pytest.fixture(scope="module")
def experimentos():
    namespace = {}
    resultados = {}
    original = plt.show
    plt.show = lambda: plt.close("all")
    try:
        for numero in (1, 2, 3):
            for indice, celda in enumerate(celdas(numero), 1):
                exec(compile(celda, f"subseccion{numero}-celda{indice}", "exec"), namespace)
            resultados[numero] = dict(namespace)
    finally:
        plt.show = original
        plt.close("all")
    return resultados


@pytest.mark.parametrize("numero,cantidad", [(1, 4), (2, 5), (3, 5)])
def test_celdas_publicadas_y_ploteo_en_una_linea(numero, cantidad):
    assert len(celdas(numero)) == cantidad
    metodos = {"plot", "stem", "set", "subplots", "annotate", "text", "legend", "axhline", "axvline", "grid", "show"}
    for celda in celdas(numero):
        for nodo in ast.walk(ast.parse(celda)):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                if nodo.func.attr in metodos:
                    assert nodo.lineno == nodo.end_lineno, nodo.func.attr


def test_tiempos_y_muestras_del_tono_real(experimentos):
    d = experimentos[1]
    assert d["N"] == 16
    assert d["N"] / d["fs"] == pytest.approx(0.002)
    assert d["t"][-1] == pytest.approx(0.001875)
    np.testing.assert_allclose(np.diff(d["t"]), 0.000125)
    np.testing.assert_allclose(d["x"][:8], [1, np.sqrt(0.5), 0, -np.sqrt(0.5), -1, -np.sqrt(0.5), 0, np.sqrt(0.5)], atol=1e-12)
    assert d["fs"] / d["f0"] == 8


def test_euler_magnitud_fase_y_sentido_del_giro(experimentos):
    d = experimentos[2]
    assert abs(d["muestra"]) == 5
    assert np.angle(d["muestra"], deg=True) == pytest.approx(53.13010235415598)
    np.testing.assert_allclose(d["z"], np.exp(1j * d["theta"]), atol=1e-12)
    np.testing.assert_allclose(np.abs(d["z"]), 1)
    np.testing.assert_allclose(d["z_pos"].real, d["z_neg"].real)
    np.testing.assert_allclose(d["z_pos"].imag, -d["z_neg"].imag)
    assert np.angle(d["z_pos"][1] / d["z_pos"][0], deg=True) == pytest.approx(45)
    assert np.angle(d["z_neg"][1] / d["z_neg"][0], deg=True) == pytest.approx(-45)
    np.testing.assert_allclose(d["suma"], d["tono_real"], atol=1e-12)


def test_angulos_equivalentes_en_eje_real_negativo():
    angulos = np.angle(np.array([complex(-1, 0.0), complex(-1, -0.0)]), deg=True)
    np.testing.assert_array_equal(angulos, [180, -180])
    np.testing.assert_allclose(np.exp(1j * np.deg2rad(angulos)), [-1, -1], atol=1e-12)


def test_picos_reales_y_complejos_y_linealidad(experimentos):
    d = experimentos[3]
    for nombre, frecuencias, magnitudes in [
        ("x_real", [-1000, 1000], [0.5, 0.5]),
        ("z_pos", [1000], [1]),
        ("z_neg", [-1000], [1]),
        ("z_suma", [-2000, 1000], [0.5, 1]),
    ]:
        f, C = d["espectro"](d[nombre], d["fs"])
        presentes = np.abs(C) > 1e-10
        np.testing.assert_array_equal(f[presentes], frecuencias)
        np.testing.assert_allclose(np.abs(C[presentes]), magnitudes)
    assert d["z_suma"][0] == pytest.approx(1.5)
    np.testing.assert_allclose(d["C_suma"], d["C1"] + d["C2"], atol=1e-12)


def test_magnitud_omite_fase_y_dft_completa_conserva_muestras(experimentos):
    d = experimentos[3]
    np.testing.assert_allclose(np.abs(d["C0"]), np.abs(d["C90"]), atol=1e-12)
    assert not np.allclose(d["x0"], d["x90"])
    for frecuencia, fase in [(-1000, -90), (1000, 90)]:
        indice = np.flatnonzero(d["f"] == frecuencia)[0]
        assert np.angle(d["C90"][indice], deg=True) == pytest.approx(fase)
    np.testing.assert_allclose(d["x_recuperado"], d["x90"], atol=1e-12)
    np.testing.assert_allclose(d["x_sin_fase"], d["x0"], atol=1e-12)
    assert not np.allclose(d["x_sin_fase"], d["x90"])


@pytest.mark.parametrize("script,cantidad", [("gen_muestras_senal.py", 2), ("gen_senales_iq.py", 3), ("gen_tiempo_frecuencia.py", 3)])
def test_generadores_de_fundamentos_reproducen_sus_png(tmp_path, script, cantidad):
    ruta = PAGINA.parent / "figures" / script
    spec = importlib.util.spec_from_file_location(ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    figuras = modulo.generar(tmp_path)
    assert len(figuras) == cantidad
    for png in figuras:
        assert png.parent == tmp_path
        assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

"""Ejecuta las celdas publicadas, comprueba los ejercicios y reproduce las figuras."""

import ast
import importlib.util
from pathlib import Path
import re

import pytest

np = pytest.importorskip("numpy")
signal = pytest.importorskip("scipy.signal")
matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "docs/sessions/03-sistemas-filtros-digitales"


def celdas(pagina):
    return re.findall(r"```python\n(.*?)```", pagina.read_text(encoding="utf-8"), flags=re.DOTALL)


@pytest.fixture(scope="module")
def clase():
    namespace = {}
    original = plt.show
    plt.show = lambda: plt.close("all")
    try:
        for indice, celda in enumerate(celdas(CARPETA / "index.md"), 1):
            exec(compile(celda, f"session03-celda{indice}", "exec"), namespace)
    finally:
        plt.show = original
        plt.close("all")
    return namespace


def test_borrador_y_ejercicios_intercalados():
    texto = (CARPETA / "index.md").read_text(encoding="utf-8")
    assert "status: draft" in texto
    assert texto.count('??? example "Solución explicada"') == 6
    for numero in (1, 2, 3):
        seccion = re.split(rf"^### {numero}\. ", texto, maxsplit=1, flags=re.MULTILINE)[1]
        seccion = re.split(r"^### \d+\. |^## Síntesis", seccion, maxsplit=1, flags=re.MULTILINE)[0]
        assert seccion.count('??? example "Solución explicada"') == 2
        assert "Qué varía" in seccion
        assert "Qué permanece fijo" in seccion
        assert "Qué debe notarse" in seccion
        assert "![" in seccion


@pytest.mark.parametrize("nombre,cantidad", [("index.md", 5), ("laboratorio-filtrado.md", 2)])
def test_celdas_y_lineas_de_ploteo_no_partidas(nombre, cantidad):
    snippets = celdas(CARPETA / nombre)
    assert len(snippets) == cantidad
    metodos = {"plot", "stem", "scatter", "bar", "set", "subplots", "text", "legend", "axvline", "grid", "show"}
    for celda in snippets:
        for nodo in ast.walk(ast.parse(celda)):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute) and nodo.func.attr in metodos:
                assert nodo.lineno == nodo.end_lineno, nodo.func.attr


def test_ganancia_retardo_convolucion_e_impulso(clase):
    np.testing.assert_array_equal(clase["y_ganancia"], [0, 2, 4, 2, 0, -2, 0, 0])
    np.testing.assert_array_equal(clase["y_retardo"], [0, 0, 0, 1, 2, 1, 0, -1])
    np.testing.assert_allclose(clase["contribuciones"], [1, 2, 1])
    np.testing.assert_allclose(clase["y_fir"], [0, 0, 1, 3, 4, 3, 1, 0, 0, 0])
    np.testing.assert_allclose(clase["respuesta"], [1/3, 1/3, 1/3, 0, 0, 0, 0, 0])


def test_ganancias_fft_cutoff_y_fase(clase):
    d = clase
    assert d["fs"] == 24000
    assert len(d["x_estable"]) == d["N"] == 4800
    assert d["N"] / d["fs"] == pytest.approx(0.2)
    indices = [np.flatnonzero(d["f"] == f0)[0] for f0 in (1000, 9000)]
    np.testing.assert_allclose(d["X"][indices], [1, 0.6], atol=1e-12)
    np.testing.assert_allclose(np.abs(d["H_tonos"]), [0.9772838842, 0.1380711875], atol=1e-10)
    np.testing.assert_allclose(np.abs(d["H_lp_tonos"]), [1.002660843, 0.000387155659], atol=1e-9)
    for espectro, H in [(d["Y_media"], d["H_tonos"]), (d["Y_lp"], d["H_lp_tonos"])]:
        np.testing.assert_allclose(espectro[indices], np.array([1, 0.6]) * np.abs(H), atol=1e-12)
        fuera = np.delete(espectro, indices)
        assert np.max(fuera) < 1e-12
    _, H_corte = signal.freqz(d["h_lp"], worN=np.array([3000]), fs=d["fs"])
    assert abs(H_corte[0]) == pytest.approx(0.5, abs=0.003)
    # También se comprueba la fase, aunque las figuras solo muestren magnitud.
    for h, y in [(d["h_media"], d["y_estable"]), (d["h_lp"], d["y_lp"][d["descarte"]:])]:
        _, H = signal.freqz(h, worN=np.array([1000, 9000]), fs=d["fs"])
        esperada = H[0] * np.exp(1j * 2 * np.pi * 1000 * d["n"] / d["fs"]) + 0.6 * H[1] * np.exp(1j * 2 * np.pi * 9000 * d["n"] / d["fs"])
        np.testing.assert_allclose(y, esperada[d["descarte"]:], atol=3e-12)


def test_soluciones_numericas_y_filtrado_iq():
    assert 3 * (1 - 2j) == 3 - 6j
    assert 2 / 8000 == pytest.approx(0.00025)
    np.testing.assert_array_equal(np.concatenate([np.zeros(2), [1, 2, -1]]), [0, 0, 1, 2, -1])
    np.testing.assert_allclose(np.convolve([3, 6, 3], np.ones(3)/3), [1, 3, 4, 3, 1])
    z, h = np.array([1+1j, 1-1j]), np.array([0.5, 0.5])
    y = np.convolve(z, h)
    np.testing.assert_allclose(y, [0.5+0.5j, 1, 0.5-0.5j])
    np.testing.assert_allclose(y, np.convolve(z.real, h) + 1j * np.convolve(z.imag, h))
    np.testing.assert_allclose(np.array([1, 0.6]) * [0.98, 0.02], [0.98, 0.012])


def test_celdas_laboratorio_y_niveles_db():
    namespace = {}
    for indice, celda in enumerate(celdas(CARPETA / "laboratorio-filtrado.md"), 1):
        exec(compile(celda, f"lab03-celda{indice}", "exec"), namespace)
    np.testing.assert_allclose(namespace["y_completa"], [1, 3, 4, 3, 1])
    np.testing.assert_allclose(namespace["y_stream"], [1, 3, 4])
    np.testing.assert_allclose(namespace["y_con_cola"], namespace["y_completa"])
    np.testing.assert_allclose(namespace["prediccion"], namespace["Y"][namespace["indices"]], atol=1e-12)
    for h, esperado in [(np.ones(3)/3, [-0.20, -17.20]), (signal.firwin(65, 3000, fs=24000), [0.023, -68.24])]:
        _, H = signal.freqz(h, worN=np.array([1000, 9000]), fs=24000)
        np.testing.assert_allclose(20*np.log10(np.abs(H)), esperado, atol=0.01)


def test_generador_reproduce_seis_figuras(tmp_path):
    ruta = CARPETA / "figures/gen_sistemas_filtros.py"
    spec = importlib.util.spec_from_file_location(ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    figuras = modulo.generar(tmp_path)
    assert len(figuras) == 6
    for png in figuras:
        assert png.parent == tmp_path
        assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

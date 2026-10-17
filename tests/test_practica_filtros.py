"""Comprueba las celdas y figuras de la práctica opcional de filtros FIR."""

import ast
import importlib.util
from pathlib import Path
import re

import pytest

np = pytest.importorskip("numpy")
signal = pytest.importorskip("scipy.signal")
matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "docs/sessions/03-sistemas-filtros-digitales"


def celdas(pagina):
    return re.findall(r"```python\n(.*?)```", pagina.read_text(encoding="utf-8"), flags=re.DOTALL)


def test_celdas_y_lineas_de_ploteo_no_partidas():
    snippets = celdas(CARPETA / "laboratorio-filtrado.md")
    assert len(snippets) == 2
    metodos = {"plot", "stem", "scatter", "bar", "set", "subplots", "text", "legend", "axvline", "grid", "show"}
    for celda in snippets:
        for nodo in ast.walk(ast.parse(celda)):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute) and nodo.func.attr in metodos:
                assert nodo.lineno == nodo.end_lineno, nodo.func.attr


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

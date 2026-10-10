"""Regresiones de la lectura geométrica de 5.2–5.4, sin copiar sus celdas."""

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
TEXTO = (SESSION / "index.md").read_text(encoding="utf-8")
APARTADOS = {
    n: TEXTO.split(f"#### 5.{n}.", 1)[1].split(f"#### 5.{n + 1}.", 1)[0]
    for n in (2, 3, 4)
}


@pytest.fixture(scope="module")
def apartados():
    """Cada apartado comienza vacío; conserva sus figuras para inspeccionar ejes."""
    resultados = {}
    original = plt.show
    try:
        for n, texto in APARTADOS.items():
            namespace, figuras = {}, []
            plt.show = lambda: figuras.append(plt.gcf())
            for celda in re.findall(r"```python\n(.*?)```", texto, flags=re.S):
                exec(compile(celda, f"apartado-5.{n}", "exec"), namespace)
            resultados[n] = (namespace, figuras)
        yield resultados
    finally:
        plt.show = original
        plt.close("all")


def test_celdas_independientes_y_sin_herramientas_anticipadas(apartados):
    assert [len(apartados[n][1]) for n in (2, 3, 4)] == [3, 1, 1]
    for n, (namespace, _) in apartados.items():
        assert "espectro_bloque" not in namespace
        assert "magnitud_db" not in namespace
        for celda in re.findall(r"```python\n(.*?)```", APARTADOS[n], flags=re.S):
            for nodo in ast.walk(ast.parse(celda)):
                if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                    if nodo.func.attr in {"plot", "stem", "quiver", "annotate", "set", "text", "legend", "subplots", "vlines"}:
                        assert nodo.lineno == nodo.end_lineno


def test_cada_suma_usa_todas_las_flechas_y_no_la_longitud_del_recorrido(apartados):
    d = apartados[2][0]
    for nombre, productos, esperado in [
        ("camino_bin1", d["productos_bin1"], 8),
        ("camino_bin2", d["productos_bin2"], 0),
        ("camino_intermedio", d["productos_intermedio"], 5.125830895483011),
    ]:
        camino = d[nombre]
        assert len(camino) == 9
        np.testing.assert_allclose(np.diff(camino), productos, atol=1e-12)
        assert np.sum(np.abs(np.diff(camino))) == pytest.approx(8)
        assert abs(camino[-1]) == pytest.approx(esperado, abs=1e-12)
    assert abs(d["camino_intermedio"][-1]) / 8 == pytest.approx(0.6407288619353766)
    assert d["productos_intermedio"][-1] == pytest.approx(np.exp(1j * np.deg2rad(157.5)))
    assert 360 * 1000 / 8000 == 45
    assert 360 * 1500 / 8000 == 67.5
    assert 360 * (1500 - 1000) / 8000 == 22.5
    assert (1500 - 1000) * (8 / 8000) == 0.5


def test_misma_escala_en_los_diagramas_comparados(apartados):
    figuras = apartados[2][1]
    entrada_y_productos = [figuras[0].axes[i] for i in (0, 2, 4)]
    sumas = [figuras[0].axes[i] for i in (3, 5)] + [figuras[2].axes[2]]
    grupos = [entrada_y_productos, sumas, figuras[2].axes[:2], apartados[4][1][0].axes[:4]]
    for grupo in grupos:
        for ax in grupo:
            assert ax.get_xlim() == grupo[0].get_xlim()
            assert ax.get_ylim() == grupo[0].get_ylim()
            assert ax.get_aspect() == 1


def test_bin6_y_fftshift_solo_reordenan(apartados):
    d = apartados[3][0]
    np.testing.assert_allclose(d["z8"], np.exp(1j * 2 * np.pi * 6000 * np.arange(8) / 8000), atol=1e-12)
    assert 360 * 6000 / 8000 == 270
    assert 360 * -2000 / 8000 == -90
    assert np.argmax(np.abs(d["C_sin_ordenar"])) == 6
    assert d["f_ordenado"][np.argmax(np.abs(d["C_ordenado"]))] == -2000
    np.testing.assert_allclose(np.fft.ifftshift(d["C_ordenado"]), d["C_sin_ordenar"])


def test_cuatro_pruebas_coinciden_con_las_barras(apartados):
    d = apartados[4][0]
    assert d["T_obs"] == 0.008
    assert np.diff(d["frecuencias"])[0] == 125
    np.testing.assert_allclose(d["vueltas_sobrantes"], [1.5, 0.5, -0.5, -1.5])
    np.testing.assert_allclose(d["barras_pruebas"], [0.21239845973980115, 0.6366836927259824, 0.6366836927259824, 0.21239845973980115])
    assert abs(d["sumas_pruebas"][0]) == pytest.approx(13.593501423347274)
    assert abs(d["sumas_pruebas"][1]) == pytest.approx(40.74775633446287)
    for prueba, barra in zip(d["pruebas"], d["barras_pruebas"]):
        k = np.flatnonzero(d["frecuencias"] == prueba)[0]
        assert abs(d["C_leakage"][k]) == pytest.approx(barra)
    assert np.count_nonzero(np.abs(d["C_leakage"]) > 1e-12) == 64
    assert np.exp(2j * np.pi * 1000 * d["T_obs"]) == pytest.approx(1)
    assert np.exp(2j * np.pi * 1062.5 * d["T_obs"]) == pytest.approx(-1)


def test_tabla_condicionada_y_excepciones_comprobadas():
    N = 64
    n = np.arange(N)
    def barra(v, w):
        return abs(np.sum(w * np.exp(2j * np.pi * v * n / N))) / np.sum(w)

    rectangular = np.ones(N)
    assert barra(0, rectangular) == pytest.approx(1)
    for v in range(1, N):
        assert barra(v, rectangular) == pytest.approx(0, abs=2e-14)
        assert barra(-v, rectangular) == pytest.approx(0, abs=2e-14)
    assert barra(0.5, rectangular) == pytest.approx(0.6366836927259824)
    assert round(barra(0.5, rectangular), 2) == 0.64
    assert barra(64, rectangular) == pytest.approx(1)
    hann = 0.5 - 0.5 * np.cos(2 * np.pi * n / N)
    assert barra(1, hann) == pytest.approx(0.5)
    assert barra(1.5, rectangular) > barra(1, rectangular)
    visible = APARTADOS[4].split('??? note "Para profundizar"', 1)[0]
    assert r"con ventana rectangular y $|\text{vueltas}|<N$" in visible
    assert "| 0 | 1 |" in visible
    assert "| Enteras distintas de cero | 0 |" in visible
    assert "| 0.5 | ≈0.64" in visible


def test_notacion_despues_de_las_figuras_y_guias_antes_de_cada_figura():
    assert APARTADOS[2].index("La misma operación escrita con símbolos") > APARTADOS[2].index("**Figura 17.")
    for texto in APARTADOS.values():
        for imagen in re.finditer(r"^!\[.*?\]\(figures/.*?\)", texto, flags=re.M):
            antes = texto[:imagen.start()].rstrip().split("\n")[-1]
            assert antes.startswith("**") and antes.endswith("**")
        for texto_corto in re.findall(r"^\*\*(?:Figura \d+\.\*\* .+|[^*\n]+\*\*)$", texto, flags=re.M):
            sin_formula = re.sub(r"\$[^$]+\$", "símbolo", texto_corto)
            for frase in re.split(r"[.!?](?:\s+|$)", sin_formula):
                assert len(frase.split()) <= 25, frase


def test_generador_etapa_a_no_modifica_figuras_posteriores(tmp_path):
    path = SESSION / "figures/gen_fft_bloque.py"
    spec = importlib.util.spec_from_file_location("gen_fft_etapa_a", path)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    paths = modulo.generar(tmp_path, solo_etapa_a=True)
    assert [p.name for p in paths] == modulo.NOMBRES[:5]
    assert len(list(tmp_path.glob("*.png"))) == 5
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in paths)

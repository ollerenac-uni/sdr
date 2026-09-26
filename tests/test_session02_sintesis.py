"""Verifica los datos y el contrato visual de las láminas de síntesis."""

import ast
import importlib.util
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("matplotlib")


ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "docs/sessions/02-tiempo-frecuencia-iq"
SCRIPT = SESSION / "figures/gen_sintesis.py"


@pytest.fixture(scope="module")
def modulo():
    spec = importlib.util.spec_from_file_location("gen_sintesis", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_muestras_tiempo_iq_y_fft_real_compleja(modulo):
    d = modulo.datos_muestras()
    assert len(d["z"]) == 16
    np.testing.assert_allclose(np.diff(d["t"]), 0.000125)
    assert d["t"][-1] * 1000 == pytest.approx(1.875)
    assert len(d["z"]) / d["fs"] * 1000 == 2
    assert np.angle(d["z"][1] * np.conj(d["z"][0])) == pytest.approx(np.pi / 4)
    np.testing.assert_allclose(np.abs(d["z"]), 1)
    np.testing.assert_allclose(d["z"][8], d["z"][0], atol=1e-12)
    for nombre, frecuencias, magnitudes in [("complejo", [1000], [1]), ("real", [-1000, 1000], [0.5, 0.5])]:
        f, C = d[nombre]
        presentes = np.abs(C) > 1e-10
        np.testing.assert_array_equal(f[presentes], frecuencias)
        np.testing.assert_allclose(np.abs(C[presentes]), magnitudes)


def test_aliasing_y_leakage_reproducen_los_ejemplos(modulo):
    d = modulo.datos_ambiguedad()
    np.testing.assert_allclose(d["z5"], d["zm3"], atol=1e-12)
    f, C = modulo.espectro(d["z5"], d["fs"])
    np.testing.assert_array_equal(f[np.abs(C) > 1e-10], [-3000])
    f, C = d["leakage"]
    assert len(C) == 64
    assert np.diff(f)[0] == 125
    for frecuencia in [1000, 1125]:
        k = np.flatnonzero(f == frecuencia)[0]
        assert abs(C[k]) == pytest.approx(0.6366836927259824)


def test_padding_conserva_el_bloque_y_los_bins_originales(modulo):
    d = modulo.datos_fft()
    f64, C64 = d["sin_padding"]
    f512, C512 = d["con_padding"]
    assert len(d["z"]) == 64
    assert len(d["z"]) / d["fs"] == 0.008
    assert np.diff(f64)[0] == 125
    assert np.diff(f512)[0] == 15.625
    np.testing.assert_allclose(C512[::8], C64, atol=1e-12)
    assert f512[np.argmax(np.abs(C512))] == 1062.5
    assert np.max(np.abs(C512)) == pytest.approx(1)


def test_ventanas_mismo_n_m_y_diferente_main_lobe(modulo):
    d = modulo.datos_fft()
    f_rect, C_rect = d["rectangular"]
    f_hann, C_hann = d["hann"]
    np.testing.assert_array_equal(f_rect, f_hann)
    assert len(f_rect) == 4096
    assert len(modulo.hann(64)) == len(d["z"])
    assert np.sum(modulo.hann(64)) == pytest.approx(32)
    for C, semiancho in [(C_rect, 125), (C_hann, 250)]:
        assert np.max(np.abs(C)) == pytest.approx(1)
        for frecuencia in [1062.5 - semiancho, 1062.5 + semiancho]:
            k = np.flatnonzero(f_rect == frecuencia)[0]
            assert abs(C[k]) < 1e-12


def test_mas_datos_separa_dos_tonos_con_la_misma_rejilla(modulo):
    d = modulo.datos_fft()
    np.testing.assert_array_equal(d["pares"][64][0], d["pares"][512][0])
    for n, esperadas in [(64, [1031.25]), (512, [1000, 1062.5])]:
        f, C = d["pares"][n]
        a = np.abs(C)
        maximos = np.flatnonzero((a[1:-1] > a[:-2]) & (a[1:-1] > a[2:])) + 1
        maximos = maximos[(f[maximos] > 850) & (f[maximos] < 1250) & (a[maximos] > 0.2)]
        np.testing.assert_array_equal(f[maximos], esperadas)


def test_rf_y_mezcla_coherentes_con_la_referencia(modulo):
    d = modulo.datos_rf()
    f, C = d["entrada"]
    presentes = np.abs(C) > 1e-10
    np.testing.assert_array_equal(f[presentes], [-600000, 0, 400000])
    np.testing.assert_allclose((d["fc"] + f[presentes]) / 1e6, [98.5, 99.1, 99.5])
    f_salida, C_salida = d["salida"]
    presentes = np.abs(C_salida) > 1e-10
    np.testing.assert_array_equal(f_salida[presentes], [-1000000, -400000, 0])
    np.testing.assert_allclose((d["fc_nuevo"] + f_salida[presentes]) / 1e6, [98.5, 99.1, 99.5])
    np.testing.assert_allclose(np.abs(C_salida[presentes]), [0.6, 0.4, 1])
    np.testing.assert_allclose(np.abs(d["y"]), np.abs(d["x"]), atol=1e-12)
    assert not np.allclose(d["y"], d["x"])


def test_laminas_con_lectura_itemizada_y_enlace_independiente(modulo):
    texto = (SESSION / "index.md").read_text(encoding="utf-8").split("## Síntesis visual", 1)[1]
    assert texto.count('target="_blank"') == 4
    for numero, nombre in zip(range(28, 32), modulo.NOMBRES):
        assert f"](figures/{nombre})" in texto
        despues = texto.split(f"**Figura {numero}.**", 1)[1].split("\n", 1)[1]
        assert despues.lstrip().startswith("- **A1. Panel A"), numero
        assert (SESSION / "figures" / nombre).is_file()
    assert "**D1. Panel D — aquí la entrada es otra:**" in texto


def test_ploteos_sin_lineas_partidas():
    metodos = {"plot", "stem", "set", "subplots", "annotate", "text", "legend", "axhline", "axvline", "axvspan", "grid", "show", "setp", "savefig"}
    for nodo in ast.walk(ast.parse(SCRIPT.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute) and nodo.func.attr in metodos:
            assert nodo.lineno == nodo.end_lineno, nodo.func.attr


def test_generador_reproduce_cuatro_png_sin_archivo_iq(modulo, tmp_path):
    paths = modulo.generar(tmp_path)
    assert [path.name for path in paths] == modulo.NOMBRES
    for path in paths:
        assert path.parent == tmp_path
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

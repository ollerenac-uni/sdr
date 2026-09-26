"""Comprueba los snippets de baseband/RF, mezcla y lectura raw de la sesión 02."""

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
CAPTURA = ROOT / "samples/fm_99p1MHz_2p4Msps_g30.cu8"


def celdas():
    texto = (SESSION / "index.md").read_text(encoding="utf-8")
    seccion = texto.split("### 6. De baseband a RF: interpretar una captura SDR", 1)[1]
    seccion = re.split(r"^## ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    return re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)


@pytest.fixture(scope="module")
def experimento():
    namespace = {}
    original_show = plt.show
    plt.show = lambda: plt.close("all")
    try:
        for numero, celda in enumerate(celdas()[:-1], start=1):
            exec(compile(celda, f"subseccion6-celda{numero}", "exec"), namespace)
    finally:
        plt.show = original_show
        plt.close("all")
    return namespace


@pytest.fixture
def raw_prueba(tmp_path):
    """Bytes extremos y centrales para detectar una resta unsigned incorrecta."""
    pares = np.tile(np.array([[0, 255], [127, 128], [255, 0], [128, 127]], dtype=np.uint8), (4096, 1))
    path = tmp_path / "prueba.cu8"
    path.write_bytes(pares.tobytes())
    return path, pares


def ejecutar_captura(experimento, ruta):
    namespace = dict(experimento, ruta_captura=ruta)
    original_show = plt.show
    plt.show = lambda: plt.close("all")
    try:
        exec(compile(celdas()[-1], "subseccion6-captura", "exec"), namespace)
    finally:
        plt.show = original_show
        plt.close("all")
    return namespace


def generador():
    spec = importlib.util.spec_from_file_location("gen_baseband_rf", SESSION / "figures/gen_baseband_rf.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_siete_celdas_y_ploteo_sin_lineas_partidas():
    assert len(celdas()) == 7
    metodos = {"plot", "stem", "set", "subplots", "annotate", "text", "legend", "axhline", "axvline", "axvspan", "grid", "show"}
    for celda in celdas():
        for nodo in ast.walk(ast.parse(celda)):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute) and nodo.func.attr in metodos:
                assert nodo.lineno == nodo.end_lineno, nodo.func.attr


def test_mapeo_baseband_rf_y_amplitudes(experimento):
    d = experimento
    presentes = np.abs(d["C_entrada"]) > 1e-10
    np.testing.assert_array_equal(d["f_bb"][presentes], [-600000, 0, 400000])
    np.testing.assert_allclose(np.abs(d["C_entrada"][presentes]), [0.6, 0.4, 1])
    np.testing.assert_allclose((d["fc"] + d["f_bb"][presentes]) / 1e6, [98.5, 99.1, 99.5])
    assert d["N"] / d["fs"] == pytest.approx(0.001)
    assert d["fs"] / d["N"] == 1000
    assert d["f_bb"][0] == -1200000
    assert d["f_bb"][-1] == 1199000


def test_mezcla_desplaza_toda_la_entrada_y_conserva_magnitud(experimento):
    d = experimento
    presentes = np.abs(d["C_salida"]) > 1e-10
    np.testing.assert_array_equal(d["f_salida"][presentes], [-1000000, -400000, 0])
    np.testing.assert_allclose(np.abs(d["C_salida"][presentes]), [0.6, 0.4, 1])
    np.testing.assert_allclose(np.abs(d["y"]), np.abs(d["x"]), atol=1e-12)
    assert not np.allclose(d["y"], d["x"])
    np.testing.assert_allclose(d["C_salida"], np.roll(d["C_entrada"], -400), atol=1e-12)
    np.testing.assert_allclose(d["objetivo_centrado"], 1, atol=1e-12)


def test_signo_opuesto_y_fase_constante(experimento):
    d = experimento
    f, C = d["espectro_iq"](d["objetivo"] * np.conj(d["oscilador"]), d["fs"])
    assert f[np.argmax(np.abs(C))] == 800000
    fase = 0.7
    centrado = d["objetivo"] * np.exp(1j * fase) * d["oscilador"]
    np.testing.assert_allclose(centrado, np.exp(1j * fase), atol=1e-12)


def test_referencia_nueva_no_cambia_rf_de_los_tonos(experimento):
    d = experimento
    assert d["fc_nuevo"] == 99500000
    rf_original = d["fc"] + d["frecuencias_bb"]
    rf_correcta = d["fc_nuevo"] + d["frecuencias_bb"] + d["f_mix"]
    rf_falsa = d["fc_nuevo"] + d["frecuencias_bb"]
    np.testing.assert_allclose(rf_correcta, rf_original)
    np.testing.assert_allclose(rf_falsa / 1e6, [98.9, 99.5, 99.9])
    np.testing.assert_array_equal(d["casos_eje"][0][1], d["casos_eje"][1][1])


def test_coseno_real_produce_dos_copias(experimento):
    d = experimento
    for f, C, frecuencias, magnitudes in [
        (d["f_compleja"], d["C_compleja"], [0], [1]),
        (d["f_coseno"], d["C_coseno"], [0, 800000], [0.5, 0.5]),
    ]:
        presentes = np.abs(C) > 1e-10
        np.testing.assert_array_equal(f[presentes], frecuencias)
        np.testing.assert_allclose(np.abs(C[presentes]), magnitudes)


def test_cruce_del_borde_y_reversibilidad(experimento):
    d = experimento
    f, C = d["espectro_iq"](d["salida_borde"], d["fs_borde"])
    np.testing.assert_array_equal(f[np.abs(C) > 1e-10], [-3000])
    np.testing.assert_allclose(d["recuperada"], d["entrada_borde"], atol=1e-12)


def test_lectura_cu8_y_escala_de_un_bloque(experimento, raw_prueba):
    path, pares = raw_prueba
    d = ejecutar_captura(experimento, path)
    esperada = ((pares[:, 0].astype(float) - 127.5) + 1j * (pares[:, 1].astype(float) - 127.5)) / 127.5
    np.testing.assert_allclose(d["z_captura"], esperada)
    assert d["z_captura"][0] == -1 + 1j
    assert len(d["z_captura"]) == 16384
    assert d["N_captura"] / d["fs_captura"] * 1000 == pytest.approx(6.826666666666667)
    assert np.diff(d["f_captura"])[0] == 146.484375
    assert np.sum(d["w_captura"]) == pytest.approx(8192)
    assert np.max(d["db_captura"]) == pytest.approx(0)
    assert np.isfinite(d["db_captura"]).all()


def test_archivo_ausente_o_incompleto_da_error_claro(experimento, tmp_path):
    with pytest.raises(FileNotFoundError, match="Falta la grabación"):
        ejecutar_captura(experimento, tmp_path / "ausente.cu8")
    corto = tmp_path / "corto.cu8"
    corto.write_bytes(bytes([0, 255, 127]))
    with pytest.raises(ValueError, match="bloque completo"):
        ejecutar_captura(experimento, corto)


def test_generador_sintetico_no_requiere_grabacion(tmp_path):
    modulo = generador()
    paths = modulo.generar(tmp_path, captura=tmp_path / "ausente.cu8", incluir_captura=False)
    assert len(paths) == 5
    for path in paths:
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_generador_completo_reproduce_seis_figuras(tmp_path, raw_prueba):
    path, _ = raw_prueba
    paths = generador().generar(tmp_path / "figuras", captura=path)
    assert len(paths) == 6
    for path in paths:
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_grabacion_oficial_si_esta_disponible(experimento):
    if not CAPTURA.is_file():
        pytest.skip("La grabación oficial se distribuye por Drive, no por Git")
    d = ejecutar_captura(experimento, CAPTURA)
    assert len(d["crudo"]) == 32768
    assert np.max(d["db_captura"]) == pytest.approx(0)
    assert d["fc_captura"] == 99100000


def test_figuras_nuevas_tienen_lectura_itemizada():
    texto = (SESSION / "index.md").read_text(encoding="utf-8")
    for numero in range(22, 28):
        despues = texto.split(f"**Figura {numero}.**", 1)[1].split("\n", 1)[1]
        assert despues.lstrip().startswith("- **"), numero

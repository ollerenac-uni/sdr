"""Ubicación, soluciones desplegables y cálculos de los ejercicios por tema."""

from pathlib import Path
import re

import pytest

np = pytest.importorskip("numpy")


ROOT = Path(__file__).resolve().parents[1]
PAGINA = ROOT / "docs/sessions/02-tiempo-frecuencia-iq/index.md"


def teoria():
    return PAGINA.read_text(encoding="utf-8").split("## Teoría", 1)[1].split("## Síntesis visual", 1)[0]


def ejercicio(identificador):
    texto = teoria().split(f"##### Ejercicio {identificador} —", 1)[1]
    return re.split(r"^#{3,5} ", texto, maxsplit=1, flags=re.MULTILINE)[0]


@pytest.mark.parametrize("numero", range(1, 7))
def test_cada_subseccion_termina_con_cuatro_ejercicios_y_soluciones(numero):
    seccion = re.split(rf"^### {numero}\. ", teoria(), maxsplit=1, flags=re.MULTILINE)[1]
    seccion = re.split(r"^### \d+\. ", seccion, maxsplit=1, flags=re.MULTILINE)[0]
    assert "Ejercicios de refuerzo" in seccion
    grupo = seccion.split("Ejercicios de refuerzo", 1)[1]
    ids = re.findall(r"^##### Ejercicio (\d+[A-D]) —", grupo, flags=re.MULTILINE)
    assert ids == [f"{numero}{letra}" for letra in "ABCD"]
    for identificador in ids:
        contenido = ejercicio(identificador)
        marcador = f'??? example "Solución del ejercicio {identificador}"'
        assert contenido.count(marcador) == 1
        enunciado, solucion = contenido.split(marcador)
        assert re.search(r"^- ", enunciado, flags=re.MULTILINE)
        assert solucion.lstrip().startswith("- **")
        lineas = [linea for linea in solucion.splitlines() if linea.strip()]
        assert all(linea.startswith("    - **") for linea in lineas)
    assert not re.search(r"^#### (?!.*Ejercicios de refuerzo)", grupo, flags=re.MULTILINE)


def test_sin_grupo_de_ejercicios_acumulado_despues_de_la_sintesis():
    texto = PAGINA.read_text(encoding="utf-8")
    assert len(re.findall(r"^##### Ejercicio \d+[A-D] —", texto, flags=re.MULTILINE)) == 24
    assert "##### Ejercicio" not in texto.split("## Síntesis visual", 1)[1]


@pytest.mark.parametrize("identificador", [f"{numero}{letra}" for numero in range(1, 7) for letra in "ABCD"])
def test_soluciones_explican_su_base_teorica_y_desarrollo_en_items(identificador):
    marcador = f'??? example "Solución del ejercicio {identificador}"'
    solucion = ejercicio(identificador).split(marcador, 1)[1]
    items = re.findall(r"^    - \*\*(.+?)\*\* (.+)$", solucion, flags=re.MULTILINE)
    assert items[0][0] == "Punto de partida:"
    assert re.search(r"(?:apartados?|subsección) \d", items[0][1], flags=re.IGNORECASE)
    assert len(items) >= 5
    assert any(titulo.startswith(("Paso ", "Panel")) for titulo, _ in items)
    assert "$" in items[0][1]
    assert any("$" in contenido for _, contenido in items[1:])


def test_calculos_de_tiempo_y_tono():
    assert 1 / 20000 * 1e6 == 50
    assert 400 / 20000 * 1000 == 20
    assert 399 / 20000 * 1000 == pytest.approx(19.95)
    assert 50 / 20000 * 1000 == 2.5
    assert "19.95" in ejercicio("1A")
    x = 0.8 * np.cos(2 * np.pi * 1000 * np.array([0, 2]) / 8000 + np.pi / 2)
    np.testing.assert_allclose(x, [0, -0.8], atol=1e-12)
    assert "x[2]=-0.8" in ejercicio("1B")
    assert 32 / 8000 * 1000 == 4
    assert 32 / 16000 * 1000 == 2
    assert 16000 / 8 == 2000
    assert "16000/8=2000" in ejercicio("1C")


def test_comprobaciones_de_limites_temporales_y_cambios_de_parametros():
    assert 400 / 20000 - 399 / 20000 == pytest.approx(1 / 20000)
    assert 40 / 8000 - 39 / 8000 == pytest.approx(1 / 8000)
    assert 39 / 8000 * 1000 == pytest.approx(4.875)
    n = np.arange(16)
    referencia = np.cos(2 * np.pi * 1000 * n / 8000)
    menor_amplitud = 0.5 * np.cos(2 * np.pi * 1000 * n / 8000)
    np.testing.assert_allclose(menor_amplitud, 0.5 * referencia)
    assert 8000 / 2000 == 4
    assert 0.5 * np.sin(2 * np.pi * 500 * 4 / 8000) == pytest.approx(0.5)
    assert 1 + 0.5 * np.exp(1j * np.pi) == pytest.approx(0.5)


def test_calculos_iq_y_giro():
    z = -3 + 4j
    assert abs(z) == 5
    assert np.angle(z, deg=True) == pytest.approx(126.86989764584402)
    assert "126.87" in ejercicio("2A")
    tono = 0.5 * np.exp(1j * (-2 * np.pi * 1000 * np.arange(2) / 8000 + np.pi / 4))
    np.testing.assert_allclose(tono, [np.sqrt(0.125) * (1 + 1j), 0.5], atol=1e-12)
    assert np.angle(tono[1] / tono[0], deg=True) == pytest.approx(-45)
    assert "-45" in ejercicio("2B")
    assert 40 / 8000 * 1000 == 5
    assert "40/8000=5" in ejercicio("2C")


def test_espectros_y_fases_de_los_ejercicios():
    t = np.arange(64) / 8000
    f = np.fft.fftfreq(64, d=1 / 8000)
    z = 0.8 * np.exp(1j * 2 * np.pi * 1000 * t) + 0.3 * np.exp(-1j * 2 * np.pi * 2000 * t)
    C = np.fft.fft(z) / 64
    presentes = np.abs(C) > 1e-10
    np.testing.assert_array_equal(f[presentes], [1000, -2000])
    np.testing.assert_allclose(np.abs(C[presentes]), [0.8, 0.3])
    assert 2 + np.exp(1j * np.pi) == pytest.approx(1)
    assert 1 + np.exp(1j * np.pi) == pytest.approx(0)
    assert "2-1=1" in ejercicio("3B")
    C0 = np.fft.fft(np.cos(2 * np.pi * 1000 * t)) / 64
    C90 = np.fft.fft(np.cos(2 * np.pi * 1000 * t + np.pi / 2)) / 64
    np.testing.assert_allclose(np.abs(C0), np.abs(C90), atol=1e-12)
    indices = [np.flatnonzero(f == frecuencia)[0] for frecuencia in [1000, -1000]]
    np.testing.assert_allclose(np.angle(C90[indices]), [np.pi / 2, -np.pi / 2], atol=1e-12)


def test_representantes_y_equivalencia_muestra_por_muestra():
    frecuencias = np.array([13000, -10000, 4000])
    representantes = ((frecuencias + 4000) % 8000) - 4000
    np.testing.assert_array_equal(representantes, [-3000, -2000, -4000])
    assert "13-2(8)=-3" in ejercicio("4A")
    n = np.arange(128)
    z7 = np.exp(1j * 2 * np.pi * 7000 * n / 8000)
    zm1 = np.exp(-1j * 2 * np.pi * 1000 * n / 8000)
    np.testing.assert_allclose(z7, zm1, atol=1e-12)
    assert z7[1] == pytest.approx(np.sqrt(0.5) * (1 - 1j))
    assert "0.7071-j0.7071" in ejercicio("4B")


def test_reduccion_de_tasa_y_caso_nyquist():
    n = np.arange(192)
    z = np.exp(1j * 2 * np.pi * 1000 * n / 24000) + 0.4 * np.exp(1j * 2 * np.pi * 9000 * n / 24000)
    salida = z[::3]
    m = np.arange(len(salida))
    np.testing.assert_allclose(salida, 1.4 * np.exp(1j * 2 * np.pi * 1000 * m / 8000), atol=1e-12)
    assert "magnitud 1.4" in ejercicio("4C")
    np.testing.assert_allclose(np.cos(np.pi * m), (-1.0) ** m, atol=1e-12)
    np.testing.assert_allclose(np.cos(np.pi * m + np.pi / 2), 0, atol=1e-12)
    np.testing.assert_allclose(np.abs(np.exp(1j * (np.pi * m + 0.7))), 1)


def test_datos_padding_coherencia_y_ventana():
    assert 960 / 48000 * 1000 == 20
    assert 3840 - 960 == 2880
    assert 48000 / 960 == 50
    assert 48000 / 3840 == 12.5
    assert "3840-960=2880" in ejercicio("5A")
    assert 1125 * 64 / 8000 == 9
    assert 1100 * 64 / 8000 == pytest.approx(8.8)
    n = np.arange(64)
    x = np.exp(1j * 2 * np.pi * 1125 * n / 8000)
    C = np.fft.fft(x) / 64
    np.testing.assert_array_equal(np.flatnonzero(np.abs(C) > 1e-10), [9])
    w = 0.5 - 0.5 * np.cos(2 * np.pi * n / 64)
    np.testing.assert_allclose(np.fft.ifft(np.fft.fft(x * w)), x * w, atol=1e-12)
    assert "recupera $x[n]w[n]$" in ejercicio("5D")


def test_normalizacion_global_no_deshace_los_pesos_de_hann():
    n = np.arange(64)
    x = np.exp(1j * (2 * np.pi * 1100 * n / 8000 + 0.7))
    w = 0.5 - 0.5 * np.cos(2 * np.pi * n / len(n))
    Xw = np.fft.fft(x * w)
    Cw = Xw / np.sum(w)
    np.testing.assert_allclose(np.fft.ifft(Cw), x * w / np.sum(w), atol=1e-12)
    np.testing.assert_allclose(np.fft.ifft(Cw) * np.sum(w), x * w, atol=1e-12)
    assert not np.allclose(np.fft.ifft(Cw) * np.sum(w), x)
    assert w[0] == 0
    otro_original = x.copy()
    otro_original[0] = -10 + 3j
    np.testing.assert_allclose(np.fft.fft(otro_original * w), Xw, atol=1e-12)


def test_referencia_rf_preserva_etiquetas_despues_de_mezcla_sin_cruce():
    fc = 99.1e6
    fs = 2.4e6
    rf = np.array([98.7e6, 99.1e6, 99.5e6])
    bb = rf - fc
    mezcla = 400e3
    bb_salida = bb + mezcla
    nueva_referencia = fc - mezcla
    assert np.all((-fs / 2 <= bb_salida) & (bb_salida < fs / 2))
    np.testing.assert_array_equal(nueva_referencia + bb_salida, rf)
    assert 99.1e6 - (-250e3) == 99.35e6
    assert 8000 / 8192 == 0.9765625


def test_rf_mezcla_y_bytes():
    np.testing.assert_allclose((433.92e6 + np.array([-350e3, 125e3])) / 1e6, [433.57, 434.045])
    np.testing.assert_allclose((433.92e6 + np.array([-1e6, 1e6])) / 1e6, [432.92, 434.92])
    assert "434.045" in ejercicio("6A")
    assert 98.7e6 - 99.1e6 == -400e3
    assert 99.1e6 - 400e3 == 98.7e6
    np.testing.assert_array_equal(np.array([0, 400e3]) + 400e3, [400e3, 800e3])
    assert "+800 kHz" in ejercicio("6B")
    assert (99.1e6 + 250e3) / 1e6 == pytest.approx(99.35)
    assert (99.5e6 + 250e3) / 1e6 == pytest.approx(99.75)
    assert "99.75" in ejercicio("6C")
    assert 48000 / 2 == 24000
    assert 24000 / 2.4e6 * 1000 == 10
    assert "24000/2400000=0.01" in ejercicio("6D")

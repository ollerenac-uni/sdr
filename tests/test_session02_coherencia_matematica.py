"""Casos límite y notación matemática auditados en la sesión 02."""

from pathlib import Path
import re

import pytest

np = pytest.importorskip("numpy")
matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt


PAGINA = Path(__file__).resolve().parents[1] / "docs/sessions/02-tiempo-frecuencia-iq/index.md"


@pytest.fixture(scope="module")
def visor_fft():
    """Ejecuta la celda publicada: no duplica la implementación del visor."""
    texto = PAGINA.read_text(encoding="utf-8")
    seccion = texto.split("### 5. Qué calcula una FFT de un bloque finito", 1)[1]
    celda = re.findall(r"```python\n(.*?)```", seccion, flags=re.DOTALL)[0]
    namespace = {}
    original = plt.show
    plt.show = lambda: plt.close("all")
    try:
        exec(compile(celda, "sesion02-referencias-dft", "exec"), namespace)
    finally:
        plt.show = original
        plt.close("all")
    return namespace


def test_referencia_positiva_y_producto_conjugado_publicados(visor_fft):
    d = visor_fft
    for k in (1, 2):
        referencia = np.exp(1j * 2 * np.pi * k * d["n8"] / 8)
        np.testing.assert_allclose(d["referencias"][k], referencia)
        productos = d["tono8"] * np.conj(referencia)
        np.testing.assert_allclose(d[f"productos_bin{k}"], productos)
        assert productos.sum() == pytest.approx(np.fft.fft(d["tono8"])[k], abs=1e-12)


@pytest.mark.parametrize("N", [15, 16])
@pytest.mark.parametrize("bin_firmado", [0, 1, -3])
def test_dft_referencia_fase_amplitud_y_signo(N, bin_firmado, visor_fft):
    n = np.arange(N)
    A, phi = 0.7, 0.43
    referencias = np.exp(1j * 2 * np.pi * np.arange(N)[:, None] * n / N)
    x = A * np.exp(1j * phi) * referencias[bin_firmado % N]
    X = np.conj(referencias) @ x
    np.testing.assert_allclose(X, np.fft.fft(x), atol=1e-12)
    assert X[bin_firmado % N] == pytest.approx(N * A * np.exp(1j * phi))
    np.testing.assert_allclose(np.delete(X, bin_firmado % N), 0, atol=1e-12)
    f, C = visor_fft["espectro_bloque"](x, 8000)
    k = np.argmax(np.abs(C))
    assert f[k] == pytest.approx(bin_firmado * 8000 / N)
    assert C[k] == pytest.approx(A * np.exp(1j * phi))


@pytest.mark.parametrize("M", [64, 129, 512])
@pytest.mark.parametrize("ventana", ["rectangular", "hann"])
def test_suma_en_hz_padding_y_normalizacion(M, ventana, visor_fft):
    N, fs, f0 = 64, 8000, 1231.25
    A, phi = 0.7, -0.43
    n = np.arange(N)
    w = np.ones(N) if ventana == "rectangular" else np.hanning(N + 1)[:-1]
    x = A * np.exp(1j * (2 * np.pi * f0 * n / fs + phi))
    f, C = visor_fft["espectro_bloque"](x, fs, ventana=w, nfft=M)
    # S_w(f) usa Hz; k solo indexa las M frecuencias de evaluación.
    S = np.exp(-1j * 2 * np.pi * f[:, None] * n / fs) @ (x * w)
    np.testing.assert_allclose(C, S / w.sum(), atol=1e-12)
    S_f0 = np.sum(x * w * np.exp(-1j * 2 * np.pi * f0 * n / fs))
    assert S_f0 / w.sum() == pytest.approx(A * np.exp(1j * phi))
    np.testing.assert_allclose(np.diff(f), fs / M)
    recuperado = np.fft.ifft(np.fft.ifftshift(C)) * w.sum()
    np.testing.assert_allclose(recuperado[:N], x * w, atol=1e-12)
    np.testing.assert_allclose(recuperado[N:], 0, atol=1e-12)


@pytest.mark.parametrize("N", [63, 64])
def test_inversa_deshace_orden_y_escala_pero_no_ventana(N, visor_fft):
    n = np.arange(N)
    x = np.exp(1j * (2 * np.pi * 0.13 * n + 0.41))
    w = np.hanning(N + 1)[:-1]
    _, C = visor_fft["espectro_bloque"](x, 8000, ventana=w)
    recuperado = np.fft.ifft(np.fft.ifftshift(C)) * w.sum()
    np.testing.assert_allclose(recuperado, x * w, atol=1e-12)
    assert abs(recuperado[0]) < 1e-12
    assert abs(x[0]) == pytest.approx(1)
    assert not np.allclose(recuperado, x)
    # Para longitudes impares, fftshift no sustituye a ifftshift.
    if N % 2:
        assert not np.allclose(np.fft.ifft(np.fft.fftshift(C)) * w.sum(), x * w)


@pytest.mark.parametrize("f0,bin_unico", [(0, 0), (4000, 32)])
@pytest.mark.parametrize("phi", [0, 0.7, np.pi / 2])
def test_coseno_en_dc_y_nyquist_suma_coeficientes_en_una_posicion(f0, bin_unico, phi):
    fs, N, A = 8000, 64, 1.3
    n = np.arange(N)
    theta = 2 * np.pi * f0 * n / fs + phi
    positivo = (A / 2) * np.exp(1j * theta)
    negativo = (A / 2) * np.exp(-1j * theta)
    x = A * np.cos(theta)
    np.testing.assert_allclose(positivo + negativo, x, atol=1e-12)
    esperado = np.zeros(N, dtype=complex)
    esperado[bin_unico] = A * np.cos(phi)
    np.testing.assert_allclose(np.fft.fft(x) / N, esperado, atol=1e-12)


def test_avance_no_envuelto_y_angulo_principal_de_alias():
    n, fs = np.arange(64), 8000
    z5 = np.exp(1j * 2 * np.pi * 5000 * n / fs)
    zmenos3 = np.exp(-1j * 2 * np.pi * 3000 * n / fs)
    np.testing.assert_allclose(z5, zmenos3, atol=1e-12)
    assert 360 * 5000 / fs == 225
    np.testing.assert_allclose(np.angle(z5[1:] * np.conj(z5[:-1]), deg=True), -135)


def test_mezclas_mas2_y_menos6_son_equivalentes_a_8ksps():
    n, fs = np.arange(64), 8000
    entrada = np.exp(1j * 2 * np.pi * 3000 * n / fs)
    mezcla2 = np.exp(1j * 2 * np.pi * 2000 * n / fs)
    mezcla_menos6 = np.exp(-1j * 2 * np.pi * 6000 * n / fs)
    esperado = np.exp(-1j * 2 * np.pi * 3000 * n / fs)
    np.testing.assert_allclose(mezcla2, mezcla_menos6, atol=1e-12)
    np.testing.assert_allclose(entrada * mezcla2, esperado, atol=1e-12)
    np.testing.assert_allclose(entrada * mezcla_menos6, esperado, atol=1e-12)


def test_fm_demodulada_es_media_del_intervalo_no_valor_final():
    fs, fm, desviacion = 192000, 1000, 75000
    beta = desviacion / fm
    n = np.arange(193)
    theta = beta * np.sin(2 * np.pi * fm * n / fs)
    z = 0.8 * np.exp(1j * theta)
    assert np.max(np.abs(np.diff(theta))) < np.pi
    frecuencia_media = fs / (2 * np.pi) * np.angle(z[1:] * np.conj(z[:-1]))
    # Promedio exacto del coseno en [(n-1)/fs, n/fs].
    mensaje_medio = np.sinc(fm / fs) * np.cos(2 * np.pi * fm * (n[1:] - 0.5) / fs)
    np.testing.assert_allclose(frecuencia_media / desviacion, mensaje_medio, atol=1e-12)
    mensaje_final = np.cos(2 * np.pi * fm * n[1:] / fs)
    assert not np.allclose(frecuencia_media / desviacion, mensaje_final, atol=1e-3)


def test_ejemplo_de_ganancia_fm_usa_tasa_del_demodulador():
    fs, desviacion, mensaje = 192000, 75000, 0.5
    frecuencia = desviacion * mensaje
    avance = 2 * np.pi * frecuencia / fs
    ganancia = fs / (2 * np.pi * desviacion)
    assert frecuencia == 37500
    assert avance == pytest.approx(1.227184630308513)
    assert ganancia == pytest.approx(0.40743665431525206)
    assert ganancia * np.angle(np.exp(1j * avance)) == pytest.approx(mensaje)

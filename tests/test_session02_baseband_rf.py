"""Regresión matemática del material de mezcla conservado para S04.

Estos casos no dependen del archivo interno .planning ni de apartados retirados.
La captura real y las nuevas celdas de S02 se prueban en test_session02_captura_real.
"""

import pytest

np = pytest.importorskip("numpy")


@pytest.fixture(scope="module")
def experimento():
    fs, fc, N = 2400000, 99100000, 2400
    t = np.arange(N) / fs
    frecuencias_bb = np.array([-600000, 0, 400000])
    amplitudes = np.array([0.6, 0.4, 1])
    x = sum(a * np.exp(1j * 2 * np.pi * f * t) for a, f in zip(amplitudes, frecuencias_bb))

    def espectro_iq(z, tasa):
        return np.fft.fftshift(np.fft.fftfreq(len(z), 1 / tasa)), np.fft.fftshift(np.fft.fft(z)) / len(z)

    f_bb, C_entrada = espectro_iq(x, fs)
    f_mix = -400000
    oscilador = np.exp(1j * 2 * np.pi * f_mix * t)
    y = x * oscilador
    f_salida, C_salida = espectro_iq(y, fs)
    objetivo = np.exp(1j * 2 * np.pi * 400000 * t)
    objetivo_centrado = objetivo * oscilador
    fc_nuevo = fc - f_mix
    casos_eje = [(f_bb, C_entrada, fc), (f_bb, C_entrada, fc_nuevo)]
    f_compleja, C_compleja = espectro_iq(objetivo_centrado, fs)
    f_coseno, C_coseno = espectro_iq(objetivo * np.cos(2 * np.pi * 400000 * t), fs)
    fs_borde = 8000
    n_borde = np.arange(64)
    entrada_borde = np.exp(1j * 2 * np.pi * 3000 * n_borde / fs_borde)
    oscilador_borde = np.exp(1j * 2 * np.pi * 2000 * n_borde / fs_borde)
    salida_borde = entrada_borde * oscilador_borde
    recuperada = salida_borde * np.conj(oscilador_borde)
    return locals()


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

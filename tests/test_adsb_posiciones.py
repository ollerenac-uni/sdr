"""PPM, límites de bloque, CRC y CPR sin mezclar aeronaves ni tiempos incompatibles."""

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from scripts.sesion09_adsb.receptor import interpretar, posicion_global, recuperar_tramas, recuperar_posiciones
from scripts.sesion09_adsb.verificar_posiciones import guardar_resultados
from scripts.sesion09_adsb.inspeccionar_adsb import construir_traza, presentar, pasos_crc

PAR = "8d40621d58c382d690c8ac2863a7"
IMPAR = "8d40621d58c386435cc412692ad6"


def pareja():
    # Vector publicado por Junzi Sun, The 1090 MHz Riddle, capítulo Airborne Position.
    return interpretar(PAR, 0, 2), interpretar(IMPAR, 8000000, 2)


def test_vector_cpr_publicado_sin_referencia_de_receptor():
    a, b = pareja()
    p = posicion_global(a, b)
    assert p["latitud"] == pytest.approx(52.26578017412606, abs=1e-10)
    assert p["longitud"] == pytest.approx(3.938912527901786, abs=1e-10)
    assert p["altitud_ft"] == 38000
    assert posicion_global(b, a) == p


@pytest.mark.parametrize("caso", ["mismo_tipo", "otra_aeronave", "mas_de_diez_segundos"])
def test_no_se_combinan_parejas_incompatibles(caso):
    a, b = pareja()
    if caso == "mismo_tipo":
        b["cpr_impar"] = 0
    elif caso == "otra_aeronave":
        b["icao"] = "abcdef"
    else:
        b["tiempo_s"] = 10.0001
    assert posicion_global(a, b) is None


@pytest.mark.parametrize("bloque", [777, 1001, 4096])
def test_ppm_con_trama_cruzando_bloque_y_crc_alterado(tmp_path, bloque):
    # Señal de prueba sintética SOLO para probar límites: la verificación usa I/Q real.
    onda = np.full(960, .001, np.float32)
    for k in (0, 8, 28, 36):
        onda[k:k+4] = 1
    bits = np.unpackbits(np.frombuffer(bytes.fromhex(PAR), np.uint8))
    for i, bit in enumerate(bits):
        k = 64+i*8+(0 if bit else 4)
        onda[k:k+4] = 1
    mala = onda.copy()
    k = 64+40*8
    mala[k:k+8] = mala[k:k+8][::-1]
    entrada = np.concatenate([np.full(333, .001), onda, np.full(100, .001), mala, np.full(100, .001)])
    archivo = tmp_path / "potencia.f32"
    entrada.astype("<f4").tofile(archivo)
    f, _ = recuperar_tramas(archivo, bloque=bloque)
    assert len(f) == 1 and f[0]["hex"] == PAR
    assert f[0]["muestra_8msps"] == 333


def test_asociar_posiciones_solo_al_icao_correcto():
    a, b = pareja()
    otro = deepcopy(a)
    otro["icao"] = "123456"
    assert len(recuperar_posiciones([a, otro, b])) == 1
    assert recuperar_posiciones([a, otro, b])[0]["icao"] == "40621d"


def test_mapa_y_exportacion_conservan_coordenadas_y_tramas(tmp_path):
    a, b = pareja()
    p = posicion_global(a, b)
    r = {"origen": {"duracion_archivo_s": 2, "descarga": {"miembro": "prueba"}},
         "resumen": {"tramas_df17_crc_valido": 2}, "tramas": [a, b], "posiciones": [p]}
    guardar_resultados(r, tmp_path)
    geo = json.loads((tmp_path / "posiciones.geojson").read_text())
    assert geo["features"][0]["geometry"]["coordinates"] == [p["longitud"], p["latitud"]]
    html = (tmp_path / "mapa.html").read_text()
    assert all(marcador not in html for marcador in
               ("__DATA__", "__LEAFLET_CSS__", "__LEAFLET_JS__", "__LEAFLET_LICENSE__"))
    assert 'src="https://unpkg.com' not in html
    assert "Redistribution and use" in html
    assert p["hex_par"] in html and p["hex_impar"] in html
    assert (tmp_path / "posiciones.csv").read_text().count("CPR global") == 1


def traza_de_prueba(tmp_path):
    a, b = pareja()
    p = posicion_global(a,b)
    datos = np.full(960, .001, dtype="<f4")
    bits = np.unpackbits(np.frombuffer(bytes.fromhex(PAR), np.uint8))
    for i, bit in enumerate(bits):
        n = 64+8*i+(0 if bit else 4)
        datos[n:n+4] = 1
    archivo = tmp_path / "potencia.f32"
    datos.tofile(archivo)
    informe = {"tramas":[a,b],"posiciones":[p]}
    return informe, archivo


def test_traza_conserva_bits_y_campos_del_mismo_mensaje(tmp_path):
    informe, archivo = traza_de_prueba(tmp_path)
    t = construir_traza(informe,archivo)
    assert t["bits"] == f"{int(PAR,16):0112b}"
    assert "".join(c["bits"] for c in t["campos"]) == t["bits"]
    assert len(t["decisiones"]) == 112
    assert t["crc_calculado"] == t["crc_recibido"] == int(PAR[-6:],16)
    assert t["cpr"]["latitud"] == pytest.approx(52.26578017412606,abs=1e-10)
    assert sum(len(c["bits"]) for c in t["me"]) == 56
    assert "B7" in presentar(t,"ppm",bloque=7) and "B6" not in presentar(t,"ppm",bloque=7)


def test_traza_no_acepta_informe_que_no_coincide_con_muestras(tmp_path):
    informe,archivo = traza_de_prueba(tmp_path)
    datos = np.memmap(archivo,dtype="<f4",mode="r+")
    datos[64:72] = datos[64:72].copy()[::-1]
    datos.flush()
    with pytest.raises(ValueError,match="no coinciden"):
        construir_traza(informe,archivo)


def test_division_crc_por_bit_y_control_negativo_publicado():
    bits = f"{int(PAR,16):0112b}"
    assert pasos_crc(bits)[-1]["despues"] == 0
    alterado = list(bits)
    alterado[40] = "1" if bits[40]=="0" else "0"
    assert pasos_crc(alterado)[-1]["despues"] != 0

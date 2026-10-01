"""La variante USRP se conserva sin reemplazar la solución sin hardware.

La compilación se comprueba en test_grafos_compilan.py; la recepción con USRP
necesita hardware y no se da por verificada mediante estas pruebas de contrato.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CADENA_ARCHIVO = {
    "blocks_file_source_0", "blocks_throttle2_0", "blocks_uchar_to_float_0",
    "blocks_add_const_vxx_0", "blocks_multiply_const_vxx_0",
    "blocks_deinterleave_0", "blocks_float_to_complex_0",
}


def cargar(nombre):
    grafo = yaml.safe_load((ROOT / "gnuradio-flowgraphs" / nombre).read_text(encoding="utf-8"))
    return grafo, {bloque["name"]: bloque for bloque in grafo["blocks"]}


def test_los_grafos_tienen_identificadores_independientes():
    referencia, _ = cargar("test2.grc")
    variante, _ = cargar("visualizador_usrp.grc")
    assert referencia["options"]["parameters"]["id"] == "test2"
    assert variante["options"]["parameters"]["id"] == "visualizador_usrp"


def test_la_referencia_lee_la_grabacion_oficial_sin_usrp():
    _, bloques = cargar("test2.grc")
    for nombre in CADENA_ARCHIVO:
        assert bloques[nombre]["states"]["state"] == "enabled"
    assert not any(bloque["id"] == "uhd_usrp_source" for bloque in bloques.values())
    assert bloques["samp_rate"]["parameters"]["value"] == "2400000"
    assert bloques["blocks_file_source_0"]["parameters"]["file"] == "../samples/fm_99p1MHz_2p4Msps_g30.cu8"
    assert bloques["soapy_rtlsdr_source_0"]["states"]["state"] == "disabled"


def test_la_variante_usa_usrp_y_no_la_cadena_de_bytes():
    _, bloques = cargar("visualizador_usrp.grc")
    fuente = bloques["uhd_usrp_source_0"]
    assert fuente["states"]["state"] == "enabled"
    assert fuente["parameters"]["type"] == "fc32"
    assert fuente["parameters"]["samp_rate"] == "samp_rate"
    for nombre in CADENA_ARCHIVO:
        assert bloques[nombre]["states"]["state"] == "disabled"
    assert bloques["soapy_rtlsdr_source_0"]["states"]["state"] == "disabled"
    assert bloques["blocks_file_source_0"]["parameters"]["file"] == "../samples/fm_99p1MHz_2p4Msps_g30.cu8"


def test_usrp_alimenta_los_visores_complejos_de_tiempo_y_frecuencia():
    grafo, bloques = cargar("visualizador_usrp.grc")
    conexiones = {tuple(conexion) for conexion in grafo["connections"]}
    for nombre in ("qtgui_freq_sink_x_0", "qtgui_time_sink_x_0"):
        assert ("uhd_usrp_source_0", "0", nombre, "0") in conexiones
        assert bloques[nombre]["states"]["state"] == "enabled"
        assert bloques[nombre]["parameters"]["type"] == "complex"

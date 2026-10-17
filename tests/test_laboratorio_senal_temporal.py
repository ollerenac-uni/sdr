"""Comprueba el paso 12 con bloques estándar y paquetes completos de muestras."""

import importlib.util
import os
import re
import subprocess

import pytest
import yaml

from test_laboratorio_enlace_digital import CARPETA, GUIA, runtime


def parametros(seccion, apartado):
    fragmento = seccion.split(apartado, 1)[1].split("### ", 1)[0]
    return dict(re.findall(r"^\| `([^`]+)` \| `([^`]+)` \|", fragmento, re.M))


@pytest.mark.parametrize("interpolacion", [4, 8], ids=["sps4", "sps8"])
def test_senal_temporal_estandar_con_pdus_completas(tmp_path, runtime, interpolacion):
    guia = GUIA.read_text(encoding="utf-8")
    seccion = guia.split("## 12. Construir la señal en el dominio del tiempo", 1)[1].split("## Referencias", 1)[0]
    p_repeat = parametros(seccion, "### 12.3.")
    p_tag = parametros(seccion, "### 12.4.")
    p_pdu = parametros(seccion, "### 12.5.")
    p_time = parametros(seccion, "### 12.7.")
    snippets = re.findall(r"```python\n(.*?)\n```", guia, re.S)
    codigos = [next(c for c in snippets if f'name="{nombre}"' in c) for nombre in ["Texto a bytes UTF-8", "Construir paquete", "Bytes a bits"]]
    ajuste = next(c for c in snippets if "self.pulso_rect.set_min_output_buffer" in c)
    variables = parametros(seccion, "### 12.2.")
    assert variables["sps"] == "4"
    variables["sps"] = str(interpolacion)
    bloques = []

    def bloque(nombre, tipo, parametros, x=0, y=0):
        bloques.append({"name": nombre, "id": tipo, "parameters": parametros,
                        "states": {"state": "enabled", "coordinate": [x, y], "rotation": 0}})

    for nombre in ["symbol_rate", "sps", "samp_rate"]:
        bloque(nombre, "variable", {"value": variables[nombre]})
    for i, codigo in enumerate(codigos):
        bloque(f"epy_block_{i}", "epy_block", {"_source_code": codigo}, 200 * i, 100)
    bloque("mensaje_a", "qtgui_edit_box_msg", {"type": "string", "value": "", "label": "Mensaje de A", "is_pair": "False", "is_static": "True", "key": "", "gui_hint": "0,0,1,2"})
    bloque("a_stream", "pdu_pdu_to_tagged_stream", {"type": "byte", "tag": "packet_len"})
    bloque("mapeador", "digital_chunks_to_symbols_xx", {"in_type": "byte", "out_type": "complex", "symbol_table": "[-1+0j, 1+0j]", "dimension": "1", "num_ports": "1"})
    bloque("simbolos_a_pdu", "pdu_tagged_stream_to_pdu", {"type": "complex", "tag": "packet_len"})
    bloque("constelacion", "qtgui_const_sink_x", {"type": "msg_complex", "name": "Simbolos BPSK", "grid": "True", "autoscale": "False", "xmin": "-1.5", "xmax": "1.5", "ymin": "-1.5", "ymax": "1.5", "style1": "0", "marker1": "0", "gui_hint": "1,0,1,1"})
    bloque(p_repeat["ID"], "blocks_repeat", {"type": p_repeat["Type"].lower(), "interp": p_repeat["Interpolation"], "vlen": p_repeat["Vector Length"]})
    bloque(p_tag["ID"], "blocks_tagged_stream_multiply_length", {"type": p_tag["IO Type"].lower(), "lengthtagname": p_tag["Length tag names"], "c": p_tag["Length Scalar"], "vlen": "1"})
    bloque(p_pdu["ID"], "pdu_tagged_stream_to_pdu", {"type": p_pdu["Item Type"].lower(), "tag": p_pdu["Length tag name"]})
    bloque(p_time["ID"], "qtgui_time_sink_x", {"type": "msg_complex", "name": p_time["Name"], "srate": p_time["Sample Rate"], "grid": "True", "autoscale": "False", "ymin": p_time["Y min"], "ymax": p_time["Y max"], "label1": "I", "label2": "Q", "style1": "1", "style2": "1", "marker1": "0", "marker2": "0", "gui_hint": "1,1,1,1", "update_time": "0.01"})
    bloque("debug_muestras", "blocks_message_debug", {"en_uvec": "False", "log_level": "info"})
    bloque("ajustar_buffers", "snippet", {"section": "main_after_init", "priority": "0", "code": ajuste})
    conexiones = [[f"epy_block_{i}", "out", f"epy_block_{i+1}", "in"] for i in range(2)] + [
        ["mensaje_a", "msg", "epy_block_0", "in"], ["epy_block_2", "out", "a_stream", "pdus"],
        ["a_stream", "0", "mapeador", "0"], ["mapeador", "0", "simbolos_a_pdu", "0"],
        ["simbolos_a_pdu", "pdus", "constelacion", "in"],
        ["mapeador", "0", "pulso_rect", "0"], ["pulso_rect", "0", "longitud_muestras", "0"],
        ["longitud_muestras", "0", "muestras_a_pdu", "0"],
        ["muestras_a_pdu", "pdus", "tiempo_bpsk", "in"], ["muestras_a_pdu", "pdus", "debug_muestras", "print"],
    ]
    grafo = {"options": {"parameters": {"id": "enlace_i09_temporal_prueba", "generate_options": "qt_gui", "title": "Prueba de senal temporal", "output_language": "python", "run": "True"}, "states": {"state": "enabled"}}, "blocks": bloques, "connections": conexiones, "metadata": {"file_format": 1}}
    archivo = tmp_path / "senal_temporal_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = r'''
import os, struct, time, zlib
import numpy as np
import pmt
from gnuradio import blocks
from PyQt5 import QtWidgets, QtCore, QtTest
from enlace_i09_temporal_prueba import enlace_i09_temporal_prueba, snippets_main_after_init
app = QtWidgets.QApplication([])
tb = enlace_i09_temporal_prueba()
snippets_main_after_init(tb)
assert tb.symbol_rate == 1000 and tb.sps in (4, 8) and tb.samp_rate == 1000 * tb.sps
observador = blocks.message_debug()
simbolos = blocks.message_debug()
tags = blocks.vector_sink_c()
tb.msg_connect((tb.muestras_a_pdu, 'pdus'), (observador, 'store'))
tb.msg_connect((tb.simbolos_a_pdu, 'pdus'), (simbolos, 'store'))
tb.connect(tb.longitud_muestras, tags)
tb.start()
tb.resize(1400, 600)
tb.show()
app.processEvents()
editor, = [w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
esperados = []
longitudes = []
def enviar(texto):
    editor.setText(texto)
    QtTest.QTest.keyClick(editor, QtCore.Qt.Key_Return)
    datos = texto.encode('utf-8')
    cuerpo = struct.pack('!H', len(datos)) + datos
    paquete = cuerpo + struct.pack('!I', zlib.crc32(cuerpo))
    bits = np.unpackbits(np.frombuffer(paquete, dtype=np.uint8), bitorder='big')
    originales = (2 * bits.astype(int) - 1).astype(np.complex64)
    esperados.append(originales)
    longitudes.append(len(originales) * tb.sps)
def esperar(numero, comprobar_visor=True):
    limite = time.monotonic() + 4
    while (observador.num_messages() < numero or simbolos.num_messages() < numero) and time.monotonic() < limite:
        QtTest.QTest.qWait(5)
    assert observador.num_messages() == numero and simbolos.num_messages() == numero
    for i, originales in enumerate(esperados):
        pdu = observador.get_message(i)
        assert pmt.is_c32vector(pmt.cdr(pdu))
        muestras = np.array(pmt.c32vector_elements(pmt.cdr(pdu)), dtype=np.complex64)
        assert np.array_equal(muestras, np.repeat(originales, tb.sps))
        assert len(muestras) == longitudes[i] and muestras.nbytes == len(muestras) * 8
        assert np.all(muestras.imag == 0)
        origen = np.array(pmt.c32vector_elements(pmt.cdr(simbolos.get_message(i))))
        assert np.array_equal(origen, originales)
    QtTest.QTest.qWait(50)
    if comprobar_visor:
        assert tb.tiempo_bpsk.nsamps() == longitudes[-1]
try:
    enviar('Hola')
    esperar(1)  # Paquete aislado: no espera un mensaje para vaciar el anterior.
    assert longitudes[-1] == 80 * tb.sps
    if os.environ.get('SDR_I09_SCREENSHOT') and tb.sps == 4:
        QtTest.QTest.qWait(100)
        assert tb.grab().save(os.environ['SDR_I09_SCREENSHOT'])
    # Paquetes consecutivos, con longitudes diferentes y UTF-8 multibyte.
    for texto in ['SDR', '¡Hola, Perú!', 'a' * 5000]:
        enviar(texto)
    esperar(4, comprobar_visor=False)
    assert longitudes[1] == 72 * tb.sps and longitudes[3] == 40048 * tb.sps
    QtTest.QTest.qWait(200)
    assert observador.num_messages() == 4  # La pausa no genera nuevas muestras.
    enviar('Hola')
    esperar(5)
    limite = time.monotonic() + 4
    while tags.nitems_read(0) < sum(longitudes) and time.monotonic() < limite:
        QtTest.QTest.qWait(5)
    assert tags.nitems_read(0) == sum(longitudes)
    etiquetas = [t for t in tags.tags() if pmt.symbol_to_string(t.key) == 'packet_len']
    assert [pmt.to_long(t.value) for t in etiquetas] == longitudes
    assert [t.offset for t in etiquetas] == list(np.cumsum([0] + longitudes[:-1]))
    print('TEMPORAL_OK', tb.sps, longitudes)
finally:
    tb.stop()
    tb.wait()
    tb.close()
'''
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    longitudes = [80 * interpolacion, 72 * interpolacion, 160 * interpolacion, 40048 * interpolacion, 80 * interpolacion]
    assert f"TEMPORAL_OK {interpolacion} {longitudes}" in resultado.stdout
    assert resultado.stdout.count(f"{80 * interpolacion * 8} bytes (printing disabled)") == 2
    assert f"{72 * interpolacion * 8} bytes (printing disabled)" in resultado.stdout
    assert f"{40048 * interpolacion * 8} bytes (printing disabled)" in resultado.stdout


def test_figuras_temporales_son_reproducibles(tmp_path):
    ruta = CARPETA / "figures/gen_enlace_senal_temporal.py"
    spec = importlib.util.spec_from_file_location("figura_temporal", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    archivos = modulo.generar(tmp_path)
    assert [p.name for p in archivos] == ["enlace-35-pulso-rectangular.png", "enlace-36-conexion-senal-temporal.png"]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in archivos)
    paquete, bits, simbolos, muestras = modulo.datos_hola()
    assert paquete.hex(" ") == "00 04 48 6f 6c 61 aa 94 8e c9"
    assert len(bits) == len(simbolos) == 80 and len(muestras) == 320

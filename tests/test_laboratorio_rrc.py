"""Comprueba la rama RRC con bloques reales y una referencia de convolución."""

import importlib.util
import json
import os
import re
import subprocess

import numpy as np
import pytest
import yaml

from test_laboratorio_enlace_digital import GUIA, runtime
from test_laboratorio_senal_temporal import parametros


def configuracion(seccion, apartado, identificador):
    fragmento = seccion.split(apartado, 1)[1].split("### ", 1)[0]
    tablas = re.findall(r"^\| Campo \| Valor \|\n\|---\|---\|\n((?:\|.*\n)+)", fragmento, re.M)
    for tabla in tablas:
        valores = dict(re.findall(r"^\| `([^`]+)` \| `([^`]+)` \|", tabla, re.M))
        if valores.get("ID") == identificador:
            return valores
    raise AssertionError(f"No se encuentra la configuración de {identificador}")


def grafo_rrc(guia, sps, alpha):
    seccion = guia.split("## 13. Construir un pulso RRC", 1)[1].split("## 14.", 1)[0]
    anterior = guia.split("## 12. Construir la señal", 1)[1].split("## 13.", 1)[0]
    variables = parametros(anterior, "### 12.2.") | parametros(seccion, "### 13.2.")
    assert variables["sps"] == "4" and variables["rrc_alpha"] == "0.35"
    variables.update(sps=str(sps), rrc_alpha=str(alpha))
    cierre = configuracion(seccion, "### 13.3.", "cierre_rrc")
    rrc = configuracion(seccion, "### 13.4.", "pulso_rrc")
    longitud = configuracion(seccion, "### 13.5.", "longitud_rrc")
    pdu = configuracion(seccion, "### 13.5.", "rrc_a_pdu")
    tiempo = configuracion(seccion, "### 13.7.", "tiempo_rrc")
    debug = configuracion(seccion, "### 13.7.", "debug_rrc")
    fragmentos = re.findall(r"```python\n(.*?)\n```", guia, re.S)
    codigos = [next(c for c in fragmentos if f'name="{nombre}"' in c)
               for nombre in ("Texto a bytes UTF-8", "Construir paquete", "Bytes a bits")]
    ajuste = next(c for c in fragmentos if "self.cierre_rrc.set_min_output_buffer" in c)
    bloques = []

    def bloque(nombre, tipo, valores):
        bloques.append({"name": nombre, "id": tipo, "parameters": valores,
                        "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0}})

    for nombre, valor in variables.items():
        bloque(nombre, "variable", {"value": valor})
    for identificador, codigo in zip((0, 2, 5), codigos):
        bloque(f"epy_block_{identificador}", "epy_block", {"_source_code": codigo})
    bloque("mensaje_a", "qtgui_edit_box_msg", {"type": "string", "value": "", "label": "Mensaje de A", "is_pair": "False", "is_static": "True", "key": "", "gui_hint": "1,0,1,2"})
    bloque("a_stream", "pdu_pdu_to_tagged_stream", {"type": "byte", "tag": "packet_len"})
    bloque("mapeador", "digital_chunks_to_symbols_xx", {"in_type": "byte", "out_type": "complex", "symbol_table": "[-1+0j, 1+0j]", "dimension": "1", "num_ports": "1"})
    bloque("simbolos_a_pdu", "pdu_tagged_stream_to_pdu", {"type": "complex", "tag": "packet_len"})
    bloque("constelacion", "qtgui_const_sink_x", {"type": "msg_complex", "name": "Simbolos BPSK", "grid": "True", "autoscale": "False", "xmin": "-1.5", "xmax": "1.5", "ymin": "-1.5", "ymax": "1.5", "gui_hint": "2,0,1,2"})
    bloque("pulso_rect", "blocks_repeat", {"type": "complex", "interp": "sps", "vlen": "1"})
    bloque("longitud_muestras", "blocks_tagged_stream_multiply_length", {"type": "complex", "lengthtagname": "packet_len", "c": "sps", "vlen": "1"})
    bloque("muestras_a_pdu", "pdu_tagged_stream_to_pdu", {"type": "complex", "tag": "packet_len"})
    bloque("tiempo_bpsk", "qtgui_time_sink_x", {"type": "msg_complex", "name": "Senal temporal BPSK", "srate": "samp_rate", "grid": "True", "autoscale": "False", "ymin": "-1.5", "ymax": "1.5", "label1": "I", "label2": "Q", "style1": "1", "style2": "1", "marker1": "0", "marker2": "0", "gui_hint": "0,0,1,1", "update_time": "0.01"})
    bloque(cierre["ID"], "digital_burst_shaper_xx", {"type": cierre["Type"].lower(), "window": cierre["Window Taps"], "pre_padding": cierre["Pre-padding Length"], "post_padding": cierre["Post-padding Length"], "insert_phasing": {"No": "False", "Yes": "True"}[cierre["Insert phasing symbols"]], "length_tag_name": cierre["Length Tag Name"]})
    bloque(rrc["ID"], "root_raised_cosine_filter", {"type": {"Complex->Complex (Interpolating)": "interp_fir_filter_ccf"}[rrc["FIR Type"]], "interp": rrc["Interpolation"], "gain": rrc["Gain"], "samp_rate": rrc["Sample Rate"], "sym_rate": rrc["Symbol Rate"], "alpha": rrc["Alpha"], "ntaps": rrc["Num Taps"]})
    bloque(longitud["ID"], "blocks_tagged_stream_multiply_length", {"type": longitud["IO Type"].lower(), "lengthtagname": longitud["Length tag names"], "c": longitud["Length Scalar"], "vlen": "1"})
    bloque(pdu["ID"], "pdu_tagged_stream_to_pdu", {"type": pdu["Item Type"].lower(), "tag": pdu["Length tag name"]})
    bloque(tiempo["ID"], "qtgui_time_sink_x", {"type": "msg_complex", "name": tiempo["Name"], "srate": tiempo["Sample Rate"], "grid": "True", "autoscale": "False", "ymin": tiempo["Y min"], "ymax": tiempo["Y max"], "label1": tiempo["Line 1 Label"], "label2": tiempo["Line 2 Label"], "style1": "1", "style2": "1", "marker1": "0", "marker2": "0", "gui_hint": "0,1,1,1", "update_time": "0.01"})
    bloque(debug["ID"], "blocks_message_debug", {"en_uvec": {"Off": "False", "On": "True"}[debug["Print PDU contents"]], "log_level": "info"})
    bloque("ajustar_buffers", "snippet", {"section": "main_after_init", "priority": "0", "code": ajuste})
    conexiones = [
        ["mensaje_a", "msg", "epy_block_0", "in"], ["epy_block_0", "out", "epy_block_2", "in"],
        ["epy_block_2", "out", "epy_block_5", "in"], ["epy_block_5", "out", "a_stream", "pdus"],
        ["a_stream", "0", "mapeador", "0"], ["mapeador", "0", "simbolos_a_pdu", "0"],
        ["simbolos_a_pdu", "pdus", "constelacion", "in"],
        ["mapeador", "0", "pulso_rect", "0"], ["pulso_rect", "0", "longitud_muestras", "0"],
        ["longitud_muestras", "0", "muestras_a_pdu", "0"], ["muestras_a_pdu", "pdus", "tiempo_bpsk", "in"],
        ["mapeador", "0", "cierre_rrc", "0"], ["cierre_rrc", "0", "pulso_rrc", "0"],
        ["pulso_rrc", "0", "longitud_rrc", "0"], ["longitud_rrc", "0", "rrc_a_pdu", "0"],
        ["rrc_a_pdu", "pdus", "tiempo_rrc", "in"], ["rrc_a_pdu", "pdus", "debug_rrc", "print"],
    ]
    grafo = {"options": {"parameters": {"id": "enlace_i10_rrc_prueba", "generate_options": "qt_gui", "title": "Prueba de pulso RRC", "output_language": "python", "run": "True"}, "states": {"state": "enabled"}}, "blocks": bloques, "connections": conexiones, "metadata": {"file_format": 1}}
    return grafo


@pytest.mark.parametrize("sps,alpha", [(4, .35), (8, .35), (4, .20), (4, .50)],
                         ids=["sps4", "sps8", "alpha020", "alpha050"])
def test_rrc_estandar_con_cierre_y_pdus_completas(tmp_path, runtime, sps, alpha):
    guia = GUIA.read_text(encoding="utf-8")
    grafo = grafo_rrc(guia, sps, alpha)
    archivo = tmp_path / "rrc_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    resultado = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    programa = r'''
import os, struct, time, zlib
import numpy as np
import pmt
from gnuradio import blocks
from gnuradio.filter import firdes
from PyQt5 import QtWidgets, QtCore, QtTest
from enlace_i10_rrc_prueba import enlace_i10_rrc_prueba, snippets_main_after_init
app = QtWidgets.QApplication([])
tb = enlace_i10_rrc_prueba()
snippets_main_after_init(tb)
rrc, rectangular, simbolos = [blocks.message_debug() for _ in range(3)]
for adaptador, observador in ((tb.rrc_a_pdu,rrc),(tb.muestras_a_pdu,rectangular),(tb.simbolos_a_pdu,simbolos)):
    tb.msg_connect((adaptador,'pdus'),(observador,'store'))
tags = blocks.vector_sink_c()
tb.connect(tb.longitud_rrc,tags)
tb.start()
tb.resize(1400,850)
tb.show()
app.processEvents()
editor, = [w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
taps = np.array(firdes.root_raised_cosine(tb.sps,tb.samp_rate,tb.symbol_rate,tb.rrc_alpha,tb.rrc_ntaps),dtype=np.float32)
assert len(taps) == tb.rrc_span*tb.sps+1 and tb.pulso_rrc.history() == tb.rrc_span+1
originales = []
longitudes = []
def enviar(texto):
    editor.setText(texto)
    QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
    datos = texto.encode('utf-8')
    cuerpo = struct.pack('!H',len(datos))+datos
    paquete = cuerpo+struct.pack('!I',zlib.crc32(cuerpo))
    bits = np.unpackbits(np.frombuffer(paquete,dtype=np.uint8),bitorder='big')
    originales.append((2*bits.astype(int)-1).astype(np.complex64))
    longitudes.append((len(bits)+tb.rrc_span)*tb.sps)
def esperar(numero,gui=True):
    limite = time.monotonic()+4
    while any(o.num_messages()<numero for o in (rrc,rectangular,simbolos)) and time.monotonic()<limite:
        QtTest.QTest.qWait(5)
    assert all(o.num_messages()==numero for o in (rrc,rectangular,simbolos))
    for i,a in enumerate(originales):
        salida = rrc.get_message(i)
        assert pmt.is_c32vector(pmt.cdr(salida))
        y = np.array(pmt.c32vector_elements(pmt.cdr(salida)),dtype=np.complex64)
        u = np.zeros(longitudes[i],dtype=np.complex64)
        u[:len(a)*tb.sps:tb.sps] = a
        esperado = np.convolve(u,taps)[:len(u)]
        assert len(y)==len(u) and y.nbytes==8*len(u)
        assert np.allclose(y,esperado,rtol=5e-7,atol=5e-7),np.max(np.abs(y-esperado))
        assert np.all(y.imag==0) and np.all(y[-(tb.sps-1):]==0)
        s = np.array(pmt.c32vector_elements(pmt.cdr(simbolos.get_message(i))),dtype=np.complex64)
        r = np.array(pmt.c32vector_elements(pmt.cdr(rectangular.get_message(i))),dtype=np.complex64)
        assert np.array_equal(s,a) and np.array_equal(r,np.repeat(a,tb.sps))
    QtTest.QTest.qWait(60)
    if gui:
        assert tb.tiempo_rrc.nsamps()==longitudes[-1]
        assert tb.tiempo_bpsk.nsamps()==len(originales[-1])*tb.sps
try:
    enviar('Hola')
    esperar(1)
    if os.environ.get('SDR_I10_SCREENSHOT') and tb.sps==4 and abs(tb.rrc_alpha-.35)<1e-8:
        assert tb.grab().save(os.environ['SDR_I10_SCREENSHOT'])
    for texto in ('SDR','¡Hola, Perú!','a'*5000):
        enviar(texto)
    esperar(4,gui=False)
    QtTest.QTest.qWait(200)
    assert all(o.num_messages()==4 for o in (rrc,rectangular,simbolos))
    enviar('Hola')
    esperar(5)
    etiquetas = [t for t in tags.tags() if pmt.symbol_to_string(t.key)=='packet_len']
    assert [pmt.to_long(t.value) for t in etiquetas]==longitudes
    assert [t.offset for t in etiquetas]==list(np.cumsum([0]+longitudes[:-1]))
    print('RRC_GUI_OK',tb.sps,tb.rrc_alpha,longitudes)
finally:
    tb.stop()
    tb.wait()
    tb.close()
'''
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "XDG_CONFIG_HOME": str(tmp_path / "config"), "XDG_STATE_HOME": str(tmp_path / "state")}
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    longitudes = [(n+8)*sps for n in (80,72,160,40048,80)]
    assert f"RRC_GUI_OK {sps} {alpha} {longitudes}" in resultado.stdout
    assert resultado.stdout.count(f"{88*sps*8} bytes (printing disabled)") == 2
    assert f"{40056*sps*8} bytes (printing disabled)" in resultado.stdout


def test_figuras_rrc_y_coeficientes_reproducibles(tmp_path, runtime):
    ruta = GUIA.parent / "figures/gen_enlace_rrc.py"
    spec = importlib.util.spec_from_file_location("figuras_rrc", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    archivos = modulo.generar(tmp_path)
    assert [p.name for p in archivos] == ["enlace-41-pulso-rrc-hola.png", "enlace-42-conexion-rrc.png"]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in archivos)
    for sps, alpha in ((4,.20),(4,.35),(4,.50),(8,.35)):
        taps, simbolos, rectangular, rrc = modulo.datos_hola(sps,alpha)
        assert len(simbolos)==80 and len(rectangular)==80*sps and len(rrc)==88*sps
        assert np.all(np.isfinite(taps)) and np.all(np.isfinite(rrc))
        programa = f"from gnuradio.filter import firdes; import json; print(json.dumps(firdes.root_raised_cosine({sps},{1000*sps},1000,{alpha},{8*sps+1})))"
        resultado = subprocess.run([runtime[1],"-c",programa],capture_output=True,text=True,timeout=10)
        assert resultado.returncode == 0, resultado.stderr
        referencia = np.array(json.loads(resultado.stdout),dtype=np.float32)
        assert np.allclose(taps,referencia,atol=2e-7,rtol=2e-6)

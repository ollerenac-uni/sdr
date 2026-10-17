"""Recupera texto desde muestras sin etiquetas ni delimitación por PDU en RX."""

import importlib.util
import re

import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_rrc import configuracion
from test_laboratorio_sincronizacion_paquete import grafo_sincronizacion


ANTIGUOS = {"rx_a_pdu", "muestrear_rx", "rx_a_stream", "debug_rx", "debug_simbolos_rx"}


def grafo_stream(guia, sps=4, alpha=0.35, alterar=False):
    grafo = grafo_sincronizacion(guia, sps, alpha, alterar)
    seccion = (
        guia.split("## 17. Recibir desde un stream", 1)[1]
        .split("## 18.", 1)[0]
        .split("## Siguiente paso", 1)[0]
    )
    gate = configuracion(seccion, "### 17.3.", "sin_etiquetas")
    sampler = configuracion(seccion, "### 17.3.", "muestrear_stream")
    debug = configuracion(seccion, "### 17.3.", "debug_sin_etiquetas")
    tiempo = configuracion(seccion, "### 17.4.", "tiempo_rx")
    const = configuracion(seccion, "### 17.4.", "constelacion_rx")
    for b in grafo["blocks"]:
        if b["name"] in ANTIGUOS:
            b["states"]["state"] = "disabled"
        if b["name"] == "ajustar_buffers":
            b["parameters"]["code"] = next(
                c
                for c in re.findall(r"```python\n(.*?)\n```", seccion, re.S)
                if "self.detectar_trama.set_min_output_buffer" in c
            )
        if b["name"] in ("tiempo_rx", "constelacion_rx"):
            cfg = tiempo if b["name"] == "tiempo_rx" else const
            b["parameters"].update(
                type=cfg["Type"].lower(), size=cfg["Number of Points"], name=cfg["Name"]
            )
    grafo["connections"] = [
        c for c in grafo["connections"] if c[0] not in ANTIGUOS and c[2] not in ANTIGUOS
    ]
    grafo["connections"].remove(["cierre_rx", "0", "filtro_rx", "0"])

    def bloque(nombre, tipo, valores):
        grafo["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )

    bloque(
        gate["ID"],
        "blocks_tag_gate",
        {
            "type": gate["Item Type"].lower(),
            "vlen": gate["Vector Length"],
            "propagate_tags": {"No": "False", "Yes": "True"}[gate["Propagate Tags"]],
            "single_key": gate["Single Key"],
        },
    )
    bloque(
        sampler["ID"],
        "blocks_keep_m_in_n",
        {
            "type": sampler["Type"].lower(),
            "m": sampler["M"],
            "n": sampler["N"],
            "offset": sampler["initial offset"],
        },
    )
    bloque(
        debug["ID"],
        "blocks_tag_debug",
        {
            "type": debug["Input Type"].lower(),
            "name": debug["Name"],
            "filter": debug["Key Filter"],
            "display": "True",
            "vlen": "1",
            "num_inputs": "1",
        },
    )
    grafo["connections"] += [
        ["cierre_rx", "0", "sin_etiquetas", "0"],
        ["sin_etiquetas", "0", "filtro_rx", "0"],
        ["sin_etiquetas", "0", "debug_sin_etiquetas", "0"],
        ["filtro_rx", "0", "muestrear_stream", "0"],
        ["filtro_rx", "0", "tiempo_rx", "0"],
        ["muestrear_stream", "0", "extraer_i", "0"],
        ["muestrear_stream", "0", "constelacion_rx", "0"],
    ]
    grafo["options"]["parameters"].update(
        id="enlace_i14_stream_prueba", title="Prueba de receptor sin etiquetas"
    )
    return grafo


@pytest.mark.parametrize("sps,alpha", [(4, 0.35), (8, 0.35), (4, 0.20), (4, 0.50)])
def test_recuperacion_sin_tags_y_sin_pdus_rx(tmp_path, runtime, sps, alpha):
    grafo = grafo_stream(GUIA.read_text(), sps, alpha)
    programa = r"""
import time,struct,zlib,pmt
import numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i14_stream_prueba import enlace_i14_stream_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);tb=enlace_i14_stream_prueba();snippets_main_after_init(tb)
assert not any(hasattr(tb,n) for n in ('rx_a_pdu','muestrear_rx','rx_a_stream'))
entrada=blocks.vector_sink_c();rx=blocks.vector_sink_c();sampled=blocks.vector_sink_c();det=blocks.vector_sink_b()
tb.connect(tb.sin_etiquetas,entrada);tb.connect(tb.filtro_rx,rx);tb.connect(tb.muestrear_stream,sampled);tb.connect(tb.detectar_trama,det)
pkts=blocks.message_debug();textos=blocks.message_debug()
tb.msg_connect((tb.paquete_rx_a_pdu,'pdus'),(pkts,'store'));tb.msg_connect((tb.epy_block_1,'out'),(textos,'store'))
editor,=[w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
corpus=['Hola','SDR','¡Hola, Perú!','a'*5000,'  texto  ','Hola'];refs=[];frames=[]
tb.start()
try:
    for i,texto in enumerate(corpus):
        d=texto.encode();b=struct.pack('>H',len(d))+d;p=b+struct.pack('>I',zlib.crc32(b));refs.append(p)
        f=bytes(tb.sync_bytes)+struct.pack('>HH',len(p),len(p))+p;frames.append(f)
        editor.setText(texto);QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
        fin=time.monotonic()+6
        while textos.num_messages()<i+1 and time.monotonic()<fin:QtTest.QTest.qWait(5)
        assert textos.num_messages()==pkts.num_messages()==i+1
        assert bytes(pmt.u8vector_elements(pmt.cdr(pkts.get_message(i))))==p
        assert pmt.symbol_to_string(textos.get_message(i))==texto
        if i==0:QtTest.QTest.qWait(150);assert textos.num_messages()==1
    QtTest.QTest.qWait(80)
    full=np.array(rx.data());sel=np.array(sampled.data())
    assert len(full)==sum((8*len(f)+16)*tb.sps for f in frames)
    assert np.array_equal(sel,full[::tb.sps])
    assert not entrada.tags() and not rx.tags() and not sampled.tags()
    offset=0
    for f in frames:
        n=8*len(f);valid=sel[offset+tb.rrc_span:offset+tb.rrc_span+n]
        assert np.array_equal((valid.real>=0).astype(np.uint8),np.unpackbits(np.frombuffer(f,dtype=np.uint8),bitorder='big'))
        offset+=n+16
    assert list(det.data())==np.concatenate([np.unpackbits(np.frombuffer(p,dtype=np.uint8),bitorder='big') for p in refs]).tolist()
    tags=det.tags();assert [pmt.symbol_to_string(t.key) for t in tags]==['packet_len']*len(refs)
    assert [pmt.to_long(t.value) for t in tags]==[8*len(p) for p in refs]
    assert [t.offset for t in tags]==list(np.cumsum([0]+[8*len(p) for p in refs[:-1]]))
    print('RX_STREAM_OK',tb.sps,tb.rrc_alpha,len(sel),flush=True)
finally:tb.stop();tb.wait();tb.close()
"""
    salida = ejecutar(grafo, programa, tmp_path, runtime)
    assert f"RX_STREAM_OK {sps} {alpha}" in salida
    assert "CRC incorrecto" not in salida


def test_muestras_reproducidas_con_tags_falsos_y_trabajo_fragmentado(tmp_path, runtime):
    grafo = grafo_stream(GUIA.read_text())
    programa = r"""
import time,pmt,numpy as np
from gnuradio import blocks,gr
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i14_stream_prueba import enlace_i14_stream_prueba,snippets_main_after_init
app=QtWidgets.QApplication([])
def crear():
    t=enlace_i14_stream_prueba();snippets_main_after_init(t);o=blocks.message_debug()
    t.msg_connect((t.epy_block_1,'out'),(o,'store'));return t,o
tb,obs=crear();wire=blocks.vector_sink_c();tb.connect(tb.cierre_rx,wire)
editor,=[w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
tb.start()
try:
    for i,texto in enumerate(['Hola','SDR']):
        editor.setText(texto);QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
        fin=time.monotonic()+5
        while obs.num_messages()<i+1 and time.monotonic()<fin:QtTest.QTest.qWait(5)
        assert obs.num_messages()==i+1
    QtTest.QTest.qWait(60);samples=np.array(wire.data(),dtype=np.complex64)
    assert len(samples)==768+736
finally:tb.stop();tb.wait();tb.close()
# Otra instancia recibe solo muestras: se añaden silencios y etiquetas falsas.
tb,obs=crear();tb.disconnect((tb.cierre_rx,0),(tb.sin_etiquetas,0))
descartar_tx=blocks.null_sink(8);tb.connect(tb.cierre_rx,descartar_tx)
signal=np.concatenate([np.zeros(7*4),samples[:768],np.zeros(11*4),samples[768:],np.zeros(3*4)]).astype(np.complex64)
tag=gr.tag_t();tag.offset=13;tag.key=pmt.intern('packet_len');tag.value=pmt.from_long(1);tag.srcid=pmt.intern('limite_falso')
tag2=gr.tag_t();tag2.offset=800;tag2.key=pmt.intern('privada');tag2.value=pmt.from_long(999);tag2.srcid=pmt.intern('limite_falso')
source=blocks.vector_source_c(signal.tolist(),False,1,[tag,tag2]);clean=blocks.vector_sink_c();filtered=blocks.vector_sink_c()
tb.connect(source,tb.sin_etiquetas);tb.connect(tb.sin_etiquetas,clean);tb.connect(tb.filtro_rx,filtered)
tb.set_max_noutput_items(13);tb.start()
try:
    fin=time.monotonic()+6
    while obs.num_messages()<2 and time.monotonic()<fin:QtTest.QTest.qWait(5)
    assert [pmt.symbol_to_string(obs.get_message(i)) for i in range(obs.num_messages())]==['Hola','SDR']
    QtTest.QTest.qWait(60);assert not clean.tags() and not filtered.tags()
    assert np.array_equal(np.array(clean.data()),signal)
    print('MUESTRAS_SIN_LIMITES_OK',flush=True)
finally:tb.stop();tb.wait();tb.close()
"""
    assert "MUESTRAS_SIN_LIMITES_OK" in ejecutar(grafo, programa, tmp_path, runtime)


def test_crc_y_ausencia_de_ruta_de_muestras(tmp_path, runtime):
    grafo = grafo_stream(GUIA.read_text(), alterar=True)
    programa = r"""
import time,pmt
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i14_stream_prueba import enlace_i14_stream_prueba,snippets_main_after_init
app=QtWidgets.QApplication([])
def crear():
    t=enlace_i14_stream_prueba();snippets_main_after_init(t);p=blocks.message_debug();o=blocks.message_debug()
    t.msg_connect((t.paquete_rx_a_pdu,'pdus'),(p,'store'));t.msg_connect((t.epy_block_1,'out'),(o,'store'))
    ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
    return t,p,o,ed
tb,pkts,textos,editor=crear()
def enviar(npkt,ntxt):
    editor.setText('Hola');QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return);fin=time.monotonic()+5
    while (pkts.num_messages()<npkt or textos.num_messages()<ntxt) and time.monotonic()<fin:QtTest.QTest.qWait(5)
    QtTest.QTest.qWait(50);assert pkts.num_messages()==npkt and textos.num_messages()==ntxt
try:
    tb.start();enviar(1,1);enviar(2,1);enviar(3,2)
    assert bytes(pmt.u8vector_elements(pmt.cdr(pkts.get_message(1))))==bytes.fromhex('00 04 49 6f 6c 61 aa 94 8e c9')
finally:tb.stop();tb.wait();tb.close()
tb,pkts,textos,editor=crear()
tb.msg_disconnect((tb.epy_block_2,'out'),(tb.epy_block_4,'in'));tb.msg_disconnect((tb.epy_block_4,'out'),(tb.envolver_trama,'pdu'))
tb.msg_connect((tb.epy_block_2,'out'),(tb.envolver_trama,'pdu'))
try:
    tb.start();enviar(1,1);enviar(2,2)
finally:tb.stop();tb.wait();tb.close()
tb,pkts,textos,editor=crear()
# Se corta únicamente la ruta de muestras hacia RX. TX sigue procesando mensajes.
tb.disconnect((tb.cierre_rx,0),(tb.sin_etiquetas,0))
descartar_tx=blocks.null_sink(8);tb.connect(tb.cierre_rx,descartar_tx)
dummy=blocks.null_source(8);tb.connect(dummy,tb.sin_etiquetas)
try:
    tb.start();editor.setText('Hola');QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
    QtTest.QTest.qWait(250);assert pkts.num_messages()==textos.num_messages()==0
    print('CRC_Y_RUTA_RX_OK',flush=True)
finally:tb.stop();tb.wait();tb.close()
"""
    salida = ejecutar(grafo, programa, tmp_path, runtime)
    assert salida.count("CRC incorrecto. Se rechaza.") == 1
    assert "CRC_Y_RUTA_RX_OK" in salida


def test_figuras_receptor_stream_reproducibles(tmp_path):
    ruta = GUIA.parent / "figures/gen_enlace_stream.py"
    spec = importlib.util.spec_from_file_location("figuras_stream", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    archivos = mod.generar(tmp_path)
    assert [p.name for p in archivos] == [
        "enlace-68-conexion-receptor-stream.png",
        "enlace-69-muestras-stream-hola.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in archivos)
    rx, sel, indices = mod.datos_stream()
    assert len(rx) == 768 and len(sel) == 192
    assert list(indices) == list(range(0, 768, 4))

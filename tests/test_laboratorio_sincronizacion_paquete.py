"""Valida la envoltura y el detector estándar con el protocolo de la guía."""

import importlib.util
import re
import subprocess

import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_recuperacion_paquete import ejecutar, grafo_paquete
from test_laboratorio_rrc import configuracion
from test_laboratorio_senal_temporal import parametros


def grafo_sincronizacion(guia, sps=4, alpha=0.35, alterar=False):
    grafo = grafo_paquete(guia, sps, alpha, alterar)
    seccion = guia.split("## 16. Detectar el comienzo y la longitud", 1)[1].split(
        "## 17.", 1
    )[0].split("## Siguiente paso", 1)[0]

    def bloque(nombre, tipo, valores):
        grafo["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )

    for nombre, valor in parametros(seccion, "### 16.2.").items():
        bloque(nombre, "variable", {"value": valor})
    tx = configuracion(seccion, "### 16.3.", "envolver_trama")
    rx = configuracion(seccion, "### 16.4.", "detectar_trama")
    debug = configuracion(seccion, "### 16.4.", "debug_trama_tx")
    tags = configuracion(seccion, "### 16.4.", "debug_deteccion")
    bloque(
        tx["ID"],
        "pdu_pdu_lambda",
        {"fn": tx["Function"], "metadict": tx["Mode"], "key": "pmt.PMT_NIL"},
    )
    bloque(
        rx["ID"],
        "digital_correlate_access_code_xx_ts",
        {
            "type": rx["IO Type"].lower(),
            "access_code": rx["Access Code"],
            "threshold": rx["Threshold"],
            "tagname": rx["Tag Name"],
        },
    )
    bloque(
        debug["ID"],
        "blocks_message_debug",
        {
            "en_uvec": {"On": "True", "Off": "False"}[debug["Print PDU contents"]],
            "log_level": debug["Log level"].lower(),
        },
    )
    bloque(
        tags["ID"],
        "blocks_tag_debug",
        {
            "type": tags["Input Type"].lower(),
            "name": tags["Name"],
            "filter": tags["Key Filter"],
            "vlen": "1",
            "num_inputs": "1",
            "display": {"On": "True", "Off": "False"}[tags["Display"]],
        },
    )
    for b in grafo["blocks"]:
        if b["name"] == "ajustar_buffers":
            b["parameters"]["code"] = next(
                c
                for c in re.findall(r"```python\n(.*?)\n```", seccion, re.S)
                if "self.detectar_trama.set_min_output_buffer" in c
            )
    conexiones = grafo["connections"]
    origen = "epy_block_4" if alterar else "epy_block_2"
    conexiones.remove([origen, "out", "epy_block_5", "in"])
    conexiones.remove(["decidir_bits", "0", "empaquetar_bits", "0"])
    conexiones += [
        [origen, "out", "envolver_trama", "pdu"],
        ["envolver_trama", "pdu", "epy_block_5", "in"],
        ["envolver_trama", "pdu", "debug_trama_tx", "print"],
        ["decidir_bits", "0", "detectar_trama", "0"],
        ["detectar_trama", "0", "empaquetar_bits", "0"],
        ["detectar_trama", "0", "debug_deteccion", "0"],
    ]
    grafo["options"]["parameters"].update(
        id="enlace_i13_sync_prueba", title="Prueba de detección de paquetes"
    )
    return grafo


@pytest.mark.parametrize("sps,alpha", [(4, 0.35), (8, 0.35), (4, 0.20), (4, 0.50)])
def test_trama_por_filtros_y_detector_recupera_corpus(tmp_path, runtime, sps, alpha):
    grafo = grafo_sincronizacion(GUIA.read_text(), sps, alpha)
    programa = r"""
import struct,time,zlib,pmt
import numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i13_sync_prueba import enlace_i13_sync_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);tb=enlace_i13_sync_prueba();snippets_main_after_init(tb)
frames=blocks.message_debug();paquetes=blocks.message_debug();textos=blocks.message_debug();seleccion=blocks.message_debug()
for origen,puerto,o in [('envolver_trama','pdu',frames),('paquete_rx_a_pdu','pdus',paquetes),('epy_block_1','out',textos),('muestrear_rx','pdu',seleccion)]:
    tb.msg_connect((getattr(tb,origen),puerto),(o,'store'))
entrada=blocks.vector_sink_b();salida=blocks.vector_sink_b()
tb.connect(tb.decidir_bits,entrada);tb.connect(tb.detectar_trama,salida)
editor,=[w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
corpus=['Hola','SDR','¡Hola, Perú!','a'*5000,'  texto  ','Hola'];refs=[];tramas=[]
assert tb.sync_bits==''.join(f'{b:08b}' for b in tb.sync_bytes)
assert tb.max_trama_bytes==5018 and tb.max_trama_bits==40144
tb.start()
try:
    for i,texto in enumerate(corpus):
        datos=texto.encode('utf-8');body=struct.pack('>H',len(datos))+datos
        pkt=body+struct.pack('>I',zlib.crc32(body));refs.append(pkt)
        frame=bytes(tb.sync_bytes)+struct.pack('>HH',len(pkt),len(pkt))+pkt;tramas.append(frame)
        editor.setText(texto);QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
        limite=time.monotonic()+6
        while (paquetes.num_messages()<i+1 or textos.num_messages()<i+1) and time.monotonic()<limite:QtTest.QTest.qWait(5)
        assert paquetes.num_messages()==textos.num_messages()==i+1
        assert bytes(pmt.u8vector_elements(pmt.cdr(frames.get_message(i))))==frame
        assert bytes(pmt.u8vector_elements(pmt.cdr(paquetes.get_message(i))))==pkt
        assert pmt.symbol_to_string(textos.get_message(i))==texto
        selected=np.array(pmt.c32vector_elements(pmt.cdr(seleccion.get_message(i))))
        assert len(selected)==8*len(frame)
        assert np.array_equal((selected.real>=0).astype(np.uint8),np.unpackbits(np.frombuffer(frame,dtype=np.uint8),bitorder='big'))
        if i==0:
            QtTest.QTest.qWait(150);assert textos.num_messages()==1
    QtTest.QTest.qWait(60)
    assert np.array_equal(np.array(entrada.data()),np.concatenate([np.unpackbits(np.frombuffer(f,dtype=np.uint8),bitorder='big') for f in tramas]))
    assert np.array_equal(np.array(salida.data()),np.concatenate([np.unpackbits(np.frombuffer(p,dtype=np.uint8),bitorder='big') for p in refs]))
    tags=[t for t in salida.tags() if pmt.symbol_to_string(t.key)=='packet_len']
    assert [pmt.to_long(t.value) for t in tags]==[8*len(p) for p in refs]
    assert [t.offset for t in tags]==list(np.cumsum([0]+[8*len(p) for p in refs[:-1]]))
    assert all(pmt.symbol_to_string(t.srcid).startswith('correlate_access_code') for t in tags)
    assert [pmt.to_long(t.value) for t in entrada.tags() if pmt.symbol_to_string(t.key)=='packet_len']==[8*len(f) for f in tramas]
    print('SINCRONIZACION_OK',tb.sps,tb.rrc_alpha,[len(f) for f in tramas],flush=True)
finally:tb.stop();tb.wait();tb.close()
"""
    salida = ejecutar(grafo, programa, tmp_path, runtime)
    assert "[22, 21, 32, 5018, 27, 22]" in salida
    assert "SINCRONIZACION_OK" in salida
    assert "CRC incorrecto" not in salida


def test_detector_sin_limites_ignora_tags_falsos_y_cabeceras_invalidas(
    tmp_path, runtime
):
    programa = r"""
import numpy as np,pmt,struct,zlib
from gnuradio import blocks,digital,gr
sync=bytes.fromhex('ac dd a4 e2 f2 8c 20 fc');code=''.join(f'{b:08b}' for b in sync)
def bits(b):return np.unpackbits(np.frombuffer(b,dtype=np.uint8),bitorder='big').tolist()
def packet(data):
    b=struct.pack('>H',len(data))+data;return b+struct.pack('>I',zlib.crc32(b))
def frame(p):return sync+struct.pack('>HH',len(p),len(p))+p
p=packet(b'Hola');q=packet(b'SDR');r=packet(b'payload'+sync+b'fin')
mal_sync=bytearray(frame(p));mal_sync[0]^=1
mal_header=sync+struct.pack('>HH',len(p),len(p)+1)+p
datos=[1,0,1,1,0]+bits(mal_sync)+[1]*17+bits(mal_header)+bits(frame(p))+[0]*3+bits(frame(q))+[1,0]*9+bits(frame(r))+[0]*9
tag=gr.tag_t();tag.offset=2;tag.key=pmt.intern('packet_len');tag.value=pmt.from_long(1);tag.srcid=pmt.intern('tx_falso')
extra=gr.tag_t();extra.offset=5;extra.key=pmt.intern('privada');extra.value=pmt.from_long(999);extra.srcid=pmt.intern('tx_falso')
t=gr.top_block();src=blocks.vector_source_b(datos,False,1,[tag,extra]);c=digital.correlate_access_code_bb_ts(code,0,'packet_len');sink=blocks.vector_sink_b()
t.connect(src,c,sink);t.run()
assert list(sink.data())==bits(p)+bits(q)+bits(r)
tags=sink.tags();assert [pmt.symbol_to_string(x.key) for x in tags]==['packet_len']*3
assert [pmt.to_long(x.value) for x in tags]==[8*len(p),8*len(q),8*len(r)]
assert [x.offset for x in tags]==[0,8*len(p),8*(len(p)+len(q))]
print('DETECTOR_SIN_LIMITES_OK')
"""
    r = subprocess.run(
        [runtime[1], "-c", programa], capture_output=True, text=True, timeout=15
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DETECTOR_SIN_LIMITES_OK" in r.stdout


def test_crc_tras_deteccion_y_restauracion(tmp_path, runtime):
    grafo = grafo_sincronizacion(GUIA.read_text(), alterar=True)
    programa = r"""
import time,pmt
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i13_sync_prueba import enlace_i13_sync_prueba,snippets_main_after_init
app=QtWidgets.QApplication([])
def instancia():
    t=enlace_i13_sync_prueba();snippets_main_after_init(t);p=blocks.message_debug();o=blocks.message_debug()
    t.msg_connect((t.paquete_rx_a_pdu,'pdus'),(p,'store'));t.msg_connect((t.epy_block_1,'out'),(o,'store'))
    editor,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
    return t,p,o,editor
tb,pkts,textos,editor=instancia()
def enviar(npkt,ntexto):
    editor.setText('Hola');QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
    limite=time.monotonic()+5
    while (pkts.num_messages()<npkt or textos.num_messages()<ntexto) and time.monotonic()<limite:QtTest.QTest.qWait(5)
    QtTest.QTest.qWait(40)
    assert pkts.num_messages()==npkt and textos.num_messages()==ntexto
try:
    tb.start();enviar(1,1);enviar(2,1);enviar(3,2)
    assert bytes(pmt.u8vector_elements(pmt.cdr(pkts.get_message(1))))==bytes.fromhex('00 04 49 6f 6c 61 aa 94 8e c9')
    tb.stop();tb.wait();tb.close();tb,pkts,textos,editor=instancia()
    tb.msg_disconnect((tb.epy_block_2,'out'),(tb.epy_block_4,'in'))
    tb.msg_disconnect((tb.epy_block_4,'out'),(tb.envolver_trama,'pdu'))
    tb.msg_connect((tb.epy_block_2,'out'),(tb.envolver_trama,'pdu'))
    tb.start();enviar(1,1);enviar(2,2)
    print('SYNC_CRC_RESTAURADO_OK')
finally:tb.stop();tb.wait();tb.close()
"""
    salida = ejecutar(grafo, programa, tmp_path, runtime)
    assert salida.count("CRC incorrecto. Se rechaza.") == 1
    assert "SYNC_CRC_RESTAURADO_OK" in salida


def test_figuras_de_trama_y_detector_reproducibles(tmp_path):
    ruta = GUIA.parent / "figures/gen_enlace_sincronizacion.py"
    spec = importlib.util.spec_from_file_location("figuras_sync", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    archivos = modulo.generar(tmp_path)
    assert [p.name for p in archivos] == [
        "enlace-60-formato-trama.png",
        "enlace-61-conexion-deteccion.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in archivos)
    assert modulo.trama_hola() == bytes.fromhex(
        "ac dd a4 e2 f2 8c 20 fc 00 0a 00 0a 00 04 48 6f 6c 61 aa 94 8e c9"
    )

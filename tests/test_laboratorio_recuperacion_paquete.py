"""Ejecuta la recuperación del paquete con los bloques estándar de la guía."""

import importlib.util
import os
from pathlib import Path
import re
import subprocess

import pytest
import yaml

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_receptor_ideal import grafo_receptor
from test_laboratorio_rrc import configuracion


GUIA = Path(os.environ.get("SDR_I12_GUIA", str(GUIA)))


def grafo_paquete(guia, sps=4, alpha=0.35, alterar=False):
    grafo = grafo_receptor(guia, sps, alpha)
    seccion = (
        guia.split("## 15. Recuperar los bytes", 1)[1]
        .split("## 16.", 1)[0]
        .split("## Siguiente paso", 1)[0]
    )

    def cfg(nombre):
        return configuracion(seccion, "### 15.3.", nombre)

    def bloque(nombre, tipo, parametros):
        grafo["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": parametros,
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )

    entrada = cfg("rx_a_stream")
    real = cfg("extraer_i")
    decisor = cfg("decidir_bits")
    pack = cfg("empaquetar_bits")
    salida = cfg("paquete_rx_a_pdu")
    debug = configuracion(seccion, "### 15.4.", "debug_paquete_rx")
    bloque(
        entrada["ID"],
        "pdu_pdu_to_tagged_stream",
        {"type": entrada["Item Type"].lower(), "tag": entrada["Length tag name"]},
    )
    bloque(real["ID"], "blocks_complex_to_real", {"vlen": real["Vector Length"]})
    bloque(decisor["ID"], "digital_binary_slicer_fb", {})
    bloque(
        pack["ID"],
        "blocks_repack_bits_bb",
        {
            "k": pack["Bits per input byte"],
            "l": pack["Bits per output byte"],
            "len_tag_key": pack["Length Tag Key"],
            "align_output": {"Output": "True", "Input": "False"}[
                pack["Packet Alignment"]
            ],
            "endianness": {"MSB": "gr.GR_MSB_FIRST", "LSB": "gr.GR_LSB_FIRST"}[
                pack["Endianness"]
            ],
        },
    )
    bloque(
        salida["ID"],
        "pdu_tagged_stream_to_pdu",
        {"type": salida["Item Type"].lower(), "tag": salida["Length tag name"]},
    )
    bloque(
        debug["ID"],
        "blocks_message_debug",
        {
            "en_uvec": {"On": "True", "Off": "False"}[debug["Print PDU contents"]],
            "log_level": debug["Log level"].lower(),
        },
    )
    codigos = re.findall(r"```python\n(.*?)\n```", guia, re.S)
    for numero, nombre in [(3, "Comprobar paquete"), (1, "Bytes a texto UTF-8")]:
        codigo = next(c for c in codigos if f'name="{nombre}"' in c)
        bloque(f"epy_block_{numero}", "epy_block", {"_source_code": codigo})
    bloque(
        "blocks_message_debug_0",
        "blocks_message_debug",
        {"en_uvec": "False", "log_level": "info"},
    )
    for b in grafo["blocks"]:
        if b["name"] == "ajustar_buffers":
            b["parameters"]["code"] = next(
                c
                for c in re.findall(r"```python\n(.*?)\n```", seccion, re.S)
                if "self.decidir_bits.set_min_output_buffer" in c
            )
    grafo["connections"] += [
        ["muestrear_rx", "pdu", "rx_a_stream", "pdus"],
        ["rx_a_stream", "0", "extraer_i", "0"],
        ["extraer_i", "0", "decidir_bits", "0"],
        ["decidir_bits", "0", "empaquetar_bits", "0"],
        ["empaquetar_bits", "0", "paquete_rx_a_pdu", "0"],
        ["paquete_rx_a_pdu", "pdus", "debug_paquete_rx", "print"],
        ["paquete_rx_a_pdu", "pdus", "epy_block_3", "in"],
        ["epy_block_3", "out", "epy_block_1", "in"],
        ["epy_block_1", "out", "blocks_message_debug_0", "print"],
    ]
    if alterar:
        codigo = next(c for c in codigos if 'name="Alterar segundo paquete"' in c)
        bloque("epy_block_4", "epy_block", {"_source_code": codigo})
        grafo["connections"].remove(["epy_block_2", "out", "epy_block_5", "in"])
        grafo["connections"] += [
            ["epy_block_2", "out", "epy_block_4", "in"],
            ["epy_block_4", "out", "epy_block_5", "in"],
        ]
    grafo["options"]["parameters"].update(
        id="enlace_i12_paquete_prueba", title="Prueba de recuperación del paquete"
    )
    return grafo


def ejecutar(grafo, programa, tmp_path, runtime):
    archivo = tmp_path / "recuperacion_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False))
    compilacion = subprocess.run(
        [runtime[0], "-o", str(tmp_path), str(archivo)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    resultado = subprocess.run(
        [runtime[1], "-c", programa],
        cwd=tmp_path,
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "MPLCONFIGDIR": str(tmp_path / "matplotlib"),
        },
        capture_output=True,
        text=True,
        timeout=35,
    )
    assert resultado.returncode == 0, resultado.stdout[-6000:] + resultado.stderr
    return resultado.stdout


@pytest.mark.parametrize(
    "sps,alpha",
    [(4, 0.35), (8, 0.35), (4, 0.20), (4, 0.50)],
    ids=["sps4", "sps8", "alpha020", "alpha050"],
)
def test_paquetes_texto_aislados_consecutivos_y_maximo(tmp_path, runtime, sps, alpha):
    grafo = grafo_paquete(GUIA.read_text(), sps, alpha)
    programa = r"""
import os,struct,time,zlib
from pathlib import Path
import numpy as np,pmt
from gnuradio import blocks,gr,digital
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i12_paquete_prueba import enlace_i12_paquete_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);tb=enlace_i12_paquete_prueba();snippets_main_after_init(tb)
observadores=[blocks.message_debug() for _ in range(4)]
for origen,puerto,o in zip(('muestrear_rx','paquete_rx_a_pdu','epy_block_3','epy_block_1'),('pdu','pdus','out','out'),observadores):
    tb.msg_connect((getattr(tb,origen),puerto),(o,'store'))
bits=blocks.vector_sink_b();paquetes=blocks.vector_sink_b()
tb.connect(tb.decidir_bits,bits);tb.connect(tb.empaquetar_bits,paquetes)
tb.resize(1150,1050);tb.show();tb.vistas.setCurrentIndex(1);tb.start();app.processEvents()
editor,=[w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
textos=['Hola','SDR','¡Hola, Perú!','a'*5000,'  texto  ','Hola']
refs=[]
def esperar(n):
    limite=time.monotonic()+6
    while any(o.num_messages()<n for o in observadores[1:]) and time.monotonic()<limite:QtTest.QTest.qWait(5)
    assert [o.num_messages() for o in observadores[1:]]==[n]*3
try:
    for i,texto in enumerate(textos):
        b=texto.encode('utf-8');c=struct.pack('!H',len(b))+b
        refs.append(c+struct.pack('!I',zlib.crc32(c)))
        editor.setText(texto);QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
        esperar(i+1)
        m=observadores[0].get_message(i);assert pmt.is_c32vector(pmt.cdr(m))
        simbolos=np.array(pmt.c32vector_elements(pmt.cdr(m)))
        assert len(simbolos)==8*len(refs[i]) and np.all(simbolos.imag==0)
        msg=observadores[1].get_message(i);assert pmt.is_u8vector(pmt.cdr(msg))
        recibido=bytes(pmt.u8vector_elements(pmt.cdr(msg)))
        assert recibido==refs[i],(i,recibido[:24].hex(),refs[i][:24].hex())
        assert np.array_equal((simbolos.real>=0).astype(np.uint8),np.unpackbits(np.frombuffer(refs[i],dtype=np.uint8),bitorder='big'))
        assert bytes(pmt.u8vector_elements(pmt.cdr(observadores[2].get_message(i))))==b
        assert pmt.symbol_to_string(observadores[3].get_message(i))==texto
        if i==0:
            QtTest.QTest.qWait(200);assert [o.num_messages() for o in observadores]==[1]*4
            carpeta=os.environ.get('SDR_I12_CAPTURE_DIR')
            if carpeta and tb.sps==4 and abs(tb.rrc_alpha-.35)<1e-8:
                p=Path(carpeta);p.mkdir(parents=True,exist_ok=True)
                assert tb.grab().save(str(p/'rx-validacion-paso15.png'))
    QtTest.QTest.qWait(60)
    assert [o.num_messages() for o in observadores]==[len(textos)]*4
    assert bytes(paquetes.data())==b''.join(refs)
    assert np.array_equal(np.array(bits.data()),np.concatenate([np.unpackbits(np.frombuffer(p,dtype=np.uint8),bitorder='big') for p in refs]))
    for sink,lengths in [(bits,[8*len(p) for p in refs]),(paquetes,[len(p) for p in refs])]:
        tags=[t for t in sink.tags() if pmt.symbol_to_string(t.key)=='packet_len']
        assert [pmt.to_long(t.value) for t in tags]==lengths
        assert [t.offset for t in tags]==list(np.cumsum([0]+lengths[:-1]))
    # Instrumentación: comprueba metadatos a través de la nueva rama estándar.
    meta=pmt.dict_add(pmt.make_dict(),pmt.intern('prueba'),pmt.from_long(15))
    tb.rx_a_stream.to_basic_block()._post(pmt.intern('pdus'),pmt.cons(meta,pmt.cdr(observadores[0].get_message(0))))
    esperar(len(textos)+1)
    for o in observadores[1:3]:
        assert pmt.to_long(pmt.dict_ref(pmt.car(o.get_message(len(textos))),pmt.intern('prueba'),pmt.PMT_NIL))==15
    assert pmt.symbol_to_string(observadores[3].get_message(len(textos)))=='Hola'
    # El comportamiento exacto del umbral se verifica con floats conocidos.
    t=gr.top_block();v=blocks.vector_source_f([-1,-1e-6,0,1e-6,1]);s=digital.binary_slicer_fb();o=blocks.vector_sink_b()
    t.connect(v,s,o);t.run();assert list(o.data())==[0,0,1,1,1]
    print('RECUPERACION_OK',tb.sps,tb.rrc_alpha,[len(p) for p in refs],flush=True)
finally:tb.stop();tb.wait();tb.close()
"""
    salida = ejecutar(grafo, programa, tmp_path, runtime)
    assert f"RECUPERACION_OK {sps} {alpha} [10, 9, 20, 5006, 15, 10]" in salida
    assert "Comprobar paquete:" not in salida
    assert "Bytes a texto:" not in salida
    assert "pdu length =         10 bytes" in salida
    assert "0000: 00 04 48 6f 6c 61 aa 94 8e c9" in salida


def test_bit_alterado_se_rechaza_despues_de_los_filtros_y_se_restaura(
    tmp_path, runtime
):
    grafo = grafo_paquete(GUIA.read_text(), alterar=True)
    programa = r"""
import struct,time,zlib,pmt
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i12_paquete_prueba import enlace_i12_paquete_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);tb=enlace_i12_paquete_prueba();snippets_main_after_init(tb)
paquetes=blocks.message_debug();textos=blocks.message_debug()
tb.msg_connect((tb.paquete_rx_a_pdu,'pdus'),(paquetes,'store'))
tb.msg_connect((tb.epy_block_1,'out'),(textos,'store'))
editor,=[w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
b=b'Hola';c=struct.pack('!H',len(b))+b;normal=c+struct.pack('!I',zlib.crc32(c))
alterado=bytearray(normal);alterado[2]^=1
assert zlib.crc32(alterado[:-4])!=struct.unpack('!I',alterado[-4:])[0]
def enviar(n,t,mal=False):
    editor.setText('Hola');QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
    fin=time.monotonic()+5
    while (paquetes.num_messages()<n or textos.num_messages()<t) and time.monotonic()<fin:QtTest.QTest.qWait(5)
    QtTest.QTest.qWait(50)
    assert paquetes.num_messages()==n and textos.num_messages()==t
    assert bytes(pmt.u8vector_elements(pmt.cdr(paquetes.get_message(n-1))))==(bytes(alterado) if mal else normal)
try:
    tb.start();enviar(1,1);enviar(2,1,True);enviar(3,2)
    assert [pmt.symbol_to_string(textos.get_message(i)) for i in range(2)]==['Hola']*2
    tb.stop();tb.wait();tb.close()
    # GRC crea un programa nuevo al restablecer y ejecutar el montaje.
    tb=enlace_i12_paquete_prueba();snippets_main_after_init(tb)
    paquetes=blocks.message_debug();textos=blocks.message_debug()
    tb.msg_connect((tb.paquete_rx_a_pdu,'pdus'),(paquetes,'store'))
    tb.msg_connect((tb.epy_block_1,'out'),(textos,'store'))
    editor,=[w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
    tb.msg_disconnect((tb.epy_block_2,'out'),(tb.epy_block_4,'in'))
    tb.msg_disconnect((tb.epy_block_4,'out'),(tb.epy_block_5,'in'))
    tb.msg_connect((tb.epy_block_2,'out'),(tb.epy_block_5,'in'))
    tb.start();enviar(1,1);enviar(2,2)
    assert [pmt.symbol_to_string(textos.get_message(i)) for i in range(2)]==['Hola']*2
    print('CRC_RECHAZO_Y_RESTAURACION_OK',flush=True)
finally:tb.stop();tb.wait();tb.close()
"""
    salida = ejecutar(grafo, programa, tmp_path, runtime)
    assert salida.count("Comprobar paquete: CRC incorrecto. Se rechaza.") == 1
    assert "Inyector: paquete 2, bit alterado." in salida
    assert "CRC_RECHAZO_Y_RESTAURACION_OK" in salida
    assert "Iola" not in salida


def test_figuras_de_decisiones_y_conexiones_reproducibles(tmp_path):
    ruta = Path(
        os.environ.get(
            "SDR_I12_GENERADOR", str(GUIA.parent / "figures/gen_enlace_recuperacion.py")
        )
    )
    spec = importlib.util.spec_from_file_location("figuras_recuperacion", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    archivos = modulo.generar(tmp_path)
    assert [p.name for p in archivos] == [
        "enlace-51-decisiones-bytes-hola.png",
        "enlace-52-conexion-recuperar-paquete.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in archivos)
    amplitudes, bits, paquete = modulo.datos_hola()
    assert len(amplitudes) == len(bits) == 80
    assert list(bits[16:24]) == [0, 1, 0, 0, 1, 0, 0, 0]
    assert paquete == bytes.fromhex("00 04 48 6f 6c 61 aa 94 8e c9")

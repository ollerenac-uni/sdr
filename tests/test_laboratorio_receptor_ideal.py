"""Comprueba el RRC receptor, cierre, retardo y selección ideal por paquete."""

import importlib.util
import os
import re
import subprocess

import numpy as np
import pytest
import yaml

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_rrc import configuracion, grafo_rrc
from test_laboratorio_senal_temporal import parametros


def grafo_receptor(guia, sps, alpha):
    grafo = grafo_rrc(guia, sps, alpha)
    seccion = guia.split("## 14. Filtrar en el receptor ideal", 1)[1].split(
        "## 15.", 1
    )[0].split("## Siguiente paso", 1)[0]
    variables = parametros(seccion, "### 14.2.")

    def cfg(apartado, identificador):
        return configuracion(seccion, apartado, identificador)

    cierre = cfg("### 14.3.", "cierre_rx")
    filtro = cfg("### 14.4.", "filtro_rx")
    adaptador = cfg("### 14.5.", "rx_a_pdu")
    selector = cfg("### 14.5.", "muestrear_rx")
    tiempo = cfg("### 14.7.", "tiempo_rx")
    constelacion = cfg("### 14.7.", "constelacion_rx")
    debug = cfg("### 14.7.", "debug_rx")
    debug_s = cfg("### 14.7.", "debug_simbolos_rx")
    vistas = cfg("### 14.8.", "vistas")
    fragmento = seccion.split("### 14.8.", 1)[1].split("### 14.9.", 1)[0]
    hints = {
        k.replace("`", ""): v
        for k, v in re.findall(r"^\| (.*?) \| `([^`]+)` \|$", fragmento, re.M)
    }
    bloques = grafo["blocks"]
    for b in bloques:
        if b["name"] == "ajustar_buffers":
            b["parameters"]["code"] = next(
                c
                for c in re.findall(r"```python\n(.*?)\n```", seccion, re.S)
                if "self.filtro_rx.set_min_output_buffer" in c
            )
        if b["name"] in ("tiempo_bpsk", "tiempo_rrc"):
            b["parameters"]["gui_hint"] = hints[b["name"]]
        if b["name"] == "mensaje_a":
            b["parameters"]["gui_hint"] = hints["QT GUI Message Edit Box existente"]
        if b["name"] == "constelacion":
            b["parameters"]["gui_hint"] = hints["QT GUI Constellation Sink existente"]

    def bloque(nombre, tipo, valores):
        bloques.append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )

    for nombre, valor in variables.items():
        bloque(nombre, "variable", {"value": valor})
    bloque(
        cierre["ID"],
        "digital_burst_shaper_xx",
        {
            "type": cierre["Type"].lower(),
            "window": cierre["Window Taps"],
            "pre_padding": cierre["Pre-padding Length"],
            "post_padding": cierre["Post-padding Length"],
            "insert_phasing": {"No": "False", "Yes": "True"}[
                cierre["Insert phasing symbols"]
            ],
            "length_tag_name": cierre["Length Tag Name"],
        },
    )
    bloque(
        filtro["ID"],
        "root_raised_cosine_filter",
        {
            "type": {"Complex->Complex (Decimating)": "fir_filter_ccf"}[
                filtro["FIR Type"]
            ],
            "decim": filtro["Decimation"],
            "gain": filtro["Gain"],
            "samp_rate": filtro["Sample Rate"],
            "sym_rate": filtro["Symbol Rate"],
            "alpha": filtro["Alpha"],
            "ntaps": filtro["Num Taps"],
        },
    )
    bloque(
        adaptador["ID"],
        "pdu_tagged_stream_to_pdu",
        {"type": adaptador["Item Type"].lower(), "tag": adaptador["Length tag name"]},
    )
    bloque(
        selector["ID"],
        "pdu_pdu_lambda",
        {
            "fn": selector["Function"],
            "metadict": selector["Mode"],
            "key": "pmt.PMT_NIL",
        },
    )
    bloque(
        tiempo["ID"],
        "qtgui_time_sink_x",
        {
            "type": "msg_complex",
            "name": tiempo["Name"],
            "srate": tiempo["Sample Rate"],
            "grid": "True",
            "autoscale": "False",
            "ymin": tiempo["Y min"],
            "ymax": tiempo["Y max"],
            "label1": tiempo["Line 1 Label"],
            "label2": tiempo["Line 2 Label"],
            "style1": "1",
            "style2": "1",
            "marker1": "0",
            "marker2": "0",
            "gui_hint": hints["tiempo_rx"],
            "update_time": ".01",
        },
    )
    bloque(
        constelacion["ID"],
        "qtgui_const_sink_x",
        {
            "type": "msg_complex",
            "name": constelacion["Name"],
            "grid": "True",
            "autoscale": "False",
            "xmin": constelacion["X min"],
            "xmax": constelacion["X max"],
            "ymin": constelacion["Y min"],
            "ymax": constelacion["Y max"],
            "gui_hint": hints["constelacion_rx"],
            "update_time": ".01",
        },
    )
    for valores in (debug, debug_s):
        bloque(
            valores["ID"],
            "blocks_message_debug",
            {
                "en_uvec": {"Off": "False", "On": "True"}[
                    valores["Print PDU contents"]
                ],
                "log_level": "info",
            },
        )
    bloque(
        vistas["ID"],
        "qtgui_tab_widget",
        {
            "num_tabs": vistas["Num Tabs"],
            "label0": vistas["Label 0"],
            "label1": vistas["Label 1"],
            "gui_hint": vistas["GUI Hint"],
        },
    )
    grafo["connections"] += [
        ["longitud_rrc", "0", "cierre_rx", "0"],
        ["cierre_rx", "0", "filtro_rx", "0"],
        ["filtro_rx", "0", "rx_a_pdu", "0"],
        ["rx_a_pdu", "pdus", "tiempo_rx", "in"],
        ["rx_a_pdu", "pdus", "debug_rx", "print"],
        ["rx_a_pdu", "pdus", "muestrear_rx", "pdu"],
        ["muestrear_rx", "pdu", "constelacion_rx", "in"],
        ["muestrear_rx", "pdu", "debug_simbolos_rx", "print"],
    ]
    grafo["options"]["parameters"].update(
        id="enlace_i11_receptor_prueba", title="Prueba del receptor ideal"
    )
    return grafo


@pytest.mark.parametrize(
    "sps,alpha",
    [(4, 0.35), (8, 0.35), (4, 0.20), (4, 0.50)],
    ids=["sps4", "sps8", "alpha020", "alpha050"],
)
def test_receptor_rrc_y_simbolos_recuperados(tmp_path, runtime, sps, alpha):
    grafo = grafo_receptor(GUIA.read_text(), sps, alpha)
    archivo = tmp_path / "receptor_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False))
    resultado = subprocess.run(
        [runtime[0], "-o", str(tmp_path), str(archivo)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    programa = r"""
import os, struct, time, zlib
from pathlib import Path
import numpy as np
import pmt
from gnuradio import blocks
from gnuradio.filter import firdes
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i11_receptor_prueba import enlace_i11_receptor_prueba,snippets_main_after_init
app=QtWidgets.QApplication([])
tb=enlace_i11_receptor_prueba();snippets_main_after_init(tb)
observadores=[blocks.message_debug() for _ in range(5)]
for origen,o in zip(('simbolos_a_pdu','muestras_a_pdu','rrc_a_pdu','rx_a_pdu','muestrear_rx'),observadores):
    tb.msg_connect((getattr(tb,origen),'pdu' if origen=='muestrear_rx' else 'pdus'),(o,'store'))
tags=blocks.vector_sink_c();tb.connect(tb.filtro_rx,tags)
ht=np.array(firdes.root_raised_cosine(tb.sps,tb.samp_rate,tb.symbol_rate,tb.rrc_alpha,tb.rrc_ntaps),dtype=np.float32)
hr=np.array(firdes.root_raised_cosine(1,tb.samp_rate,tb.symbol_rate,tb.rrc_alpha,tb.rrc_ntaps),dtype=np.float32)
g=np.convolve(ht,hr);D=tb.retardo_total;L=tb.sps;C=tb.cierre_rx_muestras
assert D==C==8*L and tb.filtro_rx.history()==len(hr)
assert np.argmax(g)==D
bound=abs(1-g[D])+np.sum(abs(g[::L]))-abs(g[D])+2e-6
originales=[];textos=[];sin_compensar=[]
tb.start();tb.resize(1100,1200);tb.show();tb.vistas.setCurrentIndex(1);app.processEvents()
editor,=[w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
assert tb.vistas.count()==2 and [tb.vistas.tabText(i) for i in range(2)]==['Transmisor','Receptor ideal']
def enviar(texto,mal=False):
    editor.setText(texto);QtTest.QTest.keyClick(editor,QtCore.Qt.Key_Return)
    b=texto.encode('utf-8');c=struct.pack('!H',len(b))+b
    paquete=c+struct.pack('!I',zlib.crc32(c))
    bits=np.unpackbits(np.frombuffer(paquete,dtype=np.uint8),bitorder='big')
    originales.append((2*bits.astype(int)-1).astype(np.complex64));textos.append(texto);sin_compensar.append(mal)
def esperar(n,gui=True):
    limite=time.monotonic()+5
    while any(o.num_messages()<n for o in observadores) and time.monotonic()<limite: QtTest.QTest.qWait(5)
    assert all(o.num_messages()==n for o in observadores),[o.num_messages() for o in observadores]
    for i,a in enumerate(originales):
        u=np.zeros((len(a)+8)*L,dtype=np.complex64);u[:len(a)*L:L]=a
        tx=np.convolve(u,ht)[:len(u)]
        entrada=np.r_[tx,np.zeros(C,dtype=np.complex64)]
        rx=np.convolve(entrada,hr)[:len(entrada)]
        datos=[]
        for o in observadores:
            mensaje=o.get_message(i);assert pmt.is_pdu(mensaje) and pmt.is_c32vector(pmt.cdr(mensaje))
            datos.append(np.array(pmt.c32vector_elements(pmt.cdr(mensaje)),dtype=np.complex64))
        assert np.array_equal(datos[0],a) and np.array_equal(datos[1],np.repeat(a,L))
        assert np.allclose(datos[2],tx,rtol=1e-6,atol=1e-6)
        y,d=datos[3:]
        assert len(y)==(len(a)+16)*L and y.nbytes==8*len(y)
        assert np.allclose(y,rx,rtol=1e-6,atol=1e-6),np.max(abs(y-rx))
        ref=rx[0 if sin_compensar[i] else D:-C:L]
        assert len(d)==len(ref) and np.allclose(d,ref,rtol=1e-6,atol=1e-6)
        assert np.all(y.imag==0) and np.all(d.imag==0) and np.all(y[-(L-1):]==0)
        assert pmt.equal(pmt.car(observadores[3].get_message(i)),pmt.car(observadores[4].get_message(i)))
        if sin_compensar[i]:
            assert len(d)==len(a)+8 and abs(d[0])<.01
        else:
            assert len(d)==len(a) and d.nbytes==8*len(a)
            assert np.max(abs(d-a))<=bound
            assert np.array_equal(np.sign(d.real),a.real)
            paquete=np.packbits((d.real>0).astype(np.uint8),bitorder='big').tobytes()
            largo=struct.unpack('!H',paquete[:2])[0]
            assert len(paquete)==2+largo+4 and paquete[2:2+largo].decode('utf-8')==textos[i]
            assert struct.unpack('!I',paquete[-4:])[0]==zlib.crc32(paquete[:-4])
    QtTest.QTest.qWait(60)
    if gui:
        assert tb.tiempo_rx.nsamps()==(len(originales[-1])+16)*L
        assert tb.tiempo_rrc.nsamps()==(len(originales[-1])+8)*L
        assert tb.tiempo_bpsk.nsamps()==len(originales[-1])*L
try:
    enviar('Hola');esperar(1)
    capturas=os.environ.get('SDR_I11_CAPTURE_DIR')
    if capturas and L==4 and abs(tb.rrc_alpha-.35)<1e-8:
        carpeta=Path(capturas);carpeta.mkdir(parents=True,exist_ok=True)
        assert tb.grab().save(str(carpeta/'rx-validacion.png'))
        tb.vistas.setCurrentIndex(0);QtTest.QTest.qWait(60)
        assert tb.grab().save(str(carpeta/'tx-validacion-paso14.png'))
        tb.vistas.setCurrentIndex(1)
    for texto in ('SDR','¡Hola, Perú!','a'*5000): enviar(texto)
    esperar(4,gui=False)
    QtTest.QTest.qWait(200);assert all(o.num_messages()==4 for o in observadores)
    enviar('Hola');esperar(5)
    correcta=tb.muestrear_rx.fn
    tb.muestrear_rx.set_fn(lambda x:x[0:-C:L]);enviar('Hola',True);esperar(6)
    tb.muestrear_rx.set_fn(correcta);enviar('Hola');esperar(7)
    etiquetas=[t for t in tags.tags() if pmt.symbol_to_string(t.key)=='packet_len']
    longitudes=[(len(a)+16)*L for a in originales]
    assert [pmt.to_long(t.value) for t in etiquetas]==longitudes
    assert [t.offset for t in etiquetas]==list(np.cumsum([0]+longitudes[:-1]))
    meta=pmt.dict_add(pmt.make_dict(),pmt.intern('prueba'),pmt.from_long(14))
    tb.muestrear_rx.handle_msg(pmt.cons(meta,pmt.cdr(observadores[3].get_message(0))))
    limite=time.monotonic()+2
    while observadores[4].num_messages()<8 and time.monotonic()<limite: QtTest.QTest.qWait(5)
    assert observadores[4].num_messages()==8
    assert pmt.equal(pmt.car(observadores[4].get_message(7)),meta)
    print('RECEPTOR_GUI_OK',L,tb.rrc_alpha,longitudes)
finally:
    tb.stop();tb.wait();tb.close()
"""
    env = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
    }
    resultado = subprocess.run(
        [runtime[1], "-c", programa],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=35,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    longitudes = [(n + 16) * sps for n in (80, 72, 160, 40048, 80, 80, 80)]
    assert f"RECEPTOR_GUI_OK {sps} {alpha} {longitudes}" in resultado.stdout
    assert f"{96 * sps * 8} bytes (printing disabled)" in resultado.stdout
    assert f"{40064 * sps * 8} bytes (printing disabled)" in resultado.stdout
    assert "704 bytes (printing disabled)" in resultado.stdout


def test_referencias_del_receptor_reproducibles(tmp_path):
    ruta = GUIA.parent / "figures/gen_enlace_receptor.py"
    spec = importlib.util.spec_from_file_location("figuras_receptor", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    archivos = modulo.generar(tmp_path)
    assert [p.name for p in archivos] == [
        "enlace-45-receptor-ideal-hola.png",
        "enlace-46-conexion-receptor-ideal.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in archivos)
    for sps, alpha in [(4, 0.35), (8, 0.35), (4, 0.20), (4, 0.50)]:
        ht, hr, a, tx, rx, indices = modulo.datos_receptor(sps, alpha)
        assert len(rx) == 96 * sps and len(indices) == len(a) == 80
        assert indices[0] == 8 * sps and indices[-1] == 87 * sps
        assert np.argmax(np.convolve(ht, hr)) == 8 * sps
        assert np.array_equal(np.sign(rx[indices].real), a.real) and np.all(
            rx.imag == 0
        )

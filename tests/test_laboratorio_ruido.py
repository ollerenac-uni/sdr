"""Comprueba el canal AWGN y las estadísticas sin modificar el GRC manual."""

import importlib.util
import json
import re
import subprocess

import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_receptor_stream import grafo_stream
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_rrc import configuracion
from test_laboratorio_senal_temporal import parametros


def grafo_ruido(guia, amplitud=None, semilla=None, sps=4, alpha=0.35, alterar=False):
    grafo = grafo_stream(guia, sps, alpha, alterar)
    seccion = (
        guia.split("## 18. Añadir ruido gaussiano", 1)[1]
        .split("## 19.", 1)[0]
        .split("## Siguiente paso", 1)[0]
    )
    variables = parametros(seccion, "### 18.2.")
    if amplitud is not None:
        variables["ruido_amplitud"] = str(amplitud)
    if semilla is not None:
        variables["ruido_semilla"] = str(semilla)

    def bloque(nombre, tipo, valores):
        grafo["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )

    for nombre, valor in variables.items():
        bloque(nombre, "variable", {"value": valor})
    noise = configuracion(seccion, "### 18.3.", "ruido")
    add = configuracion(seccion, "### 18.3.", "sumar_ruido")
    bloque(
        noise["ID"],
        "analog_noise_source_x",
        {
            "type": noise["Output Type"].lower(),
            "noise_type": {"Gaussian": "analog.GR_GAUSSIAN"}[noise["Noise Type"]],
            "amp": noise["Amplitude"],
            "seed": noise["Seed"],
        },
    )
    bloque(
        add["ID"],
        "blocks_add_xx",
        {
            "type": add["IO Type"].lower(),
            "num_inputs": add["Num Inputs"],
            "vlen": add["Vector Length"],
        },
    )
    codigos = re.findall(r"```python\n(.*?)\n```", seccion, re.S)
    init = next(c for c in codigos if "set_save_all(True)" in c)
    for b in grafo["blocks"]:
        if b["name"] == "ajustar_buffers":
            b["parameters"]["code"] += "\n" + init
    bloque(
        "resumen_ensayo",
        "snippet",
        {
            "section": "main_after_stop",
            "priority": "0",
            "code": next(c for c in codigos if "n_tx = " in c),
        },
    )
    grafo["connections"].remove(["sin_etiquetas", "0", "filtro_rx", "0"])
    grafo["connections"] += [
        ["sin_etiquetas", "0", "sumar_ruido", "0"],
        ["ruido", "0", "sumar_ruido", "1"],
        ["sumar_ruido", "0", "filtro_rx", "0"],
        ["envolver_trama", "pdu", "debug_trama_tx", "store"],
        ["paquete_rx_a_pdu", "pdus", "debug_paquete_rx", "store"],
        ["epy_block_1", "out", "blocks_message_debug_0", "store"],
    ]
    grafo["options"]["parameters"].update(
        id="enlace_i15_ruido_prueba", title="Prueba de ruido e indicadores"
    )
    return grafo


def test_potencia_compleja_y_semilla(runtime):
    programa = r"""
from gnuradio import analog,blocks,gr
import numpy as np
def muestra(a,seed):
    t=gr.top_block();s=analog.noise_source_c(analog.GR_GAUSSIAN,a,seed);h=blocks.head(8,200000);v=blocks.vector_sink_c()
    t.connect(s,h,v);t.run();return np.asarray(v.data(),dtype=np.complex64)
base=muestra(1,42)
assert np.array_equal(base,muestra(1,42)) and not np.array_equal(base,muestra(1,43))
for a in [0,.5,1,2]:
    x=muestra(a,42)
    assert np.array_equal(x,base*a)
    if a:
        assert abs(np.mean(abs(x)**2)/(a*a)-1)<.02
        assert abs(x.real.var()/(a*a/2)-1)<.02 and abs(x.imag.var()/(a*a/2)-1)<.02
        assert abs(x.mean())<a*.01
        assert abs(np.corrcoef(x.real,x.imag)[0,1])<.02
print('POTENCIA_Y_SEMILLA_OK')
"""
    r = subprocess.run(
        [runtime[1], "-c", programa], capture_output=True, text=True, timeout=20
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "POTENCIA_Y_SEMILLA_OK" in r.stdout


@pytest.mark.parametrize("sps,alpha", [(4, 0.35), (8, 0.35), (4, 0.20), (4, 0.50)])
def test_ruido_cero_conserva_corpus_y_resumen(tmp_path, runtime, sps, alpha):
    g = grafo_ruido(GUIA.read_text(), 0, 42, sps, alpha)
    programa = r"""
import time,pmt,numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i15_ruido_prueba import enlace_i15_ruido_prueba,snippets_main_after_init,snippets_main_after_stop
app=QtWidgets.QApplication([]);t=enlace_i15_ruido_prueba();snippets_main_after_init(t)
x=blocks.vector_sink_c();r=blocks.vector_sink_c();t.connect(t.sin_etiquetas,x);t.connect(t.sumar_ruido,r)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
textos=['Hola','SDR','¡Hola, Perú!','a'*5000,'  texto  ','Hola']
t.start()
try:
    for i,texto in enumerate(textos):
        ed.setText(texto);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return);fin=time.monotonic()+6
        while t.blocks_message_debug_0.num_messages()<i+1 and time.monotonic()<fin:QtTest.QTest.qWait(5)
        assert t.blocks_message_debug_0.num_messages()==i+1
        assert pmt.symbol_to_string(t.blocks_message_debug_0.get_message(i))==texto
        if i==0:
            QtTest.QTest.qWait(100);assert t.blocks_message_debug_0.num_messages()==1
            if t.sps==4 and t.rrc_alpha==.35:assert abs(np.mean(abs(np.asarray(x.data()))**2)-.906449)<1e-6
    QtTest.QTest.qWait(60)
    assert np.array_equal(x.data(),r.data()) and not x.tags() and not r.tags()
    assert len(t.debug_deteccion.current_tags())==6
finally:t.stop();t.wait();t.close()
snippets_main_after_stop(t)
print('CERO_OK')
"""
    out = ejecutar(g, programa, tmp_path, runtime)
    assert "TX=6 DET=6 RX=6 OK=6" in out
    assert "RECH=0 SIN_PDU=0 SIN_TEXTO=0" in out and "CERO_OK" in out


@pytest.mark.parametrize(
    "amplitud,semilla", [(a, s) for a in [0.5, 1, 2] for s in [42, 43, 44]]
)
def test_lotes_ruidosos_identidad_y_repetibilidad(tmp_path, runtime, amplitud, semilla):
    g = grafo_ruido(GUIA.read_text(), amplitud, semilla)
    programa = r"""
import time,json,pmt,numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i15_ruido_prueba import enlace_i15_ruido_prueba,snippets_main_after_init,snippets_main_after_stop
app=QtWidgets.QApplication([]);refs=[f'Hola {i:02d}' for i in range(1,11)]
def lote():
    t=enlace_i15_ruido_prueba();a=t.ruido_amplitud;seed=t.ruido_semilla
    snippets_main_after_init(t)
    x=blocks.vector_sink_c();r=blocks.vector_sink_c();y=blocks.vector_sink_c()
    t.connect(t.sin_etiquetas,x);t.connect(t.sumar_ruido,r);t.connect(t.filtro_rx,y)
    ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
    t.start()
    try:
        for texto in refs:
            ed.setText(texto);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return);QtTest.QTest.qWait(10)
        fin=time.monotonic()+5
        while len(y.data())<8640 and time.monotonic()<fin:QtTest.QTest.qWait(5)
        QtTest.QTest.qWait(60);assert len(y.data())==len(r.data())==len(x.data())==8640
        assert not x.tags() and not r.tags()
    finally:t.stop();t.wait();t.close()
    tx=t.debug_trama_tx.num_messages();det=len(t.debug_deteccion.current_tags());rx=t.debug_paquete_rx.num_messages();ok=t.blocks_message_debug_0.num_messages()
    assert tx==10 and 0<=ok<=rx<=det<=tx
    got=[pmt.symbol_to_string(t.blocks_message_debug_0.get_message(i)) for i in range(ok)]
    assert len(set(got))==len(got) and all(s in refs for s in got)
    assert got==sorted(got)
    clean=np.asarray(x.data());received=np.asarray(r.data());noise=received-clean
    assert np.mean(abs(noise)**2)>0
    assert np.isclose(np.mean(abs(noise)**2),a*a,rtol=.06)
    # El RRC real conserva la convolución de la suma, no usa muestras TX ocultas.
    from gnuradio.filter import firdes
    h=np.asarray(firdes.root_raised_cosine(1,4000,1000,.35,33))
    assert np.allclose(np.asarray(y.data()),np.convolve(received,h)[:len(received)],atol=1e-6)
    row={'amplitud':a,'semilla':seed,'tx':tx,'det':det,'rx':rx,'ok':ok,'rech':rx-ok,'sin_pdu':tx-rx,'sin_texto':tx-ok}
    assert row['rech']+row['sin_pdu']==row['sin_texto']
    return row,received
row,signal=lote();again,repeat=lote()
assert again==row and np.array_equal(signal,repeat)
if row['amplitud']==.5:assert row['ok']==10
if row['amplitud']==2:assert row['sin_pdu']>0
print('LOTES_JSON='+json.dumps([row]),flush=True)
"""
    out = ejecutar(g, programa, tmp_path, runtime)
    rows = json.loads(out.split("LOTES_JSON=", 1)[1].splitlines()[0])
    assert len(rows) == 1
    (tmp_path / "resultados_ruido.json").write_text(json.dumps(rows, indent=2) + "\n")


def test_resumen_crc_y_corte_de_ruta(tmp_path, runtime):
    g = grafo_ruido(GUIA.read_text(), alterar=True)
    programa = r"""
import time
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i15_ruido_prueba import enlace_i15_ruido_prueba,snippets_main_after_init,snippets_main_after_stop
app=QtWidgets.QApplication([]);t=enlace_i15_ruido_prueba();snippets_main_after_init(t)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
t.start()
try:
    for i in range(3):
        ed.setText('Hola');QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return);fin=time.monotonic()+5
        while t.debug_paquete_rx.num_messages()<i+1 and time.monotonic()<fin:QtTest.QTest.qWait(5)
        assert t.debug_paquete_rx.num_messages()==i+1
    QtTest.QTest.qWait(60);assert t.blocks_message_debug_0.num_messages()==2
finally:t.stop();t.wait();t.close()
snippets_main_after_stop(t)
t=enlace_i15_ruido_prueba();snippets_main_after_init(t)
t.disconnect((t.cierre_rx,0),(t.sin_etiquetas,0));sink=blocks.null_sink(8);t.connect(t.cierre_rx,sink)
z=blocks.vector_source_c([0j]*1024,False);t.connect(z,t.sin_etiquetas)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
t.start()
try:
    ed.setText('Hola');QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return);QtTest.QTest.qWait(150)
    assert t.debug_trama_tx.num_messages()==1 and t.debug_paquete_rx.num_messages()==t.blocks_message_debug_0.num_messages()==0
finally:t.stop();t.wait();t.close()
snippets_main_after_stop(t)
"""
    out = ejecutar(g, programa, tmp_path, runtime)
    assert "TX=3 DET=3 RX=3 OK=2" in out and "RECH=1 SIN_PDU=0 SIN_TEXTO=1" in out
    assert "TX=1 DET=0 RX=0 OK=0" in out and "RECH=0 SIN_PDU=1 SIN_TEXTO=1" in out


def test_figuras_ruido_reproducibles(tmp_path):
    ruta = GUIA.parent / "figures/gen_enlace_ruido.py"
    spec = importlib.util.spec_from_file_location("figuras_ruido", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    files = m.generar(tmp_path)
    assert [p.name for p in files] == [
        "enlace-74-conexion-ruido.png",
        "enlace-75-referencia-ruido.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in files)
    assert abs(m.potencia_hola() - 0.906449) < 1e-5


def test_resumen_aparece_al_cerrar_la_gui_real(tmp_path, runtime):
    grafo = grafo_ruido(GUIA.read_text())
    programa = r"""
from PyQt5 import QtWidgets,QtCore,QtTest
import enlace_i15_ruido_prueba as modulo
class Ensayo(modulo.enlace_i15_ruido_prueba):
    def __init__(self):
        super().__init__()
        ed,=[w for w in self._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
        def enviar():
            ed.setText('Hola');QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return)
        QtCore.QTimer.singleShot(100,enviar)
        QtCore.QTimer.singleShot(250,enviar)
        QtCore.QTimer.singleShot(1000,self.close)
modulo.main(top_block_cls=Ensayo)
"""
    salida = ejecutar(grafo, programa, tmp_path, runtime)
    assert salida.count("RESUMEN amplitud=") == 1
    assert "TX=2 DET=2 RX=2 OK=2" in salida
    assert "RECH=0 SIN_PDU=0 SIN_TEXTO=0" in salida

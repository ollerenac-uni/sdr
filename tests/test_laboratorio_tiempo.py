"""Valida retardo de canal, selección fija y control manual sin tocar el GRC."""

import importlib.util
import json
import re

import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_frecuencia import grafo_frecuencia
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_rrc import configuracion
from test_laboratorio_senal_temporal import parametros


def grafo_tiempo(
    guia, retardo=0, offset=0, sps=4, alpha=0.35, symbol_rate=1000, alterar=False
):
    g = grafo_frecuencia(guia, 0, True, sps, alpha, symbol_rate, alterar)
    seccion = guia.split("## 22.", 1)[1].split("## 23.", 1)[0]
    variables = parametros(seccion, "### 22.2.")
    assert variables == {"retardo_muestras": "0", "offset_muestreo": "0"}
    variables.update(retardo_muestras=str(retardo), offset_muestreo=str(offset))
    for nombre, valor in variables.items():
        g["blocks"].append(
            {
                "name": nombre,
                "id": "variable",
                "parameters": {"value": valor},
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )
    p = configuracion(seccion, "### 22.3.", "retardar_canal")
    g["blocks"].append(
        {
            "name": p["ID"],
            "id": "blocks_delay",
            "parameters": {
                "type": p["Type"].lower(),
                "delay": p["Delay"],
                "num_ports": p["Num Ports"],
                "vlen": p["Vector Length"],
                "showports": {"No": "False", "Yes": "True"}[p["Show Msg Ports"]],
            },
            "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
        }
    )
    keep = configuracion(seccion, "### 22.3.", "muestrear_stream")
    ejes = parametros(seccion, "### 22.5.")
    resumen = re.findall(r"```python\n(.*?)\n```", seccion, re.S)[0]
    for b in g["blocks"]:
        if b["name"] == "muestrear_stream":
            b["parameters"].update(
                type=keep["Type"].lower(),
                m=keep["M"],
                n=keep["N"],
                offset=keep["initial offset"],
            )
        if b["name"] in {"constelacion_rx", "constelacion_fase"}:
            b["parameters"].update(
                xmin=ejes["X min"],
                xmax=ejes["X max"],
                ymin=ejes["Y min"],
                ymax=ejes["Y max"],
            )
        if b["name"] == "resumen_ensayo":
            b["parameters"]["code"] += "\n" + resumen
    g["connections"].remove(["desajustar_frecuencia", "0", "sumar_ruido", "0"])
    g["connections"] += [
        ["desajustar_frecuencia", "0", "retardar_canal", "0"],
        ["retardar_canal", "0", "sumar_ruido", "0"],
    ]
    g["options"]["parameters"].update(
        id="enlace_i19_tiempo_prueba", title="Prueba de desajuste temporal inicial"
    )
    return g


PROGRAMA = r"""
import json,time,pmt,numpy as np
from gnuradio import blocks
from gnuradio.filter import firdes
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i19_tiempo_prueba import enlace_i19_tiempo_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);t=enlace_i19_tiempo_prueba();snippets_main_after_init(t)
raw,delay,full,pre,post=[blocks.vector_sink_c() for _ in range(5)]
t.connect(t.desajustar_frecuencia,raw);t.connect(t.retardar_canal,delay)
t.connect(t.filtro_rx,full);t.connect(t.muestrear_stream,pre);t.connect(t.recuperar_fase,post)
f=blocks.vector_sink_f();t.connect(t.frecuencia_a_hz,f)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
textos=TEXTOS;esperados=ESPERADOS;total=0;ventanas=[];primeros=[]
t.resize(1100,760);t.show();t.vistas.setCurrentIndex(1);QtTest.QTest.qWait(30);t.start()
try:
    for i,s in enumerate(textos):
        inicio=total;total+=(18+len(s.encode('utf-8')))*8+16
        ventanas.append((inicio,total))
        ed.setText(s);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return)
        end=time.monotonic()+6
        while (len(post.data())<total or t.blocks_message_debug_0.num_messages()<esperados[i]) and time.monotonic()<end:QtTest.QTest.qWait(5)
        QtTest.QTest.qWait(120)
        assert len(post.data())==total,(i,len(post.data()),total)
        assert t.blocks_message_debug_0.num_messages()==esperados[i]
        primeros.append(t.blocks_message_debug_0.num_messages())
        if CAPTURA and i==0:
            t._constelacion_rx_win.grab().save('tiempo-primer-hola.png')
        if i==2:
            fase=t.recuperar_fase.get_phase();n=len(post.data())
            QtTest.QTest.qWait(120)
            assert t.recuperar_fase.get_phase()==fase and len(post.data())==n
finally:t.stop();t.wait();t.close();app.processEvents()
x=np.asarray(raw.data());y=np.asarray(delay.data());v=np.asarray(full.data())
a=np.asarray(pre.data());z=np.asarray(post.data());d=t.retardo_muestras;o=t.offset_muestreo
assert len(x)==total*t.sps and len(y)==len(x)+d
modelo=np.r_[np.zeros(d,dtype=complex),x]
assert np.array_equal(y,modelo)
assert not any(s.tags() for s in (raw,delay,full,pre,post,f))
h=firdes.root_raised_cosine(1,t.samp_rate,t.symbol_rate,t.rrc_alpha,t.rrc_ntaps)
referencia=np.convolve(x,h)[:len(x)][::t.sps]
assert np.allclose(v,np.convolve(y,h)[:len(v)],atol=3e-6)
assert np.allclose(a,v[o:(len(v)//t.sps)*t.sps:t.sps],atol=3e-6)
assert len(a)==len(z)==len(f.data())==total
assert np.max(abs(a.imag))<1e-7 and np.max(abs(z.imag))<1e-7
assert np.allclose(a,z,atol=3e-6) and np.max(abs(np.asarray(f.data())))<1e-6
error_referencia=float(np.max(abs(a-referencia)))
if o==d:assert error_referencia<3e-6,error_referencia
got=[pmt.symbol_to_string(t.blocks_message_debug_0.get_message(i)) for i in range(t.blocks_message_debug_0.num_messages())]
assert got==ACEPTADOS
n=len(t.debug_deteccion.current_tags());inv=len(t.debug_invertida.current_tags())
tx=t.debug_trama_tx.num_messages();rx=t.debug_paquete_rx.num_messages()
assert tx==len(textos)
assert n+inv==rx==CANDIDATOS
errores=[]
for i,(inicio,fin) in enumerate(ventanas):
    enviado=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_trama_tx.get_message(i))))
    bits=np.unpackbits(np.frombuffer(enviado,dtype=np.uint8),bitorder='big')
    sel=a[inicio+t.rrc_span:fin-t.rrc_span]
    errores.append(int(np.count_nonzero((sel.real>=0)!=bits)))
    if o==d:assert errores[-1]==0
    if CANDIDATOS:
        recibido=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_paquete_rx.get_message(i))))
        assert recibido==enviado[12:]
if CANDIDATOS==0:assert all(e>0 for e in errores)
row=dict(retardo_muestras=d,offset_muestreo=o,sps=t.sps,symbol_rate=t.symbol_rate,
    tx=tx,normal=n,invertida=inv,det=n+inv,rx=rx,ok=len(got),textos=got,por_envio=primeros,
    error_max_referencia=error_referencia,diferencias_signo_en_instantes_nominales=errores,
    muestras_entrada=len(x),muestras_delay=len(y),muestras_filtro=len(v),muestras_seleccionadas=len(a))
print('TIEMPO_JSON='+json.dumps(row,ensure_ascii=False),flush=True)
"""


def caso(
    tmp_path,
    runtime,
    retardo,
    offset,
    textos=None,
    sps=4,
    symbol_rate=1000,
    alpha=0.35,
    alterar=False,
    falla=False,
    captura=False,
):
    textos = textos or ["Hola", "SDR", "¡Hola, Perú!", "a" * 5000, "  texto  ", "Hola"]
    esperados = [1, 1, 2] if alterar else list(range(1, len(textos) + 1))
    aceptados = ["Hola", "Hola"] if alterar else textos
    candidatos = len(textos)
    if falla:
        esperados, aceptados, candidatos = [0] * len(textos), [], 0
    programa = (
        PROGRAMA.replace("TEXTOS", repr(textos))
        .replace("ESPERADOS", repr(esperados))
        .replace("ACEPTADOS", repr(aceptados))
        .replace("CANDIDATOS", repr(candidatos))
        .replace("CAPTURA", repr(captura))
    )
    out = ejecutar(
        grafo_tiempo(GUIA.read_text(), retardo, offset, sps, alpha, symbol_rate, alterar),
        programa,
        tmp_path,
        runtime,
    )
    row = json.loads(out.split("TIEMPO_JSON=", 1)[1].splitlines()[0])
    (tmp_path / "resultado_tiempo.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2) + "\n"
    )
    assert out.count("RESUMEN amplitud=") == 1
    assert f"TIEMPO retardo_muestras={retardo} offset_muestreo={offset}" in out
    return out, row


@pytest.mark.parametrize("d,o,falla", [(0, 0, False), (2, 0, True), (2, 2, False)])
def test_tres_filas_manuales_y_primer_mensaje(tmp_path, runtime, d, o, falla):
    out, row = caso(tmp_path, runtime, d, o, ["Hola", "Hola"], falla=falla, captura=True)
    assert row["por_envio"] == ([0, 0] if falla else [1, 2])
    if falla:
        assert "RECH=0 SIN_PDU=2 SIN_TEXTO=2" in out
    assert (tmp_path / "tiempo-primer-hola.png").read_bytes().startswith(b"\x89PNG")


@pytest.mark.parametrize("d,o", [(0, 0), (2, 2)])
def test_corpus_limite_pausa_y_control_manual(tmp_path, runtime, d, o):
    _, row = caso(tmp_path, runtime, d, o)
    assert row["ok"] == 6 and row["por_envio"][0] == 1


@pytest.mark.parametrize("d,o", [(1, 0), (3, 0), (3, 3), (4, 0)])
def test_retardo_no_implica_fallo_monotono(tmp_path, runtime, d, o):
    _, row = caso(tmp_path, runtime, d, o, ["Hola", "Hola"])
    assert row["ok"] == 2


@pytest.mark.parametrize(
    "d,o,sps,rs,alpha", [(4, 4, 8, 1000, 0.35), (2, 2, 4, 2000, 0.35), (2, 2, 4, 1000, 0.20)]
)
def test_modelo_y_control_con_otras_tasas(tmp_path, runtime, d, o, sps, rs, alpha):
    caso(tmp_path, runtime, d, o, ["Hola", "SDR", "¡Hola, Perú!", "Hola"], sps, rs, alpha)


def test_crc_sigue_rechazando_con_control_manual(tmp_path, runtime):
    out, row = caso(tmp_path, runtime, 2, 2, ["Hola"] * 3, alterar=True)
    assert row["rx"] == 3 and row["ok"] == 2
    assert "CRC incorrecto" in out and "RECH=1 SIN_PDU=0 SIN_TEXTO=1" in out


def test_canal_y_selector_independientes_sin_nuevos_sincronizadores():
    anterior = grafo_frecuencia(GUIA.read_text())
    g = grafo_tiempo(GUIA.read_text(), 2, 0)
    antes = {b["name"]: b for b in anterior["blocks"]}
    bs = {b["name"]: b for b in g["blocks"]}
    assert set(bs) - set(antes) == {"retardo_muestras", "offset_muestreo", "retardar_canal"}
    assert bs["muestrear_stream"]["parameters"]["offset"] == "offset_muestreo"
    assert bs["offset_muestreo"]["parameters"]["value"] == "0"
    for nombre, b in bs.items():
        if nombre not in {"retardo_muestras", "retardar_canal", "resumen_ensayo"}:
            assert "retardo_muestras" not in str(b["parameters"])
    for nombre in ("recuperar_fase", "invertir_bits", "detectar_invertida", "frecuencia_a_hz", "frecuencia_estimada", "vistas"):
        assert bs[nombre] == antes[nombre]
    assert not any(c[3] == "dly" for c in g["connections"])
    assert {b["name"] for b in g["blocks"] if b["id"] == "epy_block"} == {
        b["name"] for b in anterior["blocks"] if b["id"] == "epy_block"
    }


def test_figuras_desde_delay_filtro_y_selector_reales(tmp_path, runtime):
    path = GUIA.parent / "figures/gen_enlace_tiempo.py"
    spec = importlib.util.spec_from_file_location("referencia_tiempo", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    datos = mod.datos_referencia(runtime[1])
    import numpy as np

    assert set(datos) == {(0, 0), (2, 0), (2, 2)}
    assert np.allclose(datos[0, 0]["seleccion"], datos[2, 2]["seleccion"], atol=3e-6)
    assert np.max(abs(datos[2, 0]["seleccion"] - datos[0, 0]["seleccion"])) > 0.5
    for (d, o), row in datos.items():
        assert row["retardo"] == d and row["offset"] == o
        assert len(row["seleccion"]) >= 192
    mod.generar_conexion(tmp_path / "conexion.png")
    mod.generar_referencia(tmp_path / "referencia.png", datos)
    assert all(p.read_bytes().startswith(b"\x89PNG") for p in tmp_path.glob("*.png"))

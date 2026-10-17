"""Valida el desajuste del canal y la estimación de Costas en sus tasas reales."""

import copy
import importlib.util
import json
import re

import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_polaridad import grafo_polaridad
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_rrc import configuracion
from test_laboratorio_senal_temporal import parametros


def grafo_frecuencia(
    guia, hz=0, activo=True, sps=4, alpha=0.35, symbol_rate=1000, alterar=False
):
    g = grafo_polaridad(guia, 0, sps, alpha, alterar)
    seccion = (
        guia.split("## 21.", 1)[1]
        .split("## 22.", 1)[0]
        .split("## Siguiente paso", 1)[0]
    )

    def bloque(nombre, tipo, valores):
        g["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )

    variables = parametros(seccion, "### 21.2.")
    assert variables["frecuencia_offset_hz"] == "0.0"
    bloque("frecuencia_offset_hz", "variable", {"value": str(hz)})
    r = configuracion(seccion, "### 21.2.", "desajustar_frecuencia")
    bloque(
        r["ID"],
        "blocks_rotator_cc",
        {
            "phase_inc": r["Phase Increment"],
            "tag_inc_update": {"No": "False", "Yes": "True"}[
                r["Tag Increment Updates"]
            ],
        },
    )
    m = configuracion(seccion, "### 21.4.", "frecuencia_a_hz")
    bloque(
        m["ID"],
        "blocks_multiply_const_vxx",
        {
            "type": m["IO Type"].lower(),
            "const": m["Constant"],
            "vlen": m["Vector Length"],
        },
    )
    v = configuracion(seccion, "### 21.5.", "frecuencia_estimada")
    base = next(b for b in g["blocks"] if b["name"] == "tiempo_rx")
    valores = copy.deepcopy(base["parameters"])
    for campo, nombre in {
        "Name": "name",
        "Number of Points": "size",
        "Sample Rate": "srate",
        "Number of Inputs": "nconnections",
        "Y Axis Label": "ylabel",
        "Y Axis Unit": "yunit",
        "Y min": "ymin",
        "Y max": "ymax",
        "Update Period": "update_time",
        "Line 1 Label": "label1",
        "GUI Hint": "gui_hint",
    }.items():
        valores[nombre] = v[campo]
    valores.update(
        type=v["Type"].lower(),
        grid={"Yes": "True", "No": "False"}[v["Grid"]],
        autoscale={"Yes": "True", "No": "False"}[v["Autoscale"]],
        entags={"Yes": "True", "No": "False"}[v["Disp. Tags"]],
        tr_mode={"Free": "qtgui.TRIG_MODE_FREE"}[v["Trigger Mode"]],
    )
    bloque(v["ID"], "qtgui_time_sink_x", valores)
    tabs = configuracion(seccion, "### 21.4.", "vistas")
    for b in g["blocks"]:
        if b["name"] == "symbol_rate":
            b["parameters"]["value"] = str(symbol_rate)
        if b["name"] == "vistas":
            b["parameters"].update(num_tabs=tabs["Num Tabs"], label2=tabs["Label 2"])
        if b["name"] == "resumen_ensayo":
            b["parameters"]["code"] += (
                "\n" + re.findall(r"```python\n(.*?)\n```", seccion, re.S)[0]
            )
        if not activo and b["name"] in {
            "recuperar_fase",
            "frecuencia_a_hz",
            "frecuencia_estimada",
        }:
            b["states"]["state"] = "disabled"
    g["connections"].remove(["rotar_fase", "0", "sumar_ruido", "0"])
    g["connections"] += [
        ["rotar_fase", "0", "desajustar_frecuencia", "0"],
        ["desajustar_frecuencia", "0", "sumar_ruido", "0"],
        ["recuperar_fase", "1", "frecuencia_a_hz", "0"],
        ["frecuencia_a_hz", "0", "frecuencia_estimada", "0"],
    ]
    if not activo:
        g["connections"] += [
            ["muestrear_stream", "0", "extraer_i", "0"],
            ["muestrear_stream", "0", "constelacion_fase", "0"],
        ]
    g["options"]["parameters"].update(
        id="enlace_i18_frecuencia_prueba", title="Prueba de frecuencia y Costas"
    )
    return g


PROGRAMA = r"""
import json,time,pmt,numpy as np
from gnuradio import blocks
from gnuradio.filter import firdes
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i18_frecuencia_prueba import enlace_i18_frecuencia_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);t=enlace_i18_frecuencia_prueba();snippets_main_after_init(t)
activo=hasattr(t,'recuperar_fase')
raw,rot,pre,post=[blocks.vector_sink_c() for _ in range(4)]
t.connect(t.rotar_fase,raw);t.connect(t.desajustar_frecuencia,rot)
t.connect(t.muestrear_stream,pre);t.connect(t.recuperar_fase if activo else t.muestrear_stream,post)
fn=blocks.vector_sink_f();fh=blocks.vector_sink_f()
if activo:t.connect((t.recuperar_fase,1),fn);t.connect(t.frecuencia_a_hz,fh)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
textos=TEXTOS;esperados=ESPERADOS;total=0;ventanas=[];primeros=[]
t.resize(1100,760);t.show();t.vistas.setCurrentIndex(2 if activo else 1)
QtTest.QTest.qWait(30);t.start()
try:
    for i,s in enumerate(textos):
        inicio=total;total+=(18+len(s.encode('utf-8')))*8+16
        ventanas.append((inicio,total))
        ed.setText(s);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return)
        end=time.monotonic()+6
        while (len(post.data())<total or (activo and (len(fh.data())<total or t.debug_paquete_rx.num_messages()<i+1 or t.blocks_message_debug_0.num_messages()<esperados[i]))) and time.monotonic()<end:QtTest.QTest.qWait(5)
        QtTest.QTest.qWait(70)
        assert len(post.data())==total
        if activo:
            assert t.debug_paquete_rx.num_messages()==i+1
            assert t.blocks_message_debug_0.num_messages()==esperados[i]
        primeros.append(t.blocks_message_debug_0.num_messages())
        if CAPTURA and i==0 and activo:
            t._frecuencia_estimada_win.grab().save('frecuencia-primer-hola.png')
        if i==2:
            fase=t.recuperar_fase.get_phase() if activo else None
            QtTest.QTest.qWait(120)
            assert len(post.data())==total
            if activo:assert t.recuperar_fase.get_phase()==fase
finally:t.stop();t.wait();t.close();app.processEvents()
x=np.asarray(raw.data());y=np.asarray(rot.data());a=np.asarray(pre.data());z=np.asarray(post.data())
assert len(x)==len(y)==total*t.sps and len(a)==len(z)==total
assert not any(o.tags() for o in (raw,rot,pre,post,fn,fh))
modelo=x*np.exp(1j*2*np.pi*t.frecuencia_offset_hz*np.arange(len(x))/t.samp_rate)
error_canal=float(np.max(abs(y-modelo)))
assert error_canal<0.002,error_canal
assert np.allclose(abs(y),abs(x),atol=2e-5)
if t.frecuencia_offset_hz==0:assert np.array_equal(x,y)
h=firdes.root_raised_cosine(1,t.samp_rate,t.symbol_rate,t.rrc_alpha,t.rrc_ntaps)
assert np.allclose(a,np.convolve(y,h)[:len(y)][::t.sps],atol=3e-6)
got=[pmt.symbol_to_string(t.blocks_message_debug_0.get_message(i)) for i in range(t.blocks_message_debug_0.num_messages())]
assert got==ACEPTADOS
n=len(t.debug_deteccion.current_tags());inv=len(t.debug_invertida.current_tags())
rx=t.debug_paquete_rx.num_messages();tx=t.debug_trama_tx.num_messages()
assert tx==len(textos)
medidas=[]
if activo:
    assert len(fn.data())==len(fh.data())==total
    f=np.asarray(fh.data());normal=np.asarray(fn.data())
    assert np.allclose(f,normal*t.symbol_rate/(2*np.pi),atol=1e-5)
    assert n+inv==rx==len(textos)
    for i,(inicio,fin) in enumerate(ventanas):
        enviado=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_trama_tx.get_message(i))))[12:]
        recibido=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_paquete_rx.get_message(i))))
        assert enviado==recibido
        lo=inicio+100 if fin-inicio<400 else fin-92;hi=fin-8
        media=float(np.mean(f[lo:hi]));error=abs(media-t.frecuencia_offset_hz)
        fase=np.unwrap(np.angle(z[lo:hi]**2))/2
        residual=float(np.polyfit(np.arange(hi-lo)/t.symbol_rate,fase,1)[0]/(2*np.pi))
        assert error<0.1,(i,media,t.frecuencia_offset_hz)
        assert abs(residual)<0.1,(i,residual)
        medidas.append(dict(indice=i,inicio=lo,fin_exclusivo=hi,estimacion_hz=media,error_hz=error,residual_hz=residual))
else:
    assert np.array_equal(a,z)
    assert (n,inv,rx,len(got))==(0,0,0,0)
row=dict(offset_hz=t.frecuencia_offset_hz,activo=activo,sps=t.sps,symbol_rate=t.symbol_rate,tx=tx,normal=n,invertida=inv,det=n+inv,rx=rx,ok=len(got),primer_ok=primeros[0],medidas=medidas,error_canal=error_canal,bytes_textos=[len(s.encode('utf-8')) for s in textos])
print('FRECUENCIA_JSON='+json.dumps(row),flush=True)
"""


def caso(
    tmp_path,
    runtime,
    hz,
    activo=True,
    textos=None,
    sps=4,
    alpha=0.35,
    symbol_rate=1000,
    alterar=False,
    captura=False,
):
    textos = textos or ["Hola", "SDR", "¡Hola, Perú!", "a" * 5000, "  texto  ", "Hola"]
    esperados = [1, 1, 2] if alterar else list(range(1, len(textos) + 1))
    aceptados = ["Hola", "Hola"] if alterar else textos
    if not activo:
        esperados, aceptados = [0] * len(textos), []
    programa = (
        PROGRAMA.replace("TEXTOS", repr(textos))
        .replace("ESPERADOS", repr(esperados))
        .replace("ACEPTADOS", repr(aceptados))
        .replace("CAPTURA", repr(captura))
    )
    out = ejecutar(
        grafo_frecuencia(
            GUIA.read_text(), hz, activo, sps, alpha, symbol_rate, alterar
        ),
        programa,
        tmp_path,
        runtime,
    )
    row = json.loads(out.split("FRECUENCIA_JSON=", 1)[1].splitlines()[0])
    (tmp_path / "resultado_frecuencia.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2) + "\n"
    )
    assert out.count("RESUMEN amplitud=") == 1
    assert f"FRECUENCIA offset_hz={hz}" in out
    return out, row


@pytest.mark.parametrize("hz", [0, 5, -5, 10, -10, 20, -20])
def test_corpus_y_frecuencia_desde_muestras(tmp_path, runtime, hz):
    _, row = caso(tmp_path, runtime, hz)
    assert row["ok"] == 6 and row["primer_ok"] == 1


@pytest.mark.parametrize("hz,activo", [(10, False), (10, True), (-10, True)])
def test_comparacion_manual_y_visor_del_primer_hola(tmp_path, runtime, hz, activo):
    _, row = caso(
        tmp_path, runtime, hz, activo, ["Hola", "Hola"], captura=activo and hz == 10
    )
    assert row["ok"] == (2 if activo else 0)
    if activo and hz == 10:
        assert (
            (tmp_path / "frecuencia-primer-hola.png")
            .read_bytes()
            .startswith(b"\x89PNG")
        )


@pytest.mark.parametrize(
    "sps,symbol_rate,alpha", [(8, 1000, 0.35), (4, 2000, 0.35), (4, 1000, 0.20)]
)
def test_tasas_y_filtros_conservan_hz(tmp_path, runtime, sps, symbol_rate, alpha):
    caso(
        tmp_path,
        runtime,
        10,
        textos=["Hola", "SDR", "¡Hola, Perú!", "Hola"],
        sps=sps,
        symbol_rate=symbol_rate,
        alpha=alpha,
    )


def test_se_conserva_el_rechazo_crc(tmp_path, runtime):
    out, row = caso(tmp_path, runtime, 10, textos=["Hola"] * 3, alterar=True)
    assert row["rx"] == 3 and row["ok"] == 2
    assert "CRC incorrecto" in out and "RECH=1 SIN_PDU=0 SIN_TEXTO=1" in out


def test_canal_independiente_y_rutas_sin_dos_productores():
    anteriores = {
        b["name"]
        for b in grafo_polaridad(GUIA.read_text(), 0)["blocks"]
        if b["id"] == "epy_block"
    }
    for activo in (True, False):
        g = grafo_frecuencia(GUIA.read_text(), 10, activo)
        bs = {b["name"]: b for b in g["blocks"]}
        for b in g["blocks"]:
            if b["name"] not in {
                "frecuencia_offset_hz",
                "desajustar_frecuencia",
                "resumen_ensayo",
            }:
                assert "frecuencia_offset_hz" not in str(b["parameters"])
        assert not any(c[3] in {"cmd", "noise"} for c in g["connections"])
        assert {b["name"] for b in g["blocks"] if b["id"] == "epy_block"} == anteriores
        entradas = [
            (c[2], c[3])
            for c in g["connections"]
            if c[3].isdigit()
            and all(bs[n]["states"]["state"] == "enabled" for n in (c[0], c[2]))
        ]
        assert len(entradas) == len(set(entradas))
        assert all(
            bs[n]["states"]["state"] == ("enabled" if activo else "disabled")
            for n in ("recuperar_fase", "frecuencia_a_hz", "frecuencia_estimada")
        )


def test_figuras_frecuencia_con_bloques_reales(tmp_path, runtime):
    path = GUIA.parent / "figures/gen_enlace_frecuencia.py"
    spec = importlib.util.spec_from_file_location("figuras_frecuencia", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    datos = m.datos_referencia(runtime[1])
    for hz, d in datos.items():
        assert len(d["pre"]) == len(d["post"]) == len(d["hz"]) == 192
        assert abs(d["hz"][100:184].mean() - hz) < 0.1
    files = m.generar(tmp_path, runtime[1], datos)
    assert [p.name for p in files] == [
        "enlace-90-conexion-frecuencia.png",
        "enlace-91-referencia-frecuencia.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in files)

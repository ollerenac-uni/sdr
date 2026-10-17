"""Comprueba adquisición y seguimiento con el GRC construido desde la guía."""

import copy
import importlib.util
import json
import re
import subprocess

import numpy as np
import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_rrc import configuracion
from test_laboratorio_senal_temporal import parametros
from test_laboratorio_tiempo import grafo_tiempo


TEXTO_RELOJ = (GUIA.parent / "texto-prueba-reloj.txt").read_text().rstrip("\n")


def grafo_reloj(
    guia, d=0, ppm=0, canal=True, activo=True, sps=4, rs=1000, alterar=False
):
    g = grafo_tiempo(guia, d, 0, sps, 0.35, rs, alterar)
    seccion = (
        guia.split("## 23.", 1)[1]
        .split("## 24.", 1)[0]
        .split("## Siguiente paso", 1)[0]
    )

    def bloque(nombre, tipo, valores, enabled=True):
        g["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {
                    "state": "enabled" if enabled else "disabled",
                    "coordinate": [0, 0],
                    "rotation": 0,
                },
            }
        )

    variables = parametros(seccion, "### 23.4.")
    assert variables == {"reloj_ppm": "0.0"}
    bloque("reloj_ppm", "variable", {"value": str(float(ppm))})
    p = configuracion(seccion, "### 23.2.", "sincronizar_simbolos")
    bloque(
        p["ID"],
        "digital_symbol_sync_xx",
        {
            "type": {"Complex": "cc"}[p["I/O Type"]],
            "ted_type": {"Gardner": "digital.TED_GARDNER"}[p["Timing Error Detector"]],
            "sps": p["Samples per Symbol"],
            "ted_gain": p["Expected TED Gain"],
            "loop_bw": p["Loop Bandwidth"],
            "damping": p["Damping Factor"],
            "max_dev": p["Maximum Deviation"],
            "osps": p["Output Samples/Symbol"],
            "resamp_type": {"MMSE, 8 tap FIR": "digital.IR_MMSE_8TAP"}[
                p["Interpolating Resampler"]
            ],
            "constellation": "digital.constellation_bpsk().base()",
            "nfilters": "128",
            "pfb_mf_taps": "[]",
        },
        activo,
    )
    n = configuracion(seccion, "### 23.3.", "descartar_ted")
    bloque(
        n["ID"],
        "blocks_null_sink",
        {
            "type": n["Input Type"].lower(),
            "num_inputs": n["Num Inputs"],
            "vlen": n["Vector Length"],
        },
        activo,
    )
    r = configuracion(seccion, "### 23.6.", "desajustar_reloj")
    bloque(
        r["ID"],
        "mmse_resampler_xx",
        {
            "type": r["Type"].lower(),
            "phase_shift": r["Phase Shift"],
            "resamp_ratio": r["Resampling Ratio"],
        },
        canal,
    )
    v = configuracion(seccion, "### 23.3.", "reloj_estimado")
    base = next(b for b in g["blocks"] if b["name"] == "frecuencia_estimada")
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
        grid={"Yes": "True"}[v["Grid"]],
        autoscale={"No": "False"}[v["Autoscale"]],
        entags={"No": "False"}[v["Disp. Tags"]],
        tr_mode={"Free": "qtgui.TRIG_MODE_FREE"}[v["Trigger Mode"]],
    )
    bloque(v["ID"], "qtgui_time_sink_x", valores, activo)
    tabs = configuracion(seccion, "### 23.3.", "vistas")
    for b in g["blocks"]:
        if b["name"] == "muestrear_stream":
            b["states"]["state"] = "disabled" if activo else "enabled"
        if b["name"] == "vistas":
            b["parameters"].update(
                num_tabs=tabs["Num Tabs"],
                label3=tabs["Label 3"],
                gui_hint=tabs["GUI Hint"],
            )
        if b["name"] == "frecuencia_estimada":
            b["parameters"]["size"] = "128"
        if b["name"] == "resumen_ensayo":
            b["parameters"]["code"] += (
                "\n" + re.findall(r"```python\n(.*?)\n```", seccion, re.S)[0]
            )
    g["connections"] += [
        ["filtro_rx", "0", "sincronizar_simbolos", "0"],
        ["sincronizar_simbolos", "0", "recuperar_fase", "0"],
        ["sincronizar_simbolos", "0", "constelacion_rx", "0"],
        ["sincronizar_simbolos", "1", "descartar_ted", "0"],
        ["sincronizar_simbolos", "2", "descartar_ted", "1"],
        ["sincronizar_simbolos", "3", "reloj_estimado", "0"],
    ]
    if canal:
        g["connections"].remove(["retardar_canal", "0", "sumar_ruido", "0"])
        g["connections"] += [
            ["retardar_canal", "0", "desajustar_reloj", "0"],
            ["desajustar_reloj", "0", "sumar_ruido", "0"],
        ]
    g["options"]["parameters"].update(
        id="enlace_i20_reloj_prueba", title="Adquisición y seguimiento temporal"
    )
    return g


PROGRAMA = r"""
import json,time,pmt,numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i20_reloj_prueba import enlace_i20_reloj_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);t=enlace_i20_reloj_prueba();snippets_main_after_init(t)
pre,post=blocks.vector_sink_c(),blocks.vector_sink_c();period=blocks.vector_sink_f()
f=blocks.vector_sink_f();t.connect(t.recuperar_fase,post);t.connect(t.filtro_rx,pre)
t.connect(t.frecuencia_a_hz,f)
if ACTIVO:t.connect((t.sincronizar_simbolos,3),period)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
t.resize(1100,760);t.show();t.vistas.setCurrentIndex(3 if ACTIVO else 1)
QtTest.QTest.qWait(30);t.start();history=[];ventanas=[];inicio=0
try:
 for i,s in enumerate(TEXTOS):
  ed.setText(s);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return)
  end=time.monotonic()+6;prev=-1;stable=0
  while time.monotonic()<end:
   QtTest.QTest.qWait(20);nn=len(post.data());stable=stable+1 if nn==prev and nn>inicio else 0;prev=nn
   if stable>=10 and t.debug_trama_tx.num_messages()==i+1:break
  assert stable>=10,('no avanzó',i,len(post.data()))
  assert t.blocks_message_debug_0.num_messages()==ESPERADOS[i],(i,t.blocks_message_debug_0.num_messages())
  history.append(dict(tx=t.debug_trama_tx.num_messages(),rx=t.debug_paquete_rx.num_messages(),ok=t.blocks_message_debug_0.num_messages(),n=len(post.data())))
  ventanas.append((inicio,len(post.data())));inicio=len(post.data())
  if CAPTURA and i==0 and ACTIVO:
   assert len(period.data())>=128
   t._reloj_estimado_win.grab().save('reloj-primer-hola.png')
   t.vistas.setCurrentIndex(2);QtTest.QTest.qWait(30)
   t._frecuencia_estimada_win.grab().save('frecuencia-primer-hola.png')
  if i==2:
   n=len(post.data());phase=t.recuperar_fase.get_phase()
   QtTest.QTest.qWait(150)
   assert n==len(post.data()) and phase==t.recuperar_fase.get_phase()
finally:t.stop();t.wait();t.close();app.processEvents()
z=np.asarray(post.data());p=np.asarray(period.data())
assert len(z)==len(f.data()) and np.max(abs(np.asarray(f.data())))<1e-6
assert not any(s.tags() for s in (pre,post,period,f))
if ACTIVO:assert len(p)==len(z)
got=[pmt.symbol_to_string(t.blocks_message_debug_0.get_message(i)) for i in range(t.blocks_message_debug_0.num_messages())]
assert got==ACEPTADOS,(got,ACEPTADOS)
n=len(t.debug_deteccion.current_tags());inv=len(t.debug_invertida.current_tags())
tx=t.debug_trama_tx.num_messages();rx=t.debug_paquete_rx.num_messages()
assert tx==len(TEXTOS) and n+inv==rx==CANDIDATOS
# Los bits conocidos solo alinean instrumentos de evaluación. No alimentan el receptor.
for i in range(rx):
 enviado=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_trama_tx.get_message(i))))
 recibido=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_paquete_rx.get_message(i))))
 if ACTIVO:assert recibido==enviado[12:]
medidas=[]
if ACTIVO:
 for s,(a,b) in zip(TEXTOS,ventanas):
  if len(s.encode())>=799:
   w=p[b-16-2048:b-16];assert len(w)==2048
   estimado=float(np.mean(w));objetivo=t.sps*(1+t.reloj_ppm*1e-6)
   error_ppm=abs(estimado-objetivo)/t.sps*1e6
   assert error_ppm<100,(estimado,objetivo,error_ppm)
   medidas.append(dict(periodo=estimado,objetivo=objetivo,error_ppm=error_ppm,ventana=[b-2064,b-16]))
row=dict(retardo_muestras=t.retardo_muestras,reloj_ppm=t.reloj_ppm,canal=CANAL,activo=ACTIVO,
 sps=t.sps,symbol_rate=t.symbol_rate,tx=tx,det=n+inv,rx=rx,ok=len(got),normal=n,invertida=inv,
 por_envio=history,textos=got,medidas=medidas,muestras=len(z))
print('RELOJ_JSON='+json.dumps(row,ensure_ascii=False),flush=True)
"""


def caso(
    tmp_path,
    runtime,
    d=0,
    ppm=0,
    canal=True,
    activo=True,
    textos=None,
    sps=4,
    rs=1000,
    alterar=False,
    captura=False,
):
    textos = textos or ["Hola", "SDR", "¡Hola, Perú!", "a" * 5000, "  texto  ", "Hola"]
    esperados, aceptados = list(range(1, len(textos) + 1)), textos
    if alterar:
        esperados, aceptados = [1, 1, 2], ["Hola", "Hola"]
    if not activo:
        assert textos == [TEXTO_RELOJ, "Hola"] and ppm == 1000
        esperados, aceptados = [0, 1], ["Hola"]
    programa = PROGRAMA
    for k, v in {
        "ACTIVO": activo,
        "CANAL": canal,
        "TEXTOS": textos,
        "ESPERADOS": esperados,
        "ACEPTADOS": aceptados,
        "CANDIDATOS": len(textos),
        "CAPTURA": captura,
    }.items():
        programa = programa.replace(k, repr(v))
    out = ejecutar(
        grafo_reloj(GUIA.read_text(), d, ppm, canal, activo, sps, rs, alterar),
        programa,
        tmp_path,
        runtime,
    )
    row = json.loads(out.split("RELOJ_JSON=", 1)[1].splitlines()[0])
    (tmp_path / "resultado_reloj.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2) + "\n"
    )
    assert out.count("RESUMEN amplitud=") == 1
    assert f"RELOJ ppm={float(ppm)} temporal={'activo' if activo else 'fijo'}" in out
    return out, row


@pytest.mark.parametrize("d", [0, 1, 2, 3])
def test_adquiere_primer_hola_sin_oraculo_ni_segundo_envio(tmp_path, runtime, d):
    _, row = caso(
        tmp_path, runtime, d=d, canal=False, textos=["Hola", "Hola"], captura=d == 2
    )
    assert [v["ok"] for v in row["por_envio"]] == [1, 2]
    if d == 2:
        for name in ("reloj-primer-hola.png", "frecuencia-primer-hola.png"):
            assert (tmp_path / name).read_bytes().startswith(b"\x89PNG")


@pytest.mark.parametrize(
    "d,ppm", [(0, 0), (2, 0), (0, 500), (2, -500), (0, 1000), (2, -1000)]
)
def test_corpus_maximo_unicode_espacios_pausa_y_periodo(tmp_path, runtime, d, ppm):
    _, row = caso(tmp_path, runtime, d=d, ppm=ppm)
    assert row["ok"] == 6 and row["por_envio"][0]["ok"] == 1
    assert len(row["medidas"]) == 1


@pytest.mark.parametrize(
    "ppm,activo", [(0, True), (1000, False), (1000, True), (-1000, True)]
)
def test_filas_manuales_largo_y_hola_no_ocultan_rechazo(tmp_path, runtime, ppm, activo):
    out, row = caso(
        tmp_path, runtime, ppm=ppm, activo=activo, textos=[TEXTO_RELOJ, "Hola"]
    )
    assert row["ok"] == (2 if activo else 1)
    if not activo:
        assert "CRC incorrecto" in out and "RECH=1 SIN_PDU=0 SIN_TEXTO=1" in out


@pytest.mark.parametrize("sps,rs", [(8, 1000), (4, 2000)])
def test_tasas_nominales_sin_usar_reloj_exacto_en_rx(tmp_path, runtime, sps, rs):
    caso(
        tmp_path,
        runtime,
        d=sps // 2,
        sps=sps,
        rs=rs,
        canal=False,
        textos=["Hola", "SDR", "¡Hola, Perú!", "Hola"],
    )


def test_crc_con_adquisicion_no_acepta_paquete_alterado(tmp_path, runtime):
    out, row = caso(tmp_path, runtime, d=2, textos=["Hola"] * 3, alterar=True)
    assert row["rx"] == 3 and row["ok"] == 2 and "CRC incorrecto" in out


def test_canal_independiente_y_un_productor_activo_por_entrada():
    g = grafo_reloj(GUIA.read_text(), d=2, ppm=1000)
    bs = {b["name"]: b for b in g["blocks"]}
    for name, b in bs.items():
        if name not in {"reloj_ppm", "desajustar_reloj", "resumen_ensayo"}:
            assert "reloj_ppm" not in str(b["parameters"])
    antes = grafo_tiempo(GUIA.read_text())
    assert {b["name"] for b in antes["blocks"] if b["id"] == "epy_block"} == {
        b["name"] for b in g["blocks"] if b["id"] == "epy_block"
    }
    for activo in (True, False):
        g = grafo_reloj(GUIA.read_text(), activo=activo)
        enabled = {b["name"] for b in g["blocks"] if b["states"]["state"] == "enabled"}
        for name in ("recuperar_fase", "constelacion_rx"):
            src = [
                c[0]
                for c in g["connections"]
                if c[2:] == [name, "0"] and c[0] in enabled
            ]
            assert src == (["sincronizar_simbolos"] if activo else ["muestrear_stream"])
    assert len(TEXTO_RELOJ.encode()) == 799 and len(TEXTO_RELOJ.split()) == 200


def test_modelo_de_reloj_tono_y_relacion_input_output(runtime):
    programa = r"""
import json,numpy as np
from gnuradio import blocks,filter,gr
out=[]
for ppm in (0,1000,-1000):
 rho=1/(1+ppm*1e-6);n=40000;w=.05;x=np.exp(1j*w*np.arange(n))
 t=gr.top_block();s=blocks.vector_source_c(x.tolist(),False)
 r=filter.mmse_resampler_cc(0,rho);z=blocks.vector_sink_c();t.connect(s,r,z);t.run()
 y=np.asarray(z.data());medido=float(np.mean(np.angle(y[1:]*y[:-1].conj())))
 assert abs(medido-w*rho)<2e-7,(ppm,medido,w*rho)
 assert abs(len(y)-n/rho)<12
 if ppm==0:assert not np.allclose(y,x[:len(y)],atol=1e-4)
 out.append(dict(ppm=ppm,ratio=rho,n=len(y),incremento=medido,objetivo=w*rho))
print(json.dumps(out))
"""
    r = subprocess.run(
        [runtime[1], "-c", programa], capture_output=True, text=True, timeout=15
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_figuras_usan_sincronizador_y_canal_estandar(tmp_path, runtime):
    path = GUIA.parent / "figures/gen_enlace_reloj.py"
    spec = importlib.util.spec_from_file_location("figuras_reloj", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    datos = mod.datos_referencia(runtime[1])
    assert datos["adquisicion"]["ok"] and all(r["ok"] for r in datos["seguimiento"])
    for r in datos["seguimiento"]:
        assert (
            abs(np.mean(r["periodo"][-2064:-16]) - 4 * (1 + r["ppm"] * 1e-6)) < 0.0004
        )
    mod.generar_conexion(tmp_path / "100.png")
    mod.generar_adquisicion(tmp_path / "101.png", datos)
    mod.generar_seguimiento(tmp_path / "102.png", datos)
    assert all(
        (tmp_path / f"{n}.png").read_bytes().startswith(b"\x89PNG")
        for n in (100, 101, 102)
    )

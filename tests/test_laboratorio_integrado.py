"""Cierra BPSK con adquisición, desajustes combinados y controles negativos."""

import json
import re

import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_reloj import TEXTO_RELOJ, grafo_reloj
from test_laboratorio_rrc import configuracion


COMBINADO = dict(grados=60, hz=10, d=2, ppm=1000, ruido=0.0)


def grafo_integrado(
    guia,
    grados=0,
    hz=0,
    d=0,
    ppm=0,
    ruido=0.0,
    semilla=42,
    preambulo=32,
    alterar=False,
    anular=False,
):
    g = grafo_reloj(guia, d=d, ppm=ppm, alterar=alterar)
    sec = guia.split("## 24.", 1)[1].split("## Siguiente etapa", 1)[0]
    fragmento = sec.split("### 24.3.", 1)[1].split("En el `PDU Lambda`", 1)[0]
    variables = dict(re.findall(r"^\| `([^`]+)` \| `([^`]+)` \|", fragmento, re.M))
    assert variables["preambulo_bytes"] == "32"
    g["blocks"].append(
        {
            "name": "preambulo_bytes",
            "id": "variable",
            "parameters": {"value": str(preambulo)},
            "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
        }
    )
    wrap = configuracion(sec, "### 24.3.", "envolver_trama")
    values = {
        "fase_grados": grados,
        "frecuencia_offset_hz": hz,
        "ruido_amplitud": ruido,
        "ruido_semilla": semilla,
    }
    for b in g["blocks"]:
        if b["name"] in values:
            b["parameters"]["value"] = str(values[b["name"]])
        if b["name"] == "max_trama_bytes":
            b["parameters"]["value"] = variables["max_trama_bytes"]
        if b["name"] == "envolver_trama":
            b["parameters"].update(fn=wrap["Function"], metadict=wrap["Mode"])
        if b["name"] == "resumen_ensayo":
            b["parameters"]["code"] += (
                "\n" + re.findall(r"```python\n(.*?)\n```", sec, re.S)[0]
            )
        if anular and b["name"] == "rotar_fase":
            b["parameters"]["const"] = "0+0j"
    g["options"]["parameters"].update(
        id="enlace_i21_integrado_prueba", title="Cierre integrado BPSK"
    )
    return g


PROGRAMA = r"""
import json,time,pmt,struct,numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i21_integrado_prueba import enlace_i21_integrado_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);t=enlace_i21_integrado_prueba();snippets_main_after_init(t)
z=blocks.vector_sink_c();f=blocks.vector_sink_f();p=blocks.vector_sink_f()
t.connect(t.recuperar_fase,z);t.connect(t.frecuencia_a_hz,f);t.connect((t.sincronizar_simbolos,3),p)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
t.start();hist=[];windows=[];start=0
try:
 for i,text in enumerate(TEXTOS):
  ed.setText(text);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return)
  end=time.monotonic()+6;prev=-1;stable=0
  while time.monotonic()<end:
   QtTest.QTest.qWait(20);n=len(z.data());stable=stable+1 if n==prev and n>start else 0;prev=n
   if stable>=10 and t.debug_trama_tx.num_messages()==i+1:break
  assert stable>=10,(i,len(z.data()))
  count=t.blocks_message_debug_0.num_messages();assert count==ESPERADOS[i],(i,count)
  hist.append(dict(tx=t.debug_trama_tx.num_messages(),det=len(t.debug_deteccion.current_tags())+len(t.debug_invertida.current_tags()),rx=t.debug_paquete_rx.num_messages(),ok=count,n=len(z.data())))
  windows.append((start,len(z.data())));start=len(z.data())
  if i==2:
   before=(len(z.data()),t.recuperar_fase.get_phase())
   QtTest.QTest.qWait(150)
   assert before==(len(z.data()),t.recuperar_fase.get_phase())
finally:t.stop();t.wait();t.close();app.processEvents()
got=[pmt.symbol_to_string(t.blocks_message_debug_0.get_message(i)) for i in range(t.blocks_message_debug_0.num_messages())]
assert got==ACEPTADOS
assert len(z.data())==len(f.data())==len(p.data())
assert not any(s.tags() for s in (z,f,p))
n=len(t.debug_deteccion.current_tags());inv=len(t.debug_invertida.current_tags())
rx=t.debug_paquete_rx.num_messages();assert n+inv==rx==len(INDICES_RX)
assert t.max_trama_bytes==5018+t.preambulo_bytes and t.max_trama_bits==8*t.max_trama_bytes
frames=[]
for i,text in enumerate(TEXTOS):
 frame=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_trama_tx.get_message(i))))
 assert frame[:t.preambulo_bytes]==bytes([0x55])*t.preambulo_bytes
 raw=frame[t.preambulo_bytes:];assert raw[:8]==bytes.fromhex('ac dd a4 e2 f2 8c 20 fc')
 a,b=struct.unpack('>HH',raw[8:12]);assert a==b==len(raw)-12==len(text.encode())+6
 assert len(frame)==t.preambulo_bytes+18+len(text.encode())
 frames.append(frame)
for j,i in enumerate(INDICES_RX):
 actual=bytes(pmt.u8vector_elements(pmt.cdr(t.debug_paquete_rx.get_message(j))))
 assert actual==frames[i][t.preambulo_bytes+12:]
measures=[];ff=np.asarray(f.data());pp=np.asarray(p.data())
for text,(a,b) in zip(TEXTOS,windows):
 if len(text.encode())>=799:
  wf=ff[b-2064:b-16];wp=pp[b-2064:b-16];assert len(wf)==len(wp)==2048
  freq=float(np.mean(wf));period=float(np.mean(wp));target=t.sps*(1+t.reloj_ppm*1e-6)
  ef=abs(freq-t.frecuencia_offset_hz);ep=abs(period-target)/t.sps*1e6
  assert ef<.2,(freq,t.frecuencia_offset_hz)
  assert ep<100,(period,target,ep)
  measures.append(dict(frecuencia=freq,periodo=period,error_hz=ef,error_periodo_ppm=ep))
row=dict(cfg=CFG,history=hist,tx=len(TEXTOS),det=n+inv,rx=rx,ok=len(got),normal=n,invertida=inv,
 medidas=measures,exactos=got==ACEPTADOS,preambulo=t.preambulo_bytes,max_trama_bytes=t.max_trama_bytes,
 textos_aceptados=got)
print('INTEGRADO_JSON='+json.dumps(row,ensure_ascii=False),flush=True)
"""


def caso(tmp_path, runtime, textos=None, alterar=False, anular=False, **cfg):
    textos = textos or ["Hola", "SDR", "¡Hola, Perú!", "a" * 5000, "  texto  ", "Hola"]
    expected, accepted, indices = (
        list(range(1, len(textos) + 1)),
        textos,
        list(range(len(textos))),
    )
    if alterar:
        expected, accepted = [1, 1, 2], ["Hola", "Hola"]
    if cfg.get("preambulo") == 0:
        assert textos == [TEXTO_RELOJ, "Hola"]
        expected, accepted, indices = [0, 1], ["Hola"], [1]
    if anular:
        expected, accepted, indices = [0] * len(textos), [], []
    p = PROGRAMA
    for k, v in {
        "TEXTOS": textos,
        "ESPERADOS": expected,
        "ACEPTADOS": accepted,
        "INDICES_RX": indices,
        "CFG": cfg,
    }.items():
        p = p.replace(k, repr(v))
    out = ejecutar(
        grafo_integrado(GUIA.read_text(), alterar=alterar, anular=anular, **cfg),
        p,
        tmp_path,
        runtime,
    )
    row = json.loads(out.split("INTEGRADO_JSON=")[1].splitlines()[0])
    (tmp_path / "resultado_integrado.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2) + "\n"
    )
    assert f"ADQUISICION preambulo_bytes={cfg.get('preambulo', 32)}" in out
    return out, row


@pytest.mark.parametrize("cfg", [{}, COMBINADO, COMBINADO | dict(ruido=0.1)])
def test_tres_filas_manuales_y_primer_texto(tmp_path, runtime, cfg):
    _, row = caso(tmp_path, runtime, textos=[TEXTO_RELOJ, "Hola"], **cfg)
    assert row["history"][0]["ok"] == 1 and row["ok"] == 2


@pytest.mark.parametrize(
    "cfg",
    [
        {},
        COMBINADO,
        COMBINADO | dict(ruido=0.1),
        dict(grados=120, hz=10, d=2, ppm=1000, ruido=0.1),
        dict(grados=120, hz=-10, d=2, ppm=-1000, ruido=0.1),
    ],
)
def test_corpus_maximo_unicode_pausa_y_bytes(tmp_path, runtime, cfg):
    _, row = caso(tmp_path, runtime, **cfg)
    assert row["ok"] == 6 and row["history"][0]["ok"] == 1


@pytest.mark.parametrize("semilla", [17, 83])
def test_ruido_en_semillas_declaradas(tmp_path, runtime, semilla):
    caso(
        tmp_path,
        runtime,
        textos=[TEXTO_RELOJ, "Hola"],
        **(COMBINADO | dict(ruido=0.1, semilla=semilla)),
    )


def test_crc_sigue_rechazando_con_desajustes_combinados(tmp_path, runtime):
    out, row = caso(
        tmp_path,
        runtime,
        textos=["Hola"] * 3,
        alterar=True,
        **(COMBINADO | dict(ruido=0.1)),
    )
    assert row["rx"] == 3 and row["ok"] == 2
    assert "CRC incorrecto" in out and "RECH=1 SIN_PDU=0 SIN_TEXTO=1" in out


def test_fallo_inicial_sin_preambulo_se_conserva(tmp_path, runtime):
    out, row = caso(
        tmp_path,
        runtime,
        textos=[TEXTO_RELOJ, "Hola"],
        **(COMBINADO | dict(preambulo=0)),
    )
    assert row["history"][0]["ok"] == 0 and row["ok"] == 1 and row["det"] == 1
    assert "RECH=0 SIN_PDU=1 SIN_TEXTO=1" in out


def test_sin_senal_de_radio_no_hay_texto_eco(tmp_path, runtime):
    _, row = caso(tmp_path, runtime, textos=["Hola"], anular=True)
    assert row["tx"] == 1 and row["rx"] == row["ok"] == 0

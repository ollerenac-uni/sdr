"""Comprueba dos hipótesis de polaridad mediante bloques estándar y CRC existente."""

import json
import importlib.util
import re
import subprocess

import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_fase import grafo_fase
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_rrc import configuracion


def grafo_polaridad(guia, grados=0, sps=4, alpha=0.35, alterar=False):
    grafo = grafo_fase(guia, grados, sps=sps, alpha=alpha, alterar=alterar)
    seccion = (
        guia.split("## 20.", 1)[1]
        .split("## 21.", 1)[0]
        .split("## Siguiente paso", 1)[0]
    )

    def bloque(nombre, tipo, valores):
        grafo["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0},
            }
        )

    m = configuracion(seccion, "### 20.3.", "invertir_bits")
    d = configuracion(seccion, "### 20.3.", "detectar_invertida")
    r = configuracion(seccion, "### 20.4.", "empaquetar_invertida")
    p = configuracion(seccion, "### 20.4.", "pdu_invertida")
    t = configuracion(seccion, "### 20.5.", "debug_invertida")
    bloque(m["ID"], "digital_map_bb", {"map": m["Map"]})
    bloque(
        d["ID"],
        "digital_correlate_access_code_xx_ts",
        {
            "type": d["IO Type"].lower(),
            "access_code": d["Access Code"],
            "threshold": d["Threshold"],
            "tagname": d["Tag Name"],
        },
    )
    bloque(
        r["ID"],
        "blocks_repack_bits_bb",
        {
            "k": r["Bits per input byte"],
            "l": r["Bits per output byte"],
            "len_tag_key": r["Length Tag Key"],
            "align_output": {"Output": "True", "Input": "False"}[r["Packet Alignment"]],
            "endianness": {"MSB": "gr.GR_MSB_FIRST", "LSB": "gr.GR_LSB_FIRST"}[
                r["Endianness"]
            ],
        },
    )
    bloque(
        p["ID"],
        "pdu_tagged_stream_to_pdu",
        {"type": p["Item Type"].lower(), "tag": p["Length tag name"]},
    )
    bloque(
        t["ID"],
        "blocks_tag_debug",
        {
            "type": t["Input Type"].lower(),
            "name": t["Name"],
            "filter": t["Key Filter"],
            "display": {"On": "True", "Off": "False"}[t["Display"]],
            "vlen": "1",
            "num_inputs": "1",
        },
    )
    codigos = re.findall(r"```python\n(.*?)\n```", seccion, re.S)
    for b in grafo["blocks"]:
        if b["name"] == "ajustar_buffers":
            b["parameters"]["code"] += "\n" + next(
                c for c in codigos if "set_min_output_buffer" in c
            )
        if b["name"] == "resumen_ensayo":
            b["parameters"]["code"] = next(c for c in codigos if "n_normal = " in c)
    grafo["connections"] += [
        ["decidir_bits", "0", "invertir_bits", "0"],
        ["invertir_bits", "0", "detectar_invertida", "0"],
        ["detectar_invertida", "0", "empaquetar_invertida", "0"],
        ["detectar_invertida", "0", "debug_invertida", "0"],
        ["empaquetar_invertida", "0", "pdu_invertida", "0"],
        ["pdu_invertida", "pdus", "epy_block_3", "in"],
        ["pdu_invertida", "pdus", "debug_paquete_rx", "store"],
        ["pdu_invertida", "pdus", "debug_paquete_rx", "print"],
    ]
    grafo["options"]["parameters"].update(
        id="enlace_i17_polaridad_prueba", title="Prueba de resolución BPSK"
    )
    return grafo


PROGRAMA = r"""
import time,json,pmt,numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i17_polaridad_prueba import enlace_i17_polaridad_prueba,snippets_main_after_init
app=QtWidgets.QApplication([]);t=enlace_i17_polaridad_prueba();snippets_main_after_init(t)
raw=blocks.vector_sink_b();flipped=blocks.vector_sink_b();z=blocks.vector_sink_c()
t.connect(t.decidir_bits,raw);t.connect(t.invertir_bits,flipped);t.connect(t.recuperar_fase,z)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
textos=TEXTOS;esperados=POR_ENVIO;total=0;t.start()
try:
    for i,s in enumerate(textos):
        ed.setText(s);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return)
        total+=(18+len(s.encode('utf-8')))*8+16
        end=time.monotonic()+5
        while (t.debug_paquete_rx.num_messages()<i+1 or len(flipped.data())<total or t.blocks_message_debug_0.num_messages()<esperados[i]) and time.monotonic()<end:QtTest.QTest.qWait(5)
        QtTest.QTest.qWait(40)
        assert t.debug_paquete_rx.num_messages()==i+1
        assert t.blocks_message_debug_0.num_messages()==esperados[i]
        if i==2:QtTest.QTest.qWait(120)
    QtTest.QTest.qWait(60)
finally:t.stop();t.wait();t.close()
b=np.asarray(raw.data(),dtype=np.uint8);inv=np.asarray(flipped.data(),dtype=np.uint8)
assert len(b)==len(inv)==len(z.data())==total
assert not raw.tags() and not flipped.tags() and not z.tags()
frame=np.asarray(pmt.u8vector_elements(pmt.cdr(t.debug_trama_tx.get_message(0))),dtype=np.uint8)
first=np.packbits(b[8:184],bitorder='big');corrected=np.packbits(inv[8:184],bitorder='big')
if INVERTIDA:
    assert np.array_equal(first,frame^255) and np.array_equal(corrected,frame)
else:assert np.array_equal(first,frame) and np.array_equal(corrected,frame^255)
n=len(t.debug_deteccion.current_tags());i=len(t.debug_invertida.current_tags())
assert (n,i)==DETECCIONES
got=[pmt.symbol_to_string(t.blocks_message_debug_0.get_message(k)) for k in range(t.blocks_message_debug_0.num_messages())]
assert got==ACEPTADOS
row=dict(fase=t.fase_grados,tx=t.debug_trama_tx.num_messages(),normal=n,invertida=i,det=n+i,rx=t.debug_paquete_rx.num_messages(),ok=len(got),textos=got)
assert row['tx']==row['rx']==row['det']==len(textos)
print('POLARIDAD_JSON='+json.dumps(row),flush=True)
"""


def caso(tmp_path, runtime, grados, textos=None, sps=4, alpha=0.35, alterar=False):
    textos = textos or ["Hola", "SDR", "¡Hola, Perú!", "a" * 5000, "  texto  ", "Hola"]
    invertida = grados in [-150, -120, 120, 150, 180]
    esperados = [1, 1, 2] if alterar else list(range(1, len(textos) + 1))
    aceptados = ["Hola", "Hola"] if alterar else textos
    n = len(textos)
    programa = (
        PROGRAMA.replace("TEXTOS", repr(textos))
        .replace("POR_ENVIO", repr(esperados))
        .replace("INVERTIDA", repr(invertida))
        .replace("DETECCIONES", repr((0, n) if invertida else (n, 0)))
        .replace("ACEPTADOS", repr(aceptados))
    )
    out = ejecutar(
        grafo_polaridad(GUIA.read_text(), grados, sps, alpha, alterar),
        programa,
        tmp_path,
        runtime,
    )
    row = json.loads(out.split("POLARIDAD_JSON=", 1)[1].splitlines()[0])
    (tmp_path / "resultado_polaridad.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2) + "\n"
    )
    assert out.count("RESUMEN amplitud=") == 1
    return out, row


@pytest.mark.parametrize(
    "grados", [-150, -120, -60, -30, 0, 30, 60, 120, 150, 180, 300, 360]
)
def test_fases_constantes_corpus_maximo_y_primer_envio(tmp_path, runtime, grados):
    _, row = caso(tmp_path, runtime, grados)
    assert row["ok"] == 6


@pytest.mark.parametrize("sps,alpha", [(8, 0.35), (4, 0.20), (4, 0.50)])
def test_ruta_invertida_con_variantes_rrc(tmp_path, runtime, sps, alpha):
    caso(tmp_path, runtime, 120, ["Hola", "SDR", "¡Hola, Perú!", "Hola"], sps, alpha)


def test_inversion_no_oculta_error_crc(tmp_path, runtime):
    out, row = caso(tmp_path, runtime, 120, ["Hola"] * 3, alterar=True)
    assert row["ok"] == 2 and "CRC incorrecto" in out
    assert "RECH=1 SIN_PDU=0 SIN_TEXTO=1" in out


@pytest.mark.parametrize("invertida", [False, True])
def test_bits_sin_etiquetas_validas_cabecera_invalida_y_paquete_cortado(
    runtime, invertida
):
    programa = r"""
import struct,zlib,time,pmt
from gnuradio import blocks,digital,gr,pdu
sync=bytes.fromhex('acdda4e2f28c20fc');code=''.join(f'{b:08b}' for b in sync)
def paquete(s):
    b=s.encode();p=struct.pack('!H',len(b))+b;return p+struct.pack('!I',zlib.crc32(p)&0xffffffff)
def trama(p):return sync+struct.pack('!H',len(p))*2+p
def bits(b):return [int(x) for x in ''.join(f'{x:08b}' for x in b)]
p,q=paquete('Hola'),paquete('SDR')
bad=sync+struct.pack('!HH',len(p),len(p)+1)+p
data=[1,0,0,1]+bits(bad)+[0]*7+bits(trama(p))+[1,0]*5+bits(trama(q))+bits(trama(p))[:-12]
if INVERTIDA:data=[1-b for b in data]
t=gr.top_block();s=pdu.pdu_to_tagged_stream(gr.types.byte_t,'longitud_tx_falsa');m=digital.map_bb([1,0]);t.connect(s,m)
original=blocks.vector_sink_b();t.connect(s,original)
meta=pmt.dict_add(pmt.make_dict(),pmt.intern('packet_len'),pmt.from_long(1))
meta=pmt.dict_add(meta,pmt.intern('privada'),pmt.from_long(99))
merged=blocks.message_debug();collectors=[];observers=[]
for src in [s,m]:
    d=digital.correlate_access_code_bb_ts(code,0,'packet_len');d.set_min_output_buffer(0,80096)
    r=blocks.repack_bits_bb(1,8,'packet_len',True,gr.GR_MSB_FIRST);u=pdu.tagged_stream_to_pdu(gr.types.byte_t)
    v=blocks.message_debug();tags=blocks.vector_sink_b()
    t.connect(src,d,r,u);t.connect(d,tags);t.msg_connect((u,'pdus'),(v,'store'));t.msg_connect((u,'pdus'),(merged,'store'))
    collectors.append(v);observers.append(tags)
chosen=1 if INVERTIDA else 0
t.start();end=time.monotonic()+3
s.to_basic_block()._post(pmt.intern('pdus'),pmt.cons(meta,pmt.init_u8vector(len(data),data)))
while (merged.num_messages()<2 or collectors[chosen].num_messages()<2 or len(observers[chosen].data())<8*len(p)+8*len(q)+8*len(p)-12) and time.monotonic()<end:time.sleep(.005)
t.stop();t.wait()
assert any(pmt.symbol_to_string(tag.key)=='packet_len' and pmt.to_long(tag.value)==1 for tag in original.tags())
assert collectors[chosen].num_messages()==2 and collectors[1-chosen].num_messages()==0
assert merged.num_messages()==2
for k,expected in enumerate([p,q]):
    msg=merged.get_message(k);assert bytes(pmt.u8vector_elements(pmt.cdr(msg)))==expected
    assert not pmt.dict_has_key(pmt.car(msg),pmt.intern('privada'))
ts=observers[chosen].tags();assert len(ts)==3
assert [pmt.to_long(tag.value) for tag in ts]==[8*len(p),8*len(q),8*len(p)]
assert all(pmt.symbol_to_string(tag.key)=='packet_len' and pmt.symbol_to_string(tag.srcid).startswith('correlate_access_code_bb_ts') for tag in ts)
assert not observers[1-chosen].tags()
print('DOS_PDU_TRES_DETECCIONES_SIN_ETIQUETAS_TX')
""".replace("INVERTIDA", repr(invertida))
    r = subprocess.run(
        [runtime[1], "-c", programa], capture_output=True, text=True, timeout=15
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DOS_PDU_TRES_DETECCIONES_SIN_ETIQUETAS_TX" in r.stdout


def test_solo_map_utiliza_los_bits_sin_angulo_del_canal():
    g = grafo_polaridad(GUIA.read_text(), 120)
    assert not any(
        b["id"] == "epy_block"
        and b["name"]
        not in {
            "epy_block_0",
            "epy_block_1",
            "epy_block_2",
            "epy_block_3",
            "epy_block_4",
            "epy_block_5",
        }
        for b in g["blocks"]
    )
    for b in g["blocks"]:
        if b["name"] not in {"fase_grados", "rotar_fase", "resumen_ensayo"}:
            assert "fase_grados" not in str(b["parameters"])
    stream_inputs = [(c[2], c[3]) for c in g["connections"] if c[3].isdigit()]
    assert len(stream_inputs) == len(set(stream_inputs))


def test_figuras_polaridad_con_bloques_reales(tmp_path, runtime):
    path = GUIA.parent / "figures/gen_enlace_polaridad.py"
    spec = importlib.util.spec_from_file_location("figuras_polaridad", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    original, raw, corrected = m.datos_hola_invertidos(runtime[1])
    assert len(original) == len(raw) == len(corrected) == 22
    assert original == corrected and raw == bytes(v ^ 255 for v in original)
    files = m.generar(tmp_path, runtime[1])
    assert [p.name for p in files] == [
        "enlace-84-conexion-polaridad.png",
        "enlace-85-bytes-polaridad.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in files)

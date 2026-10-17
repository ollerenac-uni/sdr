"""Valida recuperación de fase y ambigüedad sin editar el montaje del profesor."""

import copy
import importlib.util
import re
import subprocess

import numpy as np
import pytest

from test_laboratorio_enlace_digital import GUIA, runtime as runtime
from test_laboratorio_recuperacion_paquete import ejecutar
from test_laboratorio_rrc import configuracion
from test_laboratorio_ruido import grafo_ruido
from test_laboratorio_senal_temporal import parametros


def grafo_fase(guia, grados=0, activo=True, sps=4, alpha=0.35, alterar=False):
    grafo = grafo_ruido(guia, 0, 42, sps, alpha, alterar)
    seccion = (
        guia.split("## 19. Introducir una rotación constante", 1)[1]
        .split("## 20.", 1)[0]
        .split("## Siguiente paso", 1)[0]
    )

    def bloque(nombre, tipo, valores, estado="enabled"):
        grafo["blocks"].append(
            {
                "name": nombre,
                "id": tipo,
                "parameters": valores,
                "states": {"state": estado, "coordinate": [0, 0], "rotation": 0},
            }
        )

    variables = parametros(seccion, "### 19.2.")
    variables["fase_grados"] = str(grados)
    for nombre, valor in variables.items():
        bloque(nombre, "variable", {"value": valor})
    rotor = configuracion(seccion, "### 19.3.", "rotar_fase")
    loop = configuracion(seccion, "### 19.4.", "recuperar_fase")
    bloque(
        rotor["ID"],
        "blocks_multiply_const_vxx",
        {
            "type": rotor["IO Type"].lower(),
            "const": rotor["Constant"],
            "vlen": rotor["Vector Length"],
        },
    )
    bloque(
        loop["ID"],
        "digital_costas_loop_cc",
        {
            "w": loop["Loop Bandwidth"],
            "order": loop["Order"],
            "use_snr": {"No": "False", "Yes": "True"}[loop["Use SNR"]],
        },
        "enabled" if activo else "disabled",
    )
    visor = configuracion(seccion, "### 19.5.", "constelacion_fase")
    anterior = next(b for b in grafo["blocks"] if b["name"] == "constelacion_rx")
    valores = copy.deepcopy(anterior["parameters"])
    valores.update(
        type=visor["Type"].lower(),
        name=visor["Name"],
        size=visor["Number of Points"],
        nconnections=visor["Number of Inputs"],
        gui_hint=visor["GUI Hint"],
        update_time=visor["Update Period"],
    )
    bloque(visor["ID"], "qtgui_const_sink_x", valores)
    resumen = next(b for b in grafo["blocks"] if b["name"] == "resumen_ensayo")
    resumen["parameters"]["code"] += (
        "\n" + re.findall(r"```python\n(.*?)\n```", seccion, re.S)[0]
    )
    grafo["connections"].remove(["sin_etiquetas", "0", "sumar_ruido", "0"])
    grafo["connections"].remove(["muestrear_stream", "0", "extraer_i", "0"])
    grafo["connections"] += [
        ["sin_etiquetas", "0", "rotar_fase", "0"],
        ["rotar_fase", "0", "sumar_ruido", "0"],
        ["muestrear_stream", "0", "recuperar_fase", "0"],
        ["recuperar_fase", "0", "extraer_i", "0"],
        ["recuperar_fase", "0", "constelacion_fase", "0"],
    ]
    if not activo:
        grafo["connections"] += [
            ["muestrear_stream", "0", "extraer_i", "0"],
            ["muestrear_stream", "0", "constelacion_fase", "0"],
        ]
    grafo["options"]["parameters"].update(
        id="enlace_i16_fase_prueba", title="Prueba de fase y Costas Loop"
    )
    return grafo


PROGRAMA = r"""
import json,time,pmt,numpy as np
from gnuradio import blocks
from PyQt5 import QtWidgets,QtCore,QtTest
from enlace_i16_fase_prueba import enlace_i16_fase_prueba,snippets_main_after_init,snippets_main_after_stop
app=QtWidgets.QApplication([]);t=enlace_i16_fase_prueba();snippets_main_after_init(t)
activo=hasattr(t,'recuperar_fase')
pre=blocks.vector_sink_c();post=blocks.vector_sink_c();entrada=blocks.vector_sink_c();rotada=blocks.vector_sink_c()
t.connect(t.muestrear_stream,pre);t.connect(t.recuperar_fase if activo else t.muestrear_stream,post)
t.connect(t.sin_etiquetas,entrada);t.connect(t.rotar_fase,rotada)
ed,=[w for w in t._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
textos=TEXTOS
total=0;t.start()
try:
    for i,texto in enumerate(textos):
        ed.setText(texto);QtTest.QTest.keyClick(ed,QtCore.Qt.Key_Return)
        # Solo instrumentación: espera a que el receptor consuma sus muestras.
        total+=(12+6+len(texto.encode('utf-8')))*8+16
        fin=time.monotonic()+5
        while len(post.data())<total and time.monotonic()<fin:QtTest.QTest.qWait(5)
        assert len(post.data())==total
        if i==0:
            QtTest.QTest.qWait(40)
            # El primer mensaje termina sin necesitar otro envío.
            assert t.blocks_message_debug_0.num_messages()==PRIMERO_OK
        if i==2:QtTest.QTest.qWait(120)
    QtTest.QTest.qWait(80)
finally:t.stop();t.wait();t.close()
x=np.asarray(pre.data());z=np.asarray(post.data());raw=np.asarray(entrada.data());rot=np.asarray(rotada.data())
assert len(z)==len(x)==total and len(raw)==len(rot)==total*t.sps
assert not pre.tags() and not post.tags() and not entrada.tags() and not rotada.tags()
assert np.allclose(rot,raw*np.exp(1j*np.deg2rad(t.fase_grados)),atol=3e-7)
assert np.allclose(abs(rot),abs(raw),atol=3e-7)
# La referencia conoce el canal SOLO para evaluar. Ninguna conexión la entrega a RX.
ref=x*np.exp(-1j*np.deg2rad(t.fase_grados))
assert np.max(abs(ref.imag))<1e-6
error=np.rad2deg(np.angle(z[100:184]/ref[100:184]))
if activo and abs(t.fase_grados)<=60:
    assert np.max(abs(error))<1
    assert np.array_equal(z[8:184].real>=0,ref[8:184].real>=0)
elif activo:
    assert np.max(abs(abs(error)-180))<1
else:
    assert np.array_equal(x,z)
tx=t.debug_trama_tx.num_messages();det=len(t.debug_deteccion.current_tags());rx=t.debug_paquete_rx.num_messages();ok=t.blocks_message_debug_0.num_messages()
got=[pmt.symbol_to_string(t.blocks_message_debug_0.get_message(i)) for i in range(ok)]
assert tx==len(textos) and (tx,det,rx,ok)==CONTADORES
assert got==ACEPTADOS
snippets_main_after_stop(t)
print('FASE_JSON='+json.dumps(dict(fase=t.fase_grados,activo=activo,tx=tx,det=det,rx=rx,ok=ok,error_max=float(max(abs(error))),textos=got)),flush=True)
"""


@pytest.mark.parametrize("grados", [-60, -30, 0, 30, 60])
def test_fase_desconocida_conserva_corpus_y_primer_mensaje(tmp_path, runtime, grados):
    textos = ["Hola", "SDR", "¡Hola, Perú!", "a" * 5000, "  texto  ", "Hola"]
    p = (
        PROGRAMA.replace("TEXTOS", repr(textos))
        .replace("PRIMERO_OK", "1")
        .replace("CONTADORES", repr((6, 6, 6, 6)))
        .replace("ACEPTADOS", repr(textos))
    )
    out = ejecutar(grafo_fase(GUIA.read_text(), grados), p, tmp_path, runtime)
    assert "FASE_JSON=" in out and "costas=activo" in out


@pytest.mark.parametrize(
    "grados,activo", [(0, True), (60, False), (60, True), (120, True)]
)
def test_cuatro_condiciones_manuales(tmp_path, runtime, grados, activo):
    textos = ["Hola", "Hola"]
    ok = 0 if grados == 120 else 2
    p = (
        PROGRAMA.replace("TEXTOS", repr(textos))
        .replace("PRIMERO_OK", str(bool(ok) * 1))
        .replace("CONTADORES", repr((2, ok, ok, ok)))
        .replace("ACEPTADOS", repr(textos if ok else []))
    )
    out = ejecutar(grafo_fase(GUIA.read_text(), grados, activo), p, tmp_path, runtime)
    assert f"costas={'activo' if activo else 'sin_lazo'}" in out


@pytest.mark.parametrize("grados", [-120, 180])
def test_control_de_inversion_no_se_declara_texto_valido(tmp_path, runtime, grados):
    p = (
        PROGRAMA.replace("TEXTOS", repr(["Hola", "Hola"]))
        .replace("PRIMERO_OK", "0")
        .replace("CONTADORES", repr((2, 0, 0, 0)))
        .replace("ACEPTADOS", "[]")
    )
    out = ejecutar(grafo_fase(GUIA.read_text(), grados), p, tmp_path, runtime)
    assert "SIN_PDU=2 SIN_TEXTO=2" in out


@pytest.mark.parametrize("sps,alpha", [(8, 0.35), (4, 0.20), (4, 0.50)])
def test_fase_con_variantes_de_pulso(tmp_path, runtime, sps, alpha):
    p = (
        PROGRAMA.replace("TEXTOS", repr(["Hola", "Hola"]))
        .replace("PRIMERO_OK", "1")
        .replace("CONTADORES", repr((2, 2, 2, 2)))
        .replace("ACEPTADOS", repr(["Hola", "Hola"]))
    )
    ejecutar(
        grafo_fase(GUIA.read_text(), 60, sps=sps, alpha=alpha), p, tmp_path, runtime
    )


def test_crc_sigue_rechazando_paquete_alterado(tmp_path, runtime):
    p = (
        PROGRAMA.replace("TEXTOS", repr(["Hola"] * 3))
        .replace("PRIMERO_OK", "1")
        .replace("CONTADORES", repr((3, 3, 3, 2)))
        .replace("ACEPTADOS", repr(["Hola", "Hola"]))
    )
    out = ejecutar(grafo_fase(GUIA.read_text(), 60, alterar=True), p, tmp_path, runtime)
    assert "CRC incorrecto" in out and "RECH=1 SIN_PDU=0 SIN_TEXTO=1" in out


def test_no_se_entrega_fase_exacta_al_receptor():
    g = grafo_fase(GUIA.read_text(), 60)
    for b in g["blocks"]:
        if b["name"] not in {"fase_grados", "rotar_fase", "resumen_ensayo"}:
            assert "fase_grados" not in str(b["parameters"])
    assert not any(c[3] == "noise" for c in g["connections"])


def test_estados_respetan_la_capacidad_real_de_grc(runtime):
    programa = """
from gnuradio import gr
from gnuradio.grc.core.platform import Platform
p=Platform(version=gr.version(),version_parts=(gr.major_version(),gr.api_version(),gr.minor_version()),prefs=gr.prefs(),install_prefix=gr.prefix())
p.build_library();g=p.make_flow_graph();loop=g.new_block('digital_costas_loop_cc');loop.rewrite()
assert len(loop.sinks)==2 and len(loop.sources)==4
assert not loop.can_bypass() and not loop.set_bypassed()
assert loop.state=='enabled'
print('BYPASS_NO_DISPONIBLE_CONFIRMADO')
"""
    r = subprocess.run(
        [runtime[1], "-c", programa], capture_output=True, text=True, timeout=15
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "BYPASS_NO_DISPONIBLE_CONFIRMADO" in r.stdout
    for activo in [True, False]:
        cfg = grafo_fase(GUIA.read_text(), 60, activo)
        loop = next(b for b in cfg["blocks"] if b["name"] == "recuperar_fase")
        assert loop["states"]["state"] != "bypassed"


def test_figuras_fase_con_bloque_real(tmp_path, runtime):
    ruta = GUIA.parent / "figures/gen_enlace_fase.py"
    spec = importlib.util.spec_from_file_location("figuras_fase", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    datos = m.datos_referencia(runtime[1])
    assert set(datos) == {60, 120}
    paths = m.generar(tmp_path, runtime[1], datos)
    assert [p.name for p in paths] == [
        "enlace-79-conexion-fase.png",
        "enlace-80-referencia-fase.png",
    ]
    assert all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in paths)
    for grados, (pre, post, bits) in datos.items():
        assert len(pre) == len(post) == 192 and len(bits) == 176
        target = (2 * bits.astype(int) - 1)[92:]
        expected = target if grados == 60 else -target
        assert np.all(post[100:184].real * expected > 0)

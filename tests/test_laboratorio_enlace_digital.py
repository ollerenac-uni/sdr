"""Verifica entrada y observación de texto sin tocar el .grc del profesor."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "docs/sessions/03-sistemas-filtros-digitales"
GUIA = CARPETA / "laboratorio-enlace-digital.md"
GRCC = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
PYTHON_GR = Path(GRCC).parent / "python3"


def tablas():
    inicial = GUIA.read_text(encoding="utf-8").split("## 4.", 1)[0]
    return dict(re.findall(r"^\| `([^`]+)` \| `([^`]+)` \|", inicial, re.M))


def test_guia_es_incremental_y_preserva_la_practica_fir():
    texto = GUIA.read_text(encoding="utf-8")
    assert "status: draft" in texto
    assert "gnuradio-flowgraphs/end-to-end.grc" in texto
    assert "`ID` | `end_to_end`" in texto
    assert "`ID` | `mensaje_a`" in texto
    assert "Static Mode = True` no impide editar el texto" in texto
    assert "No se espera texto recibido en la consola" in texto
    assert "No se añade `Throttle`" in texto
    assert texto.count('??? example "Solución explicada"') == 24
    assert "## 4. Observar el mensaje con `Message Debug`" in texto
    assert "con `print` de `Message Debug`" in texto
    assert "Cambiar el foco no publica el texto" in texto
    assert "No es codificación de canal ni modulación" in texto
    assert (CARPETA / "laboratorio-filtrado.md").exists()
    assert (CARPETA / "filtros_sesion03.grc").exists()


def test_nombres_de_archivo_y_clase_no_se_confunden():
    assert not "end-to-end".isidentifier()
    assert "end_to_end".isidentifier()
    texto = GUIA.read_text(encoding="utf-8")
    assert "end_to_end.py" in texto


@pytest.fixture(scope="module")
def runtime():
    if not Path(GRCC).is_file() or not PYTHON_GR.is_file():
        pytest.skip("GNU Radio no está disponible")
    return GRCC, str(PYTHON_GR)


@pytest.mark.parametrize("con_debug", [False, True], ids=["solo_entrada", "con_message_debug"])
def test_entrada_y_observacion_de_texto(tmp_path, runtime, con_debug):
    p = tablas()
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i01a_prueba", "title": p["Title"],
            "generate_options": "qt_gui", "output_language": "python",
            "catch_exceptions": "True", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [{"name": "mensaje_a", "id": "qtgui_edit_box_msg", "parameters": {
            "type": p["Type"].lower(), "value": "", "label": p["Label"],
            "is_pair": p["Pair Mode"], "is_static": p["Static Mode"], "key": "", "gui_hint": "",
        }, "states": {"state": "enabled", "coordinate": [300, 100], "rotation": 0}}],
        "connections": [], "metadata": {"file_format": 1},
    }
    if con_debug:
        grafo["blocks"].append({
            "name": "observador_texto", "id": "blocks_message_debug",
            "parameters": {"en_uvec": "True", "log_level": "info"},
            "states": {"state": "enabled", "coordinate": [600, 100], "rotation": 0},
        })
        grafo["connections"].append(["mensaje_a", "msg", "observador_texto", "print"])
    archivo = tmp_path / "entrada_texto_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    modulo = tmp_path / "enlace_i01a_prueba.py"
    programa = """
import importlib.util, json, sys, time
import pmt
from PyQt5 import QtWidgets, QtCore, QtTest
app = QtWidgets.QApplication([])
spec = importlib.util.spec_from_file_location('entrada', sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
tb = m.enlace_i01a_prueba()
con_debug = sys.argv[2] == 'True'
if con_debug:
    # Instrumentación de la prueba: store comprueba entrega y contenido.
    # La conexión del alumno sigue siendo exclusivamente msg → print.
    tb.msg_connect((tb.mensaje_a, 'msg'), (tb.observador_texto, 'store'))
tb.start()
tb.show()
app.processEvents()
editores = [w for w in tb.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
assert len(editores) == 1, len(editores)
editor = editores[0]
assert editor.text() == ''
if con_debug:
    editor.setFocus()
    editor.setText('Sin confirmar')
    QtTest.QTest.keyClick(editor, QtCore.Qt.Key_Tab)
    QtTest.QTest.qWait(50)
    assert tb.observador_texto.num_messages() == 0
observados = []
textos = ['Hola', 'SDR', 'SDR'] if con_debug else ['Hola', 'SDR']
for numero, texto in enumerate(textos, start=1):
    editor.setText(texto)
    QtTest.QTest.keyClick(editor, QtCore.Qt.Key_Return)
    app.processEvents()
    observados.append(editor.text())
    if con_debug:
        limite = time.monotonic() + 3
        while tb.observador_texto.num_messages() < numero and time.monotonic() < limite:
            QtTest.QTest.qWait(10)
        assert tb.observador_texto.num_messages() == numero
        recibido = tb.observador_texto.get_message(numero - 1)
        assert pmt.is_symbol(recibido)
        assert pmt.symbol_to_string(recibido) == texto
tb.stop()
tb.wait()
tb.close()
print(json.dumps({'texto': observados, 'titulo': tb.windowTitle()}))
"""
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    resultado = subprocess.run([runtime[1], "-c", programa, str(modulo), str(con_debug)], env=env, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    datos = json.loads(next(linea for linea in resultado.stdout.splitlines() if linea.startswith('{"texto":')))
    assert datos["texto"] == (["Hola", "SDR", "SDR"] if con_debug else ["Hola", "SDR"])
    assert datos["titulo"] == p["Title"]
    if con_debug:
        assert resultado.stdout.count("MESSAGE DEBUG PRINT") == 3
        assert re.findall(r"^(Hola|SDR)$", resultado.stdout, re.M) == ["Hola", "SDR", "SDR"]


def test_ejemplo_de_bytes_utf8():
    assert list("Hola".encode("utf-8")) == [72, 111, 108, 97]
    assert "Hola".encode("utf-8").hex(" ") == "48 6f 6c 61"
    assert "SDR".encode("utf-8").hex(" ") == "53 44 52"
    assert "`72, 111, 108, 97`" in GUIA.read_text(encoding="utf-8")


def test_codigo_copiable_utf8_compila_y_entrega_pdus(tmp_path, runtime):
    texto_guia = GUIA.read_text(encoding="utf-8")
    fragmentos = re.findall(r"```python\n(.*?)\n```", texto_guia, re.S)
    codigo = next(c for c in fragmentos if "class blk(gr.basic_block)" in c)
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i02_prueba", "generate_options": "no_gui",
            "output_language": "python", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [
            {"name": "epy_block_0", "id": "epy_block", "parameters": {"_source_code": codigo},
             "states": {"state": "enabled", "coordinate": [300, 100], "rotation": 0}},
            {"name": "observador", "id": "blocks_message_debug", "parameters": {
                "en_uvec": "True", "log_level": "info",
            }, "states": {"state": "enabled", "coordinate": [600, 100], "rotation": 0}},
        ],
        "connections": [["epy_block_0", "out", "observador", "print"]],
        "metadata": {"file_format": 1},
    }
    archivo = tmp_path / "texto_bytes_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = """
import time
import pmt
from enlace_i02_prueba import enlace_i02_prueba
tb = enlace_i02_prueba()
# store se usa solamente para verificar el resultado de la prueba.
tb.msg_connect((tb.epy_block_0, 'out'), (tb.observador, 'store'))
tb.start()
try:
    textos = ['Hola', 'SDR', '¡Hola, Perú!', '  texto  ', '', 'Hola']
    for numero, texto in enumerate(textos, 1):
        tb.epy_block_0.to_basic_block()._post(pmt.intern('in'), pmt.intern(texto))
        limite = time.monotonic() + 3
        while tb.observador.num_messages() < numero and time.monotonic() < limite:
            time.sleep(0.01)
        assert tb.observador.num_messages() == numero
        pdu = tb.observador.get_message(numero - 1)
        assert pmt.is_dict(pmt.car(pdu))
        assert pmt.equal(pmt.car(pdu), pmt.make_dict())
        assert pmt.is_u8vector(pmt.cdr(pdu))
        datos = bytes(pmt.u8vector_elements(pmt.cdr(pdu)))
        assert datos == texto.encode('utf-8')
        assert datos.decode('utf-8') == texto
    tb.epy_block_0.to_basic_block()._post(pmt.intern('in'), pmt.from_long(7))
    time.sleep(0.1)
    assert tb.observador.num_messages() == len(textos)
finally:
    tb.stop()
    tb.wait()
"""
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert resultado.stdout.count("VERBOSE PDU DEBUG PRINT") == 6
    assert "0000: 48 6f 6c 61" in resultado.stdout
    assert "0000: 53 44 52" in resultado.stdout
    assert "se esperaba un mensaje de texto" in resultado.stdout


def test_codigos_copiables_recuperan_texto_con_un_solo_visor(tmp_path, runtime):
    texto_guia = GUIA.read_text(encoding="utf-8")
    fragmentos = re.findall(r"```python\n(.*?)\n```", texto_guia, re.S)
    tx = next(c for c in fragmentos if 'name="Texto a bytes UTF-8"' in c)
    rx = next(c for c in fragmentos if 'name="Bytes a texto UTF-8"' in c)
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i03_prueba", "generate_options": "no_gui",
            "output_language": "python", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [
            {"name": "epy_block_0", "id": "epy_block", "parameters": {"_source_code": tx},
             "states": {"state": "enabled", "coordinate": [300, 100], "rotation": 0}},
            {"name": "epy_block_1", "id": "epy_block", "parameters": {"_source_code": rx},
             "states": {"state": "enabled", "coordinate": [500, 100], "rotation": 0}},
            {"name": "observador", "id": "blocks_message_debug", "parameters": {
                "en_uvec": "True", "log_level": "info",
            }, "states": {"state": "enabled", "coordinate": [700, 100], "rotation": 0}},
        ],
        "connections": [
            ["epy_block_0", "out", "epy_block_1", "in"],
            ["epy_block_1", "out", "observador", "print"],
        ],
        "metadata": {"file_format": 1},
    }
    archivo = tmp_path / "ida_vuelta_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = """
import time
import pmt
from enlace_i03_prueba import enlace_i03_prueba
tb = enlace_i03_prueba()
# Instrumentación de prueba: el alumno solo conecta print.
tb.msg_connect((tb.epy_block_1, 'out'), (tb.observador, 'store'))
tb.start()
def comprobar(numero, texto):
    limite = time.monotonic() + 3
    while tb.observador.num_messages() < numero and time.monotonic() < limite:
        time.sleep(0.01)
    assert tb.observador.num_messages() == numero
    assert pmt.symbol_to_string(tb.observador.get_message(numero - 1)) == texto
try:
    textos = ['Hola', 'SDR', '¡Hola, Perú!', '  texto  ', '', 'Hola']
    for numero, texto in enumerate(textos, 1):
        tb.epy_block_0.to_basic_block()._post(pmt.intern('in'), pmt.intern(texto))
        comprobar(numero, texto)
    invalidos = [
        pmt.intern('No es PDU'),
        pmt.cons(pmt.make_dict(), pmt.init_f32vector(1, [1.0])),
        pmt.cons(pmt.make_dict(), pmt.init_u8vector(1, [255])),
    ]
    for mensaje in invalidos:
        tb.epy_block_1.to_basic_block()._post(pmt.intern('in'), mensaje)
    time.sleep(0.1)
    assert tb.observador.num_messages() == len(textos)
    tb.epy_block_0.to_basic_block()._post(pmt.intern('in'), pmt.intern('Fin'))
    comprobar(len(textos) + 1, 'Fin')
finally:
    tb.stop()
    tb.wait()
"""
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert resultado.stdout.count("MESSAGE DEBUG PRINT") == 7
    assert "VERBOSE PDU DEBUG PRINT" not in resultado.stdout
    assert re.findall(r"^(Hola|SDR|¡Hola, Perú!|  texto  |Fin)$", resultado.stdout, re.M) == ["Hola", "SDR", "¡Hola, Perú!", "  texto  ", "Hola", "Fin"]
    assert resultado.stdout.count("se esperaba una PDU de bytes") == 2
    assert "los bytes no forman un texto UTF-8 válido" in resultado.stdout


def test_constructor_copiable_compila_y_valida_paquetes(tmp_path, runtime):
    fragmentos = re.findall(r"```python\n(.*?)\n```", GUIA.read_text(encoding="utf-8"), re.S)
    tx = next(c for c in fragmentos if 'name="Texto a bytes UTF-8"' in c)
    constructor = next(c for c in fragmentos if 'name="Construir paquete"' in c)
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i04_prueba", "generate_options": "no_gui",
            "output_language": "python", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [
            {"name": nombre, "id": "epy_block", "parameters": {"_source_code": codigo},
             "states": {"state": "enabled", "coordinate": [300 + 200 * i, 100], "rotation": 0}}
            for i, (nombre, codigo) in enumerate([("epy_block_0", tx), ("epy_block_1", constructor)])
        ] + [{"name": "observador", "id": "blocks_message_debug", "parameters": {
            "en_uvec": "True", "log_level": "info",
        }, "states": {"state": "enabled", "coordinate": [700, 100], "rotation": 0}}],
        "connections": [["epy_block_0", "out", "epy_block_1", "in"], ["epy_block_1", "out", "observador", "print"]],
        "metadata": {"file_format": 1},
    }
    archivo = tmp_path / "constructor_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = r'''
import time
import pmt
from enlace_i04_prueba import enlace_i04_prueba

# Referencia independiente de zlib: CRC-32 reflejado, comprobado con un vector conocido.
def crc_referencia(datos):
    crc = 0xffffffff
    for byte in datos:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xedb88320 if crc & 1 else 0)
    return crc ^ 0xffffffff

assert crc_referencia(b'123456789') == 0xcbf43926
tb = enlace_i04_prueba()
# store es instrumentación de prueba; la guía conecta solo print.
tb.msg_connect((tb.epy_block_1, 'out'), (tb.observador, 'store'))
tb.start()
esperados = []

def esperar(texto):
    esperados.append(texto.encode('utf-8'))
    limite = time.monotonic() + 3
    while tb.observador.num_messages() < len(esperados) and time.monotonic() < limite:
        time.sleep(0.01)
    assert tb.observador.num_messages() == len(esperados)
    pdu = tb.observador.get_message(len(esperados) - 1)
    assert pmt.is_pdu(pdu) and pmt.is_u8vector(pmt.cdr(pdu))
    paquete = bytes(pmt.u8vector_elements(pmt.cdr(pdu)))
    datos = esperados[-1]
    assert len(paquete) == len(datos) + 6
    assert int.from_bytes(paquete[:2], 'big') == len(datos)
    assert paquete[2:-4] == datos
    assert int.from_bytes(paquete[-4:], 'big') == crc_referencia(paquete[:-4])
    if texto == 'Hola':
        assert paquete.hex(' ') == '00 04 48 6f 6c 61 aa 94 8e c9'
    return pdu

def enviar(texto):
    tb.epy_block_0.to_basic_block()._post(pmt.intern('in'), pmt.intern(texto))

try:
    validos = ['Hola', 'SDR', 'á', '¡Hola, Perú!', '  texto  ', 'uno\tdos\ntres',
               'uno\u00a0dos', ' '.join(['x'] * 500), 'a' * 5000, 'á' * 2500,
               'x ' * 499 + 'a' * 4002, 'Hola']
    for texto in validos:
        enviar(texto)
        esperar(texto)
    invalidos = ['', ' \t\n\u00a0', ' '.join(['x'] * 501), 'a' * 5001, 'á' * 2501]
    for i, texto in enumerate(invalidos):
        enviar(texto)
        # El marcador posterior prueba que el rechazo ya fue procesado.
        marcador = 'Valido' + str(i)
        enviar(marcador)
        esperar(marcador)
    tipos_invalidos = [
        pmt.intern('No es PDU'),
        pmt.cons(pmt.make_dict(), pmt.init_f32vector(1, [1.0])),
        pmt.cons(pmt.make_dict(), pmt.init_u8vector(1, [255])),
    ]
    for i, mensaje in enumerate(tipos_invalidos):
        tb.epy_block_1.to_basic_block()._post(pmt.intern('in'), mensaje)
        marcador = 'TrasError' + str(i)
        datos = marcador.encode('utf-8')
        tb.epy_block_1.to_basic_block()._post(pmt.intern('in'), pmt.cons(pmt.make_dict(), pmt.init_u8vector(len(datos), list(datos))))
        esperar(marcador)
    # Los metadatos permanecen fuera de los bytes del paquete.
    metadatos = pmt.dict_add(pmt.make_dict(), pmt.intern('prueba'), pmt.from_long(7))
    tb.epy_block_1.to_basic_block()._post(pmt.intern('in'), pmt.cons(metadatos, pmt.init_u8vector(3, list(b'Fin'))))
    assert pmt.equal(pmt.car(esperar('Fin')), metadatos)
    assert tb.observador.num_messages() == len(esperados) == 21
finally:
    tb.stop()
    tb.wait()
'''
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert resultado.stdout.count("VERBOSE PDU DEBUG PRINT") == 21
    assert "0000: 00 04 48 6f 6c 61 aa 94 8e c9" in resultado.stdout
    assert "0000: 00 02 c3 a1" in resultado.stdout
    assert resultado.stdout.count("mensaje vacío") == 2
    assert resultado.stdout.count("supera 5000 bytes") == 2
    assert resultado.stdout.count("supera 500 palabras") == 1
    assert resultado.stdout.count("se esperaba una PDU de bytes") == 2
    assert resultado.stdout.count("no forman un texto UTF-8 válido") == 1


def test_comprobador_copiable_recupera_texto_y_rechaza_alteraciones(tmp_path, runtime):
    fragmentos = re.findall(r"```python\n(.*?)\n```", GUIA.read_text(encoding="utf-8"), re.S)
    nombres = ["Texto a bytes UTF-8", "Construir paquete", "Comprobar paquete", "Bytes a texto UTF-8"]
    codigos = [next(c for c in fragmentos if f'name="{nombre}"' in c) for nombre in nombres]
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i05_prueba", "generate_options": "no_gui",
            "output_language": "python", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [
            {"name": f"epy_block_{i}", "id": "epy_block", "parameters": {"_source_code": codigo},
             "states": {"state": "enabled", "coordinate": [200 * i, 100], "rotation": 0}}
            for i, codigo in enumerate(codigos)
        ] + [{"name": "observador", "id": "blocks_message_debug", "parameters": {
            "en_uvec": "True", "log_level": "info",
        }, "states": {"state": "enabled", "coordinate": [800, 100], "rotation": 0}}],
        "connections": [[f"epy_block_{i}", "out", f"epy_block_{i+1}", "in"] for i in range(3)]
        + [["epy_block_3", "out", "observador", "print"]],
        "metadata": {"file_format": 1},
    }
    archivo = tmp_path / "comprobar_paquete_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = r'''
import struct, time, zlib
import pmt
from gnuradio import blocks
from enlace_i05_prueba import enlace_i05_prueba

def construir(datos, longitud=None):
    contenido = struct.pack('!H', len(datos) if longitud is None else longitud) + datos
    return contenido + struct.pack('!I', zlib.crc32(contenido))

def pdu(datos, metadatos=None):
    return pmt.cons(pmt.make_dict() if metadatos is None else metadatos, pmt.init_u8vector(len(datos), list(datos)))

base = construir(b'Hola')
assert base == bytes.fromhex('00 04 48 6f 6c 61 aa 94 8e c9')
tb = enlace_i05_prueba()
extraidos = blocks.message_debug()
tb.msg_connect((tb.epy_block_2, 'out'), (extraidos, 'store'))
tb.msg_connect((tb.epy_block_3, 'out'), (tb.observador, 'store'))
tb.start()
numero = 0

def esperar(texto):
    global numero
    numero += 1
    limite = time.monotonic() + 3
    while (tb.observador.num_messages() < numero or extraidos.num_messages() < numero) and time.monotonic() < limite:
        time.sleep(0.001)
    assert tb.observador.num_messages() == numero
    assert extraidos.num_messages() == numero
    assert pmt.symbol_to_string(tb.observador.get_message(numero - 1)) == texto
    salida = extraidos.get_message(numero - 1)
    assert bytes(pmt.u8vector_elements(pmt.cdr(salida))) == texto.encode('utf-8')
    return salida

def inyectar(mensaje):
    tb.epy_block_2.to_basic_block()._post(pmt.intern('in'), mensaje)

try:
    textos = ['Hola', 'SDR', 'á', '¡Hola, Perú!', '  texto  ', 'x', 'á' * 2500,
              'x ' * 499 + 'a' * 4002, 'Hola']
    for texto in textos:
        tb.epy_block_0.to_basic_block()._post(pmt.intern('in'), pmt.intern(texto))
        esperar(texto)
    # Cada bit del paquete, incluidos longitud y CRC, se altera una vez.
    alterados = []
    for posicion in range(len(base)):
        for bit in range(8):
            cambio = bytearray(base)
            cambio[posicion] ^= 1 << bit
            alterados.append(bytes(cambio))
    invalidos = [pdu(c) for c in alterados + [base[:i] for i in range(len(base))]
                 + [base + b'\x00', base + base, construir(b''), construir(b'x', 5001),
                    construir(b'x' * 5001), construir(b'Hola', 5), construir(b'x', 65535)]]
    invalidos += [pmt.intern('No es PDU'),
                  pmt.cons(pmt.make_dict(), pmt.init_f32vector(1, [1.0]))]
    for i, mensaje in enumerate(invalidos):
        inyectar(mensaje)
        marcador = 'Despues' + str(i)
        inyectar(pdu(construir(marcador.encode('utf-8'))))
        # El marcador se procesa después del inválido: detecta cualquier salida indebida.
        esperar(marcador)
    metadatos = pmt.dict_add(pmt.make_dict(), pmt.intern('longitud'), pmt.from_long(999))
    inyectar(pdu(base, metadatos))
    assert pmt.equal(pmt.car(esperar('Hola')), metadatos)
    # Un CRC correcto no garantiza UTF-8 válido. El convertidor lo rechaza, no el comprobador.
    inyectar(pdu(construir(b'\xff')))
    inyectar(pdu(construir(b'Fin')))
    limite = time.monotonic() + 3
    while (tb.observador.num_messages() < numero + 1 or extraidos.num_messages() < numero + 2) and time.monotonic() < limite:
        time.sleep(0.001)
    assert extraidos.num_messages() == numero + 2
    assert bytes(pmt.u8vector_elements(pmt.cdr(extraidos.get_message(numero)))) == b'\xff'
    assert tb.observador.num_messages() == numero + 1
    assert pmt.symbol_to_string(tb.observador.get_message(numero)) == 'Fin'
    print('RESULTADO:', len(invalidos), 'rechazos;', numero + 1, 'textos recuperados')
finally:
    tb.stop()
    tb.wait()
'''
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "VERBOSE PDU DEBUG PRINT" not in resultado.stdout
    assert resultado.stdout.count("CRC incorrecto") == 64
    assert "longitud no permitida" in resultado.stdout
    assert "tamaño no coincide" in resultado.stdout
    assert "paquete demasiado corto" in resultado.stdout
    assert resultado.stdout.count("se esperaba una PDU de bytes") == 2
    assert "los bytes no forman un texto UTF-8 válido" in resultado.stdout
    assert "RESULTADO: 99 rechazos; 110 textos recuperados" in resultado.stdout


def test_alteracion_segundo_paquete_con_enter(tmp_path, runtime):
    fragmentos = re.findall(r"```python\n(.*?)\n```", GUIA.read_text(encoding="utf-8"), re.S)
    nombres = ["Texto a bytes UTF-8", "Construir paquete", "Alterar segundo paquete", "Comprobar paquete", "Bytes a texto UTF-8"]
    codigos = [next(c for c in fragmentos if f'name="{nombre}"' in c) for nombre in nombres]
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i06_prueba", "generate_options": "qt_gui", "title": "Prueba I06",
            "output_language": "python", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [
            {"name": f"epy_block_{i}", "id": "epy_block", "parameters": {"_source_code": codigo},
             "states": {"state": "enabled", "coordinate": [200 * i, 100], "rotation": 0}}
            for i, codigo in enumerate(codigos)
        ] + [
            {"name": "mensaje_a", "id": "qtgui_edit_box_msg", "parameters": {
                "type": "string", "value": "", "label": "Mensaje de A", "is_pair": "False",
                "is_static": "True", "key": "", "gui_hint": "",
            }, "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0}},
            {"name": "observador", "id": "blocks_message_debug", "parameters": {
                "en_uvec": "True", "log_level": "info",
            }, "states": {"state": "enabled", "coordinate": [1000, 100], "rotation": 0}},
        ],
        "connections": [[f"epy_block_{i}", "out", f"epy_block_{i+1}", "in"] for i in range(4)]
        + [["mensaje_a", "msg", "epy_block_0", "in"], ["epy_block_4", "out", "observador", "print"]],
        "metadata": {"file_format": 1},
    }
    archivo = tmp_path / "alteracion_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = r'''
import time, zlib
import pmt
from gnuradio import blocks
from PyQt5 import QtWidgets, QtCore, QtTest
from enlace_i06_prueba import enlace_i06_prueba
app = QtWidgets.QApplication([])
base = bytes.fromhex('00 04 48 6f 6c 61 aa 94 8e c9')
alterado = bytes.fromhex('00 04 49 6f 6c 61 aa 94 8e c9')
assert sum(bin(a ^ b).count('1') for a, b in zip(base, alterado)) == 1
for ejecucion in range(2):
    tb = enlace_i06_prueba()
    antes, despues = blocks.message_debug(), blocks.message_debug()
    tb.msg_connect((tb.epy_block_1, 'out'), (antes, 'store'))
    tb.msg_connect((tb.epy_block_2, 'out'), (despues, 'store'))
    tb.msg_connect((tb.epy_block_4, 'out'), (tb.observador, 'store'))
    tb.start()
    tb.show()
    app.processEvents()
    try:
        editor, = [w for w in tb.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
        assert editor.text() == ''
        assert despues.num_messages() == 0
        # No cambian el texto ni la ejecución entre las tres pulsaciones.
        editor.setText('Hola')
        for numero in range(1, 4):
            QtTest.QTest.keyClick(editor, QtCore.Qt.Key_Return)
            limite = time.monotonic() + 3
            esperados = 1 if numero <= 2 else 2
            while (antes.num_messages() < numero or despues.num_messages() < numero or tb.observador.num_messages() < esperados) and time.monotonic() < limite:
                QtTest.QTest.qWait(5)
            assert antes.num_messages() == despues.num_messages() == numero
            entrada = antes.get_message(numero - 1)
            salida = despues.get_message(numero - 1)
            assert bytes(pmt.u8vector_elements(pmt.cdr(entrada))) == base
            datos = bytes(pmt.u8vector_elements(pmt.cdr(salida)))
            assert datos == (alterado if numero == 2 else base)
            assert pmt.equal(pmt.car(entrada), pmt.car(salida))
            assert (zlib.crc32(datos[:-4]) == int.from_bytes(datos[-4:], 'big')) == (numero != 2)
        # La recepción del tercero cierra la secuencia: el segundo no pudo producir texto.
        assert tb.observador.num_messages() == 2
        assert [pmt.symbol_to_string(tb.observador.get_message(i)) for i in range(2)] == ['Hola', 'Hola']
    finally:
        tb.stop()
        tb.wait()
        tb.close()
        app.processEvents()
    print('SECUENCIA_OK', ejecucion)
'''
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert resultado.stdout.count("SECUENCIA_OK") == 2
    assert resultado.stdout.count("MESSAGE DEBUG PRINT") == 4
    assert resultado.stdout.count("CRC incorrecto. Se rechaza.") == 2
    assert resultado.stdout.count("paquete 2, bit alterado.") == 2
    assert "VERBOSE PDU DEBUG PRINT" not in resultado.stdout
    assert not re.search(r"^Iola$", resultado.stdout, re.M)


def test_bytes_a_bits_copiable_preserva_orden_y_paquete(tmp_path, runtime):
    fragmentos = re.findall(r"```python\n(.*?)\n```", GUIA.read_text(encoding="utf-8"), re.S)
    nombres = ["Texto a bytes UTF-8", "Construir paquete", "Bytes a bits"]
    codigos = [next(c for c in fragmentos if f'name="{nombre}"' in c) for nombre in nombres]
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i07_prueba", "generate_options": "no_gui",
            "output_language": "python", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [
            {"name": f"epy_block_{i}", "id": "epy_block", "parameters": {"_source_code": codigo},
             "states": {"state": "enabled", "coordinate": [200 * i, 100], "rotation": 0}}
            for i, codigo in enumerate(codigos)
        ] + [{"name": "observador", "id": "blocks_message_debug", "parameters": {
            "en_uvec": "True", "log_level": "info",
        }, "states": {"state": "enabled", "coordinate": [600, 100], "rotation": 0}}],
        "connections": [["epy_block_0", "out", "epy_block_1", "in"],
                        ["epy_block_1", "out", "epy_block_2", "in"],
                        ["epy_block_2", "out", "observador", "print"]],
        "metadata": {"file_format": 1},
    }
    archivo = tmp_path / "bytes_bits_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = r'''
import struct, time, zlib
import numpy as np
import pmt
from enlace_i07_prueba import enlace_i07_prueba
tb = enlace_i07_prueba()
tb.msg_connect((tb.epy_block_2, 'out'), (tb.observador, 'store'))
tb.start()
numero = 0
meta = pmt.dict_add(pmt.make_dict(), pmt.intern('prueba'), pmt.from_long(7))
def comprobar(datos, metadata):
    global numero
    numero += 1
    limite = time.monotonic() + 3
    while tb.observador.num_messages() < numero and time.monotonic() < limite:
        time.sleep(0.005)
    assert tb.observador.num_messages() == numero
    recibido = tb.observador.get_message(numero - 1)
    assert pmt.equal(pmt.car(recibido), metadata)
    bits = np.array(pmt.u8vector_elements(pmt.cdr(recibido)), dtype=np.uint8)
    assert set(bits).issubset({0, 1})
    assert len(bits) == 8 * len(datos)
    assert np.array_equal(bits, np.unpackbits(np.frombuffer(datos, dtype=np.uint8), bitorder='big'))
    assert np.packbits(bits, bitorder='big').tobytes() == datos
    return bits
try:
    textos = ['Hola', 'SDR', 'á', '  Hola  ', 'a' * 5000, 'Hola']
    for texto in textos:
        tb.epy_block_0.to_basic_block()._post(pmt.intern('in'), pmt.intern(texto))
        datos = texto.encode('utf-8')
        cuerpo = struct.pack('!H', len(datos)) + datos
        paquete = cuerpo + struct.pack('!I', zlib.crc32(cuerpo))
        bits = comprobar(paquete, pmt.make_dict())
        if texto == 'Hola':
            assert len(bits) == 80
            assert ''.join(map(str, bits[:24])) == '000000000000010001001000'
    # Todos los valores de byte y todos sus bits, contrastados con NumPy.
    datos = bytes(range(256))
    tb.epy_block_2.to_basic_block()._post(pmt.intern('in'), pmt.cons(meta, pmt.init_u8vector(len(datos), list(datos))))
    comprobar(datos, meta)
    invalidos = [pmt.intern('No es PDU'), pmt.cons(meta, pmt.init_f32vector(1, [1.0])),
                 pmt.cons(meta, pmt.init_u8vector(0, []))]
    for invalido in invalidos:
        tb.epy_block_2.to_basic_block()._post(pmt.intern('in'), invalido)
        # Un marcador posterior demuestra rechazo sin bloquear la siguiente entrada.
        datos = b'\x00\x80\x01\xff'
        tb.epy_block_2.to_basic_block()._post(pmt.intern('in'), pmt.cons(meta, pmt.init_u8vector(len(datos), list(datos))))
        comprobar(datos, meta)
    assert numero == 10
finally:
    tb.stop()
    tb.wait()
print('BITS_OK', numero)
'''
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "BITS_OK 10" in resultado.stdout
    assert resultado.stdout.count("VERBOSE PDU DEBUG PRINT") == 10
    assert "pdu length =         80 bytes" in resultado.stdout
    assert resultado.stdout.count("Bytes a bits: se esperaba una PDU de bytes.") == 2
    assert resultado.stdout.count("Bytes a bits: vector vacío.") == 1


def test_captura_bits_hola_reconstruye_el_paquete():
    # Transcripción visual de la captura del profesor, incluidos los valores envueltos.
    filas = [
        "00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00",
        "00 01 00 00 01 00 00 00 00 01 01 00 01 01 01 01",
        "00 01 01 00 01 01 00 00 00 01 01 00 00 00 00 01",
        "01 00 01 00 01 00 01 00 01 00 00 01 00 01 00 00",
        "01 00 00 00 01 01 01 00 01 01 00 00 01 00 00 01",
    ]
    bits = bytes.fromhex(" ".join(filas))
    assert len(bits) == 80 and set(bits) == {0, 1}
    datos = bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, 80, 8))
    assert datos == bytes.fromhex("00 04 48 6f 6c 61 aa 94 8e c9")


def test_bpsk_estandar_y_constelacion_por_mensajes(tmp_path, runtime):
    guia = GUIA.read_text(encoding="utf-8")
    seccion = guia.split("## 11. Asociar bits", 1)[1].split("## Referencias", 1)[0]
    assert 'name="Bits a simbolos BPSK"' not in seccion
    for requisito in ("PDU to Tagged Stream", "Chunks to Symbols", "Tagged Stream to PDU", "Python Snippet", "Main - After Init", "packet_len", "640", "576"):
        assert requisito in seccion
    for campo, valor in [("ID", "a_stream"), ("ID", "mapeador"), ("Item Type", "Byte"),
                         ("Item Type", "Complex"), ("Length tag name", "packet_len"),
                         ("Input Type", "Byte"), ("Output Type", "Complex"),
                         ("Symbol Table", "[-1+0j, 1+0j]"), ("Dimension", "1"), ("Num Ports", "1")]:
        assert f"| `{campo}` | `{valor}` |" in seccion
    fragmentos = re.findall(r"```python\n(.*?)\n```", GUIA.read_text(encoding="utf-8"), re.S)
    nombres = ["Texto a bytes UTF-8", "Construir paquete", "Bytes a bits"]
    codigos = [next(c for c in fragmentos if f'name="{nombre}"' in c) for nombre in nombres]
    ajuste_buffers = next(c for c in fragmentos if "self.a_stream.set_min_output_buffer" in c)
    grafo = {
        "options": {"parameters": {
            "id": "enlace_i08_estandar_prueba", "generate_options": "qt_gui", "title": "Prueba BPSK estandar",
            "output_language": "python", "run": "True",
        }, "states": {"state": "enabled"}},
        "blocks": [
            {"name": f"epy_block_{i}", "id": "epy_block", "parameters": {"_source_code": codigo},
             "states": {"state": "enabled", "coordinate": [200 * i, 100], "rotation": 0}}
            for i, codigo in enumerate(codigos)
        ] + [
            {"name": "a_stream", "id": "pdu_pdu_to_tagged_stream", "parameters": {
                "type": "byte", "tag": "packet_len",
            }, "states": {"state": "enabled", "coordinate": [600, 100], "rotation": 0}},
            {"name": "mapeador", "id": "digital_chunks_to_symbols_xx", "parameters": {
                "in_type": "byte", "out_type": "complex", "symbol_table": "[-1+0j, 1+0j]", "dimension": "1", "num_ports": "1",
            }, "states": {"state": "enabled", "coordinate": [800, 100], "rotation": 0}},
            {"name": "a_pdu", "id": "pdu_tagged_stream_to_pdu", "parameters": {
                "type": "complex", "tag": "packet_len",
            }, "states": {"state": "enabled", "coordinate": [1000, 100], "rotation": 0}},
            {"name": "ajustar_buffers", "id": "snippet", "parameters": {
                "section": "main_after_init", "priority": "0", "code": ajuste_buffers,
            }, "states": {"state": "enabled", "coordinate": [800, 0], "rotation": 0}},
            {"name": "visor_tamano", "id": "blocks_message_debug", "parameters": {
                "en_uvec": "False", "log_level": "info",
            }, "states": {"state": "enabled", "coordinate": [1200, 0], "rotation": 0}},
            {"name": "mensaje_a", "id": "qtgui_edit_box_msg", "parameters": {
                "type": "string", "value": "", "label": "Mensaje de A", "is_pair": "False",
                "is_static": "True", "key": "", "gui_hint": "",
            }, "states": {"state": "enabled", "coordinate": [0, 0], "rotation": 0}},
            {"name": "constelacion", "id": "qtgui_const_sink_x", "parameters": {
                "type": "msg_complex", "name": "Simbolos BPSK", "grid": "True",
                "autoscale": "False", "xmin": "-1.5", "xmax": "1.5", "ymin": "-1.5", "ymax": "1.5",
                "style1": "0", "marker1": "0", "gui_hint": "",
            }, "states": {"state": "enabled", "coordinate": [800, 100], "rotation": 0}},
        ],
        "connections": [[f"epy_block_{i}", "out", f"epy_block_{i+1}", "in"] for i in range(2)]
        + [["mensaje_a", "msg", "epy_block_0", "in"], ["epy_block_2", "out", "a_stream", "pdus"],
           ["a_stream", "0", "mapeador", "0"], ["mapeador", "0", "a_pdu", "0"],
           ["a_pdu", "pdus", "constelacion", "in"], ["a_pdu", "pdus", "visor_tamano", "print"]],
        "metadata": {"file_format": 1},
    }
    archivo = tmp_path / "bpsk_prueba.grc"
    archivo.write_text(yaml.safe_dump(grafo, sort_keys=False), encoding="utf-8")
    compilacion = subprocess.run([runtime[0], "-o", str(tmp_path), str(archivo)], capture_output=True, text=True, timeout=45)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    programa = r'''
import os, struct, time, zlib
import numpy as np
import pmt
from gnuradio import blocks, digital
from PyQt5 import QtWidgets, QtCore, QtTest
from enlace_i08_estandar_prueba import enlace_i08_estandar_prueba, snippets_main_after_init
app = QtWidgets.QApplication([])
tb = enlace_i08_estandar_prueba()
# GRC ejecuta este hook antes de tb.start() en el main generado.
snippets_main_after_init(tb)
observador = blocks.message_debug()
tb.msg_connect((tb.a_pdu, 'pdus'), (observador, 'store'))
# Instrumentación: captura los tags del stream, sin modificar el recorrido del alumno.
tags = blocks.vector_sink_c()
tb.connect(tb.mapeador, tags)
tb.start()
tb.resize(900, 650)
tb.show()
app.processEvents()
numero = 0
meta = pmt.dict_add(pmt.make_dict(), pmt.intern('prueba'), pmt.from_long(8))
constelacion = digital.constellation_bpsk()
def comprobar(bits, metadata, comprobar_visor=True):
    global numero
    numero += 1
    limite = time.monotonic() + 3
    while (observador.num_messages() < numero or (comprobar_visor and tb.constelacion.nsamps() != len(bits))) and time.monotonic() < limite:
        QtTest.QTest.qWait(5)
    assert observador.num_messages() >= numero
    if comprobar_visor:
        assert tb.constelacion.nsamps() == len(bits)
    salida = observador.get_message(numero - 1)
    if pmt.dict_has_key(metadata, pmt.intern('prueba')):
        assert pmt.equal(pmt.dict_ref(pmt.car(salida), pmt.intern('prueba'), pmt.PMT_NIL), pmt.dict_ref(metadata, pmt.intern('prueba'), pmt.PMT_NIL))
    assert pmt.is_c32vector(pmt.cdr(salida))
    simbolos = np.array(pmt.c32vector_elements(pmt.cdr(salida)))
    esperados = np.array([constelacion.map_to_points_v(int(b))[0] for b in bits])
    assert np.array_equal(simbolos, esperados)
    assert np.all(np.abs(simbolos) == 1) and np.all(simbolos.imag == 0)
    assert np.array_equal((simbolos.real > 0).astype(int), bits)
    return simbolos
try:
    editor, = [w for w in tb._mensaje_a_win.findChildren(QtWidgets.QLineEdit) if not w.isHidden()]
    longitudes = []
    for texto in ['Hola', 'SDR', 'a' * 5000, 'Hola']:
        editor.setText(texto)
        QtTest.QTest.keyClick(editor, QtCore.Qt.Key_Return)
        datos = texto.encode('utf-8')
        cuerpo = struct.pack('!H', len(datos)) + datos
        paquete = cuerpo + struct.pack('!I', zlib.crc32(cuerpo))
        bits = np.unpackbits(np.frombuffer(paquete, dtype=np.uint8), bitorder='big')
        simbolos = comprobar(bits, pmt.make_dict())
        longitudes.append(len(bits))
        assert len(simbolos) == (len(datos) + 6) * 8
        QtTest.QTest.qWait(150)
    # Los símbolos de H pertenecen a las posiciones 16 a 23 del paquete, no al comienzo.
    assert list(simbolos[16:24].real) == [-1, 1, -1, -1, 1, -1, -1, -1]
    if os.environ.get('SDR_I08_SCREENSHOT'):
        assert tb.grab().save(os.environ['SDR_I08_SCREENSHOT'])
    # Tres PDUs consecutivas de tamaño distinto prueban delimitación y orden.
    casos = [[0, 1, 1, 0], [1], [0, 0, 1]]
    for bits in casos:
        tb.a_stream.to_basic_block()._post(pmt.intern('pdus'), pmt.cons(meta, pmt.init_u8vector(len(bits), bits)))
    for bits in casos:
        comprobar(bits, meta, comprobar_visor=False)
        longitudes.append(len(bits))
    QtTest.QTest.qWait(200)
    # Un mensaje aislado después de una pausa debe salir sin otro mensaje posterior.
    bits = [1, 0]
    tb.a_stream.to_basic_block()._post(pmt.intern('pdus'), pmt.cons(meta, pmt.init_u8vector(2, bits)))
    comprobar(bits, meta)
    longitudes.append(2)
    assert numero == 8
    assert observador.num_messages() == numero
    limite = time.monotonic() + 3
    while tags.nitems_read(0) < sum(longitudes) and time.monotonic() < limite:
        QtTest.QTest.qWait(5)
    assert tags.nitems_read(0) == sum(longitudes)
    etiquetas = [t for t in tags.tags() if pmt.symbol_to_string(t.key) == 'packet_len']
    assert [pmt.to_long(t.value) for t in etiquetas] == longitudes
    assert [t.offset for t in etiquetas] == list(np.cumsum([0] + longitudes[:-1]))
finally:
    tb.stop()
    tb.wait()
    tb.close()
print('BPSK_OK', numero)
'''
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    resultado = subprocess.run([runtime[1], "-c", programa], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=25)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "BPSK_OK 8" in resultado.stdout
    assert resultado.stdout.count("640 bytes (printing disabled)") == 2
    assert resultado.stdout.count("576 bytes (printing disabled)") == 1
    assert "320384 bytes (printing disabled)" in resultado.stdout
    assert resultado.stdout.count("VERBOSE PDU DEBUG PRINT") == 8


@pytest.mark.parametrize("generador,nombre", [
    ("gen_enlace_entrada_texto.py", "enlace-01-entrada-texto.png"),
    ("gen_enlace_paquete.py", "enlace-15-formato-paquete.png"),
    ("gen_enlace_error_bit.py", "enlace-22-error-un-bit.png"),
    ("gen_enlace_bytes_bits.py", "enlace-27-bytes-bits.png"),
    ("gen_enlace_bpsk.py", "enlace-31-mapeo-bpsk.png"),
])
def test_figura_es_reproducible(tmp_path, generador, nombre):
    import importlib.util

    ruta = CARPETA / "figures" / generador
    spec = importlib.util.spec_from_file_location("figura_enlace", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    archivo = modulo.generar(tmp_path)
    assert archivo.name == nombre
    assert archivo.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

"""Vectores externos y controles para la verificación LoRaWAN 1.0.x."""

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest
import yaml


spec = importlib.util.spec_from_file_location(
    "verificar_lorawan", Path(__file__).resolve().parents[1] / "scripts/sesion08_lora/verificar_lorawan.py"
)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)
analizar_trama = modulo.analizar_trama

# Vector público de ChirpStack/brocaar; no lo genera el código bajo prueba.
# https://github.com/brocaar/lorawan/blob/master/phypayload_test.go
TRAMA = bytes.fromhex("400403020180010001a694642615d6c3b582")
NWK = bytes([2]) * 16
APP = bytes([1]) * 16


def test_vector_externo_hello():
    r = analizar_trama(TRAMA, NWK, APP, 1)
    assert r["mic_valido"] is True
    assert r["mic_calculado"] == "d6c3b582"
    assert r["payload_descifrado_utf8"] == "hello"
    assert r["dev_addr"] == "01020304"
    assert r["direccion"] == "uplink"


def test_clave_red_incorrecta_impide_descifrado():
    r = analizar_trama(TRAMA, bytes(16), APP, 1)
    assert r["mic_valido"] is False
    assert r["payload_descifrado_hex"] is None


def test_clave_aplicacion_incorrecta_no_cambia_mic():
    r = analizar_trama(TRAMA, NWK, bytes(16), 1)
    assert r["mic_valido"] is True
    assert r["payload_descifrado_hex"] != b"hello".hex()


def test_alteracion_payload_invalida_mic():
    alterada = bytearray(TRAMA)
    alterada[9] ^= 1
    r = analizar_trama(bytes(alterada), NWK, APP, 1)
    assert r["mic_valido"] is False
    assert r["payload_descifrado_hex"] is None


def test_bits_altos_contador_participan_en_mic():
    r = analizar_trama(TRAMA, NWK, APP, 65537)
    assert r["mic_valido"] is False


@pytest.mark.parametrize("contador", [-1, 0, 2**32 + 1])
def test_contador_incompatible_se_rechaza(contador):
    with pytest.raises(ValueError, match="FCnt"):
        analizar_trama(TRAMA, NWK, APP, contador)


def test_no_se_admite_join_como_trama_de_datos():
    with pytest.raises(ValueError, match="tramas de datos"):
        analizar_trama(bytes(23), NWK, APP)


def test_fopts_truncados_se_rechazan():
    with pytest.raises(ValueError, match="FOpts"):
        analizar_trama(bytes.fromhex("60dc5de601a62300fc27e690"), NWK, APP)


def test_trama_real_con_comando_mac_usa_nwk_s_key():
    # Brno, paquete 99: FPort=0 usa NwkSKey, no AppSKey.
    r = analizar_trama(
        bytes.fromhex("40dc5de60180010000fab0f3e457"),
        bytes.fromhex("e2898779a03de59e2317b149abf00238"), bytes(16), 1,
    )
    assert r["mic_valido"] is True
    assert r["fport"] == 0
    assert r["tipo_payload"] == "MAC commands"
    assert r["payload_descifrado_hex"] == "0d"


def test_downlink_real_sin_frm_payload():
    r = analizar_trama(
        bytes.fromhex("60dc5de6018c00000d51c16150ae061100000000bc032ea4"),
        bytes.fromhex("e2898779a03de59e2317b149abf00238"), bytes(16), 0,
    )
    assert r["mic_valido"] is True
    assert r["direccion"] == "downlink"
    assert r["fport"] is None
    assert r["payload_descifrado_hex"] is None


def test_cadena_iq_generado_y_entrega_del_laboratorio(tmp_path):
    grcc = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
    python_gr = Path(grcc).parent / "python3"
    if not python_gr.is_file():
        pytest.skip("GNU Radio no está disponible")
    root = Path(__file__).resolve().parents[1]
    programa = root / "scripts/sesion08_lora/verificar_lorawan_iq.py"
    muestras = tmp_path / "output/lorawan-iq"
    r = subprocess.run(
        [str(python_gr), "-B", str(programa), "--salida", str(muestras)],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    informe = json.loads((muestras / "verificacion.json").read_text())
    assert informe["controles_aprobados"] is True
    bueno, alterado = informe["casos"]
    assert bueno["lora_phy"]["crc_valido"] is True
    assert bueno["lorawan"]["payload_descifrado_utf8"] == "timeout"
    assert alterado["lora_phy"]["crc_valido"] is True
    assert alterado["lorawan"]["mic_valido"] is False
    assert informe["sync_word_0x12_tramas"] == 0

    # La alternativa opcional de GRC debe conservar el mismo resultado.
    carpeta_grafos = tmp_path / "gnuradio/flowgraphs"
    carpeta_grafos.mkdir(parents=True)
    grafo = carpeta_grafos / "lora_recuperar_trama.grc"
    shutil.copyfile(root / "gnuradio/flowgraphs/lora_recuperar_trama.grc", grafo)
    compilacion = subprocess.run([grcc, "-o", str(carpeta_grafos), str(grafo)],
                                capture_output=True, text=True, timeout=30)
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    recepcion = subprocess.run([str(python_gr), str(grafo.with_suffix(".py"))],
                              cwd=carpeta_grafos, capture_output=True, text=True, timeout=30)
    assert recepcion.returncode == 0, recepcion.stdout + recepcion.stderr
    assert "(crc_valid . #t)" in recepcion.stdout
    assert (muestras / "trama_recibida.bin").read_bytes().hex() == bueno["lora_phy"]["payload_hex"]

    # El recorrido principal no depende del archivo producido por File Sink.
    (muestras / "trama_recibida.bin").unlink()
    inspector = root / "scripts/sesion08_lora/inspeccionar_lora.py"
    inspeccion = subprocess.run(
        [str(python_gr), str(inspector), "--archivo", str(muestras / "correcto.sigmf-data"),
         "--salida", str(muestras / "traza"), "--etapa", "phypayload"],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert inspeccion.returncode == 0, inspeccion.stdout + inspeccion.stderr
    assert (muestras / "traza/03_phypayload.bin").read_bytes().hex() == bueno["lora_phy"]["payload_hex"]
    extractor = root / "scripts/sesion08_lora/extraer_mensaje.py"
    extraccion = subprocess.run([str(python_gr), str(extractor)], cwd=tmp_path,
                               capture_output=True, text=True, timeout=10)
    assert extraccion.returncode == 0, extraccion.stdout + extraccion.stderr
    assert (muestras / "trama_recibida.bin").read_bytes().hex() == bueno["lora_phy"]["payload_hex"]
    assert (muestras / "mensaje_cifrado.bin").read_bytes() == bytes.fromhex("dbf5a4e31239d0")
    assert "FRMPayload (bytes 10 a 16)" in extraccion.stdout


@pytest.mark.parametrize("entrada", [bytes(19), bytes(20), bytes.fromhex("80" + "00"*4 + "0f" + "00"*14)])
def test_extractor_no_crea_entregas_si_la_entrada_es_incompatible(tmp_path, entrada):
    import sys
    root = Path(__file__).resolve().parents[1]
    archivo = tmp_path / "entrada.bin"
    archivo.write_bytes(entrada)
    salida = tmp_path / "entrega"
    r = subprocess.run(
        [sys.executable, str(root / "scripts/sesion08_lora/extraer_mensaje.py"),
         "--entrada", str(archivo), "--salida", str(salida)],
        capture_output=True, text=True, timeout=10,
    )
    assert r.returncode != 0
    assert not salida.exists()


def test_reto_fopts_de_la_guia_tiene_los_campos_y_limites_esperados():
    guia = (Path(__file__).resolve().parents[1] / "docs/sessions/06/clase6.md").read_text()
    reto = guia.split("## 9. Reto", 1)[1].split("## 10.", 1)[0]
    trama = bytes.fromhex(re.search(r"```text\n(.*?)```", reto, re.S).group(1))
    r = analizar_trama(trama, bytes(16), bytes(16))
    assert len(trama) == 22
    assert trama[5] & 0x0F == 3
    assert r["fopts_hex"] == "06a403"
    assert r["fport"] == 0x11
    assert r["frm_payload_cifrado_hex"] == "89c917d5d16f"
    assert r["mic_recibido"] == "5da145ff"


def test_sesion_y_alcance_de_entrega_coinciden_con_la_navegacion():
    root = Path(__file__).resolve().parents[1]
    guia = (root / "docs/sessions/06/clase6.md").read_text()
    metadatos = yaml.safe_load(guia.split("---", 2)[1])
    assert metadatos["session"] == 8
    assert metadatos["title"].startswith("Sesión 8")
    config = yaml.load((root / "mkdocs.yml").read_text(), Loader=yaml.BaseLoader)
    sesiones = next(e["Sesiones"] for e in config["nav"] if "Sesiones" in e)
    assert any(e.get("08 — Señales LoRa") == "sessions/06/clase6.md"
               for e in sesiones if isinstance(e, dict))
    entrega = guia.split("## 10. Entrega", 1)[1].split("## 11.", 1)[0]
    assert "Laboratorio #5" in entrega and "tarea-lab05-[codigo_uni]" in entrega
    assert "trama_recibida.bin" in entrega and "20 bytes" in entrega
    assert "mensaje_cifrado.bin" in entrega and "7 bytes cifrados" in entrega

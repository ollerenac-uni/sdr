"""Vectores externos y controles para la verificación LoRaWAN 1.0.x."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


spec = importlib.util.spec_from_file_location(
    "verificar_lorawan", Path(__file__).resolve().parents[1] / "scripts/verificar_lorawan.py"
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


def test_cadena_iq_real_de_gnuradio_y_controles(tmp_path):
    grcc = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
    python_gr = Path(grcc).parent / "python3"
    if not python_gr.is_file():
        pytest.skip("GNU Radio no está disponible")
    programa = Path(__file__).resolve().parents[1] / "scripts/verificar_lorawan_iq.py"
    r = subprocess.run(
        [str(python_gr), "-B", str(programa), "--salida", str(tmp_path)],
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    informe = json.loads((tmp_path / "verificacion.json").read_text())
    assert informe["controles_aprobados"] is True
    bueno, alterado = informe["casos"]
    assert bueno["lora_phy"]["crc_valido"] is True
    assert bueno["lorawan"]["payload_descifrado_utf8"] == "timeout"
    assert alterado["lora_phy"]["crc_valido"] is True
    assert alterado["lorawan"]["mic_valido"] is False
    assert informe["sync_word_0x12_tramas"] == 0

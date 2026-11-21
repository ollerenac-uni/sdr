"""Aceptación por la aplicación, autenticidad y estado ante replay LoRaWAN."""

import json
from pathlib import Path
import subprocess
import sys

from scripts.sesion08_lora.crc_lora import crc_lora
from scripts.sesion08_lora.simular_replay import (
    Paquete, Receptor, crear_uplink, ejecutar_experimento, empaquetar, reproducir,
)


def test_crc_compartido_conserva_el_valor_observado_en_la_senal():
    trama = bytes.fromhex("80dc5de60190040001dbf5a4e31239d05321687b")
    assert crc_lora(trama) == (0xca2b, 0xa250)


def test_replay_autentico_solo_repite_la_entrega_en_el_vulnerable():
    r = ejecutar_experimento()
    assert r["comprobaciones_aprobadas"]
    assert [e["con_fcnt"]["entregado"] for e in r["eventos"]] == [True, True, False]
    assert [e["vulnerable"]["entregado"] for e in r["eventos"]] == [True, True, True]
    replay = r["eventos"][-1]["con_fcnt"]
    assert replay["crc_valido"] and replay["mic_valido"]
    assert replay["ultimo_fcnt_antes"] == replay["ultimo_fcnt_despues"] == 5
    assert r["resumen"]["con_fcnt"]["ultimo_dato"] == "temp=80"
    assert r["resumen"]["vulnerable"]["ultimo_dato"] == "temp=25"


def test_copia_no_modifica_los_bytes_ni_recalcula_el_crc():
    paquete = Paquete(crear_uplink(b"temp=25", 4), 0x1234)
    assert reproducir(paquete) == paquete


def test_primera_trama_con_contador_cero_y_duplicado_no_se_entrega():
    receptor = Receptor(True)
    paquete = empaquetar(crear_uplink(b"temp=25", 0))
    assert receptor.recibir(paquete)["entregado"]
    duplicado = receptor.recibir(paquete)
    assert not duplicado["entregado"]
    assert duplicado["motivo"] == "FCNT_ANTIGUO_O_REPETIDO"
    assert len(receptor.entregas) == 1


def test_mic_invalido_no_puede_avanzar_el_contador_ni_bloquear_el_valido():
    receptor = Receptor(True)
    receptor.recibir(empaquetar(crear_uplink(b"temp=25", 4)))
    falso = bytearray(crear_uplink(b"temp=80", 5))
    falso[-1] ^= 1  # Mantiene estructura y FCnt; MIC incorrecto con CRC nuevo.
    rechazo = receptor.recibir(empaquetar(falso))
    assert rechazo["crc_valido"] and not rechazo["mic_valido"]
    assert rechazo["ultimo_fcnt_despues"] == 4
    assert rechazo["estado_aplicacion"] == "temp=25"
    valido = receptor.recibir(empaquetar(crear_uplink(b"temp=80", 5)))
    assert valido["entregado"] and valido["ultimo_fcnt_despues"] == 5


def test_crc_invalido_no_actualiza_estado():
    receptor = Receptor(True)
    paquete = empaquetar(crear_uplink(b"temp=25", 4))
    rechazo = receptor.recibir(Paquete(paquete.phypayload, paquete.crc_recibido ^ 1))
    assert rechazo["motivo"] == "CRC_INVALIDO"
    assert rechazo["mic_valido"] is None
    assert receptor.ultimos == {} and receptor.entregas == []


def test_controles_de_alteracion_se_rechazan_en_ambos_receptores():
    for caso in ejecutar_experimento()["controles"]:
        for tipo in ("vulnerable", "con_fcnt"):
            r = caso[tipo]
            assert r["crc_valido"] and not r["mic_valido"]
            assert not r["entregado"] and r["motivo"] == "MIC_INVALIDO"
        assert caso["con_fcnt"]["ultimo_fcnt_despues"] == 5


def test_comandos_del_alumno_y_archivos_sin_preparar_iq(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts/sesion08_lora/simular_replay.py"
    for etapa, esperado in (("tramas", "A_replay"), ("replay", "DESCARTA"),
                            ("controles", "MIC_INVALIDO"), ("todo", "temp=80")):
        salida = tmp_path / etapa
        r = subprocess.run([sys.executable, str(script), "--etapa", etapa, "--salida", str(salida)],
                           cwd=tmp_path, capture_output=True, text=True, timeout=15)
        assert r.returncode == 0, r.stdout + r.stderr
        assert esperado in r.stdout and "APROBADAS" in r.stdout
        assert (salida / "A_normal.bin").read_bytes() == (salida / "A_replay.bin").read_bytes()
        assert all(len(p.read_bytes()) == 20 for p in salida.glob("*.bin"))
        informe = json.loads((salida / "replay.json").read_text())
        assert informe["comprobaciones_aprobadas"]

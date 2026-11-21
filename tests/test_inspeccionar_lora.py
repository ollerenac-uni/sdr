"""La inspección debe deducir la longitud del I/Q, no del vector conocido."""

import json
from pathlib import Path
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
PYTHON_GR = Path.home() / "radioconda/bin/python"
TRAMA = bytes.fromhex("80dc5de60190040001dbf5a4e31239d05321687b")


@pytest.mark.parametrize("extra,relleno", [(b"", 25), (b"\x01", 15), (b"\x01\x02", 5)])
def test_longitud_y_contenido_se_recuperan_de_la_cabecera(tmp_path, extra, relleno):
    if not PYTHON_GR.is_file():
        pytest.skip("Radioconda no está disponible")
    trama = TRAMA + extra
    archivo = tmp_path / "senal.sigmf-data"
    generacion = subprocess.run(
        [str(PYTHON_GR), "-c",
         "import sys; from pathlib import Path; "
         "from scripts.sesion08_lora.verificar_lorawan_iq import guardar_iq; "
         "guardar_iq(bytes.fromhex(sys.argv[1]), Path(sys.argv[2]))",
         trama.hex(), str(archivo)],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert generacion.returncode == 0, generacion.stdout + generacion.stderr
    salida = tmp_path / "traza"
    recepcion = subprocess.run(
        [str(PYTHON_GR), str(ROOT / "scripts/sesion08_lora/inspeccionar_lora.py"),
         "--archivo", str(archivo), "--salida", str(salida)],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert recepcion.returncode == 0, recepcion.stdout + recepcion.stderr
    r = json.loads((salida / "traza.json").read_text())
    assert len(r["simbolos"]) == 43
    assert len(r["bits_simbolos"]) == 301
    assert (salida / "01_simbolos_bits.txt").read_text().strip() == r["bits_simbolos"]
    h, c = r["cabecera"], r["contenido"]
    assert h["longitud_bytes"] == len(trama)
    assert h["bits_decodificados"][:8] == f"{len(trama):08b}"
    assert h["cr_indice"] == 1 and h["crc_presente"] and h["checksum_valido"]
    assert c["bits_codificados"] == 245
    assert c["bits_relleno"] == relleno and c["crc_valido"]
    assert len(c["bloques"]) == 7
    assert sum(len(b["filas_gray"]) for b in c["bloques"]) == 35
    palabras = [p for b in c["bloques"] for p in b["palabras"]]
    assert len(palabras) == 49
    assert sum(p["rol"] == "contenido" for p in palabras) == 2*len(trama)
    assert sum(p["rol"] == "CRC" for p in palabras) == 4
    assert sum(p["rol"] == "relleno" for p in palabras) == relleno//5
    assert all(p["bits"] == "00000" for p in palabras if p["rol"] == "relleno")
    assert bytes(b["recuperado"] for b in c["bytes"] if b["rol"] == "contenido") == trama
    assert all(b["mascara"] is None for b in c["bytes"] if b["rol"] == "CRC")
    assert c["crc_calculo"]["calculado"] == c["crc_calculo"]["recibido"]
    assert bytes.fromhex(c["payload_hex"]) == trama
    assert (salida / "03_phypayload.bin").read_bytes() == trama
    if not extra:
        assert h["bits_decodificados"] == "00010100001100010111"
        assert r["bits_simbolos"][:56] == (
            "10110010110001110000100000011101001001000111000011001001")
        assert c["crc_hex"] == "50 a2"
        assert c["bloques"][0]["palabras"][0]["bits"] == "11110"
        assert c["bytes"][0]["antes_blanqueo"] == 0x7f
        assert c["bytes"][0]["mascara"] == 0xff
        assert c["bytes"][0]["recuperado"] == 0x80
        assert c["crc_calculo"] == {"sobre_primeros_n_menos_2": 0xca2b,
                                    "ultimos_dos_contenido": 0x687b,
                                    "calculado": 0xa250, "recibido": 0xa250}
        # El primer bit de cada palabra procede de una posición distinta de S1.
        # La primera palabra completa, en cambio, combina las ocho filas.
        filas = h["filas_desentrelazador"]
        assert "".join(filas[i][(i-1) % 5] for i in range(8)) == "10001011"
        assert h["palabras_fec"][0] == "10001011"
        assert h["nibbles"][0] == 1


@pytest.fixture(scope="module")
def muestra_comandos(tmp_path_factory):
    if not PYTHON_GR.is_file():
        pytest.skip("Radioconda no está disponible")
    archivo = tmp_path_factory.mktemp("lora_cli") / "muestra.sigmf-data"
    r = subprocess.run(
        [str(PYTHON_GR), "-c",
         "import sys; from pathlib import Path; "
         "from scripts.sesion08_lora.verificar_lorawan_iq import guardar_iq; "
         "guardar_iq(bytes.fromhex(sys.argv[1]), Path(sys.argv[2]))", TRAMA.hex(), str(archivo)],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    return archivo


def ejecutar_comando(archivo, salida, etapa, *otros):
    return subprocess.run(
        [str(PYTHON_GR), str(ROOT / "scripts/sesion08_lora/inspeccionar_lora.py"),
         "--archivo", str(archivo), "--salida", str(salida), "--etapa", etapa, *otros],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )


@pytest.mark.parametrize("etapa,archivo,fragmentos", [
    ("gray", "05_gray.txt", ["S09", "0011110", "0010011", "S43"]),
    ("desentrelazado", "06_desentrelazado.txt", ["7 1 2 3 4", "11110", "P49"]),
    ("fec", "07_fec.txt", ["p RX", "p XOR", "0111", "P49"]),
    ("relleno", "08_relleno.txt", ["P45", "EXCLUIR", "CONSERVAR", "44 utiles"]),
    ("bytes", "09_bytes.txt", ["B1/B2", "P07=1110", "P08=0001", "00011110"]),
    ("blanqueo", "10_blanqueo.txt", ["01111111", "11111111", "10000000", "sin XOR"]),
    ("crc", "11_crc.txt", ["P41", "P44", "ca2b", "687b", "a250", "VALIDO"]),
    ("phypayload", "12_phypayload.txt", ["10000000", "01111011", TRAMA.hex(" ")]),
])
def test_cada_transicion_tiene_comando_y_tabla_completa(muestra_comandos, tmp_path, etapa, archivo, fragmentos):
    salida = tmp_path / "salida"
    r = ejecutar_comando(muestra_comandos, salida, etapa)
    assert r.returncode == 0, r.stdout + r.stderr
    informe = (salida / archivo).read_text()
    assert r.stdout.startswith(informe.rstrip())
    for fragmento in fragmentos:
        assert fragmento in informe
    assert " | " in informe
    encontrados = set(re.findall(r"^\[B(\d+) ", informe, re.M))
    esperados = {"6", "7"} if etapa == "crc" else set("123456") if etapa == "phypayload" else set("1234567")
    assert encontrados == esperados
    assert (salida / "03_phypayload.bin").read_bytes() == TRAMA
    guia = (ROOT / "docs/sessions/06/clase6.md").read_text()
    assert f"python scripts/sesion08_lora/inspeccionar_lora.py --etapa {etapa}" in guia


@pytest.mark.parametrize("etapa,bloque,archivo", [
    ("gray", "1", "05_gray_B1.txt"),
    ("desentrelazado", "1", "06_desentrelazado_B1.txt"),
    ("fec", "1", "07_fec_B1.txt"),
    ("relleno", "7", "08_relleno_B7.txt"),
])
def test_filtro_por_bloque_conserva_su_matriz_completa(muestra_comandos, tmp_path, etapa, bloque, archivo):
    salida = tmp_path / "salida"
    r = ejecutar_comando(muestra_comandos, salida, etapa, "--bloque", bloque)
    assert r.returncode == 0, r.stdout + r.stderr
    informe = (salida / archivo).read_text()
    assert r.stdout.startswith(informe.rstrip())
    assert set(re.findall(r"^\[B(\d+) ", informe, re.M)) == {bloque}
    if etapa == "relleno":
        assert all(f"P{n}" in informe for n in range(43, 50))
        assert "P01" not in informe
    elif etapa in ("desentrelazado", "fec"):
        assert all(f"P{n:02d}" in informe for n in range(1, 8))


@pytest.mark.parametrize("etapa,bloque,mensaje", [
    ("bytes", "1", "Las parejas de bytes y el CRC se presentan completos"),
    ("gray", "8", "--bloque debe estar entre 1 y 7"),
])
def test_filtros_incompatibles_se_explican(muestra_comandos, tmp_path, etapa, bloque, mensaje):
    r = ejecutar_comando(muestra_comandos, tmp_path / "salida", etapa, "--bloque", bloque)
    assert r.returncode == 2
    assert mensaje in r.stderr


def test_nueva_carpeta_conserva_las_rutas_de_muestras_desde_otro_directorio(tmp_path):
    if not PYTHON_GR.is_file():
        pytest.skip("Radioconda no está disponible")
    r = subprocess.run(
        [str(PYTHON_GR), "-c",
         "import json, sys; sys.path.insert(0, sys.argv[1]); "
         "from scripts.sesion08_lora import verificar_lora_915 as lora; "
         "from scripts.sesion08_lora import verificar_lorawan_brno as brno; "
         "print(json.dumps({'lora_root': str(lora.ROOT), 'captura': str(lora.CAPTURA), "
         "'brno_root': str(brno.ROOT), 'carpeta_brno': str(brno.CARPETA)}))", str(ROOT)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    rutas = json.loads(r.stdout)
    assert Path(rutas["lora_root"]) == ROOT
    assert Path(rutas["brno_root"]) == ROOT
    assert Path(rutas["captura"]) == ROOT / "gnuradio/samples/lora-915-osu/IQ_1.sigmf-data"
    assert Path(rutas["carpeta_brno"]) == ROOT / "gnuradio/samples/lorawan-brno"

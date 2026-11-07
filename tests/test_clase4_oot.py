"""El módulo OOT, el código de la clase y el flowgraph se mantienen compatibles."""

import ast
import os
from pathlib import Path
import re
import shutil
import subprocess
import textwrap

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULO = ROOT / "gnuradio/gr-cbs33m"
GRCC = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
PYTHON_GR = Path(GRCC).parent / "python3"


@pytest.fixture(scope="module")
def runtime():
    if not Path(GRCC).is_file() or not PYTHON_GR.is_file():
        pytest.skip("GNU Radio no está disponible")
    return GRCC, str(PYTHON_GR)


def test_codigo_de_la_guia_coincide_con_los_bloques_distribuidos():
    guia = (ROOT / "docs/sessions/04/clase4.md").read_text()
    fragmentos = [textwrap.dedent(f) for f in re.findall(r"^    ```python\n(.*?)^    ```", guia, re.S | re.M)]
    for nombre in ("cu8_a_c64", "rotador_frecuencia"):
        arboles = [ast.parse(f) for f in fragmentos if f"class {nombre}(" in f and "def work(" in f]
        assert len(arboles) == 1
        clase_guia = next(n for n in arboles[0].body if isinstance(n, ast.ClassDef))
        fuente = ast.parse((MODULO / f"python/cbs33m/{nombre}.py").read_text())
        clase_modulo = next(n for n in fuente.body if isinstance(n, ast.ClassDef))
        assert ast.dump(clase_guia) == ast.dump(clase_modulo)


def test_conversion_y_continuidad_con_el_runtime_real(runtime, tmp_path):
    resultado = subprocess.run(
        [runtime[1], "-B", str(MODULO / "python/cbs33m/qa_cbs33m.py")],
        env={**os.environ, "MPLCONFIGDIR": str(tmp_path / "mpl")},
        capture_output=True, text=True, timeout=30,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_grafo_compila_con_puertos_y_callbacks_del_oot(runtime, tmp_path):
    grafo = ROOT / "gnuradio/flowgraphs/fm.grc"
    datos = yaml.safe_load(grafo.read_text())
    propios = {b["name"]: b["id"] for b in datos["blocks"] if b["id"].startswith("cbs33m_")}
    assert propios == {
        "conversor_iq": "cbs33m_cu8_a_c64",
        "centrar_emisora": "cbs33m_rotador_frecuencia",
        "centrar_rds": "cbs33m_rotador_frecuencia",
    }
    assert not any(b["id"] == "epy_block" for b in datos["blocks"])
    assert not any("snippet" in b["id"] for b in datos["blocks"])
    assert ["ganancia_rds", "0", "normalizar_rds", "0"] in datos["connections"]
    assert ["normalizar_rds", "0", "fase_rds", "0"] in datos["connections"]
    env = {
        **os.environ,
        "GRC_BLOCKS_PATH": str(MODULO / "grc"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    resultado = subprocess.run([runtime[0], "-o", str(tmp_path), str(grafo)],
                               env=env, capture_output=True, text=True, timeout=60)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    generado = (tmp_path / "fm.py").read_text()
    assert "from gnuradio import cbs33m" in generado
    assert "self.centrar_emisora.set_frecuencia_mezcla(" in generado
    assert "epy_block" not in generado


def test_instalacion_visible_sin_rutas_del_repositorio(runtime, tmp_path):
    """Una compilación con GRC_BLOCKS_PATH podría ocultar una instalación ausente."""
    env = {
        k: v for k, v in os.environ.items()
        if k not in ("GRC_BLOCKS_PATH", "PYTHONPATH")
    }
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    comprobacion = subprocess.run(
        [runtime[1], str(MODULO / "instalar.py"), "--comprobar"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert comprobacion.returncode == 0, (
        "Instala el módulo con el Python de Radioconda antes de esta prueba:\n"
        + comprobacion.stdout + comprobacion.stderr
    )
    # El perfil principal puede recibir desde RTL-SDR. Activar también la rama
    # de archivo en una copia temporal para comprobar el conversor instalado.
    datos = yaml.safe_load((ROOT / "gnuradio/flowgraphs/fm.grc").read_text())
    datos["options"]["parameters"]["id"] = "fm_archivo_prueba"
    for bloque in datos["blocks"]:
        if bloque["name"] in {"fuente_captura", "conversor_iq", "ritmo_visores"}:
            bloque["states"]["state"] = "enabled"
        if bloque["name"] == "rtlsdr_source_0":
            bloque["states"]["state"] = "disabled"
        if bloque["name"] == "fuente_captura":
            bloque["parameters"]["file"] = "captura.cu8"
    (tmp_path / "captura.cu8").write_bytes(bytes([127, 128]) * 1024)
    grafo_archivo = tmp_path / "fm_archivo_prueba.grc"
    grafo_archivo.write_text(yaml.safe_dump(datos, sort_keys=False))
    generado = subprocess.run(
        [runtime[0], "-o", str(tmp_path), str(grafo_archivo)], cwd=tmp_path,
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert generado.returncode == 0, generado.stdout + generado.stderr
    codigo = (tmp_path / "fm_archivo_prueba.py").read_text()
    assert "from gnuradio import cbs33m" in codigo
    assert "cbs33m.cu8_a_c64(" in codigo
    assert codigo.count("cbs33m.rotador_frecuencia(") == 2

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

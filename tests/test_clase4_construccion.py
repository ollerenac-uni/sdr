"""Reconstrucción real por etapas, solo en una copia desechable de Radioconda.

Activar con CBS33M_TEST_PREFIX=/tmp/<radioconda-clonado>. Se exige que ese
entorno no tenga CBS33M y se conserva intacto el Radioconda habitual.
"""

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_construccion_por_etapas_desde_modulo_vacio(tmp_path):
    configurado = os.environ.get("CBS33M_TEST_PREFIX")
    if not configurado:
        pytest.skip("Requiere una copia desechable de Radioconda en CBS33M_TEST_PREFIX")
    prefijo = Path(configurado).resolve()
    assert prefijo.is_relative_to(Path(tempfile.gettempdir()).resolve())
    python = prefijo / "bin/python"
    modtool = prefijo / "bin/gr_modtool"
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "GRC_BLOCKS_PATH")}
    env.update(PATH=f"{prefijo / 'bin'}:{env.get('PATH', '')}",
               XDG_CACHE_HOME=str(tmp_path / "cache"),
               PYTHONDONTWRITEBYTECODE="1")

    def ejecutar(argumentos, cwd=tmp_path, entrada=None, correcto=True):
        resultado = subprocess.run([str(a) for a in argumentos], cwd=cwd, env=env,
                                   input=entrada, text=True, capture_output=True, timeout=90)
        assert (resultado.returncode == 0) == correcto, resultado.stdout + resultado.stderr
        return resultado

    ejecutar([python, "-c", "import importlib.util; "
              "assert importlib.util.find_spec('gnuradio.cbs33m') is None"])
    paquete = Path(ejecutar([python, "-c", "import gnuradio; "
                            "print(gnuradio.__path__[0])"]).stdout.strip()) / "cbs33m"
    ejecutar([modtool, "newmod", "--scm-mode", "no", "cbs33m"])
    modulo = tmp_path / "gr-cbs33m"
    shutil.copyfile(ROOT / "gnuradio/gr-cbs33m/instalar.py", modulo / "instalar.py")
    guia = (ROOT / "docs/sessions/04/clase4.md").read_text()
    fragmentos = [(lenguaje, textwrap.dedent(codigo)) for lenguaje, codigo in
                  re.findall(r"^    ```(python|yaml)\n(.*?)^    ```", guia, re.S | re.M)]

    def completar(nombre):
        codigo = next(c for l, c in fragmentos if l == "python"
                      and f"class {nombre}(" in c and "def work(" in c)
        yaml = next(c for l, c in fragmentos if l == "yaml"
                    and c.startswith(f"id: cbs33m_{nombre}\n"))
        (modulo / f"python/cbs33m/{nombre}.py").write_text(codigo)
        (modulo / f"grc/cbs33m_{nombre}.block.yml").write_text(yaml)

    def biblioteca(nombres):
        codigo = """
from gnuradio import gr
from gnuradio.grc.core.platform import Platform
plataforma = Platform(version=gr.version(), install_prefix=gr.prefix(), prefs=gr.prefs())
plataforma.build_library()
presentes = {n for n in ('cu8_a_c64', 'rotador_frecuencia')
             if 'cbs33m_' + n in plataforma.blocks}
assert presentes == ESPERADOS, presentes
""".replace("ESPERADOS", repr(set(nombres)))
        ejecutar([python, "-c", codigo])

    def instantanea():
        archivos = list(paquete.glob("*.py"))
        archivos += list((prefijo / "share/gnuradio/grc/blocks").glob("cbs33m_*.block.yml"))
        manifiesto = prefijo / "share/gnuradio/manifests/cbs33m/MANIFEST.yml"
        if manifiesto.is_file():
            archivos.append(manifiesto)
        return {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in archivos}

    ejecutar([modtool, "add", "--scm-mode", "no", "-l", "python", "-t", "decimator",
              "--argument-list", "escala=127.5", "cu8_a_c64"], modulo, "CBS33M\nn\n")
    incompleto = ejecutar([python, "instalar.py"], modulo, correcto=False)
    assert "No se pudo preparar CBS33M" in incompleto.stderr
    ejecutar([python, "-c", "import importlib.util; "
              "assert importlib.util.find_spec('gnuradio.cbs33m') is None"])
    completar("cu8_a_c64")
    ejecutar([python, "instalar.py"], modulo)
    antes = instantanea()
    ejecutar([python, "instalar.py", "--comprobar"], modulo)
    ejecutar([python, "instalar.py"], modulo)
    assert instantanea() == antes  # Comprobación e instalación repetida no reescriben.
    biblioteca(["cu8_a_c64"])
    ejecutar([python, "-c", """
import numpy as np
from gnuradio import gr, blocks, cbs33m
assert not hasattr(cbs33m, 'rotador_frecuencia')
fuente = blocks.vector_source_b([255, 0, 0, 255, 127, 128] * 100)
conversor = cbs33m.cu8_a_c64()
salida = blocks.vector_sink_c()
tb = gr.top_block()
tb.connect(fuente, conversor, salida)
tb.run()
esperado = [1-1j, -1+1j, (-0.5+0.5j)/127.5] * 100
np.testing.assert_allclose(salida.data(), esperado, atol=1e-7)
"""])

    ejecutar([modtool, "add", "--scm-mode", "no", "-l", "python", "-t", "sync",
              "--argument-list", "frecuencia_mezcla=0.0, samp_rate=2.4e6",
              "rotador_frecuencia"], modulo, "CBS33M\nn\n")
    antes = instantanea()
    ejecutar([python, "instalar.py"], modulo, correcto=False)
    assert instantanea() == antes  # Una plantilla pendiente conserva la instalación anterior.
    completar("rotador_frecuencia")
    ejecutar([python, "instalar.py"], modulo)
    ejecutar([python, "instalar.py", "--comprobar"], modulo)
    biblioteca(["cu8_a_c64", "rotador_frecuencia"])
    # La QA usa el paquete instalado, no los archivos de la referencia.
    qa = (ROOT / "gnuradio/gr-cbs33m/python/cbs33m/qa_cbs33m.py").read_text()
    inicio = qa.index("CARPETA = ")
    fin = qa.index("class TestBloquesCBS33M")
    ejecutar([python, "-c", qa[:inicio] + "from gnuradio import cbs33m\n\n" + qa[fin:]])
    ejecutar([prefijo / "bin/grcc", "-o", tmp_path,
              ROOT / "gnuradio/flowgraphs/fm.grc"])
    generado = (tmp_path / "fm.py").read_text()
    assert "cbs33m.cu8_a_c64(" in generado
    assert generado.count("cbs33m.rotador_frecuencia(") == 2
    assert "self.centrar_emisora.set_frecuencia_mezcla(" in generado

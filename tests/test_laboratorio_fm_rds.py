"""El caso de diagnóstico conserva audio y recupera RDS al corregir una tasa."""

import os
from pathlib import Path
import shutil
import subprocess
import textwrap

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
FLOWGRAPHS = ROOT / "gnuradio/flowgraphs"
GRCC = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
PYTHON_GR = Path(GRCC).parent / "python3"
CAPTURA = ROOT / "gnuradio/samples/fm-lima-20261107/fm_lima_fc89p4MHz_2p048Msps_g20p7_30s.cu8"


@pytest.mark.skipif(not Path(GRCC).is_file() or not PYTHON_GR.is_file(), reason="Requiere GNU Radio")
@pytest.mark.skipif(not CAPTURA.is_file(), reason="Descargar la captura A del Drive del laboratorio 4")
def test_falla_controlada_afecta_rds_y_conserva_audio(tmp_path):
    original = FLOWGRAPHS / "fm_lab04_diagnostico.grc"
    datos = yaml.safe_load(original.read_text())
    datos["options"]["parameters"]["id"] = "fm_lab04_control"
    for bloque in datos["blocks"]:
        if bloque["name"] == "centrar_rds":
            bloque["parameters"]["samp_rate"] = "tasa_canal"
    control = tmp_path / "fm_lab04_control.grc"
    control.write_text(yaml.safe_dump(datos, sort_keys=False, allow_unicode=True))
    for grafo in (original, control):
        compilacion = subprocess.run(
            [GRCC, "-o", str(tmp_path), str(grafo)], cwd=FLOWGRAPHS,
            capture_output=True, text=True, timeout=60,
        )
        assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr

    codigo = textwrap.dedent('''
        import importlib.util
        import json
        from pathlib import Path
        import numpy as np
        import pmt
        from PyQt5 import Qt
        from gnuradio import blocks

        app = Qt.QApplication([])
        def ejecutar(nombre):
            spec = importlib.util.spec_from_file_location(nombre, CARPETA / (nombre + ".py"))
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            modulo.audio.sink = lambda *a, **kw: blocks.vector_sink_f()
            tb = getattr(modulo, nombre)()
            grupos = blocks.message_debug()
            tb.msg_connect((tb.decodificador_rds, "out"), (grupos, "store"))
            tb.run()
            pi = set()
            for i in range(grupos.num_messages()):
                datos = bytes(pmt.u8vector_elements(pmt.cdr(grupos.get_message(i))))
                pi.add(datos[:2].hex().upper())
            audio = np.asarray(tb.audio_mono.data(), dtype=np.float32).copy()
            tb.close()
            app.processEvents()
            return grupos.num_messages(), pi, audio

        malos, _, audio_malo = ejecutar("fm_lab04_diagnostico")
        buenos, pi, audio_bueno = ejecutar("fm_lab04_control")
        assert malos == 0, malos
        assert buenos > 0 and pi == {"F030"}, (buenos, pi)
        assert len(audio_bueno) > 1400000
        assert len(audio_bueno) == len(audio_malo)
        np.testing.assert_allclose(audio_malo, audio_bueno, rtol=2e-4, atol=1e-5)
        print("Grupos defectuoso/corregido:", malos, buenos)
        print("Muestras de audio por caso:", len(audio_bueno))
        (CARPETA / "resultado.json").write_text(json.dumps({
            "grupos_defectuoso": malos, "grupos_corregido": buenos,
            "pi_corregido": sorted(pi), "muestras_audio_por_caso": len(audio_bueno),
            "diferencia_maxima_audio": float(np.max(np.abs(audio_malo - audio_bueno))),
        }, indent=2))
    ''').replace("CARPETA", f"Path({str(tmp_path)!r})")
    resultado = subprocess.run(
        [str(PYTHON_GR), "-c", codigo], cwd=FLOWGRAPHS,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "XDG_CONFIG_HOME": str(tmp_path / "config")},
        capture_output=True, text=True, timeout=120,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr

"""Regresión real de unidades y republicación de PS al resintonizar, sin USB."""

import os
from pathlib import Path
import shutil
import subprocess
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[1]
GRCC = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")
PYTHON_GR = Path(GRCC).parent / "python3"


@pytest.mark.skipif(not Path(GRCC).is_file() or not PYTHON_GR.is_file(), reason="Requiere GNU Radio y Qt")
def test_unidades_y_nombre_se_recuperan_tras_volver_a_la_misma_emisora(tmp_path):
    nombre = "fm"
    compilacion = subprocess.run(
        [GRCC, "-o", str(tmp_path), str(ROOT / f"gnuradio/flowgraphs/{nombre}.grc")],
        capture_output=True, text=True, timeout=60,
    )
    assert compilacion.returncode == 0, compilacion.stdout + compilacion.stderr
    codigo = textwrap.dedent('''
        import importlib.util
        import time
        import numpy as np
        import pmt
        from PyQt5 import Qt
        from gnuradio import blocks, gr

        spec = importlib.util.spec_from_file_location("receptor", RUTA)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        class FuenteSinUSB(gr.hier_block2):
            def __init__(self, *a, **kw):
                gr.hier_block2.__init__(self, "RTL simulado", gr.io_signature(0,0,0),
                                       gr.io_signature(1,1,gr.sizeof_gr_complex))
                self.datos = blocks.vector_source_c([0j] * 4096, True)
                self.ritmo = blocks.throttle(gr.sizeof_gr_complex, 2400000)
                self.connect(self.datos, self.ritmo, self)
                self.frecuencia = None
            def set_center_freq(self, valor, canal=0): self.frecuencia = valor
            def set_sample_rate(self, valor): self.ritmo.set_sample_rate(valor)
            def set_time_unknown_pps(self, *a): pass
            def set_freq_corr(self, *a): pass
            def set_dc_offset_mode(self, *a): pass
            def set_iq_balance_mode(self, *a): pass
            def set_gain_mode(self, *a): pass
            def set_gain(self, *a): pass
            def set_if_gain(self, *a): pass
            def set_bb_gain(self, *a): pass
            def set_antenna(self, *a): pass
            def set_bandwidth(self, *a): pass

        modulo.osmosdr.source = FuenteSinUSB
        modulo.audio.sink = lambda *a, **kw: blocks.null_sink(gr.sizeof_float)
        app = Qt.QApplication([])
        tb = getattr(modulo, CLASE)()
        assert not any(n.startswith("snippets_") for n in vars(modulo))
        # Limitación de unidades de la biblioteca instalada, no de la sintonía RF.
        assert tb.panel_rds.freq.text() == "0.0"
        tb.set_frecuencia_emisora(88.9)
        assert tb.panel_rds.freq.text() == "88.9"
        assert tb.rtlsdr_source_0.frecuencia == 88900000
        assert tb.frecuencia_mezcla == 0
        tb.start()
        tb.flowgraph_started.set()

        def esperar(segundos=0.25):
            limite = time.monotonic() + segundos
            while time.monotonic() < limite:
                app.processEvents()
                time.sleep(0.005)

        def enviar_nombre():
            for k in range(4):
                datos = [0xf0, 0x30, 0, k, 0, 0, *b"PRUEBAFM"[2*k:2*k+2], *b"ABCD"]
                tb.parser_rds.to_basic_block()._post(pmt.intern("in"),
                    pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(12, datos)))
            esperar()

        try:
            enviar_nombre()
            assert tb.panel_rds.station.text() == "PRUEBAFM"
            tb.fase_rds.set_frequency(0.1)
            tb.set_frecuencia_emisora(90.5)
            esperar()
            assert tb.panel_rds.station.text() == ""
            assert tb.rtlsdr_source_0.frecuencia == 90500000
            assert abs(tb.fase_rds.get_frequency() - 0.1) < 1e-5
            tb.set_frecuencia_emisora(88.9)
            esperar()
            enviar_nombre()
            assert tb.panel_rds.station.text() == "PRUEBAFM"
            assert tb.panel_rds.freq.text() == "88.9"
            assert not hasattr(tb, "_timer_estado_rds")
            tb.set_desplazamiento_sintonia(250000)
            assert tb.rtlsdr_source_0.frecuencia == 88650000
            assert tb.frecuencia_mezcla == -250000
        finally:
            tb.stop()
            tb.wait()
            tb.close()
    ''').replace("RUTA", repr(str(tmp_path / f"{nombre}.py")))
    codigo = codigo.replace("CLASE", repr(nombre))
    resultado = subprocess.run(
        [str(PYTHON_GR), "-c", codigo], capture_output=True, text=True, timeout=30,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "XDG_CONFIG_HOME": str(tmp_path / "config")},
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr

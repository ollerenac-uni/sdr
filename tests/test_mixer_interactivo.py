"""Contrasta el modelo JavaScript de la página con NumPy y el material publicado."""
import ast
import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np
import markdown
import pytest

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "docs/sessions/02-tiempo-frecuencia-iq"
MODEL = ROOT / "docs/javascripts/sdr-mixer-model.js"
FS = 2400000


@pytest.fixture(scope="module")
def model():
    node = shutil.which("node")
    if not node:
        pytest.skip("Las pruebas del modelo interactivo requieren Node.js")
    script = """
      const M = require(process.argv[1]);
      const configurations = [
        {mixHz: -400000, phaseDeg: 0},
        {mixHz: -400000, phaseDeg: 45},
        {mixHz: -400000, phaseDeg: 90, neighbors: false},
        {mixHz: -400000, mode: 'fm', neighbors: false},
        {toneHz: 800000, mixHz: 800000, phaseDeg: 30},
        {toneHz: 0, phaseDeg: 45}
      ];
      const cases = configurations.map((config) => {
        const params = {...M.DEFAULTS, ...config};
        const block = M.block(params);
        return {params, ...block, spectrum: M.spectrum(block.output), sample: M.sample(params, 1)};
      });
      const z = {i: 0.3, q: -0.7};
      const recovered = M.rotate(M.rotate(z, 1.2), -1.2);
      console.log(JSON.stringify({cases, recovered, wrapped: M.wrapFrequency(5000, 8000)}));
    """
    result = subprocess.run([node, "-e", script, str(MODEL)], text=True, capture_output=True, check=True, timeout=20)
    return json.loads(result.stdout)


def as_complex(values):
    return np.array([z["i"] + 1j * z["q"] for z in values])


def test_modelo_coincide_con_las_exponenciales_del_curso(model):
    n = np.arange(240)
    t = n / FS
    for case in model["cases"]:
        p = case["params"]
        phase_message = 1.2 * np.sin(2 * np.pi * 100000 * t) if p["mode"] == "fm" else 0
        expected = np.exp(1j * (2 * np.pi * p["toneHz"] * t + np.deg2rad(p["phaseDeg"]) + phase_message))
        np.testing.assert_allclose(as_complex(case["desiredInput"]), expected, atol=1e-12)
        np.testing.assert_allclose(as_complex(case["desiredOutput"]), expected * np.exp(1j * 2 * np.pi * p["mixHz"] * t), atol=1e-12)


def test_centrar_no_obliga_a_eliminar_q(model):
    for case, phase in zip(model["cases"][:3], [0, 45, 90]):
        np.testing.assert_allclose(as_complex(case["desiredOutput"]), np.exp(1j * np.deg2rad(phase)), atol=1e-12)
    assert model["cases"][1]["sample"]["output"]["q"] == pytest.approx(np.sqrt(0.5))
    assert model["cases"][2]["sample"]["output"]["q"] == pytest.approx(1)


def test_mezcla_conserva_magnitud_de_toda_la_entrada(model):
    for case in model["cases"]:
        np.testing.assert_allclose(np.abs(as_complex(case["input"])), np.abs(as_complex(case["output"])), atol=1e-12)


def test_modulacion_no_se_convierte_en_constante_al_centrar(model):
    case = model["cases"][3]
    y = as_complex(case["desiredOutput"])
    assert np.ptp(y.imag) > 1
    assert not np.allclose(y, y[0])
    np.testing.assert_allclose(np.abs(y), 1, atol=1e-12)


def test_dft_de_javascript_coincide_con_fft_de_numpy(model):
    frequencies = np.fft.fftshift(np.fft.fftfreq(240, d=1 / FS))
    for case in model["cases"]:
        coefficients = case["spectrum"]
        np.testing.assert_allclose([c["frequency"] for c in coefficients], frequencies)
        expected = np.fft.fftshift(np.fft.fft(as_complex(case["output"]))) / 240
        np.testing.assert_allclose(as_complex(coefficients), expected, atol=1e-11)


def test_se_desplazan_los_tres_tonos_sin_filtrar(model):
    coefficients = model["cases"][0]["spectrum"]
    present = [(c["frequency"], c["magnitude"]) for c in coefficients if c["magnitude"] > 1e-7]
    np.testing.assert_allclose(present, [[-1000000, 0.6], [-400000, 0.4], [0, 1]], atol=1e-11)


def test_periodicidad_y_mezcla_inversa(model):
    assert model["wrapped"] == -3000
    assert model["recovered"] == pytest.approx({"i": 0.3, "q": -0.7})
    coefficients = model["cases"][4]["spectrum"]
    assert any(c["frequency"] == -800000 and c["magnitude"] == pytest.approx(1) for c in coefficients)


def test_componentes_coincidentes_se_suman_complejamente(model):
    case = model["cases"][5]
    dc = next(c for c in case["spectrum"] if c["frequency"] == 0)
    assert dc["magnitude"] == pytest.approx(abs(np.exp(1j * np.pi / 4) + 0.4))


def test_pagina_integrada_y_figuras_con_respaldo():
    page = (SESSION / "mezcla-interactiva.md").read_text()
    config = (ROOT / "mkdocs.yml").read_text()
    assert "mezcla-interactiva.md" in config
    for asset in ("javascripts/sdr-mixer-model.js", "javascripts/sdr-mixer.js", "stylesheets/sdr-mixer.css"):
        assert asset in config
        assert (ROOT / "docs" / asset).is_file()
    assert re.findall(r"^\*\*Figura (\d+)\.\*\*", page, flags=re.MULTILINE) == ["1", "2", "3"]
    for kind in ("iq", "time", "spectrum"):
        assert f'data-plot="{kind}"' in page
        assert f'data-reading="{kind}"' in page
    assert page.count('data-preset="') == 4
    assert page.count('data-preset-select') == 3
    assert page.count('??? example "Solución explicada"') == 3
    assert 'data-controls hidden markdown="0"' in page


def test_markdown_conserva_controles_y_figuras_dentro_del_componente():
    class ComponentParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.controls = set()
            self.values = set()
            self.plots = set()
            self.readings = set()

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            inside = "data-sdr-mixer" in attrs or any(root for _, root in self.stack)
            if inside:
                for attribute, found in (("data-control", self.controls), ("data-value", self.values), ("data-plot", self.plots), ("data-reading", self.readings)):
                    if attribute in attrs:
                        found.add(attrs[attribute])
            if tag not in {"input", "img", "br", "hr", "meta", "link"}:
                self.stack.append((tag, "data-sdr-mixer" in attrs))

        def handle_endtag(self, tag):
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    del self.stack[index:]
                    break

    page = (SESSION / "mezcla-interactiva.md").read_text()
    html = markdown.markdown(page, extensions=["md_in_html", "admonition", "pymdownx.details"])
    parser = ComponentParser()
    parser.feed(html)
    assert parser.controls == {"toneHz", "mixHz", "phaseDeg", "mode", "neighbors", "sample"}
    assert parser.values == {"tone", "mix", "phase", "sample", "input", "output", "frequency", "phase-sum"}
    assert parser.plots == parser.readings == {"iq", "time", "spectrum"}


def test_script_reproduce_las_tres_figuras_y_no_parte_lineas_de_ploteo(tmp_path):
    path = SESSION / "figures/gen_mezcla_interactiva.py"
    spec = importlib.util.spec_from_file_location("gen_mezcla_interactiva", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    outputs = module.generar(tmp_path)
    assert len(outputs) == 3
    for output in outputs:
        assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    methods = {"plot", "stem", "set", "subplots", "annotate", "text", "legend", "axhline", "axvline", "grid", "savefig"}
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in methods:
            assert node.lineno == node.end_lineno

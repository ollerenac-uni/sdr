# Laboratorio de muestreo — Plan de implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Publicar `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`, una guía hermana de la Sesión 01 que enseña la relación entre `fs`, tiempo, número de muestras y tamaño de FFT, y cómo la decimación y la interpolación cambian el espectro.

**Architecture:** Una página Markdown nueva en la carpeta de S01, con su propia numeración de figuras. Un generador versionado fabrica el tono sintético `.cu8`; tres grafos `.grc` derivados de `test2.grc` sostienen el calentamiento, la decimación y la interpolación; un script de figuras produce los PNG. Cada hecho numérico que cita la página lo comprueba un test.

**Tech Stack:** MkDocs 1.6 + mkdocs-material 9.7.x, GNU Radio 3.10.12 de radioconda (`grcc`, `firdes`), NumPy 1.26 y PyYAML de `/usr/bin/python3` para tests y figuras, `od` de coreutils.

**Diseño aprobado:** `docs/plans/2026-09-12-lab-muestreo-design.md`. Léelo primero.

**Convenciones:**
- Idioma español; términos técnicos en inglés con glosa la primera vez. Reglas de `AGENTS.md`, sobre todo la numeración de figuras.
- Tests con `/usr/bin/python3 -m pytest -q tests/`; radioconda no trae pytest. `mkdocs build --strict` siempre desde la raíz.
- Un commit por tarea en `main`, mensaje en español, terminado con las líneas:
  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01FWTMM6jn922Bhyb4wQGuoU
  ```
- **No hacer `git push` sin confirmación explícita del profesor.** El primer punto de control es la Tarea 8.
- Desviación consciente del skill, igual que en el plan de 2026-09-05: la guía es prosa. El plan fija los hechos exactos (comandos, salidas, números, rutas); quien ejecute escribe la prosa sin inventar hechos. Si un hecho no está aquí ni en el diseño, se verifica antes de escribirlo.
- `index.md` de S01 **no se toca**: está en revisión.
- `test.grc` falla a propósito. No lo arregles.

**Dependencias:** las Tareas 15 y 16 esperan las grabaciones de la Tarea 14, que hace el profesor. Todo lo demás parte del tono sintético o de `samples/fm_99p1MHz_2p4Msps_g30.cu8`, que ya existe.

---

## Hechos verificados que usa este plan

| Hecho | Valor | Cómo se verificó |
|---|---|---|
| Tasas que acepta `librtlsdr` | 225 001–300 000 y 900 001–3 200 000 Hz | desensamblado de `~/radioconda/lib/librtlsdr.so.2` |
| `rtl_sdr -n` | cuenta muestras, escribe 2 bytes por muestra | `-n 24000000` produjo los 48 000 000 bytes de la grabación oficial |
| Cadena de `test2.grc` | `file_source → throttle2 → uchar_to_float → add_const → multiply_const → deinterleave → float_to_complex → sinks` | `tests/test_test_flowgraph.py` |
| Ventana por defecto del Freq Sink en `test2.grc` | `window.WIN_BLACKMAN_hARRIS` | volcado del `.grc` |
| Ventana rectangular disponible | `window.WIN_RECTANGULAR` | `qtgui_freq_sink_x.block.yml` |
| Trigger del Time Sink | `tr_mode`, `tr_slope` (`qtgui.TRIG_SLOPE_POS`), `tr_level`, `tr_chan`, `tr_delay` | `qtgui_time_sink_x.block.yml`. Ojo: el `default` de `tr_slope` en el yml dice `TRIG_MODE_POS`, un error tipográfico de GNU Radio |
| Ids y parámetros de filtros | `fir_filter_xxx`: `type`, `decim`, `taps`; `interp_fir_filter_xxx`: `type`, `interp`, `taps`; `blocks_keep_one_in_n`: `type`, `n`. **Ojo:** los archivos se llaman `filter_fir_filter_xxx.block.yml` y `filter_interp_fir_filter_xxx.block.yml`, pero el `id:` no lleva el prefijo `filter_`. Con el nombre del archivo como id, GRC crea un bloque ficticio y `grcc` falla con `Port is not connected` | yml de bloques de radioconda y `grcc` |
| `firdes.low_pass` | `low_pass(gain, sampling_freq, cutoff_freq, transition_width, window=WIN_HAMMING, param=6.76)`; con `(1, 2.4e6, 120e3, 30e3)` da **193** coeficientes | ejecutado con `~/radioconda/bin/python` |
| `grcc` | compila `test2.grc` sin GUI, `exit=0` | ejecutado |
| Comentarios de `test2.grc` | `description` menciona Soapy, el comentario del File Source dice «convertida de CU8 a complex64» (falso) y el del Throttle dice «a samp_rate» con valor `2*samp_rate`. Todo grafo derivado debe reescribirlos | leído en la Tarea 4 |
| Tono: bytes de n = 0, 8, 16, 24 | (228,128), (128,228), (28,128), (127,28) | archivo generado y leído con `od` |
| Tono: rango | 28–228 | medido |
| Tono: FFT de 32 | máximo en el bin 1; bin 1 / mayor del resto = 623.6 | medido |
| Tono: ciclos sucesivos | **no** son idénticos byte a byte: donde el valor cae en .5 el redondeo varía. n=32 da (228, **127**) frente a (228, 128) en n=0 | medido con los tests en un directorio temporal |
| 228 normalizado | (228 − 127.5)/127.5 = 0.7882 | calculado |
| `od -Ad -tu1 -w2 -N64 -v` | 33 líneas: 32 muestras y la dirección final `0000064` | ejecutado |
| `od -An -tu1 -w2 -N4800 -v <grabación oficial> \| wc -l` | `2400` | ejecutado |
| Tamaño de la grabación oficial | `48000000` (`stat -c %s`) | ejecutado |
| S02 §5 explica ventanas | `docs/sessions/02-tiempo-frecuencia-iq/index.md:177-189` | leído |

Salida exacta de `od -Ad -tu1 -w2 -N64 -v samples/tono_1kHz_32kSps.cu8`:

```
0000000 228 128
0000002 226 147
0000004 220 166
0000006 211 183
0000008 198 198
0000010 183 211
0000012 166 220
0000014 147 226
0000016 128 228
0000018 108 226
0000020  89 220
0000022  72 211
0000024  57 198
0000026  44 183
0000028  35 166
0000030  29 147
0000032  28 128
0000034  29 108
0000036  35  89
0000038  44  72
0000040  57  57
0000042  72  44
0000044  89  35
0000046 108  29
0000048 127  28
0000050 147  29
0000052 166  35
0000054 183  44
0000056 198  57
0000058 211  72
0000060 220  89
0000062 226 108
0000064
```

La dirección avanza de dos en dos porque cada línea son dos bytes: **n = dirección / 2**.

---

### Task 1: Commitear la corrección del diseño

El documento de diseño ya está corregido en disco: orden real de la cadena, redondeo en n=24, 0.788, y dependencias de §4 y §6.

**Files:**
- Modify: `docs/plans/2026-09-12-lab-muestreo-design.md` (ya editado)
- Create: `docs/plans/2026-09-12-lab-muestreo.md` (este plan)

**Step 1: Verificar**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`
Expected: `40 passed, 114 subtests passed`; build sin errores (`plans/` está en `exclude_docs`).

**Step 2: Commit**

```bash
git add docs/plans/2026-09-12-lab-muestreo-design.md docs/plans/2026-09-12-lab-muestreo.md
git commit -m "Plan del laboratorio de muestreo y corrección del orden de la cadena en el diseño"
```

---

### Task 2: Página esqueleto, entrada de nav y red de numeración

**Files:**
- Create: `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`
- Modify: `mkdocs.yml:76`
- Modify: `tests/test_numeracion_figuras.py:16` y todas las apariciones de `sesion.parent.name`

**Step 1: Escribir el test que falla**

Añadir a la clase `TestNumeracionDeFiguras` de `tests/test_numeracion_figuras.py`:

```python
    def test_cubre_todas_las_paginas_de_cada_sesion(self):
        """Una guía hermana de index.md también numera figuras y necesita la misma red."""
        paginas = set(ROOT.glob("docs/sessions/*/*.md"))
        self.assertTrue(
            paginas <= set(SESIONES),
            f"Páginas sin revisar: {sorted(str(p.relative_to(ROOT)) for p in paginas - set(SESIONES))}",
        )
```

**Step 2: Crear la página esqueleto**

`docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`:

```markdown
---
title: "Laboratorio: muestreo, FFT, decimación e interpolación"
session: 1
description: "Relación entre frecuencia de muestreo, tiempo, número de muestras y tamaño de FFT, y cómo la decimación y la interpolación cambian el espectro."
status: draft
---

# Laboratorio: muestreo, FFT, decimación e interpolación

## 1. Calentamiento: el milisegundo que se puede contar

## 2. Las mismas reglas donde no se pueden contar

## 3. La escalera con hardware real

!!! warning "Pendiente"
    Esta parte necesita dos grabaciones nuevas, a 1.2 MS/s y a 300 kS/s, que todavía no están publicadas.

## 4. Decimación en software

## 5. El careo: grabado contra decimado

!!! warning "Pendiente"
    Esta parte necesita la grabación a 300 kS/s, que todavía no está publicada.

## 6. Interpolación
```

**Step 3: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_numeracion_figuras.py`
Expected: FAIL en `test_cubre_todas_las_paginas_de_cada_sesion`, citando `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`.

**Step 4: Ampliar el glob y desambiguar las etiquetas**

En `tests/test_numeracion_figuras.py`, sustituir la línea 16 por:

```python
SESIONES = sorted(ROOT.glob("docs/sessions/*/*.md"))
```

Con dos archivos por carpeta, `sesion.parent.name` ya no identifica la página. Añadir tras `pies_de`:

```python
def nombre(sesion):
    return str(sesion.relative_to(ROOT / "docs/sessions"))
```

y sustituir todas las apariciones:

```bash
sed -i 's/sesion\.parent\.name/nombre(sesion)/g' tests/test_numeracion_figuras.py
```

**Step 5: Anidar la entrada de nav**

En `mkdocs.yml`, sustituir la línea 76:

```yaml
      - "01 — Introducción a SDR": sessions/01-introduccion-sdr/index.md
```

por:

```yaml
      - "01 — Introducción a SDR":
          - sessions/01-introduccion-sdr/index.md
          - "Laboratorio de muestreo": sessions/01-introduccion-sdr/laboratorio-muestreo.md
```

El tema tiene `navigation.indexes`, así que `index.md` pasa a ser la portada de la sección.

**Step 6: Verificar**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`
Expected: todo en verde, con un test más que antes; build sin avisos.

**Step 7: Commit**

```bash
git add docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md mkdocs.yml tests/test_numeracion_figuras.py
git commit -m "Laboratorio de muestreo: esqueleto, nav bajo S01 y numeración de figuras en todas las páginas"
```

---

### Task 3: Generador del tono sintético

**Files:**
- Create: `samples/gen_tono.py`
- Test: `tests/test_gen_tono.py`

`.gitignore` ignora `*.cu8`, no la carpeta: el `.py` se versiona y el `.cu8` no.

**Step 1: Escribir el test que falla**

`tests/test_gen_tono.py`:

```python
"""El tono sintético del laboratorio de muestreo: los números que la guía cita."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "samples/gen_tono.py"


def cargar():
    spec = importlib.util.spec_from_file_location("gen_tono", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestTono(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.iq = cargar().tono()
        cls.i, cls.q = cls.iq[0::2], cls.iq[1::2]

    def test_son_6400_bytes_sin_signo(self):
        self.assertEqual(self.iq.dtype, np.uint8)
        self.assertEqual(self.iq.size, 6400)

    def test_un_cuarto_de_ciclo_son_8_muestras(self):
        """La guía pide encontrar los 90° en od: estos cuatro pares son los que leerá."""
        self.assertEqual((self.i[0], self.q[0]), (228, 128))
        self.assertEqual((self.i[8], self.q[8]), (128, 228))
        self.assertEqual((self.i[16], self.q[16]), (28, 128))
        self.assertEqual((self.i[24], self.q[24]), (127, 28))

    def test_la_muestra_32_empieza_otro_ciclo(self):
        """I vuelve a 228; Q sale 127 y no 128 porque 127.5 se redondea según el residuo."""
        self.assertEqual((self.i[32], self.q[32]), (228, 127))

    def test_usa_la_escala_sin_recortar(self):
        self.assertEqual((int(self.iq.min()), int(self.iq.max())), (28, 228))

    def test_fft_de_32_pone_el_tono_en_el_bin_1(self):
        d = self.iq.astype(float) - 127.5
        espectro = np.abs(np.fft.fft((d[0::2] + 1j * d[1::2])[:32]))
        self.assertEqual(int(espectro.argmax()), 1)
        self.assertGreater(espectro[1], 500 * np.delete(espectro, 1).max())


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_gen_tono.py`
Expected: FAIL con `FileNotFoundError` sobre `samples/gen_tono.py`.

**Step 3: Implementación mínima**

`samples/gen_tono.py`:

```python
#!/usr/bin/env python3
"""Tono complejo de 1 kHz muestreado a 32 kS/s, en formato .cu8 como el del RTL-SDR.

Desde la raíz del repositorio:

    python samples/gen_tono.py

Escribe samples/tono_1kHz_32kSps.cu8: 3200 muestras, 6400 bytes, 0.1 s.
"""

from pathlib import Path

import numpy as np

FS = 32_000  # muestras por segundo
F0 = 1_000  # Hz
AMPLITUD = 100  # niveles del ADC alrededor del cero, que en .cu8 está en 127.5
DURACION = 0.1  # s
SALIDA = Path(__file__).parent / "tono_1kHz_32kSps.cu8"


def tono():
    """Bytes I, Q, I, Q... del tono complejo."""
    n = np.arange(round(FS * DURACION))
    z = AMPLITUD * np.exp(2j * np.pi * F0 * n / FS)
    iq = np.empty(2 * n.size, dtype=np.uint8)
    iq[0::2] = np.round(127.5 + z.real)
    iq[1::2] = np.round(127.5 + z.imag)
    return iq


if __name__ == "__main__":
    tono().tofile(SALIDA)
    print(f"{SALIDA.name}: {SALIDA.stat().st_size} bytes")
```

**Step 4: Ejecutar test y generador**

Run: `/usr/bin/python3 -m pytest -q tests/test_gen_tono.py && ~/radioconda/bin/python samples/gen_tono.py && od -Ad -tu1 -w2 -N64 -v samples/tono_1kHz_32kSps.cu8`
Expected: 5 passed; `tono_1kHz_32kSps.cu8: 6400 bytes`; la salida de `od` idéntica a la de «Hechos verificados».

**Step 5: Commit**

```bash
git add samples/gen_tono.py tests/test_gen_tono.py
git status --short samples/   # el .cu8 NO debe aparecer
git commit -m "Generador del tono de 1 kHz a 32 kS/s para el calentamiento del laboratorio de muestreo"
```

---

### Task 4: Grafo del calentamiento

**Files:**
- Create: `gnuradio-flowgraphs/warmup_32k.grc`
- Test: `tests/test_flowgraph_calentamiento.py`
- Modify: `tests/test_test_flowgraph.py`, método `test_los_identificadores_no_colisionan`
- Test: `tests/test_grafos_compilan.py`

**Step 1: Escribir el test que falla**

`tests/test_flowgraph_calentamiento.py`:

```python
"""Contrato del grafo del calentamiento: la cadena de test2.grc a 32 kS/s sobre el tono."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def cargar(nombre):
    grafo = yaml.safe_load((ROOT / "gnuradio-flowgraphs" / nombre).read_text(encoding="utf-8"))
    return grafo, {b["name"]: b for b in grafo["blocks"]}, {tuple(c) for c in grafo["connections"]}


class TestCalentamiento(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafo, cls.b, cls.c = cargar("warmup_32k.grc")

    def p(self, nombre):
        return self.b[nombre]["parameters"]

    def test_identidad_y_tasa(self):
        self.assertEqual(self.grafo["options"]["parameters"]["id"], "warmup_32k")
        self.assertEqual(self.p("samp_rate")["value"], "32000")

    def test_lee_el_tono_como_bytes(self):
        fuente = self.p("blocks_file_source_0")
        self.assertEqual(fuente["file"], "../samples/tono_1kHz_32kSps.cu8")
        self.assertEqual(fuente["type"], "byte")
        self.assertEqual(self.p("blocks_throttle2_0")["samples_per_second"], "2*samp_rate")

    def test_misma_cadena_que_test2(self):
        cadena = ["blocks_file_source_0", "blocks_throttle2_0", "blocks_uchar_to_float_0",
                  "blocks_add_const_vxx_0", "blocks_multiply_const_vxx_0", "blocks_deinterleave_0"]
        for origen, destino in zip(cadena, cadena[1:]):
            self.assertIn((origen, "0", destino, "0"), self.c)
        for sumidero in ("qtgui_freq_sink_x_0", "qtgui_time_sink_x_0"):
            self.assertIn(("blocks_float_to_complex_0", "0", sumidero, "0"), self.c)

    def test_el_time_sink_muestra_un_milisegundo_quieto(self):
        t = self.p("qtgui_time_sink_x_0")
        self.assertEqual((t["size"], t["srate"]), ("32", "samp_rate"))
        self.assertEqual(t["tr_mode"], "qtgui.TRIG_MODE_NORM")
        self.assertEqual(t["tr_slope"], "qtgui.TRIG_SLOPE_POS")
        self.assertEqual(t["tr_level"], "0.78")

    def test_el_freq_sink_da_bins_de_1_khz_sin_ensanchar_la_raya(self):
        f = self.p("qtgui_freq_sink_x_0")
        self.assertEqual((f["fftsize"], f["bw"], f["fc"]), ("32", "samp_rate", "0"))
        self.assertEqual(f["wintype"], "window.WIN_RECTANGULAR")

    def test_sin_hardware(self):
        """El dongle no puede muestrear a 32 kS/s: no hay fuente de hardware."""
        self.assertFalse([n for n in self.b if n.startswith("soapy_")])


if __name__ == "__main__":
    unittest.main()
```

En `tests/test_test_flowgraph.py`, sustituir el cuerpo de `test_los_identificadores_no_colisionan` por:

```python
        grafos = sorted((ROOT / "gnuradio-flowgraphs").glob("*.grc"))
        ids = [yaml.safe_load(g.read_text(encoding="utf-8"))["options"]["parameters"]["id"] for g in grafos]
        self.assertEqual(len(ids), len(set(ids)), f"ids duplicados: {ids}")
```

`tests/test_grafos_compilan.py`, que protege a todos los grafos, presentes y futuros:

```python
"""Todo .grc del repositorio debe cargar en GNU Radio Companion.

Los tests de contrato leen el YAML y pueden pasar con un grafo que GRC no carga: un id de
bloque mal escrito (filter_fir_filter_xxx en vez de fir_filter_xxx) crea un bloque ficticio
y deja puertos sin conectar. Solo compilar lo detecta.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
GRCC = shutil.which("grcc") or str(Path.home() / "radioconda/bin/grcc")


@unittest.skipUnless(Path(GRCC).exists(), "grcc no disponible: instala radioconda")
class TestGrafosCompilan(unittest.TestCase):
    def test_cada_grc_compila(self):
        for grafo in sorted((ROOT / "gnuradio-flowgraphs").glob("*.grc")):
            with self.subTest(grafo=grafo.name), tempfile.TemporaryDirectory() as tmp:
                r = subprocess.run([GRCC, "-o", tmp, str(grafo)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-800:])


if __name__ == "__main__":
    unittest.main()
```

Hoy pasa con los tres grafos existentes (`RTL_SDR_rcv.grc`, `test.grc`, `test2.grc`): verificado.

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_flowgraph_calentamiento.py`
Expected: FAIL con `FileNotFoundError` sobre `warmup_32k.grc`.

**Step 3: Derivar el grafo de `test2.grc`**

Script de un solo uso, no se versiona:

```bash
/usr/bin/python3 - <<'PYEOF'
import copy, yaml
from pathlib import Path
d = Path("gnuradio-flowgraphs")
g = yaml.safe_load((d / "test2.grc").read_text(encoding="utf-8"))
fuera = {"soapy_rtlsdr_source_0", "freq", "rfGain", "M"}
g["blocks"] = [b for b in g["blocks"] if b["name"] not in fuera]
g["connections"] = [c for c in g["connections"] if c[0] not in fuera and c[2] not in fuera]
g["options"]["parameters"]["id"] = "warmup_32k"
g["options"]["parameters"]["title"] = "Laboratorio de muestreo - Calentamiento a 32 kS/s"
b = {x["name"]: x["parameters"] for x in g["blocks"]}
b["samp_rate"]["value"] = "32000"
b["blocks_file_source_0"]["file"] = "../samples/tono_1kHz_32kSps.cu8"
b["qtgui_time_sink_x_0"].update(size="32", tr_mode="qtgui.TRIG_MODE_NORM",
    tr_slope="qtgui.TRIG_SLOPE_POS", tr_level="0.78", tr_chan="0", tr_delay="0")
b["qtgui_freq_sink_x_0"].update(fftsize="32", fc="0", wintype="window.WIN_RECTANGULAR")
(d / "warmup_32k.grc").write_text(
    yaml.safe_dump(g, sort_keys=False, allow_unicode=True), encoding="utf-8")
PYEOF
```

Por qué 0.78: normalizadas, la muestra n=−1 vale 0.7725 y la n=0 vale 0.7882. Un disparo por flanco de subida en 0.78 cae exactamente en n=0, así la pantalla empieza en el máximo de I y se compara línea a línea con `od`.

**Step 4: Compilar con `grcc` y ejecutar los tests**

Run:
```bash
D=$(mktemp -d) && ~/radioconda/bin/grcc -o "$D" gnuradio-flowgraphs/warmup_32k.grc; echo "exit=$?"; rm -rf "$D"
/usr/bin/python3 -m pytest -q tests/
```
Expected: `exit=0`; todo en verde.

**Step 5: Comprobación visual (con el profesor)**

Abrir `gnuradio-flowgraphs/warmup_32k.grc` en GRC y ejecutar con F6, tras generar el tono en la Tarea 3.

Expected:
- Time Sink: un ciclo completo de ancho 1 ms, **quieto**; la curva real empieza arriba, en 0.788.
- Freq Sink: la raya del tono en +1 kHz a unos −2 dB, eje de −16 a +16 kHz, y un peine de torres entre −58 y −68 dB separado por huecos que caen a −140 (error de cuantización; ver §1.5 en la Tarea 6).

Verificado ya sin interfaz por la revisión de calidad de la Tarea 4, con capturas `offscreen` y leyendo `time_sink_c_impl.cc` de GNU Radio 3.10.12: con `tr_delay = 0` la primera muestra dibujada es la del disparo, n=0; `tr_chan 0` es la parte real; la imagen queda quieta. Falta solo la mirada del profesor.

Si el trazo no empieza en el máximo, el parámetro a ajustar es `tr_delay`. Anota el valor que funcione y actualiza el test.

**Step 6: Commit**

```bash
git add gnuradio-flowgraphs/warmup_32k.grc tests/test_flowgraph_calentamiento.py tests/test_test_flowgraph.py
git commit -m "Grafo del calentamiento a 32 kS/s y comprobación de ids en todos los .grc"
```

---

### Task 5: Figura 1 — un milisegundo en bytes

**Files:**
- Create: `docs/sessions/01-introduccion-sdr/figures/gen_muestreo.py`
- Create: `docs/sessions/01-introduccion-sdr/figures/muestreo-un-milisegundo.png` (generado)
- Test: `tests/test_gen_muestreo_figures.py`

**Step 1: Escribir el test que falla**

`tests/test_gen_muestreo_figures.py`:

```python
"""Figura del calentamiento: los bytes de od dibujados contra el índice y el tiempo."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "docs/sessions/01-introduccion-sdr/figures/gen_muestreo.py"


def cargar():
    spec = importlib.util.spec_from_file_location("gen_muestreo", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestFiguraMuestreo(unittest.TestCase):
    def test_dibuja_33_muestras_para_que_se_vea_el_regreso(self):
        n, i, q = cargar().un_milisegundo()
        self.assertEqual(len(n), 33)
        self.assertEqual((i[0], q[0], i[8], q[8]), (228, 128, 128, 228))
        self.assertEqual((i[32], q[32]), (228, 127))

    def test_genera_el_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = cargar().generar(Path(tmp))
            self.assertEqual(ruta.name, "muestreo-un-milisegundo.png")
            self.assertGreater(ruta.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_gen_muestreo_figures.py`
Expected: FAIL, falta `gen_muestreo.py`.

**Step 3: Implementación**

`docs/sessions/01-introduccion-sdr/figures/gen_muestreo.py`:

```python
#!/usr/bin/env python3
"""Figura del laboratorio de muestreo: 33 muestras del tono, bytes contra índice y tiempo.

    python gen_muestreo.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = Path(__file__).parent
GEN_TONO = Path(__file__).parents[4] / "samples/gen_tono.py"
BLUE, ORANGE = "#1e40af", "#c2410c"


def un_milisegundo():
    spec = importlib.util.spec_from_file_location("gen_tono", GEN_TONO)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    iq = gen.tono()
    return np.arange(33), iq[0:66:2], iq[1:66:2]


def generar(salida: Path = OUT) -> Path:
    n, i, q = un_milisegundo()
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=300)
    ax.stem(n - 0.12, i, linefmt=BLUE, markerfmt="o", basefmt=" ", label="I (bytes pares)")
    ax.stem(n + 0.12, q, linefmt=ORANGE, markerfmt="s", basefmt=" ", label="Q (bytes impares)")
    ax.axhline(127.5, color="0.4", ls="--", lw=1)
    ax.text(32.6, 131, "cero = 127.5", ha="right", color="0.3", fontsize=9)
    for k in (0, 8, 16, 24):
        ax.annotate(f"n={k}\n({i[k]}, {q[k]})", (k, max(i[k], q[k])), xytext=(0, 12),
                    textcoords="offset points", ha="center", fontsize=8)
    ax.set_xlim(-1, 33)
    ax.set_ylim(0, 270)
    ax.set_xlabel("índice de muestra n  (una línea de od)")
    ax.set_ylabel("valor del byte")
    ax.set_xticks(range(0, 33, 4))
    arriba = ax.secondary_xaxis("top", functions=(lambda x: x / 32, lambda t: t * 32))
    arriba.set_xlabel("tiempo (ms)  =  n / 32")
    ax.legend(loc="lower left", fontsize=9)
    ruta = salida / "muestreo-un-milisegundo.png"
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


if __name__ == "__main__":
    print(generar())
```

**Step 4: Ejecutar test, generar y mirar**

Run: `/usr/bin/python3 -m pytest -q tests/test_gen_muestreo_figures.py && /usr/bin/python3 docs/sessions/01-introduccion-sdr/figures/gen_muestreo.py`
Expected: 2 passed; imprime la ruta del PNG. **Abre el PNG y revísalo**: dos peines en cuadratura, anotaciones legibles que no se pisan, eje superior de 0 a 1 ms. Si alguna anotación colisiona, muévela a una esquina fija con `transAxes`, según el antipatrón de `.continue-here.md`.

**Step 5: Commit**

```bash
git add docs/sessions/01-introduccion-sdr/figures/gen_muestreo.py docs/sessions/01-introduccion-sdr/figures/muestreo-un-milisegundo.png tests/test_gen_muestreo_figures.py
git commit -m "Figura del milisegundo de 32 muestras para el laboratorio de muestreo"
```

---

### Task 6: Sección 1 — Calentamiento

**Files:**
- Modify: `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`
- Test: `tests/test_laboratorio_muestreo.py`

**Step 1: Escribir el test que falla**

`tests/test_laboratorio_muestreo.py`:

```python
"""Lo que la guía del laboratorio de muestreo afirma, comprobado contra la realidad."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PAGINA = ROOT / "docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md"
GITHUB = "https://github.com/ollerenac-uni/sdr/blob/main/"


def texto():
    return PAGINA.read_text(encoding="utf-8")


class TestCalentamiento(unittest.TestCase):
    def test_la_salida_de_od_publicada_es_la_real(self):
        """Regla de AGENTS.md: todo comando se ejecuta antes de publicarse."""
        spec = importlib.util.spec_from_file_location("gen_tono", ROOT / "samples/gen_tono.py")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "tono.cu8"
            gen.tono().tofile(ruta)
            salida = subprocess.run(["od", "-Ad", "-tu1", "-w2", "-N64", "-v", str(ruta)],
                                    capture_output=True, text=True, check=True).stdout
        pagina = texto()
        for linea in salida.splitlines():
            self.assertIn(linea, pagina, f"La guía no muestra la línea real de od: {linea!r}")

    def test_enlaza_el_generador_y_el_grafo(self):
        pagina = texto()
        self.assertIn(GITHUB + "samples/gen_tono.py", pagina)
        self.assertIn(GITHUB + "gnuradio-flowgraphs/warmup_32k.grc", pagina)

    def test_cita_los_numeros_que_sostienen_el_ejercicio(self):
        pagina = texto()
        for dato in ("od -Ad -tu1 -w2 -N64 -v samples/tono_1kHz_32kSps.cu8",
                     "0.788", "31.25 Hz", "32 ms", "0000064", "WIN_RECTANGULAR"):
            self.assertIn(dato, pagina)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_laboratorio_muestreo.py`
Expected: FAIL en los tres tests.

**Step 3: Escribir la sección**

Antes de `## 1.`, añadir una introducción breve que diga para quién es (quien ya conecta bloques pero no domina la relación entre `fs`, tiempo, muestras y FFT), que continúa la Parte A de la Sesión 01 añadiendo el eje que allí falta, y una tabla de materiales:

| Archivo | Qué es |
|---|---|
| [`gen_tono.py`](https://github.com/ollerenac-uni/sdr/blob/main/samples/gen_tono.py) | Genera `tono_1kHz_32kSps.cu8`. Secciones 1 |
| [`warmup_32k.grc`](https://github.com/ollerenac-uni/sdr/blob/main/gnuradio-flowgraphs/warmup_32k.grc) | Grafo de la sección 1 |
| `fm_99p1MHz_2p4Msps_g30.cu8` | La grabación de la Sesión 01. Secciones 2, 4 y 6 |

Bajo `## 1.`, cinco subsecciones con estos hechos exactos. La prosa es libre; los números, no.

**1.1 Predecir con papel.** Antes de ejecutar nada, el alumno responde: a 32 kS/s, ¿cuántas muestras hay en 1 ms? (32) ¿En 1 s? (32 000) ¿Cuánto dura un archivo de 6400 bytes? (6400 / 2 = 3200 muestras; 3200 / 32 000 = 0.1 s). Presentar la regla `N = fs · T` y el atajo: **en 1 ms hay tantas muestras como kS/s tenga `fs`**, porque 1 ms es 1/1000 s. Respuestas en `??? question`.

**1.2 Generar y contar.** Comandos, con (base) de radioconda activo y desde `sdr/`:

```bash
python samples/gen_tono.py
od -Ad -tu1 -w2 -N64 -v samples/tono_1kHz_32kSps.cu8
```

Salida: el bloque completo de «Hechos verificados», copiado tal cual. Lectura guiada:
- `-N64` pide 64 bytes, que son 32 muestras, que son 1 ms.
- Salen 33 líneas: 32 muestras y una final, `0000064`, con la dirección donde termina la lectura.
- La dirección avanza de dos en dos; n = dirección / 2.
- Primera columna I, segunda Q, igual que en A5 de la Sesión 01.

**1.3 Encontrar los 90°.** Pedir que localice I máximo y Q máximo. I máximo en n=0 (228), Q máximo en n=8 (dirección `0000016`, 228). Ocho de 32 muestras son un cuarto de ciclo: 90°. Enlazar con la hélice de la [Sesión 01, §2.4](index.md#24-punto-4-del-voltaje-real-a-las-muestras-complejas-iq), donde I y Q son las proyecciones de una flecha que gira (no con los fasores de §2.4.1, que dibujan componentes espectrales fijas), **sin escribir su número**: `test_las_citas_en_el_texto_apuntan_a_figuras_existentes` compara cada «Figura N» con las figuras de *esta* página, que tiene 3; «Figura 9» haría fallar el test. Insertar la figura:

```markdown
![Treinta y tres muestras del tono de 1 kHz a 32 kS/s: bytes de I y Q contra el índice n y contra el tiempo en milisegundos](figures/muestreo-un-milisegundo.png)

**Figura 1.** Un milisegundo del tono, muestra a muestra: en cada posición n están los dos bytes de una línea de `od`, I y Q del mismo instante.
```

Seguida de lectura guiada: la línea discontinua es el cero (127.5, lo que A6 de S01 midió como promedio) y los tallos crecen desde ella, hacia arriba o hacia abajo, con la misma forma que dibujará el Time Sink; I es el círculo azul relleno y Q el cuadrado rojo hueco, en la misma posición porque son el mismo instante; cada etiqueta da n y la dirección que imprime `od`, que es 2n; I y Q se persiguen con un cuarto de ciclo de retraso; la muestra 32 vuelve al máximo de I, pero su Q sale 127 y no 128, por el redondeo del aviso siguiente.

Añadir un aviso `!!! info` sobre el redondeo: en n=8 `od` da I=128 y en n=24 da 127, aunque el coseno vale cero en ambos. El cero del formato es 127.5, a medio camino entre dos enteros. Cuando la cuenta da **exactamente** 127.5 (n=0 en Q, n=8 en I), NumPy redondea al par: 128. Cuando la coma flotante deja un residuo del orden de 1e-14 que mueve la suma (n=16, 24, 32), el signo del residuo decide: n=24 da −1.8e-14 y sale 127. Por eso ciclos sucesivos pueden diferir en ±1 justo en esos valores. No es un error del archivo. Hechos medidos: residuo en n=8 = +6.1e-15, menor que medio paso de coma flotante en 127.5 (7.1e-15), así que la suma queda en 127.5 exacto.

**1.4 El mismo milisegundo en GNU Radio.** Abrir `warmup_32k.grc`, F6. Es la cadena de la Parte C de la Sesión 01 con dos cambios: `samp_rate = 32000` y el archivo. Hechos:
- Time Sink con `size = 32` → dibuja 32 muestras = 1 ms. Leyenda `I` (azul) y `Q` (rojo), con rejilla. Tiene un disparo (*trigger*) en 0.78 sobre la parte real, flanco de subida, para que la imagen quede quieta empezando en n=0: I arranca en 0.788 y Q en 0.
- La altura inicial de la curva real es 0.788 y no 228: (228 − 127.5) / 127.5 = 0.788. Los bloques `Add Const` y `Multiply Const` hacen esa cuenta. Pedir al alumno que calcule la altura en n=8 para Q y la compruebe.

**1.5 El tamaño de FFT.** Freq Sink con `fftsize = 32`, `bw = samp_rate`, ventana `WIN_RECTANGULAR`:
- Eje de −16 a +16 kHz: la FFT de una señal compleja muestra de −fs/2 a +fs/2.
- 32 bins repartidos en 32 kHz → separación de 1000 Hz. El tono cae exacto en el bin de +1 kHz, a unos −2 dB: 20·log10(0.788).
- Lo que no es el tono: un peine de torres entre unos −58 y −68 dB, con huecos que caen al fondo de la escala (−140). Es el error de redondear a 8 bits: el ADC no puede escribir 227.3 y escribe 227. Queda unos 60 dB por debajo del tono. Enlazar con «ADC de 8 bits» de la Parte A de la Sesión 01, sin cifra de figura. **No** subir `ymin` para esconderlo: se explica en una frase y en un `??? question`. Comprobar las cifras mirando el grafo en ejecución antes de escribirlas.
- Pedir que cambie `fftsize` a 1024: separación 32 000 / 1024 = 31.25 Hz; la FFT abarca 1024 / 32 000 s = 32 ms. La raya sigue en 1 kHz.
- La regla en los dos sentidos: `Δf = fs/N` y `T = N/fs`. Más resolución en frecuencia cuesta más tiempo de observación.
- `!!! note`: la ventana es rectangular a propósito. Con la Blackman-Harris que trae `test2.grc` la raya se ensancha varios bins; por qué, lo explica la [Sesión 02 §5](../02-tiempo-frecuencia-iq/index.md). No explicar la fuga aquí.

**Step 4: Verificar**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`
Expected: todo en verde, incluida la numeración de la Figura 1.

**Step 5: Commit**

```bash
git add docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md tests/test_laboratorio_muestreo.py
git commit -m "Laboratorio de muestreo §1: el milisegundo contado en od y visto en GNU Radio"
```

---

### Task 7: Sección 2 — Las mismas reglas donde no se pueden contar

**Files:**
- Modify: `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`
- Modify: `tests/test_laboratorio_muestreo.py`

**Step 1: Escribir el test que falla**

Añadir a `tests/test_laboratorio_muestreo.py`:

```python
class TestGrabacionReal(unittest.TestCase):
    def test_cita_las_cuentas_a_24_msps(self):
        pagina = texto()
        for dato in ("stat -c %s samples/fm_99p1MHz_2p4Msps_g30.cu8", "48000000",
                     "od -An -tu1 -w2 -N4800 -v samples/fm_99p1MHz_2p4Msps_g30.cu8 | wc -l",
                     "2343.75 Hz", "426.7 µs"):
            self.assertIn(dato, pagina)

    @unittest.skipUnless((ROOT / "samples/fm_99p1MHz_2p4Msps_g30.cu8").exists(),
                         "Falta samples/fm_99p1MHz_2p4Msps_g30.cu8; se descarga de Drive")
    def test_un_milisegundo_son_2400_lineas(self):
        salida = subprocess.run(
            "od -An -tu1 -w2 -N4800 -v samples/fm_99p1MHz_2p4Msps_g30.cu8 | wc -l",
            shell=True, cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertEqual(salida.strip(), "2400")
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_laboratorio_muestreo.py`
Expected: FAIL en `test_cita_las_cuentas_a_24_msps`; `test_un_milisegundo_son_2400_lineas` pasa ya.

**Step 3: Escribir la sección**

Hechos exactos:

- Duración a partir del tamaño, tres pestañas como en S01:
  - Linux: `stat -c %s samples/fm_99p1MHz_2p4Msps_g30.cu8` → `48000000`
  - macOS: `stat -f %z samples/fm_99p1MHz_2p4Msps_g30.cu8`
  - Windows: `(Get-Item samples\fm_99p1MHz_2p4Msps_g30.cu8).Length` en PowerShell. **Ejecutarlo en Windows antes de publicar**; si no hay máquina, omitir la pestaña.
  - Cuenta: 48 000 000 / 2 = 24 000 000 muestras; / 2 400 000 = 10 s.
- 1 ms a 2.4 MS/s son 2400 muestras = 4800 bytes. Ya no se cuentan a mano: se cuentan con `wc -l`.
  ```bash
  od -An -tu1 -w2 -N4800 -v samples/fm_99p1MHz_2p4Msps_g30.cu8 | wc -l
  ```
  Salida `2400`. Explicar por qué `-An` y no `-Ad`: sin columna de direcciones, `od` no imprime la línea final y `wc -l` cuenta solo muestras.
- En `test2.grc` (Sesión 01): Time Sink `size = 1024` → 1024 / 2 400 000 s = **426.7 µs**, menos de medio milisegundo. Freq Sink `fftsize = 1024` → **2343.75 Hz** entre bins, sobre un eje de 2.4 MHz.
- Ejercicio: qué `size` hay que poner al Time Sink para ver exactamente 1 ms (2400), y qué `fftsize` para bins de 1 kHz como en la sección 1 (2400, que no es potencia de dos; el Freq Sink solo ofrece potencias de dos en su menú, así que el más cercano es 2048 → 1171.9 Hz). **Verificar en GRC** si el campo `fftsize` acepta 2400 escrito a mano antes de afirmar nada; escribir lo que ocurra.
- Cierre: es la misma regla que en la sección 1, ahora con números que no caben en pantalla.

Respuestas en `??? question`.

**Step 4: Verificar**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`
Expected: todo en verde.

**Step 5: Commit**

```bash
git add docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md tests/test_laboratorio_muestreo.py
git commit -m "Laboratorio de muestreo §2: la regla N = fs·T aplicada a la grabación de 2.4 MS/s"
```

---

### Task 8: Punto de control — revisión del profesor

**Step 1: Servir el sitio**

Run: `mkdocs serve -a 127.0.0.1:9000`
Expected: la página aparece en la nav bajo «01 — Introducción a SDR» → «Laboratorio de muestreo», con el aviso de borrador.

**Step 2: Pedir revisión**

Presentar al profesor §1 y §2, la Figura 1 y el grafo en ejecución. Aplicar sus observaciones en ciclos cortos: verificar numéricamente cada objeción antes de responder, rediseñar en vez de justificar.

**Step 3: Push, solo con confirmación**

Si el profesor lo aprueba: `git push` y comprobar que la Action de despliegue termina en verde con `gh run list --limit 1`.

---

### Task 9: Funciones de decimación e interpolación, y sus figuras

**Files:**
- Create: `docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py`
- Create: `figures/decimacion-con-y-sin-filtro.png`, `figures/interpolacion-con-y-sin-filtro.png` (generados)
- Test: `tests/test_gen_decimacion_figures.py`

**Step 1: Escribir el test que falla**

La lógica se prueba con tonos sintéticos, sin depender de la grabación. Solo la generación de las figuras la necesita.

`tests/test_gen_decimacion_figures.py`:

```python
"""Decimación e interpolación del laboratorio de muestreo: aliasing e imágenes, con tonos."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py"
MUESTRA = ROOT / "samples/fm_99p1MHz_2p4Msps_g30.cu8"
FS = 2_400_000


def cargar():
    spec = importlib.util.spec_from_file_location("gen_decimacion", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def pico(x, fs):
    """Frecuencia del bin más fuerte, en Hz."""
    espectro = np.abs(np.fft.fft(x))
    return np.fft.fftfreq(x.size, 1 / fs)[espectro.argmax()]


def tono(f, fs, n):
    return np.exp(2j * np.pi * f * np.arange(n) / fs)


class TestDecimacion(unittest.TestCase):
    def test_el_filtro_tiene_los_193_coeficientes_de_firdes(self):
        self.assertEqual(cargar().pasabajos(FS, 120e3, 30e3).size, 193)

    def test_sin_filtro_400_khz_se_pliega_a_100_khz(self):
        y = cargar().decimar(tono(400e3, FS, 240_000), 8, filtrar=False)
        self.assertAlmostEqual(pico(y, FS / 8), 100e3, delta=FS / 8 / y.size)

    def test_con_filtro_400_khz_desaparece(self):
        g = cargar()
        x = tono(400e3, FS, 240_000) + 0.01 * tono(50e3, FS, 240_000)
        y = g.decimar(x, 8, filtrar=True)[100:]
        self.assertAlmostEqual(pico(y, FS / 8), 50e3, delta=FS / 8 / y.size)


class TestInterpolacion(unittest.TestCase):
    def test_solo_ceros_deja_imagenes_de_la_misma_potencia(self):
        g = cargar()
        y = g.interpolar(tono(50e3, FS / 8, 30_000), 8, filtrar=False)
        espectro = np.abs(np.fft.fft(y))
        f = np.fft.fftfreq(y.size, 1 / FS)
        base = espectro[np.argmin(abs(f - 50e3))]
        imagen = espectro[np.argmin(abs(f - 350e3))]
        self.assertAlmostEqual(imagen / base, 1.0, places=2)

    def test_con_filtro_las_imagenes_caen_mas_de_40_db(self):
        g = cargar()
        y = g.interpolar(tono(50e3, FS / 8, 30_000), 8, filtrar=True)[200:]
        espectro = np.abs(np.fft.fft(y))
        f = np.fft.fftfreq(y.size, 1 / FS)
        base = espectro[abs(f - 50e3) < 2e3].max()
        imagen = espectro[abs(f - 350e3) < 2e3].max()
        self.assertLess(20 * np.log10(imagen / base), -40)


@unittest.skipUnless(MUESTRA.exists(), "Falta samples/fm_99p1MHz_2p4Msps_g30.cu8; se descarga de Drive")
class TestFigurasConLaGrabacion(unittest.TestCase):
    def test_genera_las_dos_figuras(self):
        with tempfile.TemporaryDirectory() as tmp:
            rutas = cargar().generar(Path(tmp))
            self.assertEqual([r.name for r in rutas],
                             ["decimacion-con-y-sin-filtro.png", "interpolacion-con-y-sin-filtro.png"])
            for r in rutas:
                self.assertGreater(r.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_gen_decimacion_figures.py`
Expected: FAIL, falta el script.

**Step 3: Implementación**

`docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py`:

```python
#!/usr/bin/env python3
"""Figuras de decimación e interpolación del laboratorio de muestreo.

Necesita samples/fm_99p1MHz_2p4Msps_g30.cu8, que no está en el repositorio y se
descarga de Drive. Sin ella el script se detiene con un mensaje claro.

    python gen_decimacion.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = Path(__file__).parent
MUESTRA = Path(__file__).parents[4] / "samples/fm_99p1MHz_2p4Msps_g30.cu8"
FS = 2_400_000
D = 8
BLUE, RED, GREEN = "#1e40af", "#b91c1c", "#15803d"


def pasabajos(fs, corte, transicion, ganancia=1.0):
    """FIR con ventana Hamming, mismo número de coeficientes que firdes.low_pass."""
    ntaps = int(53 * fs / (22 * transicion)) | 1  # ponytail: fórmula de firdes para Hamming (53 dB)
    k = np.arange(ntaps) - ntaps // 2
    h = np.sinc(2 * corte * k / fs) * np.hamming(ntaps)
    return ganancia * h / h.sum()


def decimar(x, d, filtrar):
    if filtrar:
        fs_out = FS / d
        x = np.convolve(x, pasabajos(FS, 0.4 * fs_out, 0.1 * fs_out), mode="same")
    return x[::d]


def interpolar(x, d, filtrar):
    y = np.zeros(x.size * d, dtype=complex)
    y[::d] = x
    if filtrar:
        fs_in = FS / d
        y = np.convolve(y, pasabajos(FS, 0.4 * fs_in, 0.1 * fs_in, ganancia=d), mode="same")
    return y


def leer(segundos=0.5):
    if not MUESTRA.exists():
        raise SystemExit(f"Falta {MUESTRA}. Descárgala de la carpeta 'samples' del curso en Drive.")
    d = np.fromfile(MUESTRA, dtype=np.uint8, count=2 * int(FS * segundos)).astype(np.float32)
    return ((d[0::2] - 127.5) + 1j * (d[1::2] - 127.5)) / 127.5


def psd_db(x, fs, nfft=1024):
    bloques = x[: x.size // nfft * nfft].reshape(-1, nfft) * np.hanning(nfft)
    p = np.mean(np.abs(np.fft.fft(bloques, axis=1)) ** 2, axis=0)
    return np.fft.fftshift(np.fft.fftfreq(nfft, 1 / fs)), 10 * np.log10(np.fft.fftshift(p) + 1e-12)


def panel(ax, x, fs, color, titulo):
    f, p = psd_db(x, fs)
    ax.plot(f / 1e3, p, color=color, lw=0.8)
    ax.set_title(titulo, fontsize=10, loc="left")
    ax.set_xlabel("frecuencia relativa a 99.1 MHz (kHz)")
    ax.set_ylabel("dB")


def generar(salida: Path = OUT):
    x = leer()
    rutas = []

    fig, ax = plt.subplots(3, 1, figsize=(10, 9), dpi=300)
    panel(ax[0], x, FS, BLUE, "(a) Grabación original, 2.4 MS/s")
    panel(ax[1], decimar(x, D, filtrar=False), FS / D, RED, f"(b) Keep 1 in {D}: 300 kS/s sin filtro")
    panel(ax[2], decimar(x, D, filtrar=True), FS / D, GREEN, f"(c) Decimating FIR Filter: 300 kS/s con filtro")
    fig.tight_layout()
    rutas.append(salida / "decimacion-con-y-sin-filtro.png")
    fig.savefig(rutas[-1], bbox_inches="tight", facecolor="white")
    plt.close(fig)

    y = decimar(x, D, filtrar=True)
    fig, ax = plt.subplots(3, 1, figsize=(10, 9), dpi=300)
    panel(ax[0], y, FS / D, GREEN, "(a) Punto de partida: 300 kS/s")
    panel(ax[1], interpolar(y, D, filtrar=False), FS, RED, f"(b) Solo insertar ceros: 2.4 MS/s")
    panel(ax[2], interpolar(y, D, filtrar=True), FS, BLUE, f"(c) Interpolating FIR Filter: 2.4 MS/s")
    fig.tight_layout()
    rutas.append(salida / "interpolacion-con-y-sin-filtro.png")
    fig.savefig(rutas[-1], bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return rutas


if __name__ == "__main__":
    for r in generar():
        print(r)
```

**Step 4: Ejecutar tests y generar**

Run: `/usr/bin/python3 -m pytest -q tests/test_gen_decimacion_figures.py && /usr/bin/python3 docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py`
Expected: 6 passed; dos rutas impresas.

Si `test_con_filtro_las_imagenes_caen_mas_de_40_db` falla por poco, **no bajes el umbral a ciegas**: mide la atenuación real y ponla en el test y en la prosa. Hamming da ~53 dB en la banda eliminada, pero `mode="same"` y los bordes pueden recortarlo.

Abre los dos PNG. En la decimación, (b) debe mostrar picos que en (c) no están. En la interpolación, (b) debe mostrar copias del espectro repetidas cada 300 kHz y (c) solo la central.

**Step 5: Commit**

```bash
git add docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py docs/sessions/01-introduccion-sdr/figures/decimacion-con-y-sin-filtro.png docs/sessions/01-introduccion-sdr/figures/interpolacion-con-y-sin-filtro.png tests/test_gen_decimacion_figures.py
git commit -m "Figuras de decimación e interpolación con y sin filtro para el laboratorio de muestreo"
```

---

### Task 10: Grafo de decimación

**Files:**
- Create: `gnuradio-flowgraphs/decimacion.grc`
- Test: `tests/test_flowgraph_decimacion.py`

**Step 1: Escribir el test que falla**

`tests/test_flowgraph_decimacion.py`:

```python
"""Contrato del grafo de decimación: mismo factor, con y sin filtro, lado a lado."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
TAPS = "firdes.low_pass(1, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)"


class TestDecimacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        g = yaml.safe_load((ROOT / "gnuradio-flowgraphs/decimacion.grc").read_text(encoding="utf-8"))
        cls.g, cls.b, cls.c = g, {x["name"]: x for x in g["blocks"]}, {tuple(c) for c in g["connections"]}

    def p(self, nombre):
        return self.b[nombre]["parameters"]

    def test_parte_de_la_grabacion_oficial(self):
        self.assertEqual(self.g["options"]["parameters"]["id"], "decimacion")
        self.assertEqual(self.p("blocks_file_source_0")["file"], "../samples/fm_99p1MHz_2p4Msps_g30.cu8")
        self.assertEqual(self.p("samp_rate")["value"], "2400000")
        self.assertEqual(self.p("D")["value"], "8")

    def test_sin_filtro(self):
        self.assertEqual(self.p("blocks_keep_one_in_n_0")["type"], "complex")
        self.assertEqual(self.p("blocks_keep_one_in_n_0")["n"], "D")
        self.assertIn(("blocks_float_to_complex_0", "0", "blocks_keep_one_in_n_0", "0"), self.c)
        self.assertIn(("blocks_keep_one_in_n_0", "0", "qtgui_freq_sink_sin_filtro", "0"), self.c)
        self.assertEqual(self.p("qtgui_freq_sink_sin_filtro")["bw"], "samp_rate/D")

    def test_con_filtro(self):
        fir = self.p("fir_filter_xxx_0")
        self.assertEqual((fir["type"], fir["decim"], fir["taps"]), ("ccf", "D", TAPS))
        self.assertIn(("blocks_float_to_complex_0", "0", "fir_filter_xxx_0", "0"), self.c)
        self.assertIn(("fir_filter_xxx_0", "0", "qtgui_freq_sink_con_filtro", "0"), self.c)
        self.assertEqual(self.p("qtgui_freq_sink_con_filtro")["bw"], "samp_rate/D")

    def test_sin_hardware(self):
        self.assertFalse([n for n in self.b if n.startswith("soapy_")])


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_flowgraph_decimacion.py`
Expected: FAIL, falta el `.grc`.

**Step 3: Derivar el grafo de `test2.grc`**

```bash
/usr/bin/python3 - <<'PYEOF'
import copy, yaml
from pathlib import Path
d = Path("gnuradio-flowgraphs")
g = yaml.safe_load((d / "test2.grc").read_text(encoding="utf-8"))
fuera = {"soapy_rtlsdr_source_0", "freq", "rfGain", "M", "qtgui_time_sink_x_0"}
g["blocks"] = [b for b in g["blocks"] if b["name"] not in fuera]
g["connections"] = [c for c in g["connections"] if c[0] not in fuera and c[2] not in fuera]
g["options"]["parameters"]["id"] = "decimacion"
g["options"]["parameters"]["title"] = "Laboratorio de muestreo - Decimación con y sin filtro"
g["options"]["parameters"]["description"] = "Decima la grabación oficial de 2.4 MS/s por D con Keep 1 in N y con Decimating FIR, para comparar los espectros."
por_nombre = {b["name"]: b for b in g["blocks"]}
por_nombre["blocks_file_source_0"]["parameters"]["comment"] = "Lee el .cu8 byte a byte: I, Q, I, Q... sin signo, con el cero en 127.5."
por_nombre["blocks_throttle2_0"]["parameters"]["comment"] = "Limita el flujo a 2*samp_rate bytes por segundo, dos por muestra compleja. Sin hardware que marque el ritmo, el archivo se leería a toda velocidad."
original = por_nombre["qtgui_freq_sink_x_0"]
original["parameters"].update(fc="99.1e6", name='"Original, 2.4 MS/s"')

def estados(x, y):
    return {"bus_sink": False, "bus_source": False, "bus_structure": None,
            "coordinate": [x, y], "rotation": 0, "state": "enabled"}

g["blocks"].append({"name": "D", "id": "variable", "parameters": {"comment": "", "value": "8"},
                    "states": estados(300, 12)})
g["blocks"].append({"name": "blocks_keep_one_in_n_0", "id": "blocks_keep_one_in_n",
                    "parameters": {"type": "complex", "n": "D", "vlen": "1"}, "states": estados(1100, 300)})
g["blocks"].append({"name": "fir_filter_xxx_0", "id": "fir_filter_xxx",
                    "parameters": {"type": "ccf", "decim": "D", "samp_delay": "0",
                                   "taps": "firdes.low_pass(1, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)"},
                    "states": estados(1100, 450)})
for nombre, titulo, y in (("qtgui_freq_sink_sin_filtro", '"Keep 1 in D: sin filtro"', 300),
                          ("qtgui_freq_sink_con_filtro", '"Decimating FIR: con filtro"', 450)):
    s = copy.deepcopy(original)
    s["name"] = nombre
    s["parameters"].update(bw="samp_rate/D", name=titulo)
    s["states"] = estados(1350, y)
    g["blocks"].append(s)
g["connections"] += [
    ["blocks_float_to_complex_0", "0", "blocks_keep_one_in_n_0", "0"],
    ["blocks_keep_one_in_n_0", "0", "qtgui_freq_sink_sin_filtro", "0"],
    ["blocks_float_to_complex_0", "0", "fir_filter_xxx_0", "0"],
    ["fir_filter_xxx_0", "0", "qtgui_freq_sink_con_filtro", "0"],
]
(d / "decimacion.grc").write_text(yaml.safe_dump(g, sort_keys=False, allow_unicode=True), encoding="utf-8")
PYEOF
```

**Step 4: Compilar y ejecutar tests**

Run:
```bash
D=$(mktemp -d) && ~/radioconda/bin/grcc -o "$D" gnuradio-flowgraphs/decimacion.grc; echo "exit=$?"; rm -rf "$D"
/usr/bin/python3 -m pytest -q tests/
```
Expected: `exit=0`; todo en verde. Si `grcc` se queja de un parámetro que falta en los bloques nuevos, añádelo con el `default` de su `.block.yml` en `~/radioconda/share/gnuradio/grc/blocks/`.

**Step 5: Comprobación visual (con el profesor)**

F6. Tres Freq Sink: original de ±1.2 MHz, y dos de ±150 kHz. El de «sin filtro» debe mostrar picos que el de «con filtro» no tiene. Cambiar `D` a 2 y repetir: con ±600 kHz de banda, ¿se pliega algo?

**Step 6: Commit**

```bash
git add gnuradio-flowgraphs/decimacion.grc tests/test_flowgraph_decimacion.py
git commit -m "Grafo de decimación con Keep 1 in N y Decimating FIR lado a lado"
```

---

### Task 11: Sección 4 — Decimación en software

**Files:**
- Modify: `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`
- Modify: `tests/test_laboratorio_muestreo.py`

**Step 1: Medir antes de escribir**

La prosa debe nombrar qué picos se pliegan y a dónde, con números medidos, no supuestos:

```bash
/usr/bin/python3 - <<'PYEOF'
import importlib.util, numpy as np
spec = importlib.util.spec_from_file_location("g", "docs/sessions/01-introduccion-sdr/figures/gen_decimacion.py")
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
x = g.leer()
f, p = g.psd_db(x, g.FS)
suelo = np.median(p)
print(f"suelo de ruido original: {suelo:.1f} dB")
picos = [(f[k], p[k]) for k in range(1, f.size - 1)
         if p[k] > suelo + 15 and p[k] >= p[k-1] and p[k] >= p[k+1]]
fs_out = g.FS / g.D
for fk, pk in picos:
    plegado = (fk + fs_out / 2) % fs_out - fs_out / 2
    print(f"pico {fk/1e3:8.1f} kHz ({(99.1e6+fk)/1e6:.2f} MHz) {pk-suelo:5.1f} dB sobre el suelo -> sin filtro cae en {plegado/1e3:7.1f} kHz")
PYEOF
```

Anota la salida en el informe de la tarea. Elige **una** emisora concreta que se pliegue dentro de ±150 kHz para contarla en la prosa, con su frecuencia real y la plegada. Si picos contiguos pertenecen a la misma emisora FM (lóbulo de ~200 kHz), agrúpalos a mano.

**Step 2: Escribir el test que falla**

Añadir a `tests/test_laboratorio_muestreo.py`, sustituyendo `<MHz_real>` y `<kHz_plegado>` por los valores medidos:

```python
class TestDecimacion(unittest.TestCase):
    def test_enlaza_el_grafo_y_la_figura(self):
        pagina = texto()
        self.assertIn(GITHUB + "gnuradio-flowgraphs/decimacion.grc", pagina)
        self.assertIn("figures/decimacion-con-y-sin-filtro.png", pagina)

    def test_cita_el_filtro_y_el_ejemplo_medido(self):
        pagina = texto()
        for dato in ("firdes.low_pass(1, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)", "193",
                     "<MHz_real>", "<kHz_plegado>"):
            self.assertIn(dato, pagina)
```

**Step 3: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_laboratorio_muestreo.py`
Expected: FAIL en la clase `TestDecimacion`.

**Step 4: Escribir la sección**

Hechos:
- Decimar por D divide `fs` por D. 2.4 MS/s ÷ 8 = 300 kS/s; ÷ 2 = 1.2 MS/s. Con la regla de la sección 1: la banda visible pasa de ±1.2 MHz a ±150 kHz.
- Lo que había fuera de ±150 kHz no desaparece por quedarse con una de cada ocho muestras: se **pliega** dentro. Fórmula de plegado: `f' = ((f + fs'/2) mod fs') − fs'/2`. Ejemplo medido en el Step 1.
- `Keep 1 in N` solo descarta muestras. `Decimating FIR Filter` filtra primero y luego descarta. Filtro: `firdes.low_pass(1, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)`: corte en 120 kHz y transición de 30 kHz para D=8, que acaba justo en 150 kHz. 193 coeficientes con la ventana Hamming por defecto.
- Figura 2 con pie `**Figura 2.** …` y lectura guiada panel a panel.
- Enlazar con la Sesión 01: el DDC del RTL2832U ya hace esta operación dentro del chip (la figura de la decimación en la cadena de recepción de [`index.md`](index.md), nombrada sin su número por la misma razón que en 1.3, y sin volver a insertar la imagen).
- Ejercicio en el grafo: `D = 2`. Pregunta: ¿aparece aliasing? La respuesta sale del grafo, no de la teoría. Anotar lo observado.

**Step 5: Verificar y commit**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`
Expected: todo en verde, Figura 2 numerada.

```bash
git add docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md tests/test_laboratorio_muestreo.py
git commit -m "Laboratorio de muestreo §4: decimación con y sin filtro sobre la grabación oficial"
```

---

### Task 12: Grafo de interpolación

**Files:**
- Create: `gnuradio-flowgraphs/interpolacion.grc`
- Test: `tests/test_flowgraph_interpolacion.py`

**Step 1: Escribir el test que falla**

`tests/test_flowgraph_interpolacion.py`:

```python
"""Contrato del grafo de interpolación: 300 kS/s de vuelta a 2.4 MS/s, con y sin filtro."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


class TestInterpolacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        g = yaml.safe_load((ROOT / "gnuradio-flowgraphs/interpolacion.grc").read_text(encoding="utf-8"))
        cls.g, cls.b, cls.c = g, {x["name"]: x for x in g["blocks"]}, {tuple(c) for c in g["connections"]}

    def p(self, nombre):
        return self.b[nombre]["parameters"]

    def test_identidad(self):
        self.assertEqual(self.g["options"]["parameters"]["id"], "interpolacion")

    def test_primero_baja_a_300_ksps(self):
        fir = self.p("fir_filter_xxx_0")
        self.assertEqual((fir["type"], fir["decim"]), ("ccf", "D"))
        self.assertIn(("fir_filter_xxx_0", "0", "qtgui_freq_sink_300k", "0"), self.c)
        self.assertEqual(self.p("qtgui_freq_sink_300k")["bw"], "samp_rate/D")

    def test_solo_ceros(self):
        sin = self.p("interp_fir_filter_xxx_ceros")
        self.assertEqual((sin["type"], sin["interp"], sin["taps"]), ("ccf", "D", "[1.0]"))
        self.assertIn(("fir_filter_xxx_0", "0", "interp_fir_filter_xxx_ceros", "0"), self.c)
        self.assertIn(("interp_fir_filter_xxx_ceros", "0", "qtgui_freq_sink_ceros", "0"), self.c)
        self.assertEqual(self.p("qtgui_freq_sink_ceros")["bw"], "samp_rate")

    def test_con_filtro(self):
        con = self.p("interp_fir_filter_xxx_filtro")
        self.assertEqual((con["type"], con["interp"]), ("ccf", "D"))
        self.assertEqual(con["taps"], "firdes.low_pass(D, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)")
        self.assertIn(("fir_filter_xxx_0", "0", "interp_fir_filter_xxx_filtro", "0"), self.c)
        self.assertIn(("interp_fir_filter_xxx_filtro", "0", "qtgui_freq_sink_filtro", "0"), self.c)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_flowgraph_interpolacion.py`
Expected: FAIL, falta el `.grc`.

**Step 3: Derivar de `decimacion.grc`**

```bash
/usr/bin/python3 - <<'PYEOF'
import copy, yaml
from pathlib import Path
d = Path("gnuradio-flowgraphs")
g = yaml.safe_load((d / "decimacion.grc").read_text(encoding="utf-8"))
fuera = {"blocks_keep_one_in_n_0", "qtgui_freq_sink_sin_filtro", "qtgui_freq_sink_x_0"}
g["blocks"] = [b for b in g["blocks"] if b["name"] not in fuera]
g["connections"] = [c for c in g["connections"] if c[0] not in fuera and c[2] not in fuera]
g["options"]["parameters"]["id"] = "interpolacion"
g["options"]["parameters"]["title"] = "Laboratorio de muestreo - Interpolación con y sin filtro"
g["options"]["parameters"]["description"] = "Baja la grabación oficial a 300 kS/s y la vuelve a subir a 2.4 MS/s insertando ceros, con y sin Interpolating FIR."
por_nombre = {b["name"]: b for b in g["blocks"]}
sink300 = por_nombre.pop("qtgui_freq_sink_con_filtro")
sink300["name"] = "qtgui_freq_sink_300k"
sink300["parameters"]["name"] = '"Punto de partida: 300 kS/s"'
g["connections"] = [[c[0], c[1], "qtgui_freq_sink_300k" if c[2] == "qtgui_freq_sink_con_filtro" else c[2], c[3]]
                    for c in g["connections"]]

def estados(x, y):
    return {"bus_sink": False, "bus_source": False, "bus_structure": None,
            "coordinate": [x, y], "rotation": 0, "state": "enabled"}

for sufijo, taps, titulo, y in (
        ("ceros", "[1.0]", '"Solo ceros: 2.4 MS/s"', 600),
        ("filtro", "firdes.low_pass(D, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)",
         '"Interpolating FIR: 2.4 MS/s"', 750)):
    g["blocks"].append({"name": f"interp_fir_filter_xxx_{sufijo}", "id": "interp_fir_filter_xxx",
                        "parameters": {"type": "ccf", "interp": "D", "taps": taps, "samp_delay": "0"},
                        "states": estados(1350, y)})
    s = copy.deepcopy(sink300)
    s["name"] = f"qtgui_freq_sink_{sufijo}"
    s["parameters"].update(bw="samp_rate", name=titulo)
    s["states"] = estados(1600, y)
    g["blocks"].append(s)
    g["connections"] += [["fir_filter_xxx_0", "0", f"interp_fir_filter_xxx_{sufijo}", "0"],
                         [f"interp_fir_filter_xxx_{sufijo}", "0", f"qtgui_freq_sink_{sufijo}", "0"]]
(d / "interpolacion.grc").write_text(yaml.safe_dump(g, sort_keys=False, allow_unicode=True), encoding="utf-8")
PYEOF
```

**Step 4: Compilar, tests, comprobación visual**

Run:
```bash
D=$(mktemp -d) && ~/radioconda/bin/grcc -o "$D" gnuradio-flowgraphs/interpolacion.grc; echo "exit=$?"; rm -rf "$D"
/usr/bin/python3 -m pytest -q tests/
```
Expected: `exit=0`; todo en verde.

Con el profesor, F6: el sink de 300 kS/s muestra ±150 kHz; «solo ceros» muestra ±1.2 MHz con **ocho copias** de esa banda; «con filtro» solo la central y el resto vacío.

**Step 5: Commit**

```bash
git add gnuradio-flowgraphs/interpolacion.grc tests/test_flowgraph_interpolacion.py
git commit -m "Grafo de interpolación: inserción de ceros contra Interpolating FIR"
```

---

### Task 13: Sección 6 — Interpolación

**Files:**
- Modify: `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`
- Modify: `tests/test_laboratorio_muestreo.py`

**Step 1: Escribir el test que falla**

```python
class TestInterpolacion(unittest.TestCase):
    def test_enlaza_el_grafo_y_la_figura(self):
        pagina = texto()
        self.assertIn(GITHUB + "gnuradio-flowgraphs/interpolacion.grc", pagina)
        self.assertIn("figures/interpolacion-con-y-sin-filtro.png", pagina)

    def test_cita_los_hechos(self):
        pagina = texto()
        for dato in ("[1.0]", "firdes.low_pass(D, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)"):
            self.assertIn(dato, pagina)
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_laboratorio_muestreo.py`
Expected: FAIL en `TestInterpolacion`.

**Step 3: Escribir la sección**

Hechos:
- Interpolar por D multiplica `fs` por D: 300 kS/s × 8 = 2.4 MS/s. Banda visible de ±150 kHz a ±1.2 MHz.
- Primer paso de toda interpolación: insertar D − 1 ceros entre muestras. `Interpolating FIR Filter` con `taps = [1.0]` hace solo eso. El espectro de 300 kHz aparece repetido cada 300 kHz: son **imágenes**, la contraparte de los alias de la sección 4.
- Con `firdes.low_pass(D, samp_rate, 0.4*samp_rate/D, 0.1*samp_rate/D)` las imágenes se eliminan. La ganancia D compensa que siete de cada ocho muestras sean cero.
- La idea central: el resultado tiene 2.4 MS/s pero **la misma información que a 300 kS/s**. Fuera de ±150 kHz solo queda banda vacía. Interpolar no recupera las emisoras que la decimación eliminó.
- Figura 3 con pie y lectura guiada. Atenuación de las imágenes: la medida en la Tarea 9, no la teórica.
- Cierre de la guía, tres reglas: `N = fs·T`, `Δf = fs/N`, y «bajar `fs` sin filtrar pliega; subir `fs` sin filtrar replica».

**Step 4: Verificar y commit**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`
Expected: todo en verde, Figura 3 numerada.

```bash
git add docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md tests/test_laboratorio_muestreo.py
git commit -m "Laboratorio de muestreo §6: interpolación, imágenes y banda vacía"
```

---

### Task 14: [Profesor] Grabaciones a 1.2 MS/s y 300 kS/s

Acción humana. Bloquea las Tareas 15 y 16. Conviene hacerla en la misma sesión con el dongle que las tres capturas de ganancia de la Sesión 02.

**Step 1: Grabar**

Misma antena, posición y ganancia que la grabación oficial. Desde `sdr/`, con (base) activo:

```bash
rtl_sdr -f 99.1e6 -s 1200000 -g 30 -n 12000000 samples/fm_99p1MHz_1p2Msps_g30.cu8
rtl_sdr -f 99.1e6 -s 300000  -g 30 -n 3000000  samples/fm_99p1MHz_0p3Msps_g30.cu8
```

**Step 2: La tasa prohibida, en vivo**

```bash
rtl_sdr -f 99.1e6 -s 600000 -g 30 -n 6000000 /tmp/prueba_600k.cu8 2>&1 | tee /tmp/prueba_600k.log
ls -l /tmp/prueba_600k.cu8
```

Por el binario se sabe que `librtlsdr` imprime `Invalid sample rate: 600000 Hz` y devuelve error. **Lo que no está verificado es qué hace `rtl_sdr` después**: si aborta, o si avisa y graba igualmente a otra tasa. Copiar el log completo y el tamaño del archivo, si existe. La sección 3 contará lo que ocurra de verdad.

**Step 3: Comprobar y publicar**

```bash
stat -c %s samples/fm_99p1MHz_1p2Msps_g30.cu8 samples/fm_99p1MHz_0p3Msps_g30.cu8
sha256sum samples/fm_99p1MHz_1p2Msps_g30.cu8 samples/fm_99p1MHz_0p3Msps_g30.cu8
```

Expected: `24000000` y `6000000`.

Subir ambas a la carpeta `samples` de Drive y entregar, de cada una: nombre, `fc`, `fs`, ganancia, antena, duración, formato, SHA-256.

---

### Task 15: Sección 3 — La escalera con hardware real

**Bloqueada por la Tarea 14.**

**Files:**
- Modify: `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`
- Modify: `tests/test_laboratorio_muestreo.py`
- Modify: `AGENTS.md`, tabla de «Datos y archivos pesados»

**Step 1: Escribir el test que falla**

Sustituir `<sha_1p2>`, `<sha_0p3>` y `<mensaje_600k>` por lo entregado en la Tarea 14:

```python
class TestEscalera(unittest.TestCase):
    def test_metadatos_de_las_grabaciones(self):
        pagina = texto()
        for dato in ("fm_99p1MHz_1p2Msps_g30.cu8", "24000000", "<sha_1p2>",
                     "fm_99p1MHz_0p3Msps_g30.cu8", "6000000", "<sha_0p3>"):
            self.assertIn(dato, pagina)

    def test_la_tasa_prohibida(self):
        pagina = texto()
        for dato in ("225 001", "300 000", "900 001", "3 200 000", "<mensaje_600k>"):
            self.assertIn(dato, pagina)

    def test_quita_el_aviso_de_pendiente(self):
        seccion = texto().split("## 3.")[1].split("## 4.")[0]
        self.assertNotIn("Pendiente", seccion)
```

**Step 2: Ejecutar y ver el fallo**

Run: `/usr/bin/python3 -m pytest -q tests/test_laboratorio_muestreo.py`
Expected: FAIL en `TestEscalera`.

**Step 3: Escribir la sección**

Hechos:
- Tabla de las tres grabaciones: nombre, `fs`, tamaño, duración, SHA-256, con la descarga y la comprobación de hash igual que en la Sesión 01.
- La escalera 2.4 → 1.2 → 0.6 → 0.3 y el peldaño prohibido. Rangos válidos de `librtlsdr`: 225 001–300 000 y 900 001–3 200 000 Hz. Comando de la Tarea 14, Step 2, y su salida real.
- Con la regla de las secciones 1 y 2: a igual `fftsize = 1024`, separación entre bins de 2343.75, 1171.875 y 292.97 Hz; banda visible de ±1.2 MHz, ±600 kHz y ±150 kHz; tamaño del archivo proporcional a `fs`.
- Ejercicio: abrir cada grabación en `test2.grc` cambiando `samp_rate` y el archivo, y contar cuántas emisoras se ven.
- Quitar el aviso `!!! warning "Pendiente"`.

En `AGENTS.md`, añadir las dos grabaciones a la tabla de rutas, con la misma forma de la oficial.

**Step 4: Verificar y commit**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`

```bash
git add docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md tests/test_laboratorio_muestreo.py AGENTS.md
git commit -m "Laboratorio de muestreo §3: tres grabaciones reales y la tasa que el driver rechaza"
```

---

### Task 16: Sección 5 — El careo

**Bloqueada por la Tarea 14.**

**Files:**
- Create: `gnuradio-flowgraphs/careo.grc`
- Test: `tests/test_flowgraph_careo.py`
- Modify: `docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md`, `tests/test_laboratorio_muestreo.py`

**Step 1: Test del grafo**

`tests/test_flowgraph_careo.py`:

```python
"""Contrato del careo: grabación real a 300 kS/s contra la de 2.4 MS/s decimada, en un solo sink."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


class TestCareo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        g = yaml.safe_load((ROOT / "gnuradio-flowgraphs/careo.grc").read_text(encoding="utf-8"))
        cls.g, cls.b, cls.c = g, {x["name"]: x for x in g["blocks"]}, {tuple(c) for c in g["connections"]}

    def p(self, nombre):
        return self.b[nombre]["parameters"]

    def test_dos_fuentes_con_su_propio_throttle(self):
        self.assertEqual(self.p("fuente_2p4")["file"], "../samples/fm_99p1MHz_2p4Msps_g30.cu8")
        self.assertEqual(self.p("fuente_0p3")["file"], "../samples/fm_99p1MHz_0p3Msps_g30.cu8")
        self.assertEqual(self.p("throttle_2p4")["samples_per_second"], "2*samp_rate")
        self.assertEqual(self.p("throttle_0p3")["samples_per_second"], "2*samp_rate/D")

    def test_un_solo_sink_con_dos_entradas_a_300k(self):
        s = self.p("qtgui_freq_sink_x_0")
        self.assertEqual((s["nconnections"], s["bw"]), ("2", "samp_rate/D"))
        self.assertIn(("fir_filter_xxx_0", "0", "qtgui_freq_sink_x_0", "0"), self.c)
        self.assertIn(("f2c_0p3", "0", "qtgui_freq_sink_x_0", "1"), self.c)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Construir el grafo**

Partir de `decimacion.grc` en un script de un solo uso, siguiendo el patrón de la Tarea 10: renombrar la cadena existente con sufijo `_2p4` (`fuente_2p4`, `throttle_2p4`, …), duplicarla con sufijo `_0p3` apuntando al archivo de 300 kS/s con `samples_per_second = 2*samp_rate/D`, quitar `Keep 1 in N` y sus sinks, y dejar un único `qtgui_freq_sink_x_0` con `nconnections = 2`, `bw = samp_rate/D`, entrada 0 desde el FIR y entrada 1 desde `f2c_0p3`. Nombres de bloques exactamente como en el test. Compilar con `grcc`, `exit=0`.

**Step 3: Test de contenido y sección**

```python
class TestCareo(unittest.TestCase):
    def test_declara_el_limite_de_la_comparacion(self):
        seccion = texto().split("## 5.")[1].split("## 6.")[0]
        self.assertNotIn("Pendiente", seccion)
        self.assertIn(GITHUB + "gnuradio-flowgraphs/careo.grc", seccion)
        self.assertIn("cualitativ", seccion)
```

Hechos para la prosa:
- Mismo `fs` final, dos orígenes: la grabación hecha a 300 kS/s por el chip, y la de 2.4 MS/s decimada por el FIR de GNU Radio. Las dos trazas en el mismo sink.
- **Límite, en un `!!! warning`**: las capturas son secuenciales y la emisora cambió de contenido entre una y otra, así que la comparación es cualitativa, nunca muestra a muestra. La de 300 kS/s trae el filtro analógico y el diezmado interno del RTL2832U, no el FIR de GNU Radio. Comparar bordes de filtro y suelo de ruido, sí; comparar bytes, no.
- Qué comparar, con lo observado en GRC por el profesor: forma de los bordes a ±150 kHz y altura del suelo de ruido. Escribir lo que se vea, no lo que se espere.

**Step 4: Verificar y commit**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict`

```bash
git add gnuradio-flowgraphs/careo.grc tests/test_flowgraph_careo.py docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md tests/test_laboratorio_muestreo.py
git commit -m "Laboratorio de muestreo §5: careo entre la grabación a 300 kS/s y la decimada"
```

---

### Task 17: Cierre

**Step 1: Verificación completa**

Run: `/usr/bin/python3 -m pytest -q tests/ && mkdocs build --strict && git status --short`
Expected: todo en verde; árbol limpio; ningún `.cu8` ni `.py` generado por GRC en el índice.

**Step 2: Actualizar el estado del diseño**

En `docs/plans/2026-09-12-lab-muestreo-design.md`, cambiar `**Estado:** diseño aprobado, sin implementar` por `**Estado:** implementado`, y anotar al final cualquier desviación que haya surgido durante la ejecución.

**Step 3: Revisión y push**

La página conserva `status: draft` hasta que el profesor la apruebe. Push solo con su confirmación, y comprobar la Action con `gh run list --limit 1`.

```bash
git add docs/plans/2026-09-12-lab-muestreo-design.md
git commit -m "Diseño del laboratorio de muestreo marcado como implementado"
```

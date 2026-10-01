# Verificación de la sesión 02 y recuperación del laboratorio #2

Fecha: 2026-10-01. Documento auxiliar para el profesor; `plans/` está excluido de MkDocs.

## Resultado y alcance

- Se revisaron los conceptos de las seis subsecciones, sus fórmulas, las 24 soluciones desplegables y la síntesis visual. No se detectaron errores algebraicos ni respuestas numéricas incorrectas bajo las hipótesis declaradas. Se corrigió una descripción de paneles y se precisaron dos formulaciones.
- Se ejecutaron las 36 celdas Python publicadas. Se comprobaron sus resultados con relaciones matemáticas independientes y se probaron los generadores de las 31 figuras, sin sobrescribir los PNG del profesor.
- Se recuperó el laboratorio FM del backup, conservando su cadena original a 2.048 MS/s. Se corrigieron afirmaciones de alcance excesivo, se añadieron instrucciones de construcción y se explicó la demodulación mediante avance de fase.
- Se verificó la cadena DSP procedente del `.grc` con FM sintética y con la captura local. No se verificaron audición, hardware físico ni calibración RF. La sesión y el laboratorio siguen en borrador.

## 1. Conceptos contrastados

| Subsección | Comprobación | Resultado y condiciones | Fuente primaria |
|---|---|---|---|
| 1. Muestras y tiempo | Muestreo frente a cuantización; $T_s=1/f_s$, $t_n=n/f_s$, duración nominal $N/f_s$. | Correcto para muestreo uniforme. El último índice es $N-1$; no se confunde su instante con la duración nominal del bloque. | [MIT: sampling y quantization](https://ocw.mit.edu/courses/6-003-signals-and-systems-fall-2011/95b4b245722073e5d0c4ea95b384446e_MIT6_003F11_lec22.pdf). |
| 2. I/Q | Representación $I+jQ$, Euler, magnitud, atan2 y sentido del giro. | Correcto. La señal física real y su representación compleja no se presentan como dos señales físicas independientes. | [MathWorks: complex baseband](https://www.mathworks.com/help/phased/gs/standards-and-conventions.html), [NumPy: angle](https://numpy.org/doc/stable/reference/generated/numpy.angle.html). |
| 3. Tiempo y frecuencia | Coseno con dos contribuciones $A/2$; tono complejo con un signo; suma lineal e inversa de DFT completa. | Correcto. Las magnitudes de los ejemplos corresponden a ciclos enteros y escala FFT/N. Conservar solo magnitud no conserva fase. | [NumPy: definición, inversa y simetría de DFT](https://numpy.org/doc/stable/reference/routines.fft.html). |
| 4. Aliasing | Igualdad de $f_0+kf_s$; intervalo representativo; borde de Nyquist; filtrado antes de reducir tasa. | Correcto. +5 y −3 kHz a 8 kS/s son iguales muestra por muestra, no solo en magnitud. El caso real low-pass no se generaliza a cualquier RF bandpass. | [TU Eindhoven: periodicidad y equivalencia](https://spseducation.tue.nl/disciplines/discrete/discretesignalprocessing_sampling_sampling/), [MIT: anti-aliasing](https://ocw.mit.edu/courses/6-003-signals-and-systems-fall-2011/95b4b245722073e5d0c4ea95b384446e_MIT6_003F11_lec22.pdf). |
| 5. FFT de bloque | DFT, orden de bins, leakage, $N$ frente a $M$, normalización y ventanas. | Correcto. Padding cambia la rejilla, no el tiempo observado. Las anchuras $2f_s/N$ y $4f_s/N$ corresponden a rectangular y Hann periódica del ejemplo; no son garantías universales de resolución. | [NumPy: FFT](https://numpy.org/doc/stable/reference/routines.fft.html), [SciPy: spectral analysis](https://docs.scipy.org/doc/scipy/tutorial/signal.html#spectral-analysis). |
| 6. Baseband/RF | $f_{RF}=f_c+f_{BB}$; mezcla $f_0\mapsto f_0+f_{mix}$ y referencia $f_c'=f_c-f_{mix}$; CU8. | Correcto bajo convención sin inversión y banda seleccionada sin aliasing. La mezcla no recibe otra banda RF, y una etiqueta no transforma los datos. Las igualdades se comprobaron también mediante los tonos de las celdas. | [MathWorks: baseband y portadora](https://www.mathworks.com/help/phased/gs/standards-and-conventions.html); derivación algebraica y pruebas de la sesión. |

### Precisiones aplicadas a la teoría y las soluciones

1. **Subsección 2.3:** se documentan las dos representaciones numéricas ±180° sobre el eje I negativo. Se añadió una prueba con cero positivo y negativo en Q; ambos ángulos representan el mismo punto.
2. **Subsección 5.7:** se hace explícito que la anchura $4f_s/N$ corresponde a la Hann periódica definida en la sesión. No se extiende sin más a la variante simétrica.
3. **Ejercicio 3D:** el panel superior izquierdo de la Figura 7 muestra I de cada tono, no I y Q de ambos. El panel inferior izquierdo sí muestra I y Q de la suma. Se corrigió esa identificación; los cálculos de 1.5 y 0.5 eran correctos.
4. **Cierre y síntesis:** se eliminó la incompatibilidad editorial con el laboratorio restaurado. La teoría sigue preparando filtros; el laboratorio implementa una cadena con bloques, sin exigir el diseño interno de los filtros.

## 2. Verificación individual de las 24 soluciones

Las sustituciones y sus unidades se contrastaron con las fórmulas del apartado citado. Las pruebas de ejercicios y de celdas verifican cálculos, secuencias, coeficientes y contraejemplos; las pruebas de texto comprueban además ubicación y estructura desplegable.

| Ejercicio | Resultado comprobado | Veredicto |
|---|---|---|
| 1A | 50 µs entre muestras; 20 ms nominales; última muestra 19.95 ms; índice 50 a 2.5 ms. | Correcto. |
| 1B | Período 1 ms; ocho muestras/ciclo; $x[0]=0$, $x[2]=-0.8$ a 0.25 ms. | Correcto. |
| 1C | Mismos datos: 4 ms correctos frente a 2 ms con etiqueta errónea; frecuencia atribuida 2 kHz. | Correcto. |
| 1D | Amplitud 0.5; tono de 2 kHz con cuatro muestras/ciclo; fase π/2 sin cambiar tasa ni período. | Correcto. |
| 2A | $-3+j4$, magnitud 5, fase 126.87° en el segundo cuadrante. | Correcto. |
| 2B | Magnitud 0.5; $z[0]\approx0.3536+j0.3536$, $z[1]=0.5$; avance −45°. | Correcto. |
| 2C | 40 muestras complejas, 80 componentes reales, 5 ms; última pareja a 4.875 ms. | Correcto. |
| 2D | Coseno de amplitud 1.2: dos tonos de magnitud 0.6 a ±500 Hz; I sola no distingue signos con fases indicadas. | Correcto. |
| 3A | Componentes +1 kHz/0.8 y −2 kHz/0.3; muestra inicial 1.1; sin copias conjugadas obligatorias. | Correcto. |
| 3B | $2+e^{j\pi}=1$ con fase cero; magnitudes iguales cancelan y la fase del resultado nulo es indeterminada. | Correcto. |
| 3C | Magnitudes 0.5 en ±1 kHz; fases ±90° para el segundo coseno; inversa completa recupera sus muestras. | Correcto. |
| 3D | $z[0]=1.5$ sin tercer tono; cambiar la segunda fase a π produce $z[0]=0.5$. | Correcto tras precisar qué curvas muestra cada panel. |
| 4A | Representantes de +13, −10 y +4 kHz: −3, −2 y −4 kHz. | Correcto. |
| 4B | +7 y −1 kHz: igualdad para todo índice entero; en $n=1$, $0.7071-j0.7071$. | Correcto. |
| 4C | Reducción 24→8 kS/s: +9 kHz coincide con +1 kHz; magnitud 1.4 con las fases del enunciado. | Correcto; se distingue de otras fases. |
| 4D | Coseno en Nyquist: $(-1)^n$ o cero según fase; complejo $(-1)^ne^{j\phi}$ mantiene magnitud 1. | Correcto; ±Nyquist siguen siendo equivalentes. |
| 5A | 20 ms; 2880 ceros; rejillas de 50 y 12.5 Hz; Nyquist 24 kHz. | Correcto. |
| 5B | 9 ciclos para 1125 Hz frente a 8.8 para 1100 Hz; solo el primero coincide con un bin. | Correcto; el máximo de rejilla no retunea el tono. |
| 5C | Padding, ventana y más muestras son cambios distintos; con $M=8192$, ambas rejillas son 0.9765625 Hz. | Correcto; el panel D usa otra señal. |
| 5D | Inversa devuelve $xw$; desnormalizar no elimina la ventana; $w[0]=0$ impide recuperar ese dato por división. | Correcto. |
| 6A | RF 433.57 y 434.045 MHz; intervalo nominal [432.92,434.92) MHz. | Correcto. |
| 6B | Objetivo −400 kHz; multiplicador +400 kHz; nuevo centro 98.7 MHz; otras componentes +400 y +800 kHz. | Correcto, sin cruce de borde. |
| 6C | RF correcta 99.35 MHz frente a etiqueta falsa 99.75 MHz; mezcla −250 kHz y referencia 99.35 MHz. | Correcto. |
| 6D | 48000 bytes CU8 son 24000 muestras y 10 ms; −1 MHz corresponde a 98.1 MHz con los metadatos indicados. | Correcto. |

## 3. Laboratorio FM recuperado

Origen: `backups/sesion-02-2026-09-26/02-tiempo-frecuencia-iq/laboratorio-receptor-fm.md`. Destino: `docs/sessions/02-tiempo-frecuencia-iq/laboratorio-receptor-fm.md`.

### Correcciones y comprobaciones

- **Metadatos y tasas:** se conserva CU8 a 2.048 MS/s, bytes a 4.096 Mitems/s, resampler 3/32, canal a 192 kS/s y audio a 48 kS/s. Se añade la variante para la otra captura, a 2.4 MS/s, con resampler 2/25. La variante no utiliza el mismo archivo renombrado.
- **Throttle:** se retira la garantía de «audio a mitad de velocidad» ante una tasa Byte equivocada. Se calcula el suministro insuficiente; el clock de `Audio Sink` sigue a 48 kS/s y puede haber underruns.
- **Banda nominal:** se retira la afirmación general de que 192 kS/s bastan para cualquier canal FM. El filtro automático del resampler se documenta separadamente del intervalo nominal. El bloque usa 0.4 cuando no hay taps y el ancho indicado es cero. [Fuente del resampler](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-filter/lib/rational_resampler_impl.cc).
- **Demodulación:** se deriva $\widehat f=f_s\arg(zz^*_{prev})/(2\pi)$ del avance de fase y se establece su condición de no ambigüedad. Se contrasta el signo con el producto conjugado implementado. [Fuente de Quadrature Demod](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/lib/quadrature_demod_cf_impl.cc).
- **Parámetros:** en la versión instalada el campo se llama `Quadrature Rate`, no `Channel Rate`. Se comprobó en `analog_wfm_rcv.block.yml` instalado y en el Python generado por `grcc`.
- **Alcance:** se documentan salida mono, referencia de desviación de 75 kHz y ausencia de decoders stereo/RDS en esta cadena. [Fuente de WBFM Receive](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/wfm_rcv.py).
- **De-emphasis:** se documenta la constante predeterminada de 75 µs, sin atribuírsela a la emisora local. [Fuente del filtro](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/fm_emph.py).
- **Rutas:** el receptor tenía una ruta absoluta local. Se repuso `../samples/fm_99p1MHz_2p048Msps_g30.cu8`, preservando la posición de bloques ajustada por el profesor.
- **Soapy:** se indica desactivar los siete bloques de la ruta CU8, no solo File Source y Throttle. Esa variante compila; no se ejecutó con hardware.

### Ejecución de la cadena real de procesamiento

`tests/test_laboratorio_fm.py` carga el `.grc` publicado y genera variantes temporales. Conserva conversión CU8, resampler, `WBFM Receive` y volumen. Para medir una entrada finita sustituye Throttle por Copy, visores por Null Sink y Audio Sink por Vector Sink. No modifica el `.grc` del alumno ni necesita una tarjeta de audio.

| Entrada | Comprobación | Resultado observado |
|---|---|---|
| FM sintética CU8: moduladora 1 kHz, desviación 15 kHz, tasa 2.048 MS/s | Resampler 3/32 y salida interpretada a 48 kS/s. | Pico 1000.208 Hz; RMS 0.025615 con volumen 0.2; más de 99.99 % de energía espectral en la vecindad ±10 Hz del tono. |
| Misma construcción sintética a 2.4 MS/s | Resampler 2/25; mismo resto de la cadena. | Pico 1000.208 Hz; RMS 0.025614. |
| Primer segundo de la captura CU8 a 2.048 MS/s | Toda la cadena DSP del laboratorio. | 47991 muestras de salida, todas finitas; RMS 0.062605 después de excluir transitorios iniciales. |

La ligera diferencia respecto de 48000 muestras pertenece al procesamiento de un archivo finito y a los bordes de los filtros; no se interpreta como un cambio de tasa. El pico de la captura real no se utiliza como prueba de emisora ni como una moduladora conocida. La prueba sintética no incorpora pre-emphasis; la amplitud resultante incluye de-emphasis y volumen, y no debe igualar sin más a la moduladora original.

## 4. Verificación ejecutable

Entorno usado:

- MkDocs 1.6.1, Python 3.10.12.
- Pruebas numéricas: NumPy 1.26.4 y Matplotlib 3.10.8.
- Compilación y DSP: GNU Radio 3.10.12.0 en radioconda, Python 3.12.9 y NumPy 2.2.3.

Comandos ejecutados desde la raíz:

```bash
mkdocs build --strict
pytest -q tests/test_session02_fundamentos.py tests/test_session02_aliasing.py tests/test_session02_fft_bloque.py tests/test_session02_baseband_rf.py tests/test_session02_sintesis.py tests/test_session02_ejercicios.py tests/test_flowgraph_receptor_fm.py tests/test_laboratorio_fm.py tests/test_numeracion_figuras.py
pytest -q -s tests/test_laboratorio_fm.py
pytest -q tests/
grcc -o /tmp/sdr-fm-audit gnuradio-flowgraphs/receptor_fm_99p1_2p048Msps.grc
```

- **MkDocs strict:** correcto; laboratorio y enlaces locales válidos.
- **Pruebas enfocadas en esta entrega:** 109 passed y 170 subtests passed; ninguna omitida.
- **Pruebas DSP del laboratorio:** 6 passed, incluyendo las dos tasas sintéticas, captura real y compilación de la variante Soapy.
- **Numeración:** las 31 figuras de teoría conservan su secuencia; no se insertaron figuras nuevas.
- **Suite completa:** 160 passed, 199 subtests passed y 3 failed. Los tres fallos ajenos a esta entrega se detallan debajo; no se considera una suite global aprobada.
- **Advertencia de entorno:** Matplotlib avisa sobre Axes3D por coexistencia de instalaciones. Los gráficos utilizados aquí son 2D y las pruebas finalizaron.

### Fallos existentes ajenos al alcance

La suite completa detecta tres fallos en `tests/test_test_flowgraph.py`, vinculados a cambios previos del profesor en `gnuradio-flowgraphs/test2.grc`: File Source desactivado y dos comprobaciones de ruta absoluta. No se revirtió ese trabajo ni se modificó `test.grc`, cuya lectura equivocada es intencional en otro laboratorio. Por esos fallos no se declara verde la suite global.

Este informe recoge la revisión local previa a la solicitud de commit y push. Los 11 archivos del backup se conservaron en disco; su retirada del seguimiento y la regla `/backups/` se incluyen en la entrega solicitada.

Verificación previa al commit: se comprobó también una copia temporal de los archivos preparados en el índice Git, con acceso a las muestras locales mediante enlaces. MkDocs estricto pasó; la suite obtuvo 161 passed, 199 subtests passed y 2 failed, sin omisiones. Los dos fallos de ruta de `test2.grc` también están presentes en `HEAD`; los cambios locales de ese grafo no se incluyeron en el commit. No se declara aprobada la suite global ni se corrigen aquí esos fallos ajenos al alcance.

## 5. Límites y revisión del profesor

- Una prueba de software no verifica audición en los parlantes, drivers RTL-SDR, recepción física ni calidad de la antena.
- El raw no demuestra por sí solo sample rate, frecuencia de adquisición o parámetros del transmisor. Se usaron los metadatos documentados del curso y no se incorporaron grabaciones a Git.
- No se midió respuesta RF calibrada ni se certificó recepción FM stereo/RDS. Tampoco se verificó la disponibilidad de cada archivo en Google Drive, solo los archivos locales usados en las pruebas.
- La revisión cubre veracidad e implementación del laboratorio solicitado, no aprueba por el profesor una introducción pendiente ni elimina `status: draft`.

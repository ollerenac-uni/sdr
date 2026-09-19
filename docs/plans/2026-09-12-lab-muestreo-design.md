# Guía de laboratorio: muestreo, FFT, decimación e interpolación

**Fecha:** 2026-09-12
**Estado:** diseño aprobado, sin implementar
**Asociada a:** Sesión 01 — Introducción a la Radio Definida por Software

## Problema que resuelve

El alumno que llega a esta guía ya sabe conectar bloques en GNU Radio Companion: sources,
sinks y bloques de procesamiento. Lo que no tiene asentado es la aritmética que los
gobierna, que es donde se atasca casi todo el mundo al empezar en SDR:

- la relación entre frecuencia de muestreo, tiempo y número de muestras,
- el periodo de una señal contado en muestras,
- qué significa el tamaño de FFT que se escribe en un sink del GUI.

La Parte A del laboratorio de la Sesión 01 lleva al alumno del bit al número con `xxd` y
`od`, y establece el formato `cu8` con su cero en 127.5. **No menciona el tiempo en ningún
momento.** Imprime una muestra por línea pero nunca dice en qué instante ocurrió esa línea
ni cuántas líneas son un milisegundo. El tamaño de FFT no aparece.

Esta guía llena ese hueco y, con las mismas herramientas, extiende la destreza al eje que
falta.

## Ubicación y alcance

Archivo hermano dentro de la carpeta de la Sesión 01, no una sección nueva de `index.md`:

```
docs/sessions/01-introduccion-sdr/laboratorio-muestreo.md
```

Razón: `index.md` está en revisión del profesor con sus 19 figuras ya numeradas. Añadir
contenido dentro reabre esa revisión sobre un documento que crece. Un archivo hermano deja
`index.md` congelado e intacto, y la guía numera sus figuras desde 1 sin desplazar nada.

Entrada de `nav` anidada bajo la Sesión 01.

### Consecuencia sobre la prueba de numeración

`tests/test_numeracion_figuras.py` recorre `docs/sessions/*/index.md`. Ese glob codifica el
supuesto «una sesión es un archivo», que esta guía rompe: sus figuras quedarían sin la
protección que exige AGENTS.md.

**Decisión:** ampliar el glob a `docs/sessions/*/*.md` como parte de la implementación, de
modo que cada archivo se valide por separado y cada uno numere sus figuras desde 1.

## Hechos verificados

Todo dato de esta sección se comprobó antes de escribirlo, según la regla de AGENTS.md.

### Tasas de muestreo que admite el RTL-SDR

Desensamblado de `rtlsdr_set_sample_rate` en `~/radioconda/lib/librtlsdr.so.2`, que es el
binario exacto que ejecutarán los alumnos:

```
lea -0x36ee9(%rsi),%eax   ; fs - 225001
cmp $0x2d6517,%eax        ; > 2974999 (sin signo) -> rechaza
ja  reject
lea -0x493e1(%rsi),%eax   ; fs - 300001
cmp $0x927bf,%eax         ; <= 599999 -> rechaza
jbe reject
```

Válido: **225 001 – 300 000 Hz** y **900 001 – 3 200 000 Hz**. Todo lo demás lo rechaza el
driver con `Invalid sample rate: %u Hz`.

### El archivo del calentamiento

Tono complejo generado con NumPy, `fs` 32 kSps, `f₀` 1 kHz, amplitud 100, duración 0.1 s.
Pesa 6400 bytes, así que no depende de Google Drive.

| Magnitud | Valor | Por qué ese valor |
|---|---|---|
| `fs` | 32 kSps | 1 ms = 32 muestras = una pantalla de `od` |
| `f₀` | 1 kHz | 32 muestras por ciclo, un ciclo entero por milisegundo |
| FFT | 32 | RBW = 1000 Hz, el tono cae en el bin 1 exacto |
| Amplitud | 100 | rango de bytes 28–228, usa la escala sin recortar |

Primeras muestras medidas sobre el archivo generado:

| n | I | Q | fase |
|---|---|---|---|
| 0 | 228 | 128 | 0°, I máximo y Q en el cero |
| 8 | 128 | 228 | 90°, I en el cero y Q máximo |
| 16 | 28 | 128 | 180° |
| 24 | 127 | 28 | 270° |
| 32 | — | — | vuelve a empezar: un ciclo = 1 ms |

El cuarto de ciclo cae en la muestra 8, exacta: **los 90° entre I y Q se leen como dos
números en `od`**, y enlazan con la hélice de la Figura 9 de la Sesión 01 (§2.4), donde I y Q son las proyecciones de $e^{j2\pi f_0 t}$.

FFT de 32 puntos sobre las 32 primeras muestras: `|X[1]| = 3205.73` frente a ~1 en los
bins vecinos. El 1.7 % de energía fuera del bin 1 es ruido de cuantización por redondear a
enteros, no fuga espectral.

### Grabaciones necesarias

Las hace el profesor con el dongle. Todo idéntico salvo `fs`: `fc` 99.1 MHz, ganancia 30,
10 s, misma antena y posición.

| fs | 2.4 M ÷ fs | Driver | Tamaño | Estado |
|---|---|---|---|---|
| 2 400 000 | ÷1 | acepta | 48 MB | ya existe en `samples/` |
| 1 200 000 | ÷2 exacto | acepta | 24 MB | **grabar** |
| 300 000 | ÷8 exacto | acepta | 6 MB | **grabar** |

Se eligen por dar cociente entero con 2.4 Msps. Con cocientes no enteros (1.8 M, 1.024 M,
250 k) haría falta un *rational resampler* para comparar real contra decimado, lo que
ensucia la lección.

Las tres tasas elegidas permiten comparar directamente la grabación de 2.4 Msps con
versiones a la mitad y a un octavo de su tasa.

## Estructura

### §1 Calentamiento: el milisegundo que se puede contar

Sobre el tono sintético. No introduce ningún bloque nuevo: reutiliza la cadena de siete
bloques que el alumno ya construyó en la Parte C de la Sesión 01, cambiando `samp_rate` a
32000 y el archivo.

```
file_source -> throttle2(byte, 2*samp_rate) -> uchar_to_float -> add_const(-127.5)
            -> multiply_const(1/127.5) -> deinterleave -> float_to_complex -> time/freq sink
```

Orden fijado por `tests/test_test_flowgraph.py::test_la_cadena_completa_esta_conectada_en_orden`.

Cinco pasos, cada uno confirmando al anterior:

1. **Predecir con papel.** Cuántas muestras hay en 1 ms, cuántas en 1 s, cuánto dura un
   archivo de 6400 bytes.
2. **Contar en `od`.** `od -Ad -tu1 -w2 -N64 -v` imprime 32 líneas. Coinciden con lo
   predicho.
3. **Encontrar los 90°.** Localizar la muestra de I máximo y la de Q máximo: 8 muestras de
   32, un cuarto de ciclo. La cuadratura medida en bytes.
4. **Ver el mismo milisegundo en GNU Radio.** El Time Sink dibuja un ciclo por milisegundo.
   Se comparan alturas con los bytes de `od`, pasando por el `−127.5` y el `/127.5`.
   En n=24 `od` da `I=127` y en n=8 `I=128`, aunque el coseno vale cero en ambos. En n=8 la
   cuenta da 127.5 exacto y NumPy redondea al par; en n=24 un residuo de −1.8e-14 la deja por
   debajo y sale 127. La guía lo dice.
5. **Tocar el tamaño de FFT.** Con 32, una raya limpia en 1 kHz. Con 1024, la raya sigue
   pero la ventana pasa a durar 32 ms. La regla se lee en los dos sentidos: `RBW = fs/N` y
   `duración = N/fs`.

El paso 4 debe explicar que la división por 127.5 es la que convierte el 228 de `od` en el
0.788 del Time Sink. Sin eso, el alumno ve dos números distintos y supone que uno está mal.

La fuga espectral **no** entra aquí: ya vive en la Sesión 02 §5.

### §2 Las mismas reglas donde no se pueden contar

La grabación real de 2.4 Msps. Un milisegundo son 2400 muestras y el conteo a mano deja de
ser viable: la fórmula sustituye al conteo. Con FFT de 1024, RBW 2343.75 Hz y una ventana
que dura 426.7 µs.

### §3 Tres tasas de muestreo reales

2.4 → 1.2 → 0.3 Msps. A igual tamaño de FFT, qué cambia: ancho de banda visible, RBW y
peso del archivo.

### §4 Decimación en software

Bajar la grabación de 2.4 Msps a 1.2 (÷2) y a 300 k (÷8). El contraste que sostiene la
sección: `Keep 1 in N` contra `Decimating FIR Filter`. Mismo factor, mismo archivo, dos
espectros distintos. El aliasing se ve en vez de enunciarse.

### §5 El careo: real contra decimado

Grabación real a 300 kSps contra la de 2.4 Msps decimada a 300 kSps.

**Límite que la guía debe declarar en voz alta:** las capturas son secuenciales y la emisora
cambia de contenido entre una y otra, así que la comparación es cualitativa, nunca muestra a
muestra. Además la grabación de 300 k trae el filtro analógico y el diezmado interno del
RTL-SDR, no el FIR de GNU Radio. Comparar bordes de filtro y suelo de ruido, sí; comparar
bytes, no.

### §6 Interpolación

El camino inverso, 300 k → 2.4 M. El espectro no recupera nada: aparece ancho de banda
vacío. Interpolar no inventa información.

## Decisiones

| Decisión | Razón |
|---|---|
| Archivo hermano, no sección de `index.md` | Congela la revisión en curso de la Sesión 01 |
| Ampliar el glob del test a `docs/sessions/*/*.md` | El archivo nuevo quedaría sin protección de numeración |
| Calentamiento con archivo sintético | El alumno debe poder **predecir** los bytes; con FM real son impredecibles |
| Versionar el generador, no el `.cu8` | `.gitignore` cubre `*.cu8`, y generarlo enseña qué hay dentro |
| Sin bloques nuevos en el calentamiento | La dificultad es aritmética, no de conexión de bloques |
| fs = 32 kSps | Único orden de magnitud donde 1 ms cabe en una pantalla de `od` |
| Grabar 1.2 Msps y 300 kSps | Únicos cocientes enteros de 2.4 Msps que el driver acepta |
| La fuga espectral se queda en S02 §5 | Ya está explicada ahí; repetirla duplica |

## Trabajo que depende del profesor

- Grabar `1 200 000` y `300 000` Sps con los demás parámetros idénticos a la grabación
  oficial, subirlas a la carpeta de Drive y dar nombre, `fc`, `fs`, ganancia, antena,
  duración, formato y SHA-256 de cada una.

Conviene que salgan de la misma sesión con el dongle que las tres capturas de ganancia que
espera la Sesión 02.

La guía se escribe sin esperar a esas grabaciones: §1, §2, §4 y §6 parten del tono sintético
o de la grabación oficial de 2.4 Msps. Solo §3 y §5 las necesitan.

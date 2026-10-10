---
title: "Laboratorio #2 — Demodulador FM en GNU Radio"
session: 2
description: "Receptor FM mono desde la captura CU8 oficial a 2.4 MS/s, con espectro, waterfall y entrada RTL-SDR opcional."
---

# Laboratorio #2 — Demodulador FM en GNU Radio

- El laboratorio utiliza la misma captura de 2.4 MS/s que S01 y la teoría de S02.
- La cadena selecciona la banda central y entrega audio mono a 48 kS/s.
- El estudiante observa la captura mediante un espectro y un waterfall. No necesita un dongle.

## Objetivos

1. Reconstruir muestras complejas desde bytes CU8.
2. Calcular las tasas de entrada, canal y audio.
3. Relacionar espectro y waterfall con los metadatos de la captura.
4. Explicar cómo el giro entre muestras permite demodular FM.
5. Implementar y verificar la cadena en GNU Radio Companion.

El diseño detallado de los filtros queda para S03 y S04. Aquí se utilizan bloques con parámetros conocidos y límites explícitos.

## Archivos y requisitos

| Recurso | Ubicación | Uso |
|---|---|---|
| Grafo de referencia | `gnuradio-flowgraphs/receptor_fm_99p1_2p4Msps.grc` | Comparar parámetros y conexiones. |
| Captura oficial | `samples/fm_99p1MHz_2p4Msps_g30.cu8` | I/Q a 2.4 MS/s, con referencia RF de 99.1 MHz. |
| GNU Radio Companion | Equipo local | Construir y ejecutar el grafo. |
| Parlantes o audífonos | Equipo local | Escuchar audio mono a 48 kS/s. |

- Las grabaciones se distribuyen por la [carpeta de muestras](https://drive.google.com/drive/folders/1tP8u1tQZDnvi_-ZAxZ3J8tehdKwi92an?usp=drive_link), fuera de Git.
- La [sesión 1](../01-introduccion-sdr/index.md#descargar-la-grabacion) explica la descarga de la captura oficial.
- El grafo utiliza `../samples/fm_99p1MHz_2p4Msps_g30.cu8`, porque se ejecuta desde `gnuradio-flowgraphs/`.
- La fuente RTL-SDR queda desactivada. Solo se utiliza en la extensión opcional.

## 1. Seguir las tasas antes de conectar bloques

```text
Archivo CU8: 4 800 000 bytes/s
    → reconstrucción I/Q: 2.4 MS/s complejas
    → Rational Resampler, 2/25: 192 kS/s complejas
    → WBFM Receive, audio decimation 4: 48 kS/s reales
    → volumen → Audio Sink
```

| Punto | Tipo de item | Tasa de items |
|---|---|---:|
| File Source y Throttle | Un byte I o Q | 4 800 000 items/s |
| Después de UChar to Float, antes de Deinterleave | Un float I o Q | 4 800 000 items/s |
| Cada salida de Deinterleave | Un float I o un float Q | 2 400 000 items/s |
| Float to Complex | Una muestra I+jQ | 2.4 MS/s |
| Rational Resampler | Una muestra compleja | 192 kS/s |
| WBFM Receive | Una muestra real de audio | 48 kS/s |

- I y Q corresponden al mismo instante. Dos bytes CU8 forman una muestra compleja.
- El Throttle de tipo Byte utiliza `Sample Rate = 2*samp_rate`.
- Throttle limita el ritmo de suministro. No cambia los valores, no filtra ni convierte el sampling rate de la señal.

$$
f_{s,\mathrm{canal}}=2400000\frac{2}{25}=192000\ \mathrm{S/s},\qquad
f_{s,\mathrm{audio}}=\frac{192000}{4}=48000\ \mathrm{S/s}.
$$

??? example "Comprobación 1.1 — Throttle incorrecto"

    - **Datos:** la entrada es Byte y cada muestra I/Q requiere dos bytes.
    - **Cálculo:** un Throttle de 2400000 bytes/s suministraría $2400000/2=1200000$ muestras complejas por segundo de reloj.
    - **Resultado:** sería la mitad del ritmo necesario para reproducir esta captura en tiempo real.
    - **Interpretación:** el archivo sigue representando muestras adquiridas a 2.4 MS/s. El límite de suministro no cambia sus metadatos.
    - **Consecuencia:** Audio Sink puede sufrir underruns, es decir, falta de datos para su reloj. Pueden aparecer cortes o pausas.
    - **Límite:** no se garantiza un tono a media frecuencia. Audio Sink permanece configurado a 48 kS/s.

??? example "Comprobación 1.2 — Tamaño y duración"

    - **Datos:** la captura tiene 48 000 000 bytes CU8 y $f_s=2400000$ S/s.
    - **Muestras:** $N=48000000/2=24000000$ parejas I/Q.
    - **Duración:** $T=N/f_s=24000000/2400000=10$ s.
    - **Interpretación:** el tamaño permite contar muestras. Sin el sampling rate documentado, no permite calcular su duración.

## 2. Reconstruir I/Q desde CU8

1. El estudiante crea un grafo con salida `QT GUI` y lo guarda en `gnuradio-flowgraphs/`.
2. Asigna un ID propio, como `lab02_fm_estudiante`, distinto del ID de la referencia.
3. Define `samp_rate = 2400000`, `freq = 99.1e6` y `volume = 0.2`.
4. Conecta los siete bloques de la ruta CU8 en el orden de la tabla.

| Bloque | Parámetros | Operación |
|---|---|---|
| File Source | Byte; Repeat: Yes; ruta relativa de la captura | Leer I,Q,I,Q,… |
| Throttle | Byte; Sample Rate: `2*samp_rate` | Limitar el suministro. |
| UChar to Float | Valores predeterminados | Representar cada byte unsigned como float. |
| Add Const | Float; Constant: `-127.5` | Centrar cada componente. |
| Multiply Const | Float; Constant: `1/127.5` | Normalizar cada componente. |
| Deinterleave | Float; Streams: 2; Block Size: 1 | Separar I y Q alternados. |
| Float to Complex | Vector Length: 1 | Reconstruir I+jQ. |

- La salida 0 de Deinterleave entra en el puerto real 0 de Float to Complex.
- La salida 1 entra en el puerto imaginario 1. Los dos puertos representan el mismo índice de muestra.
- Para bytes $u_I[n]$ y $u_Q[n]$, la conversión es:

$$z[n]=\frac{u_I[n]-127.5}{127.5}+j\frac{u_Q[n]-127.5}{127.5}.$$

??? note "Para profundizar"

    - Un byte 0 produce −1; un byte 255 produce +1.
    - Los códigos 127 y 128 producen valores pequeños de signos opuestos, no cero exacto.
    - Que I y Q estén entre −1 y +1 no implica $|z|\leq1$. Por ejemplo, $|-1+j|=\sqrt{2}$.
    - La conversión conserva los códigos disponibles, con redondeo numérico. No recupera información perdida por cuantización o clipping previo.
    - Estos bloques no agregan metadatos RF al archivo raw.

??? example "Comprobación 2.1 — File Source no debe ser Complex"

    - **Formato disponible:** CU8 contiene dos bytes unsigned por muestra compleja.
    - **Tipo Complex:** en esta ruta, GNU Radio espera dos float32, equivalentes a ocho bytes por muestra.
    - **Error:** seleccionar Complex reinterpreta bytes con un formato equivocado. No ejecuta la conversión de la tabla.
    - **Solución:** leer Byte y reconstruir I/Q mediante los siete bloques indicados.

## 3. Reducir la tasa y observar el canal

1. Se conecta Float to Complex a Rational Resampler.
2. Se configura entrada y salida Complex, `Interpolation = 2`, `Decimation = 25`, `Taps = []` y `Fractional BW = 0`.
3. Se añaden los tres visores de la tabla como ramas de observación.

| Visor | Entrada | Bandwidth | FFT y ventana | Intervalo RF nominal |
|---|---|---|---|---|
| QT GUI Frequency Sink, RF | Antes del resampler | `samp_rate` | 4096, Hann | [97.9, 100.3) MHz |
| QT GUI Waterfall Sink, RF | Antes del resampler | `samp_rate` | 4096, Hann | [97.9, 100.3) MHz |
| QT GUI Frequency Sink, Canal | Después del resampler | `192000` | 1024, Blackman-Harris | [99.004, 99.196) MHz |

- Los tres visores utilizan `Type = Complex` y `Center Frequency = freq`.
- El resampler filtra y cambia la tasa. No toma simplemente una de cada 25 muestras.
- La cadena permite una práctica de audio mono. Los 192 kS/s no garantizan conservar toda emisión FM completa y sin distorsión.

**Lectura de los visores:**

- **RF:** las bandas aparecen respecto a 99.1 MHz. La separación entre bins es $2400000/4096=585.9375$ Hz.
- **Waterfall:** el color muestra potencia y su variación temporal. Una línea estable no identifica por sí sola un transmisor o una interferencia.
- **Canal:** la nueva banda es más estrecha por el filtro y la reducción de tasa. La separación entre bins es $192000/1024=187.5$ Hz.

??? note "Para profundizar"

    - En GNU Radio 3.10.12, taps vacíos y Fractional BW de cero solicitan el diseño predeterminado con ancho fraccional 0.4.
    - Para esta reducción, la banda de paso nominal llega aproximadamente a ±76.8 kHz, con transición hacia ±96 kHz.
    - No es un filtro ideal de corte abrupto. El diseño detallado se estudiará después.
    - El extremo RF derecho no representa un bin adicional independiente del borde izquierdo de Nyquist.
    - Los visores no están calibrados en dBm. Sus normalizaciones no necesariamente coinciden con las figuras Colab.
    - El waterfall de referencia inicia con Intensity Min de −100 y Max de −20. Es una escala de visualización ajustable, no una medición absoluta.
    - Update Period de 0.10 s controla la actualización del visor. No significa que cada fila replique el promedio temporal de Colab.
    - Fuente del filtro: [rational_resampler_impl.cc](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-filter/lib/rational_resampler_impl.cc).
    - Fuente del visor: [QT GUI Waterfall Sink](https://wiki.gnuradio.org/index.php/QT_GUI_Waterfall_Sink).

??? example "Comprobación 3.1 — Cambiar freq con un archivo fijo"

    - **Datos:** una componente aparece en +250 kHz respecto a 99.1 MHz.
    - **RF correcta:** $99.1+0.250=99.35$ MHz.
    - **Etiqueta incorrecta:** escribir 99.5 MHz en el visor produce $99.5+0.250=99.75$ MHz, sin modificar las muestras.
    - **Interpretación:** cambiar etiquetas no sintoniza otra emisora. S04 explicará cómo desplazar y seleccionar un canal fuera del centro.

## 4. Del giro entre muestras al audio FM

- La [teoría de 6.5](index.md#65-como-permite-fm-recuperar-el-audio) muestra cómo el mensaje modifica el giro entre muestras.
- WBFM Receive recibe la banda central seleccionada, en formato complejo, y entrega audio mono real.
- Se configura **`Quadrature Rate = 192000`** y **`Audio Decimation = 4`**.
- Después se conecta Multiply Const de tipo Float, con constante `volume`.
- La salida entra en Audio Sink: una entrada, `Sample Rate = 48000` y `OK to Block = No`.
- `volume` utiliza QT GUI Range: mínimo 0, máximo 1, paso 0.05 y valor inicial 0.2.

??? note "Para profundizar"

    - Para $z[n]=Ae^{j\theta[n]}$, con $A>0$, el producto es $z[n]z^*[n-1]=A^2e^{j(\theta[n]-\theta[n-1])}$.
    - Si el giro verdadero es menor que media vuelta, el argumento principal permite estimar la frecuencia media durante ese intervalo:

    $$\widehat f[n]=\frac{f_s}{2\pi}\arg\left(z[n]z^*[n-1]\right).$$

    - Aquí $f_s=192000$ S/s. El resultado se expresa en Hz, no en amplitud de audio.
    - Para FM centrada, dividir por la desviación de referencia estima el mensaje medio del intervalo antes del filtrado de audio.
    - El ángulo principal no distingue giros separados por vueltas completas. Una muestra de magnitud nula tampoco proporciona una fase definida.
    - Quadrature Demod implementa el producto conjugado y el argumento, multiplicados por una ganancia.
    - Fuente: [quadrature_demod_cf_impl.cc](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/lib/quadrature_demod_cf_impl.cc).
    - WBFM Receive incluye discriminación de fase, filtrado de audio, decimación y de-emphasis.
    - Utiliza desviación nominal de 75 kHz y ganancia $G=f_s/(2\pi\,75000)\approx0.4074$.
    - Esa referencia no demuestra la desviación real de una emisora.
    - Con mensaje 0.5 y desviación de 75 kHz, la frecuencia relativa es 37 500 Hz.
    - Su giro es aproximadamente 1.2272 rad. Multiplicar por $G$ produce 0.5 antes de los filtros.
    - Fuente: [wfm_rcv.py](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/wfm_rcv.py).
    - De-emphasis compensa el realce de altas frecuencias de transmisión. La constante predeterminada del bloque es 75 µs.
    - Esa configuración no garantiza coincidencia automática con el transmisor local.
    - Fuente: [fm_emph.py](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/fm_emph.py).
    - No se añade decoder stereo ni decoder RDS. Escuchar audio no demuestra que esas partes de la emisión se hayan recuperado.

??? example "Comprobación 4.1 — Tasa de Audio Sink"

    - **Datos:** el demodulador recibe 192 000 muestras complejas/s y utiliza decimación de audio 4.
    - **Cálculo:** $192000/4=48000$ muestras reales/s.
    - **Tipo:** son valores de audio. No contienen otra pareja I/Q que deba dividirse entre dos.
    - **Interpretación:** Audio Sink utiliza la tasa representada por esas muestras. Otra configuración no corrige metadatos incorrectos de la captura.

## 5. Ejecutar y registrar observaciones

1. Se comprueban archivo, ruta relativa, sampling rate e ID propio del grafo.
2. Se comprueba que la ruta CU8 está activa y Soapy RTLSDR Source está desactivado.
3. Se comparan parámetros y conexiones con la referencia de 2.4 MS/s.
4. Se ejecuta con F6 y se aumenta el volumen gradualmente.
5. Se registra cada visor, con sus ejes y su escala. Se compara el waterfall con la sección 6.3 de la teoría.
6. Se explica por separado qué muestra el espectro y qué se escucha en el audio.

- Repeat de valor Yes vuelve al inicio del archivo. Puede aparecer una discontinuidad; no es una adquisición nueva.
- La cadena debe producir muestras complejas a 192 kS/s y audio real a 48 kS/s.
- La compilación no garantiza una calidad de recepción determinada. La audición y las observaciones se documentan por separado.

??? note "Variante anterior: captura a 2.048 MS/s"

    - Se conserva `gnuradio-flowgraphs/receptor_fm_99p1_2p048Msps.grc` con su ID independiente.
    - Esa referencia utiliza `../samples/fm_99p1MHz_2p048Msps_g30.cu8`, `samp_rate = 2048000` y resampler 3/32.
    - Su Throttle de bytes utiliza $2(2048000)=4096000$ items/s.
    - El resultado sigue siendo $2048000(3/32)=192000$ S/s. Las etapas de audio conservan sus parámetros.
    - Su intervalo nominal es [98.076, 100.124) MHz. No contiene necesariamente completas las bandas cercanas a los bordes.
    - La referencia anterior no incluye el nuevo waterfall. El archivo no debe renombrarse para hacerlo pasar por la captura oficial de 2.4 MS/s.
    - Son grabaciones diferentes. No se atribuyen sus diferencias de contraste únicamente al sampling rate.

## 6. Extensión opcional con RTL-SDR

1. Se detiene el grafo antes de cambiar la fuente.
2. Se desactivan los siete bloques de la ruta CU8, desde File Source hasta Float to Complex. El control de volumen permanece activo.
3. Se activa Soapy RTLSDR Source con salida `Complex Float32`, `Sample Rate = samp_rate` y `Center Frequency = freq`.
4. Se conservan ganancia manual de 30 dB y AGC desactivado, como en la referencia.
5. Su salida se conecta al resampler, al Frequency Sink RF y al Waterfall Sink RF.
6. Se revisa la [configuración del RTL-SDR](../../setup/rtl-sdr.md) y se ejecuta nuevamente.

- La fuente de hardware proporciona el ritmo de adquisición. No se añade Throttle a esa ruta.
- En esta variante, `freq` sí configura el receptor. Con el archivo fijo solo modifica las etiquetas de los visores.
- Se pueden recibir señales y niveles distintos. Cambiar de fuente no equivale a cambiar únicamente el procesamiento.

??? example "Comprobación 6.1 — Una fuente activa"

    - **Entrada:** el resampler recibe un flujo complejo. Dos fuentes conectadas no forman automáticamente una suma ni un selector.
    - **Selección:** se utiliza Float to Complex o Soapy, pero no ambas rutas activas.
    - **Tasa:** la nueva referencia configura ambas alternativas a 2.4 MS/s y utiliza resampler 2/25.
    - **Interpretación:** tasas iguales no implican muestras iguales. La fuente en vivo adquiere otros datos.

## 7. Diagnóstico breve

| Síntoma | Revisión inicial |
|---|---|
| El archivo no abre | Nombre, ubicación en samples y ruta relativa. |
| Hay underruns o cortes | Throttle de bytes a `2*samp_rate`, tasas y carga del equipo. |
| El audio o los tiempos no corresponden | Sampling rate documentado de la captura, no solo el rótulo del visor. |
| Hay espectro, pero no audio | Quadrature Rate, decimación 4, Audio Sink a 48000, volumen y salida del sistema. |
| El waterfall tiene un solo color | Intensidad mínima y máxima; presencia de datos; Bandwidth y tipo Complex. |
| La señal parece ruido | Tipo Byte, normalización y orden I/Q. |
| Las etiquetas RF parecen desplazadas | Correspondencia entre `freq` y los metadatos. |
| Soapy no abre el dongle | Volver a la ruta de archivo y revisar el dispositivo por separado. |

## Entrega

1. Grafo `.grc` con ID propio, rutas relativas y sin grabaciones añadidas a Git.
2. Tabla de tasas con sus cálculos, distinguiendo bytes, componentes, muestras complejas y audio.
3. Capturas de los tres visores con ejes y escalas. En el waterfall se señalan una banda y una línea estable.
4. Explicación en viñetas de conversión CU8, resampling, demodulación y volumen. Se identifica dónde la salida deja de ser I/Q.
5. Justificación de por qué cambiar las etiquetas RF no sintoniza otra señal del archivo.
6. Si se utiliza la variante anterior o el dongle, descripción de los cambios y los metadatos correspondientes.

## Lecturas y referencias

- [Teoría de S02: lectura de una captura SDR](index.md#6-leer-una-captura-sdr-real).
- [GNU Radio: Rational Resampler](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-filter/lib/rational_resampler_impl.cc).
- [GNU Radio: Quadrature Demod](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/lib/quadrature_demod_cf_impl.cc).
- [GNU Radio: WBFM Receive](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/wfm_rcv.py).
- [GNU Radio: FM de-emphasis](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/fm_emph.py).
- [GNU Radio: QT GUI Waterfall Sink](https://wiki.gnuradio.org/index.php/QT_GUI_Waterfall_Sink).

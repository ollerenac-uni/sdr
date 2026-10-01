---
title: "Laboratorio #2 — Demodulador FM en GNU Radio"
session: 2
description: "Implementación de un receptor FM mono, con una captura CU8 a 2.048 MS/s y una fuente RTL-SDR opcional."
status: draft
---

# Laboratorio #2 — Demodulador FM en GNU Radio

Esta guía recupera el laboratorio de receptor FM que acompañaba la versión anterior de la sesión. Conserva su cadena principal: captura I/Q a 2.048 MS/s, resampler 3/32, `WBFM Receive` a 192 kS/s y audio mono a 48 kS/s.

## Objetivos

Al finalizar, el estudiante será capaz de:

1. Reconstruir muestras complejas a partir de un archivo CU8, sin confundir bytes con muestras I/Q.
2. Calcular y configurar las tasas de las etapas de recepción y de audio.
3. Relacionar los ejes de los visores con la frecuencia central y con la tasa de cada etapa.
4. Explicar cómo el cambio de fase entre muestras permite demodular FM.
5. Implementar la cadena en GNU Radio Companion y distinguir qué operaciones realiza cada bloque.

La construcción no requiere diseñar los taps de los filtros desde cero. Los bloques se utilizan como sistemas cuyas entradas, salidas y parámetros deben entenderse. El análisis detallado de sus filtros queda para el tema de sistemas y filtrado.

## Archivos y requisitos

| Recurso | Ubicación | Uso |
|---|---|---|
| [Grafo de referencia](https://github.com/ollerenac-uni/sdr/blob/main/gnuradio-flowgraphs/receptor_fm_99p1_2p048Msps.grc) | `sdr/gnuradio-flowgraphs/receptor_fm_99p1_2p048Msps.grc` | Comparar parámetros y conexiones. |
| `fm_99p1MHz_2p048Msps_g30.cu8` | `sdr/samples/` | Captura I/Q centrada en 99.1 MHz a 2.048 MS/s. |
| GNU Radio Companion | Equipo local | Construir y ejecutar el flowgraph. |
| Parlantes o audífonos | Equipo local | Escuchar la salida a 48 kS/s. |

- **Distribución:** las grabaciones se entregan fuera de Git, en la [carpeta de muestras del curso](https://drive.google.com/drive/folders/1tP8u1tQZDnvi_-ZAxZ3J8tehdKwi92an?usp=drive_link). Se consulta también la [descarga de muestras de la sesión 1](../01-introduccion-sdr/index.md#descargar-la-grabacion).
- **Ruta del archivo:** el `.grc` espera `../samples/fm_99p1MHz_2p048Msps_g30.cu8`. La ruta se interpreta desde `gnuradio-flowgraphs/`, donde se ejecuta el grafo. Una ruta absoluta del equipo del profesor no sirve en otro equipo.
- **Dos capturas diferentes:** la subsección 6.7 de la teoría utiliza una captura a **2.4 MS/s**. Este laboratorio conserva la de **2.048 MS/s**. El sample rate correcto procede de los metadatos, no del valor que se escriba en el visor ni de renombrar el archivo.
- **Sin hardware obligatorio:** la ruta principal utiliza el archivo. El dongle se reserva para una extensión opcional.

## 1. Seguir las tasas antes de conectar bloques

La cadena principal es:

```text
Archivo CU8: bytes I,Q alternados
        ↓  4 096 000 bytes/s
Conversión CU8 → I+jQ
        ↓  2.048 MS/s complejas
Rational Resampler: interpolación 3, decimación 32
        ↓  192 kS/s complejas
WBFM Receive: audio decimation 4
        ↓  48 kS/s reales, audio mono
Control de volumen → Audio Sink
```

| Punto de la cadena | Tipo de un item | Tasa de items |
|---|---|---:|
| `File Source` y `Throttle` | Un byte I o Q | 4 096 000 items/s |
| Después de `UChar to Float`, antes de `Deinterleave` | Un float I o Q | 4 096 000 items/s |
| Cada salida de `Deinterleave` | Un float I o un float Q | 2 048 000 items/s |
| `Float to Complex` | Una muestra I+jQ | 2.048 MS/s |
| Salida del `Rational Resampler` | Una muestra compleja | 192 kS/s |
| Salida de `WBFM Receive` | Una muestra real de audio | 48 kS/s |

- **Pareja, no dos instantes:** I y Q de una muestra corresponden al mismo índice. Dos bytes CU8 forman una muestra compleja, como se explicó en las subsecciones 2 y 6.7.
- **Ritmo de reproducción:** el `Throttle` es de tipo `Byte`, con `Sample Rate = 2*samp_rate`. Así permite pasar aproximadamente $2(2048000)=4096000$ bytes por segundo de reloj. No convierte el formato, no interpola y no filtra.
- **Tasa de señal frente a reloj del computador:** $f_s$ describe el tiempo que representan las muestras. `Throttle` limita cuánto tarda el programa en entregarlas; no modifica los valores ni convierte una captura a otro sample rate. En esta ruta, `Audio Sink` tiene `OK to Block = No`, como en el grafo de referencia.

El resampler establece la relación entre las tasas complejas:

$$
f_{s,\mathrm{canal}}=f_{s,\mathrm{entrada}}\frac{L}{D}
=2048000\frac{3}{32}=192000\ \text{S/s}.
$$

El bloque de recepción entrega audio con otra decimación:

$$
f_{s,\mathrm{audio}}=\frac{f_{s,\mathrm{canal}}}{D_a}
=\frac{192000}{4}=48000\ \text{S/s}.
$$

??? example "Comprobación 1.1 — Throttle a samp_rate en una ruta Byte"

    - **Cálculo:** $2048000$ bytes/s permiten formar $2048000/2=1024000$ muestras I/Q por segundo de reloj, la mitad de la tasa necesaria para reproducir esta captura en tiempo real.
    - **Qué no cambia:** la secuencia almacenada sigue representando muestras tomadas a 2.048 MS/s. La división anterior describe el suministro al programa, no una nueva adquisición.
    - **Consecuencia posible:** al mantenerse `Audio Sink` a 48 kS/s, llega audio insuficiente para su reloj; pueden aparecer underruns, cortes o pausas. No se garantiza que la tarjeta reproduzca un tono a la mitad de su frecuencia: su tasa de audio sigue configurada a 48 kS/s.

??? example "Comprobación 1.2 — tamaño de un segundo de captura"

    - **Muestras:** en un segundo hay $N=f_sT=2048000(1)=2048000$ parejas I/Q.
    - **Bytes:** cada pareja ocupa dos bytes; por tanto, $2N=4096000$ bytes. No se aplica este cálculo a un archivo `complex64`, que utiliza otro tamaño de item.
    - **Duración:** una captura CU8 de 40960000 bytes contiene $40960000/2=20480000$ muestras. Con estos metadatos, $T=N/f_s=10$ s. El tamaño por sí solo no permite descubrir $f_s$.

## 2. Reconstruir I/Q desde CU8

El estudiante crea un flowgraph con salida `QT GUI`, lo guarda en `gnuradio-flowgraphs/` y asigna un `ID` propio, por ejemplo `lab02_fm_estudiante`. Se definen `samp_rate = 2048000`, `freq = 99.1e6` y `volume = 0.2`.

La primera parte se construye en este orden:

| Bloque | Parámetro principal | Operación |
|---|---|---|
| `File Source` | Output Type: `Byte`; Repeat: `Yes`; ruta relativa indicada arriba | Leer I,Q,I,Q,... sin interpretar los bytes como floats. |
| `Throttle` | Type: `Byte`; Sample Rate: `2*samp_rate` | Limitar el suministro del archivo. |
| `UChar to Float` | Valor por defecto | Representar cada byte unsigned como float. |
| `Add Const` | Type: `Float`; Constant: `-127.5` | Desplazar el centro del formato a cero. |
| `Multiply Const` | Type: `Float`; Constant: `1/127.5` | Normalizar cada componente. |
| `Deinterleave` | Type: `Float`; Number of Streams: `2`; Block Size: `1` | Separar items alternados en I y Q. |
| `Float to Complex` | Vector Length: `1` | Unir ambas componentes en una muestra compleja. |

- **Conexiones iniciales:** los primeros cinco bloques se conectan en cadena a `Deinterleave`.
- **Puerto I:** la salida 0 de `Deinterleave` se conecta a la entrada real 0 de `Float to Complex`.
- **Puerto Q:** la salida 1 se conecta a la entrada imaginaria 1. No se conectan ambos flujos al mismo puerto.
- **Conversión:** si los bytes son $u_I[n]$ y $u_Q[n]$, se obtiene

$$
z[n]=\frac{u_I[n]-127.5}{127.5}+j\frac{u_Q[n]-127.5}{127.5}.
$$

- **Extremos:** un byte 0 se representa como −1 y uno 255 como +1. Como el centro 127.5 queda entre dos códigos enteros, 127 y 128 producen valores pequeños de signos opuestos, no cero exacto.
- **Magnitud compleja:** que I y Q estén entre −1 y +1 no implica $|z|\leq1$. Por ejemplo, $-1+j$ tiene magnitud $\sqrt{2}$. La magnitud se calcula con $\sqrt{I^2+Q^2}$, como en la subsección 2.2.

??? example "Comprobación 2.1 — por qué no se declara Complex el File Source"

    - **Formato esperado por ese tipo:** `Complex` en esta ruta de GNU Radio corresponde a dos float32, con ocho bytes por muestra compleja.
    - **Formato disponible:** CU8 utiliza dos bytes, uno unsigned para I y otro para Q. No contiene floats almacenados.
    - **Error:** escoger `Complex` no ejecuta la conversión anterior; reinterpreta grupos de ocho bytes con un formato equivocado. La reconstrucción requiere leer bytes y aplicar los bloques de la tabla.

??? example "Comprobación 2.2 — qué información conserva la conversión"

    - **Valores disponibles:** cada componente de CU8 tiene 256 códigos posibles. La transformación asigna a cada código un valor float distinto, con el redondeo numérico habitual.
    - **Qué no se recupera:** se conservan los códigos de la captura, pero no se crean niveles de amplitud que el archivo nunca tuvo. Los bits perdidos por cuantización o clipping previo no reaparecen al normalizar.
    - **Tiempo y referencia:** estos bloques tampoco incorporan una frecuencia central ni un sample rate al archivo raw. Esos datos siguen dependiendo de la documentación de la captura.

## 3. Reducir la tasa y observar el canal

Se añade `Rational Resampler`, con entrada y salida `Complex`, `Interpolation = 3`, `Decimation = 32`, `Taps = []` y `Fractional BW = 0`. Su entrada se conecta a `Float to Complex`.

- **No es tomar una de cada 32 muestras:** el bloque realiza resampling con filtrado y relación 3/32. El filtro es necesario para controlar el aliasing al reducir la tasa, como mostró la subsección 4.7.
- **Configuración automática:** en GNU Radio 3.10.12, taps vacíos y `Fractional BW = 0` solicitan el filtro predeterminado, con ancho fraccional 0.4. Para esta reducción, su banda de paso de diseño llega aproximadamente a ±76.8 kHz y la transición hasta ±96 kHz. No es un filtro ideal de corte abrupto. [Implementación del resampler](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-filter/lib/rational_resampler_impl.cc).
- **Límite del ejemplo:** 192 kS/s dan un intervalo nominal de 192 kHz, no una garantía de conservar todo el espectro de cualquier emisión FM. Este montaje es una práctica de recepción mono; no certifica fidelidad de una señal de radiodifusión completa.

Se conectan dos `QT GUI Frequency Sink`, ambos de tipo `Complex`, FFT de 1024 puntos y `Center Frequency = freq`:

| Visor | Entrada | Bandwidth | Intervalo RF nominal con $f_c=99.1$ MHz |
|---|---|---:|---|
| RF | Antes del resampler | `samp_rate` | 98.076 a 100.124 MHz |
| Canal | Después del resampler | `192000` | 99.004 a 99.196 MHz |

- **Qué se debe observar en RF:** el cero de baseband corresponde a 99.1 MHz. Los desplazamientos a izquierda y derecha se interpretan con $f_{\mathrm{RF}}=f_c+f_{\mathrm{BB}}$.
- **Qué se debe observar en Canal:** cambia el ancho del eje porque cambia el sample rate. También se modificó la señal mediante el filtro; no se trata solo de ampliar una zona del dibujo original.
- **Extremos del eje:** los valores de la tabla son bordes nominales. Los bins representan $[-f_s/2,f_s/2)$; no hay dos frecuencias discretas independientes en los dos extremos de Nyquist.
- **Separación entre bins:** con 1024 puntos resulta $2048000/1024=2000$ Hz antes del resampler y $192000/1024=187.5$ Hz después. No equivale por sí sola a la capacidad de separar emisoras, como explicó la subsección 5.
- **Escala vertical:** los visores del grafo de referencia utilizan Blackman-Harris y no tienen calibración de potencia RF. No se exige que sus alturas coincidan con las figuras Colab, que utilizan otras ventanas y normalizaciones; los dB del visor no se presentan como dBm.

??? example "Comprobación 3.1 — cambiar freq durante la reproducción"

    - **Ejemplo:** una componente a +250 kHz en la captura corresponde a $99.1+0.250=99.35$ MHz.
    - **Reetiquetado erróneo:** si se cambia `freq` a 99.5 MHz sin transformar las muestras, el visor la etiquetaría como $99.5+0.250=99.75$ MHz. El dato físico no cambió.
    - **Operación necesaria:** para centrar esa componente se utilizaría una mezcla de −250 kHz y se seguiría la nueva referencia, como en las subsecciones 6.3 y 6.4. Esa mezcla no forma parte de la ruta principal: aquí el canal de interés ya está centrado.

## 4. Del cambio de fase al audio FM

Las subsecciones 2.3 y 4.1 relacionaron frecuencia y avance de fase. Para un tono complejo, $\Delta\theta=2\pi f_0/f_s$. En FM ese avance no es constante: cambia con la información moduladora.

Si $z[n]=Ae^{j\theta[n]}$ y $A$ es constante y no nula, el producto de dos muestras consecutivas, conjugando la anterior, es

$$
z[n]z^*[n-1]=A^2e^{j(\theta[n]-\theta[n-1])}.
$$

Su argumento entrega la diferencia de fase, módulo $2\pi$. Bajo un avance sin ambigüedad, $|\Delta\theta[n]|<\pi$, se estima la frecuencia media durante ese intervalo:

$$
\widehat f[n]=\frac{f_s}{2\pi}\operatorname{arg}\left(z[n]z^*[n-1]\right).
$$

- **Relación con el tono:** si el avance es constante, esta operación recupera su frecuencia. Si cambia, la salida sigue ese cambio.
- **Relación con FM centrada:** en un modelo de frecuencia $f[n]=\Delta f\,m[n]$, con $m[n]$ normalizada y sin offset de portadora, dividir $\widehat f[n]$ entre $\Delta f$ recupera una estimación de $m[n]$ antes del filtrado de audio.
- **Límite de fase:** el argumento es un ángulo principal. No distingue avances que difieran en vueltas completas, igual que en el aliasing de la subsección 4. No se interpreta una muestra de magnitud nula como si tuviera fase fiable.
- **Bloque utilizado:** `Quadrature Demod` implementa el producto conjugado y el argumento multiplicado por una ganancia. [Fuente de GNU Radio](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/lib/quadrature_demod_cf_impl.cc).

El estudiante conecta `WBFM Receive` a la salida del resampler, con **`Quadrature Rate = 192000`** y **`Audio Decimation = 4`**. Se utiliza el nombre del parámetro mostrado por GNU Radio Companion 3.10.12.

- **Entrada y salida:** el bloque recibe muestras complejas y entrega muestras reales de audio mono.
- **Operaciones internas:** incluye demodulación de fase, filtrado de audio y decimación. No basta cambiar el tipo de `Complex` a `Float` para obtener el audio.
- **Escala interna:** la implementación utiliza una desviación de referencia de 75 kHz y ganancia $G=f_s/(2\pi\,75000)$. A 192 kS/s, $G\approx0.4074$. Esa referencia del bloque no demuestra por sí sola la desviación real de la emisora. [Implementación de WBFM Receive](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/wfm_rcv.py).
- **De-emphasis:** también incluye este filtrado, que modifica la respuesta del audio; su constante predeterminada es 75 µs. Se documenta como una elección de la implementación, sin asumir que coincida automáticamente con la del transmisor local. [Implementación de de-emphasis](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/fm_emph.py).
- **Alcance:** no se añade un decoder stereo ni un decoder RDS. Escuchar audio no demuestra que todas esas partes de una emisión se hayan recuperado.

Después se conectan `Multiply Const` de tipo `Float`, con constante `volume`, y `Audio Sink` con una entrada, `Sample Rate = 48000` y `OK to Block = No`. Para disponer de un control visible, `volume` puede definirse mediante `QT GUI Range`, entre 0 y 1, paso 0.05 y valor inicial 0.2, como en la referencia.

??? example "Comprobación 4.1 — por qué Audio Sink debe quedar a 48000"

    - **Tasa recibida:** el resampler entrega 192000 muestras complejas/s y `Audio Decimation = 4` produce $192000/4=48000$ muestras reales/s.
    - **Tipo:** estas muestras son valores de audio; no contienen una pareja I/Q que deba dividirse nuevamente entre dos.
    - **Correspondencia:** `Audio Sink` debe reproducirlas a la tasa que representan. Una configuración diferente cambia la interpretación temporal del audio o causa problemas de suministro; no corrige un archivo de entrada con metadatos equivocados.

## 5. Ejecutar y registrar observaciones

1. Se verifica que la captura correcta está en `samples/` y que la ruta del `File Source` es relativa.
2. Se comparan las conexiones y tipos del montaje del estudiante con el grafo de referencia. El `ID` del estudiante se mantiene distinto del de la referencia.
3. En la referencia, `File Source` y toda la cadena CU8 están activos; `Soapy RTLSDR Source` está desactivado. No se mezclan las dos rutas.
4. Se ejecuta desde GNU Radio Companion con **F6** y se aumenta el volumen gradualmente. El contenido de la grabación y la salida de audio del equipo determinan lo que se escucha.
5. Se registra cada visor con su eje de frecuencia y se explica la diferencia entre las dos etapas mediante los ítems de la sección 3.

- **Repetición:** `Repeat = Yes` vuelve al inicio al terminar el archivo. Puede haber una discontinuidad en ese retorno; no representa una nueva observación del entorno RF.
- **Archivo fijo:** cambiar `freq` solo modifica etiquetas en esta ruta. No se recibe otra emisora ni se reescribe la frecuencia central de adquisición.
- **Expectativa verificable:** debe haber muestras en ambas etapas complejas y una salida real a 48 kS/s. La interpretación de la captura y la audición se documentan por separado; no se presume una calidad determinada solo porque el grafo compile.

### Si solo se dispone de la captura a 2.4 MS/s

No se renombra el archivo para hacerlo pasar por la captura de 2.048 MS/s. Se guarda una variante con otro `ID` y se cambian **conjuntamente** estos parámetros:

| Parámetro | Valor para la variante |
|---|---|
| `File Source` | `../samples/fm_99p1MHz_2p4Msps_g30.cu8` |
| `samp_rate` | `2400000` |
| `Throttle`, Byte | `2*samp_rate`, equivalente a 4800000 bytes/s |
| `Rational Resampler` | Interpolation: `2`; Decimation: `25` |

- **Comprobación:** $2400000(2/25)=192000$ S/s. `WBFM Receive`, el visor de canal y `Audio Sink` conservan 192000, decimación 4 y 48000, respectivamente.
- **Primer visor:** su `Bandwidth = samp_rate` pasa a 2.4 MHz. Con la misma referencia de 99.1 MHz, los bordes nominales son 97.9 y 100.3 MHz.
- **Contenido:** aunque ambas capturas documenten 99.1 MHz, no se supone que contengan el mismo instante ni las mismas amplitudes. Ajustar la cadena conserva una interpretación temporal correcta; no convierte una grabación en la otra.

## 6. Extensión opcional con RTL-SDR

Para recibir en vivo se detiene el grafo y se selecciona una sola ruta:

1. Se desactivan los **siete bloques de la ruta CU8**: `File Source`, `Throttle`, `UChar to Float`, `Add Const`, el `Multiply Const` de normalización, `Deinterleave` y `Float to Complex`. No se desactiva el control de volumen de la salida de audio.
2. Se activa `Soapy RTLSDR Source`, que en la referencia está desactivado.
3. Se mantiene su salida `Complex Float32`, `Sample Rate = samp_rate`, `Center Frequency = freq`, ganancia manual 30 dB y AGC desactivado, como en el grafo.
4. Se conecta directamente al resampler y al visor RF; el hardware ya entrega muestras complejas. No se aplica la conversión CU8 a esa salida.
5. Se ejecuta nuevamente. Los requisitos del dispositivo se revisan en la [guía de configuración del RTL-SDR](../../setup/rtl-sdr.md).

- **Clock de adquisición:** la fuente de hardware proporciona el ritmo de las muestras. No se añade el `Throttle` de archivo a esa ruta.
- **Sintonización real:** en esta variante, `freq` sí configura la frecuencia central de la fuente Soapy. La variable tiene una función distinta de la que tenía con un archivo fijo.
- **Comparación válida:** pueden variar la señal, la interferencia, el nivel y el ruido respecto a la captura. Se distingue cambiar de fuente de cambiar el procesamiento digital.

??? example "Comprobación 6.1 — por qué no quedan activas ambas fuentes"

    - **Entrada del resampler:** espera un solo flujo complejo. Dos fuentes no constituyen automáticamente una suma ni una selección entre ellas.
    - **Selección:** en la ruta de archivo la entrada procede de `Float to Complex`; en la ruta de hardware procede de Soapy. Se desactiva completamente la ruta que no se utiliza.
    - **Misma tasa declarada:** ambas rutas de esta referencia proporcionan 2.048 MS/s complejas; se mantiene el resampler 3/32. Esa coincidencia no implica que los valores de las muestras sean iguales.

## 7. Diagnóstico breve

| Síntoma | Revisión inicial |
|---|---|
| El grafo no abre el archivo | Se comprueban el nombre, la ruta relativa y la presencia de la captura en `samples/`. |
| Hay underruns o cortes de audio | Se revisan captura, `Throttle = 2*samp_rate` en Byte, carga del equipo y tasas de las etapas. |
| Los tiempos o el audio no corresponden | Se revisa el sample rate documentado; una captura a 2.4 MS/s no se declara a 2.048 MS/s. |
| Hay espectro, pero no audio | Se verifican `Quadrature Rate = 192000`, decimación 4, salida a 48000 y volumen; también la salida de audio del sistema. |
| La señal parece ruido | Se revisan formato Byte, normalización CU8 y orden de las entradas I y Q. |
| Las frecuencias RF parecen desplazadas | Se comprueba que `freq` corresponde a los metadatos; cambiar etiquetas no mezcla muestras. |
| Soapy no abre el dongle | Se vuelve a la ruta de archivo y se revisan driver y configuración del dispositivo por separado. |

## Entrega

El estudiante entrega:

1. El `.grc` construido, con un `ID` propio y sin rutas absolutas ni archivos I/Q dentro de Git.
2. La tabla de tasas completada: bytes de entrada, flujos I y Q, flujo complejo, salida del resampler y audio. Cada número se acompaña de su cálculo.
3. Una captura de cada visor, identificando la tasa, los bordes nominales, la referencia RF y la posición del canal objetivo.
4. Una explicación itemizada de qué hacen la conversión CU8, el resampling, la demodulación y el control de volumen. Se identifica qué etapa deja de tener una salida I/Q.
5. Una justificación de por qué cambiar `freq` no sintoniza otra señal del archivo. Si se utiliza la variante a 2.4 MS/s o el dongle, se documentan los cambios por separado.

## Lecturas y referencias

- [GNU Radio 3.10.12 — Rational Resampler](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-filter/lib/rational_resampler_impl.cc): relación entre tasas y filtro automático.
- [GNU Radio 3.10.12 — Quadrature Demod](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/lib/quadrature_demod_cf_impl.cc): producto conjugado y cálculo del argumento.
- [GNU Radio 3.10.12 — WBFM Receive](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/wfm_rcv.py): parámetros de entrada, demodulación y salida mono.
- [GNU Radio 3.10.12 — FM de-emphasis](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-analog/python/analog/fm_emph.py): constante predeterminada del filtro de audio.

La estructura procede del laboratorio respaldado del curso. Los parámetros anteriores se verifican contra GNU Radio 3.10.12; no se atribuye a sus valores predeterminados una garantía de calibración o de compatibilidad con toda emisora.

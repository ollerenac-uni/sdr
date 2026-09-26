---
title: "Laboratorio: receptor FM con archivo I/Q y RTL-SDR"
session: 2
description: "Construcción de un receptor FM de radiodifusión con una captura CU8 reproducible y una fuente Soapy RTL-SDR opcional."
status: draft
---

# Laboratorio: receptor FM con archivo I/Q y RTL-SDR

Esta guía adapta el flujo de [RTL-SDR FM Receiver de GNU Radio](https://wiki.gnuradio.org/index.php?title=RTL-SDR_FM_Receiver). La diferencia es la fuente: por defecto el receptor reproduce un archivo I/Q de 99.1 MHz. El dongle es una alternativa para observar la misma cadena en vivo.

## Objetivo

Construir y ejecutar un receptor de FM de radiodifusión con esta cadena:

```text
Archivo CU8 o Soapy RTL-SDR
        ↓  2.048 MS/s complejas
Rational Resampler: 3/32
        ↓  192 kS/s complejas
WBFM Receive
        ↓  48 kS/s reales
Control de volumen → Audio Sink
```

El archivo CU8 no llega directamente al resampler. Antes se convierte de bytes alternados I,Q a muestras complejas normalizadas.

## Archivos y requisitos

| Recurso | Ubicación | Uso |
|---|---|---|
| [`receptor_fm_99p1_2p048Msps.grc`](https://github.com/ollerenac-uni/sdr/blob/main/gnuradio-flowgraphs/receptor_fm_99p1_2p048Msps.grc) | `sdr/gnuradio-flowgraphs/` | Grafo del laboratorio. |
| `fm_99p1MHz_2p048Msps_g30.cu8` | `sdr/samples/` | Captura CU8 de 99.1 MHz a 2.048 MS/s. |
| Parlantes o audífonos | Equipo local | Salida de audio a 48 kHz. |

La captura se distribuye fuera de Git, en la carpeta de muestras del curso. El grafo espera la ruta relativa `../samples/fm_99p1MHz_2p048Msps_g30.cu8`; no debe sustituirse por una ruta absoluta.

## 1. Las tasas de la cadena

| Punto de la cadena | Tipo | Tasa |
|---|---|---:|
| Archivo CU8 | bytes I,Q alternados | 4 096 000 bytes/s |
| Señal I/Q reconstruida | compleja | 2.048 MS/s |
| Salida del resampler | compleja | 192 kS/s |
| Salida de `WBFM Receive` | real, audio mono | 48 kS/s |

El archivo tiene dos bytes por muestra compleja. Por esa razón el `Throttle` de la ruta de archivo se configura a `2*samp_rate`, no a `samp_rate`.

El `Rational Resampler` usa interpolación 3 y decimación 32:

$$
2,048,000\frac{3}{32}=192,000\ \text{S/s}.
$$

El bloque `WBFM Receive` recibe 192 kS/s y usa `Audio Decimation = 4`:

$$
\frac{192,000}{4}=48,000\ \text{S/s}.
$$

El valor 192 kS/s deja una ventana compleja de ±96 kHz. Es suficiente para procesar el canal FM centrado en la captura y permite que el audio llegue a 48 kS/s con una decimación entera.

??? question "1.1. ¿Qué cambia si el `Throttle` se configura a 2.048 MS/s?"
    La cadena no cambia de formato, pero el archivo se reproduce a la mitad de la velocidad real. El `File Source` entrega bytes, no muestras complejas: necesita dos bytes por cada muestra I/Q.

??? question "1.2. ¿Cuántos bytes contiene un segundo de esta captura?"
    Hay 2 048 000 muestras complejas por segundo y dos bytes por muestra. El resultado es 4 096 000 bytes por segundo.

## 2. Acondicionar el archivo CU8

El `File Source` está configurado como `Byte`. Los bloques siguientes realizan estas operaciones:

1. `UChar to Float`: representa cada byte como un número.
2. `Add Const = -127.5`: desplaza el centro del formato CU8 a cero.
3. `Multiply Const = 1/127.5`: escala aproximadamente I y Q al intervalo de −1 a +1.
4. `Deinterleave`: separa la secuencia I,Q,I,Q,... en dos flujos.
5. `Float to Complex`: reconstruye cada muestra como $I+jQ$.

La conversión es

$$
z[n]=\frac{u_I[n]-127.5}{127.5}+j\frac{u_Q[n]-127.5}{127.5}.
$$

`Rational Resampler` y `WBFM Receive` reciben entonces muestras complejas, igual que si procedieran directamente del RTL-SDR.

??? question "2.1. ¿Por qué un `File Source` de tipo `Complex` no sirve para este archivo?"
    Un `Complex` de GNU Radio ocupa dos `float32`: ocho bytes por muestra. El archivo CU8 solo tiene dos bytes por muestra, uno para I y uno para Q. Declararlo como `Complex` agrupa los bytes con un formato equivocado.

??? question "2.2. ¿Qué dato se pierde al pasar de CU8 a muestras complejas normalizadas?"
    No se pierde información adicional en la conversión: los 8 bits de I y los 8 bits de Q se representan como valores de coma flotante. La limitación de resolución ya estaba en los bytes de la captura.

## 3. Ejecutar con el archivo

1. Coloca la muestra en `samples/`.
2. Abre `receptor_fm_99p1_2p048Msps.grc`.
3. Confirma que `File Source` está activo y `Soapy RTLSDR Source` está desactivado.
4. Ejecuta con **F6**.
5. Sube `Volumen` gradualmente hasta obtener audio.

El primer `QT GUI Frequency Sink` representa 2.048 MHz: desde 98.076 hasta 100.124 MHz cuando se etiqueta con 99.1 MHz como centro. El segundo representa el canal después del resampler: desde 99.004 hasta 99.196 MHz.

La captura ya está centrada en 99.1 MHz. Cambiar la variable `freq` mientras se reproduce el archivo solo cambia las etiquetas de los visores; no retunea los datos grabados.

??? question "3.1. ¿Por qué el segundo visor muestra menos espectro?"
    El resampler reduce la tasa de 2.048 MS/s a 192 kS/s. Para señal compleja, el intervalo visible tiene el mismo ancho que la tasa: pasa de 2.048 MHz a 192 kHz.

## 4. Activar el RTL-SDR opcional

Quien tenga un dongle puede usar la misma cadena de demodulación:

1. Detiene el grafo.
2. Desactiva `File Source` y `Throttle`.
3. Activa `Soapy RTLSDR Source`.
4. Ejecuta de nuevo.

La fuente Soapy entrega `Complex Float32` a 2.048 MS/s, por lo que entra directamente al `Rational Resampler`. Mantiene `Center Frequency = freq`, `Sample Rate = samp_rate`, ganancia manual de 30 dB y AGC desactivado.

No se deben dejar activas las dos fuentes: ambas intentarían alimentar la misma entrada del resampler.

??? question "4.1. ¿Qué diferencia debe mantenerse al comparar archivo y dongle?"
    La fuente de archivo reproduce una captura fija. La fuente Soapy recibe el entorno actual: pueden cambiar nivel, interferencias, frecuencia real de la emisora y ruido. La cadena digital es la misma, pero la señal de entrada no tiene por qué serlo.

## 5. Diagnóstico breve

| Síntoma | Revisión inicial |
|---|---|
| El grafo termina o no hay espectro | verificar el nombre y la ruta relativa de la muestra. |
| El audio se reproduce demasiado rápido o lento | confirmar `Throttle = 2*samp_rate` y que la captura es 2.048 MS/s. |
| Hay espectro, pero no audio | comprobar `WBFM Receive` a 192 kS/s, decimación 4, `Audio Sink` a 48 kHz y volumen. |
| La señal parece ruido | revisar que la conversión CU8 está activa y que I y Q llegan a puertos distintos de `Float to Complex`. |
| No abre el dongle | volver a la ruta de archivo y consultar la [guía de configuración RTL-SDR](../../setup/rtl-sdr.md). |

## Entrega sugerida

El estudiante registra:

1. los cuatro valores de tasa de la tabla de la sección 1;
2. una captura de cada visor, con su intervalo de frecuencia anotado;
3. una explicación de por qué el archivo CU8 necesita acondicionamiento;
4. si dispone de dongle, una nota separando lo observado con la captura y en vivo.

## Lectura de referencia

- [GNU Radio Wiki: RTL-SDR FM Receiver](https://wiki.gnuradio.org/index.php?title=RTL-SDR_FM_Receiver). Origen de la relación 2.048 MS/s, resampler 3/32, `WBFM Receive` a 192 kS/s y audio a 48 kS/s.
- [GNU Radio Wiki: WBFM Receive](https://wiki.gnuradio.org/index.php/WBFM_Receive). Entrada compleja, salida de audio real y significado de `Channel Rate` y `Audio Decimation`.

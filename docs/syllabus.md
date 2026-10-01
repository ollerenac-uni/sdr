---
title: Syllabus
description: "Temario de las 16 sesiones del curso SDR y sus laboratorios guiados."
---

# Syllabus — Radio Definida por Software

[Descargar syllabus en PDF](downloads/syllabus-sdr.pdf)

El curso comprende 16 sesiones de 2 h de clase y 2 h de laboratorio. Cuando un
tema lo requiera, parte del tiempo de laboratorio podrá dedicarse a la explicación
teórica.

Los laboratorios utilizan archivos de muestras I/Q `.cu8` y señales generadas en
Python o GNU Radio. No requieren hardware SDR individual, pero sí una computadora
con GNU Radio; los ejemplos de Python pueden ejecutarse en Google Colab. El
profesor podrá realizar demostraciones Tx–Rx con el USRP B210 y el RTL-SDR, y
distribuir las capturas para su análisis. El enlace QPSK se construye por etapas
desde la sesión 5.

El objetivo es comprender y configurar un receptor QPSK sencillo. Los apuntes se
concentran en pocas ideas clave y un experimento principal por sesión. Los
laboratorios son guiados y utilizan código y flowgraphs preparados; no se exige
implementar desde cero todos los algoritmos de sincronización. Se incluyen sesiones
de integración y consolidación. Multipath, equalization adaptativa y OFDM quedan
como temas complementarios, fuera del programa obligatorio.

El temario presenta el programa previsto. Los apuntes y las guías de laboratorio se
publicarán progresivamente en el [índice de sesiones](sessions/index.md).

| Sesión | Clase: tema principal y descripción | Laboratorio: tema principal y descripción |
|:------:|---|---|
| 01 | **Introducción.** Se presenta la Radio Definida por Software, la arquitectura del receptor RTL-SDR y sus parámetros de adquisición. | **Laboratorio #1: muestreo y lectura de I/Q.** Se interpreta un archivo `.cu8` y se observan sus muestras y su espectro. |
| 02 | **Señales y espectro en SDR.** Se estudian las muestras I/Q, el muestreo, la FFT y la relación entre baseband y RF. | **Laboratorio #2: demodulador FM.** Se construye un receptor FM en GNU Radio para recuperar audio desde una captura `.cu8`. |
| 03 | **Sistemas y filtros digitales.** Se explica la respuesta al impulso y la convolución mediante filtros sencillos y ejemplos de entrada y salida. | **Laboratorio #3: filtrado digital.** Se modifica un ejemplo preparado en Python y GNU Radio para comparar una señal antes y después del filtrado. |
| 04 | **Selección de canal y decimación.** Se explica cómo la mezcla compleja y el filtrado permiten seleccionar un canal y reducir su sampling rate. | **Laboratorio #4: selección de un canal.** Se configura un flowgraph preparado para aislar un canal de una captura y observar el efecto de decimar con y sin filtro. |
| 05 | **De bits a símbolos: BPSK y QPSK.** Se relacionan bits, símbolos y constelaciones, y se distinguen bit rate, symbol rate y sampling rate. | **Laboratorio #5: bits y constelaciones.** Se utiliza código preparado para representar bits como símbolos BPSK/QPSK y recuperar los bits de símbolos ideales. |
| 06 | **Pulse shaping y matched filtering.** Se explica cómo los símbolos forman una señal, qué hacen los filtros RRC y cómo se observa la interferencia entre símbolos (ISI). | **Laboratorio #6: pulsos y eye diagram.** Se modifican los parámetros de filtros root-raised cosine en un ejemplo preparado y se observan los pulsos, el espectro y el diagrama de ojo. |
| 07 | **Enlace digital ideal.** Se reúne lo aprendido para explicar un Tx y un Rx QPSK sin ruido ni offsets, con las referencias de recepción conocidas. | **Laboratorio #7: enlace QPSK guiado.** Se completa un flowgraph con bloques preparados y se comparan los bits transmitidos y recuperados, considerando los retardos de los filtros. |
| 08 | **Ruido y medición de errores.** Se explica la relación señal a ruido (SNR) y la tasa de errores de bit (BER) mediante el enlace digital ya construido. | **Laboratorio #8: ruido y BER.** Se añade ruido controlado al enlace ideal y se compara la constelación y la BER para distintos niveles de ruido. |
| 09 | **Offset de frecuencia y fase.** Se explica el carrier frequency offset (CFO) y se distingue su efecto del de un offset de fase constante. | **Laboratorio #9: observación de offsets.** Se añaden offsets por separado a un enlace preparado y se observan sus efectos en el espectro y la constelación. |
| 10 | **Corrección de frecuencia y fase.** Se explica la corrección inicial de CFO y el seguimiento de fase mediante un Costas loop, sin desarrollar sus algoritmos desde cero. | **Laboratorio #10: corrección de offsets.** Se configura un estimador de CFO preparado y un Costas loop, y se compara la señal antes y después de la corrección, observando la ambigüedad de fase de QPSK. |
| 11 | **Symbol timing recovery.** Se explica por qué debe recuperarse el instante de decisión y cómo afecta una diferencia entre los relojes de muestreo. | **Laboratorio #11: recuperación de timing.** Se utiliza un bloque de sincronización preparado y se compara la recepción con y sin corrección de timing. |
| 12 | **Tramas y recuperación del mensaje.** Se explica cómo un preamble permite localizar el inicio de un mensaje y resolver la ambigüedad de fase de QPSK. | **Laboratorio #12: detección de tramas.** Se utiliza un ejemplo preparado de correlación para localizar el preamble, resolver la ambigüedad de fase y comparar el mensaje recibido con el original. |
| 13 | **Integración del receptor QPSK.** Se revisa cómo se conectan las etapas de filtrado, sincronización y recuperación del mensaje, sin introducir un algoritmo nuevo. | **Laboratorio #13: receptor integrado.** Se reúnen los bloques trabajados en un flowgraph guiado y se comprueba su funcionamiento con señales simuladas. |
| 14 | **Recepción desde una captura I/Q.** Se explica cómo trasladar el receptor simulado a una captura con parámetros conocidos, preparada por el profesor. | **Laboratorio #14: receptor desde un archivo `.cu8`.** Se utiliza el receptor integrado para recuperar un mensaje de una captura QPSK y contrastarlo con la referencia entregada. |
| 15 | **Evaluación y diagnóstico del receptor.** Se revisan fallas comunes del receptor mediante el espectro, las constelaciones y la comparación de los datos recuperados. | **Laboratorio #15: diagnóstico guiado.** Se analizan capturas preparadas con dificultades acotadas y se documentan los ajustes del receptor y los errores de bit respecto de una referencia. |
| 16 | **Síntesis y demostración del enlace.** Se consolida el recorrido desde los bits transmitidos hasta el mensaje recuperado y se reconocen los límites del receptor estudiado. | **Laboratorio #16: demostración y cierre.** Se reproduce el receptor con una captura de referencia y se explican sus etapas y resultados; la demostración Tx–Rx del profesor es opcional. |

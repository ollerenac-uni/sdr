---
title: Syllabus
description: "Temario de las 15 sesiones del curso SDR y sus laboratorios."
---

# Syllabus — Radio Definida por Software

[Descargar syllabus en PDF](downloads/syllabus-sdr.pdf)

El curso comprende 15 sesiones de 2 h de clase y 2 h de laboratorio. Cuando un
tema lo requiera, parte del tiempo de laboratorio podrá dedicarse a la explicación
teórica.

Los laboratorios utilizan archivos de muestras I/Q `.cu8` y señales generadas en
Python o GNU Radio. No requieren hardware individual. El profesor podrá realizar
demostraciones Tx–Rx con el USRP B210 y el RTL-SDR, y distribuir las capturas para
su análisis. El enlace QPSK se construye por etapas desde la sesión 5.

El temario presenta el programa previsto. Los apuntes y las guías de laboratorio se
publicarán progresivamente en el [índice de sesiones](sessions/index.md).

| Sesión | Clase: tema principal y descripción | Laboratorio: tema principal y descripción |
|:------:|---|---|
| 01 | **Introducción a la Radio Definida por Software.** Se describe la arquitectura del receptor RTL-SDR y el significado de sus parámetros de adquisición. | **Laboratorio #1: muestreo y lectura de I/Q.** Se interpreta un archivo `.cu8` y se observan sus muestras y su espectro. |
| 02 | **Señales y espectro en SDR.** Se estudian las muestras I/Q, el muestreo, la FFT y la relación entre baseband y RF. | **Laboratorio #2: demodulador FM.** Se construye un receptor FM en GNU Radio para recuperar audio desde una captura `.cu8`. |
| 03 | **Sistemas y filtros digitales.** Se estudian la respuesta al impulso, la convolución y el efecto de los filtros sobre una señal. | **Laboratorio #3: filtrado digital.** Se implementa un filtro sencillo en Python y GNU Radio, y se comparan las señales antes y después del filtrado. |
| 04 | **Selección de canal y cambios de sampling rate.** Se estudian la mezcla compleja, el filtrado y la conversión de la tasa de muestreo. | **Laboratorio #4: selección y decimación de un canal.** Se aísla un canal de una captura y se compara la decimación con y sin filtro. |
| 05 | **De bits a señales: BPSK y QPSK.** Se relacionan bits, símbolos y constelaciones, y se distinguen bit rate, symbol rate y sampling rate. | **Laboratorio #5: enlace BPSK/QPSK ideal.** Se construye un Tx y un Rx virtuales para generar señales BPSK/QPSK y recuperar sus bits sin errores añadidos. |
| 06 | **Pulse shaping y matched filtering.** Se estudian la forma de los pulsos, el filtrado adaptado y la interferencia entre símbolos (ISI). | **Laboratorio #6: filtros RRC y eye diagram.** Se incorporan filtros root-raised cosine al enlace y se observa cómo el roll-off cambia el espectro y el diagrama de ojo. |
| 07 | **Ruido y desempeño del enlace.** Se estudian el ruido gaussiano, la relación señal a ruido (SNR) y la tasa de errores de bit (BER). | **Laboratorio #7: medición de BER.** Se añade ruido controlado al enlace y se relaciona la dispersión de la constelación con los errores de recepción. |
| 08 | **PLL y sincronización de fase.** Se estudian los lazos de seguimiento de fase, la rotación de constelaciones y la ambigüedad de fase en QPSK. | **Laboratorio #8: recuperación de fase.** Se completa un PLL didáctico y se observa la corrección de fase en un enlace BPSK/QPSK mediante un Costas loop. |
| 09 | **Sincronización de frecuencia.** Se estudia el carrier frequency offset (CFO), su efecto sobre la señal y los métodos de estimación y corrección. | **Laboratorio #9: estimación y corrección de CFO.** Se implementa un estimador sencillo y se compara la señal antes y después de corregir su offset de frecuencia. |
| 10 | **Symbol timing recovery.** Se estudian la recuperación del instante de decisión, el timing offset y la diferencia entre los relojes de muestreo. | **Laboratorio #10: recuperación de timing.** Se trabaja con un detector de error de timing y se evalúa un sincronizador frente a offsets y deriva del reloj. |
| 11 | **Frame synchronization y recuperación del mensaje.** Se estudian la detección del inicio de trama, el preamble, la correlación y la comprobación de errores mediante CRC. | **Laboratorio #11: recuperación de tramas QPSK.** Se localizan tramas, se resuelve la ambigüedad de fase y se compara el mensaje recuperado con el transmitido. |
| 12 | **Canal multipath y channel estimation.** Se estudian las trayectorias múltiples, sus retardos y la estimación de la respuesta del canal mediante señales conocidas. | **Laboratorio #12: modelado y estimación del canal.** Se introduce un canal con varias trayectorias y se estiman sus coeficientes a partir de una secuencia de entrenamiento. |
| 13 | **Equalization adaptativa.** Se estudia cómo un filtro adaptativo reduce la distorsión del canal y cómo el algoritmo LMS ajusta sus coeficientes. | **Laboratorio #13: equalizer LMS.** Se implementa la actualización de los coeficientes y se compara la constelación y la BER antes y después de equalizar. |
| 14 | **Introducción a OFDM.** Se estudian las subcarriers ortogonales, la IFFT/FFT, el cyclic prefix y la equalization por subcarrier. | **Laboratorio #14: enlace OFDM básico.** Se construye un enlace con sincronización conocida y se observa el efecto del multipath, del cyclic prefix y del CFO. |
| 15 | **Integración y evaluación de un receptor SDR.** Se integran las etapas del receptor QPSK y se estudia cómo identificar fallas y evaluar su desempeño. | **Laboratorio #15: receptor QPSK desde una captura.** Se recupera el mensaje de un archivo `.cu8` nuevo y se documentan las correcciones y los resultados obtenidos. |

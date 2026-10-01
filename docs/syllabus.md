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

## Por qué se sigue esta secuencia

El curso sigue un recorrido sencillo: pasar de observar muestras a recuperar un
mensaje. Cada etapa utiliza lo aprendido en la anterior. Primero se trabaja con
ejemplos controlados y después se incorporan dificultades, una a la vez, utilizando
código y bloques preparados.

### Sesiones 1 y 2 — Entender qué entrega el receptor

Se conoce el equipo y se aprende qué representan las muestras I/Q, cómo se
relacionan con el tiempo y cómo se observa su espectro. Esta base permite
interpretar una captura antes de procesarla. El laboratorio FM ofrece un primer
ejemplo de recuperación de información desde un archivo de muestras.

### Sesiones 3 y 4 — Preparar la señal

Una captura puede contener varios canales. Se aprende a filtrar, seleccionar el
canal deseado y reducir su sampling rate. Estas herramientas se estudian primero
porque se reutilizan en el receptor digital de las sesiones siguientes.

### Sesiones 5 y 6 — Convertir bits en una señal

Se relacionan bits, símbolos y constelaciones BPSK/QPSK. Después se observa cómo
los pulsos y los filtros convierten esos símbolos en una señal de muestras.
Los ejemplos preparados permiten comprender cada etapa sin tener que construir
todavía un receptor completo.

### Sesión 7 — Hacer funcionar un enlace ideal

Se reúnen las etapas anteriores en un Tx y un Rx QPSK, sin ruido ni offsets y con
las referencias de recepción conocidas. Se comprueba que los bits recuperados
coincidan con los transmitidos. Esta sesión deja una base que funciona antes de
añadir dificultades y da tiempo para consolidar lo aprendido.

### Sesión 8 — Observar el efecto del ruido

Se añade ruido al enlace que ya funciona y se observa cómo cambia la constelación
y cuántos errores de bit aparecen. Así, SNR y BER se relacionan con un experimento
concreto. Se prioriza medir y comparar resultados, sin desarrollar todas las
expresiones teóricas de desempeño.

### Sesiones 9 a 11 — Comprender y corregir los desajustes

Se observa primero qué ocurre cuando las referencias de frecuencia, fase o timing
del receptor no coinciden con las del transmisor. Después se utilizan un
estimador de CFO, un Costas loop y un bloque de timing recovery preparados para
corregir esos desajustes. Cada problema se estudia por separado, manteniendo las
otras referencias controladas. El objetivo es entender qué hace cada bloque y
comparar la señal antes y después de la corrección, no programar todos sus
algoritmos desde cero. El orden de aprendizaje no obliga a conectar los bloques
en ese mismo orden en el receptor integrado.

### Sesión 12 — Pasar de símbolos a un mensaje

Recuperar símbolos no basta para identificar dónde comienza el mensaje. Se
introduce un preamble conocido para localizar el inicio de la trama y resolver la
ambigüedad de fase de QPSK. Se compara el mensaje recuperado con una referencia,
sin construir un protocolo de comunicación completo.

### Sesión 13 — Integrar y comprobar el receptor

Se conectan las etapas ya trabajadas y se comprueba el receptor completo con
señales simuladas. No se añade un algoritmo nuevo: se reserva tiempo para resolver
dificultades de integración y reconocer qué aporta cada bloque.

### Sesiones 14 a 16 — Trabajar con capturas y consolidar

Se pasa del enlace simulado a capturas QPSK preparadas por el profesor, con
parámetros conocidos y datos de referencia. Se practican la recuperación del
mensaje, el diagnóstico de fallas y la comparación de resultados. El cierre se
dedica a explicar y reproducir el receptor construido, sin añadir otro sistema de
comunicación. No se espera recibir cualquier señal QPSK desconocida; multipath,
equalization adaptativa y OFDM quedan fuera del programa obligatorio.

## Sesiones y laboratorios

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

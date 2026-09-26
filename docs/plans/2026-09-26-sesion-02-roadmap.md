# Roadmap de la sesión 02 — Señales y espectro en SDR

Fecha: 2026-09-26.

Este archivo conserva las decisiones acordadas con el profesor. Se consulta antes
de desarrollar o revisar cada parte de la sesión 2 para mantener su alcance y
su progresión. Es un documento auxiliar: `plans/` está excluido de MkDocs.

## Contexto y propósito

- La sesión 1 presenta cómo el RTL2832U produce y entrega muestras I/Q. También
  introduce mezcla, muestreo, filtrado y decimación dentro del receptor.
- La sesión 2 desarrolla la capacidad de interpretar esas muestras y predecir
  lo que muestran las representaciones en tiempo y frecuencia.
- Haber visto un concepto en la sesión 1 no se considera evidencia de dominio.
  Se retoma brevemente cuando resulte necesario para una predicción o medición.
- El diseño previo del curso indica Señales y Sistemas como prerrequisito.
- La versión anterior de la sesión está respaldada en
  `backups/sesion-02-2026-09-26/`, junto con sus figuras, laboratorio y pruebas.

Pregunta conductora:

> ¿Qué contienen las muestras que entrega el SDR y cómo se interpretan en el
> tiempo y en la frecuencia?

## Objetivos acordados

1. Calcular el intervalo entre muestras y la duración de un bloque a partir de
   la tasa de muestreo y del número de muestras.
2. Interpretar las componentes I/Q de una señal, calcular su magnitud y fase,
   y explicar la diferencia entre una senoide real y una senoide compleja.
3. Relacionar las representaciones en tiempo y frecuencia, y predecir el
   espectro de un tono real, un tono complejo y una suma de tonos.
4. Interpretar el eje de frecuencias de una FFT y explicar cómo el número de
   muestras y la ventana afectan el espectro observado.
5. Distinguir aliasing y spectral leakage, y comprobar sus efectos con señales
   conocidas.
6. Relacionar las frecuencias en baseband con las frecuencias RF de una captura
   SDR y predecir el desplazamiento producido por una mezcla compleja.

## Progresión de la teoría

Los objetivos describen capacidades al finalizar la sesión. Las subsecciones
organizan el camino para desarrollarlas. Cada subsección tiene un objetivo
principal y reutiliza capacidades anteriores; no hay una correspondencia
obligatoria de una subsección por objetivo.

| Subsección | Contenido previsto | Objetivo principal y conexiones |
|---|---|---|
| 1. De las muestras a una señal | Señal continua y secuencia de muestras; tiempo discreto y amplitud cuantizada; tasa de muestreo, intervalo y duración; amplitud, frecuencia, período y fase de una senoide. | Objetivo 1. Prepara I/Q y la interpretación de la FFT. |
| 2. Señales reales y señales complejas I/Q | Componentes I y Q; magnitud y fase; senoide compleja como rotación; signo de la frecuencia; senoide real como suma de dos senoides complejas. | Objetivo 2. Prepara los objetivos 3 y 6. |
| 3. Una señal, dos representaciones: tiempo y frecuencia | Qué revela cada dominio; suma de tonos; magnitud y fase espectral; espectros reales y complejos; diferencia entre la transformada completa y una pantalla de magnitud. | Objetivo 3. Reutiliza el objetivo 2 y prepara el 4. |
| 4. Muestreo y aliasing | Frecuencia en Hz y en ciclos por muestra; frecuencias equivalentes; periodicidad del espectro en tiempo discreto; intervalo representativo; condición de muestreo y filtrado previo. | Parte del objetivo 5. Reutiliza los objetivos 1 y 3. |
| 5. Qué calcula una FFT de un bloque finito | DFT y FFT; bins y eje de frecuencias; duración del bloque; spectral leakage; ventanas; separación entre bins y resolución efectiva. | Objetivo 4 y cierre del objetivo 5. Reutiliza los objetivos 1 a 3. |
| 6. De baseband a RF: interpretar una captura SDR | Frecuencia central; frecuencia relativa y absoluta; señales por encima y por debajo del centro; mezcla compleja; diferencia entre reetiquetar un visor y transformar muestras. | Objetivo 6. Integra las capacidades anteriores. |

## Alcance de la primera subsección

Punto de partida: los valores que entrega el receptor forman una secuencia
ordenada. Para interpretarla hacen falta su tasa de muestreo y un eje temporal.

Desarrollo previsto:

1. Presentar `x(t)` y `x[n]`, distinguiendo valor de la señal, índice de muestra
   e instante de muestreo.
2. Diferenciar muestreo en tiempo y cuantización de amplitud, retomando el ADC
   de la sesión 1 sin repetir la arquitectura del equipo.
3. Relacionar tasa de muestreo, intervalo entre muestras y posición temporal.
4. Interpretar un bloque de N muestras y su duración. Distinguir la duración
   nominal del bloque del tiempo entre su primera y última muestra.
5. Usar una senoide real sencilla para identificar amplitud, frecuencia,
   período y fase. El desarrollo de I/Q corresponde a la subsección 2.
6. Cerrar con una comprobación breve de lectura de muestras y cálculo temporal.

No desarrollar aquí FFT, espectros, aliasing, ventanas, mezcla ni filtros.
La subsección construye las herramientas temporales que esos temas necesitan.

## Método y evaluación

- Cada subsección introduce una idea, incluye una comprobación breve y
  reutiliza lo aprendido. Las ecuaciones permiten predecir algo observable.
- El laboratorio empieza con señales sintéticas conocidas y termina con la
  grabación oficial de la sesión 1; el dongle no es requisito.
- Experimentos previstos: tono real frente a complejo; cambios de frecuencia
  y fase; tono alineado y no alineado con un bin y comparación de ventanas;
  variaciones de N y tasa de muestreo; ubicación de una señal en la captura.
- La entrega registra predicción, observación y explicación, además del `.grc`.
- La evaluación comprueba capacidades por separado y su integración en una
  misma captura SDR. Las capturas de pantalla requieren interpretación.
- La versión completa tendrá objetivos, introducción, teoría numerada,
  síntesis, al menos cinco ejercicios con solución, laboratorio y lecturas.
- Los ejercicios de refuerzo se sitúan al cierre de cada una de las seis
  subsecciones teóricas, no en un bloque acumulado al final. Los enunciados
  son visibles y las soluciones se despliegan en bloques `??? example`, con
  explicaciones itemizadas; las comprobaciones breves de la teoría se conservan.
- Cada solución remite a los apartados y fórmulas que utiliza, desarrolla la
  sustitución de los datos paso a paso y explica el resultado con sus unidades.
  Incluye una comprobación o una advertencia sobre el error conceptual que
  permite detectar; no se limita a entregar la respuesta numérica.

## Límites y decisiones de estilo

- Lenguaje simple, tercera persona y términos habituales de SDR en inglés
  cuando corresponda, sin traducciones forzadas. Se mantienen I/Q, FFT,
  aliasing, spectral leakage, bins y baseband.
- En los snippets, cada instrucción de ploteo se mantiene en una sola línea,
  aunque sea larga. No se divide una llamada entre varias líneas: el profesor
  indicó que esa división dificulta su visualización.
- No desarrollar un catálogo de transformadas ni el algoritmo interno de FFT.
- Sistemas aparece como puente breve hacia la siguiente sesión. Respuesta al
  impulso, convolución, respuesta en frecuencia y FIR se reservan para ella.
- El diagnóstico detallado de AGC, saturación, DC y ppm se distribuye después;
  no desplaza el objetivo principal de interpretar señales.
- El receptor FM completo se pospone hasta explicar filtrado y cambios de tasa.
- Toda figura nueva respeta la numeración, el pie y la lectura guiada del
  repositorio. Las figuras por código conservan su script reproducible.
- Desde la subsección 4, las lecturas guiadas se presentan en listas: cada
  panel, fila o columna se identifica y se explica qué debe observarse.
  Las aclaraciones generales van en ítems separados, no en párrafos largos.
- La síntesis se prepara para exposición con dos paneles de Chrome: imagen
  independiente y lectura itemizada. Las letras de los paneles se repiten en
  los ítems, en orden; cada lámina tiene un enlace para abrirla por separado.
- Antes de incorporar datos técnicos o comandos al material del alumno se
  verifican fuentes primarias y se ejecutan los comandos, respectivamente.

## Referencias y estado

- Libro: `referencia/SDR4Engineers.pdf`. Solo se revisó el índice; el capítulo 2
  sirve como mapa de fundamentos, no como contenido para una sola sesión.
- Laboratorios: `gnuradio-labs-referencia/Lesson_1` para señales y `Lesson_2`
  para sistemas. Los flowgraphs se revisaron como referencias; todavía no se
  ha verificado su ejecución para la nueva sesión.
- La secuencia posterior propuesta es representar señales, seleccionar
  canales, recuperar información analógica, recuperar símbolos digitales,
  sincronizar e interpretar tramas. No constituye un nuevo syllabus aprobado.
- Completado: título y seis objetivos en la página de la sesión.
- Completado: subtítulo de teoría y de la subsección 1.
- Desarrollado para revisión del profesor: subsección 1, con un tono de 1 kHz
  a 8 kS/s, cuatro celdas copiables para Colab, dos figuras reproducibles y
  comprobaciones breves. Se distingue duración del bloque y última muestra.
- Aclaración acordada: `x[n]` en la subsección 1 es un ejemplo real. La señal
  física recibida es real y la salida I/Q es una representación compleja en
  baseband. Una pareja I/Q corresponde a una muestra, no a dos instantes.
- Desarrollado para revisión del profesor: subsección 2, con magnitud y fase,
  tono complejo, sentidos de giro y descomposición de una senoide real;
  cinco celdas Colab y Figuras 3 a 5 con script reproducible. No incluye FFT.
- Se distingue el tono ideal, cuyas componentes son seno y coseno, de una
  captura genérica: I y Q no tienen que ser siempre senoides desfasadas 90°.
- Desarrollado para revisión del profesor: subsección 3, con comparación entre
  coseno y tonos complejos, suma de tonos, magnitud y fase espectral, y
  recuperación de muestras con la transformada completa. Cinco celdas Colab
  y Figuras 6 a 8 con script reproducible.
- La FFT de la subsección 3 se usa como visor: espectro de ambos lados y
  magnitud lineal escalada por N. Tonos con ciclos enteros en el bloque.
  Los detalles de bins, ventanas y spectral leakage siguen reservados para
  la subsección 5. La fase se grafica solo en componentes presentes.
- Desarrollado para revisión del profesor: subsección 4, con siete celdas Colab
  autocontenidas y seis experimentos visuales (Figuras 9 a 14). Cada experimento
  declara qué se varía, qué se mantiene fijo y qué debe observarse.
- Aliasing: cosenos de 1 y 9 kHz con muestras iguales a 8 kS/s; tonos I/Q de
  +5 y −3 kHz equivalentes; mapa periódico de frecuencias; tono fijo de +3 kHz
  adquirido a 12, 8 y 4 kS/s; fase de un coseno real en Nyquist; superposición
  de +1 y +9 kHz al reducir de 24 a 8 kS/s sin filtrado previo.
- Las curvas continuas son referencias conocidas, no reconstrucciones desde
  las muestras. El caso límite real de Nyquist se distingue del tono complejo.
  El intervalo centrado tiene ancho total fs para I/Q, no fs/2.
- El filtrado se modela eliminando el tono conocido antes de descartar muestras;
  no se implementa ni diseña un filtro real. Sistemas y filtros siguen reservados
  para la siguiente sesión. Se separa aliasing de spectral leakage.
- `figures/gen_aliasing.py` reproduce las figuras ejecutando las celdas de la
  subsección publicada: los snippets y las figuras comparten implementación.
- Desarrollado para revisión del profesor: subsección 5, con diez apartados,
  ocho celdas Colab y siete figuras reproducibles (Figuras 15 a 21). La DFT
  se interpreta como comparación con tonos de referencia y suma compleja.
- Se explican el orden de `fft`, `fftfreq` y `fftshift`; tono alineado frente
  a tono entre bins; repetición del bloque y spectral leakage; zero padding;
  ventanas rectangular y Hann periódica; duración y separación de tonos;
  componente débil próxima a otra fuerte; aliasing frente a leakage.
- Decisión didáctica: N cuenta muestras adquiridas y M es longitud de FFT.
  La separación de salida es fs/M, pero el tiempo observado es N/fs. Se
  compara el mismo bloque con más ceros y bloques con más datos reales.
- La escala es magnitud de tonos, corregida por suma de pesos de ventana.
  Los dB son relativos a magnitud 1, no dBm ni PSD. No se implementan PSD,
  promediado, calibración de potencia ni el algoritmo interno de FFT.
- Cada experimento declara lo que cambia y lo que se mantiene fijo. La
  Figura 16 amplía el reinicio del bloque; no se exige igualdad entre primera
  y última muestra. Las figuras con padding no representan nueva adquisición.
- `figures/gen_fft_bloque.py` ejecuta las mismas celdas publicadas para evitar
  divergencia entre figuras y Colab. Hay pruebas numéricas y de reproducibilidad.
- Desarrollado para revisión del profesor: subsección 6, con ocho apartados,
  siete celdas Colab y seis figuras reproducibles (Figuras 22 a 27). Se conecta
  frecuencia relativa y RF usando la referencia documentada de la captura.
- Experimentos: los mismos coeficientes con eje baseband y RF; mezcla compleja
  de tres tonos; etiquetas falsas frente a referencia actualizada tras mezclar;
  multiplicador complejo frente a coseno real; cruce del borde y mezcla inversa;
  lectura de 16384 muestras de la grabación oficial a 2.4 MS/s y 99.1 MHz.
- La convención de mezcla es y[n] = x[n] exp(j 2π f_mix n/fs): las frecuencias
  se suman. Para centrar una componente se usa la frecuencia opuesta. Centrar
  no filtra, no reduce la tasa y no recupera la información perdida al adquirir.
- Las etiquetas RF después de mezclar se interpretan para componentes sin
  cruce del borde; la banda desplazada no equivale a una nueva adquisición RF.
  La figura real utiliza Hann periódica y dB relativos al máximo del bloque,
  sin padding, PSD, promediado ni calibración de potencia.
- `figures/gen_baseband_rf.py` ejecuta las celdas publicadas. La última figura
  requiere el archivo oficial en samples/; no se incorpora la grabación a Git.
  Las pruebas sintéticas funcionan también sin disponer de la grabación.
- Desarrollado para revisión del profesor: síntesis visual con cuatro láminas
  reproducibles (Figuras 28 a 31), lecturas itemizadas por panel y una guía de
  cierre. Conecta muestras/tiempo/IQ/FFT, aliasing frente a leakage, padding
  frente a ventana y más datos, y baseband/RF frente a mezcla compleja.
- `figures/gen_sintesis.py` genera las láminas con señales sintéticas conocidas;
  no requiere el archivo I/Q ni añade nuevos experimentos al recorrido teórico.
  La comparación de FFT declara que el último panel usa el par de tonos, no
  el tono único de los otros tres; se conserva N frente a M en las explicaciones.
- Desarrollado para revisión del profesor: 24 ejercicios de refuerzo, cuatro
  por subsección, con identificadores 1A–6D. Combinan cálculo, predicción,
  interpretación de figuras y explicación de errores; no anticipan conceptos
  de subsecciones posteriores ni añaden nuevas celdas al recorrido de Colab.
- Pendiente: introducción, laboratorio y lecturas.
  El desarrollo continúa por partes con el profesor; la sesión sigue en borrador.

Al avanzar, se actualiza este estado y se registran aquí los cambios de alcance
acordados. El contenido del backup no se reincorpora automáticamente.

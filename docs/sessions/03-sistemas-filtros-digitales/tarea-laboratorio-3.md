---
title: "Tarea del laboratorio 3"
session: 3
description: "Diagnóstico y evaluación del enlace BPSK: recorrido del mensaje, sincronización, preámbulo, entrega útil e integridad."
status: draft
---

# Tarea del laboratorio 3

## Propósito

El estudiante evalúa el enlace BPSK completo construido en la [sección 24 del laboratorio 3](index.md#24-cerrar-la-etapa-bpsk-con-el-enlace-integrado).
La tarea reúne cinco actividades y un reto integrador. Las evidencias de las actividades se reutilizan en el informe final.

BPSK significa *Binary Phase Shift Keying* y utiliza dos estados de fase.
CRC significa *Cyclic Redundancy Check*, comprobación cíclica de redundancia.
El texto se representa mediante la codificación UTF-8 utilizada en el laboratorio.

Al terminar, el estudiante debe poder:

- Seguir el contenido desde el texto hasta las muestras y desde las muestras hasta el texto recuperado.
- Relacionar una pérdida con la etapa que dejó de cumplir su función.
- Distinguir adquisición inicial, seguimiento, detección del paquete y comprobación de integridad.
- Justificar una longitud de preámbulo mediante resultados reproducibles.
- Comparar la entrega útil con el tiempo de señal utilizado por el modelo.

## Preparación y reglas comunes

1. El estudiante guarda una copia de su flowgraph, diagrama de bloques, y configura un `ID` exclusivo en `Options`.
2. Completa los cambios de [24.2 a 24.4](index.md#242-comprobar-el-orden-activo-del-canal) antes de medir.
3. Comprueba `preambulo_bytes = 32`, la función de `PDU Lambda` (`ID = envolver_trama`) y el máximo de trama actualizado.
4. Comprueba que `Delay` (`ID = retardar_canal`) esté habilitado y conectado en serie con el remuestreador.
5. Conserva `Symbol Sync`, `Costas Loop` y ambas rutas de polaridad activos. El selector fijo queda deshabilitado.
6. Ejecuta la referencia integrada y confirma la recuperación del primer mensaje antes de enviar el siguiente.

La referencia utiliza estos valores:

| Variable | Valor |
|---|---|
| `symbol_rate` | `1000` símbolos/s |
| `sps` | `4` muestras por símbolo |
| `samp_rate` | `4000` muestras/s |
| `rrc_alpha` | `0.35` |
| `rrc_span` | `8` intervalos de símbolo |
| `preambulo_bytes` | `32` bytes |
| `ruido_semilla` | `42` |
| `fase_grados`, `frecuencia_offset_hz`, `retardo_muestras` y `reloj_ppm` | `0` |
| `ruido_amplitud` | `0.0` |

La tasa de símbolos se representa con $R_s$. La tasa de muestreo se representa con $f_s$.
El factor $L=\mathrm{sps}$ relaciona ambas tasas: $f_s=L R_s$.

- Cada experimento declara qué cambia, qué permanece fijo y qué se observa.
- Cada caso comienza con una ejecución nueva, excepto cuando se comparan mensajes consecutivos dentro del mismo lote.
- El estudiante deja terminar el procesamiento de un envío antes de realizar el siguiente.
- Las pausas del operador no reinician automáticamente los lazos.
- El texto admite hasta 500 palabras y 5000 bytes UTF-8 por mensaje. El identificador, si se añade al texto, cuenta dentro de ese límite.
- Se conserva `Threshold = 0` en ambos detectores de acceso.
- Se conservan el CRC y la retirada de etiquetas mediante `Tag Gate` (`ID = sin_etiquetas`).
- Los valores configurados en el canal se usan para evaluar el resultado. No se suministran como correcciones exactas a los sincronizadores.

## Cómo registrar y comparar los resultados

### Contadores del enlace

Una PDU, *Protocol Data Unit* o unidad de datos de protocolo, reúne metadatos y un vector de datos.

| Contador | Qué registra |
|---|---|
| `TX` | Tramas publicadas por el transmisor. |
| `DET` | Detecciones registradas entre las dos rutas de polaridad. |
| `RX` | PDUs de paquetes completos entregadas al comprobador. |
| `OK` | Textos publicados por el receptor después de las comprobaciones. |

Una entrega correcta exige comparar el contenido recibido con el texto esperado.
El estudiante comprueba mayúsculas, Unicode, espacios, orden y ausencia de duplicados.
Un duplicado no cuenta como una segunda entrega correcta.

Una constelación alineada no demuestra por sí sola que se recuperó el mensaje.
Los contadores y la comparación del contenido deben apoyar la interpretación.

### Tiempo de señal y tasa útil

Para esta tarea, $N_c$ cuenta las muestras que salen de `Tag Gate` (`ID = sin_etiquetas`) hacia el canal durante un lote.
El punto de medida queda antes de `Fractional Resampler` (`ID = desajustar_reloj`).
Cada muestra se cuenta una sola vez, aunque la salida alimente más de una rama.

En este montaje, ambos cierres se añaden antes de `Tag Gate`.
Por tanto, $N_c$ incluye el cierre de transmisión y los ceros destinados a completar el filtrado receptor.
Esta convención permite comparar todos los casos con el mismo registro de entrada al canal.

El estudiante puede añadir esta línea al `Python Snippet` de resumen, con `Section of Flowgraph = Main - After Stop`:

```python
print(f"MUESTRAS_CANAL={self.sin_etiquetas.nitems_written(0)}", flush=True)
```

Se conservan las líneas anteriores del resumen y el snippet de ampliación de buffers.

El tiempo del registro se calcula con la tasa nominal anterior al remuestreo:

$$
T_{\mathrm{registro}}=\frac{N_c}{f_s}.
$$

Si $B_{\mathrm{ok}}$ es la suma de bytes UTF-8 de texto entregados correctamente, la tasa útil de la tarea es:

$$
G_{\mathrm{util}}=\frac{8B_{\mathrm{ok}}}{T_{\mathrm{registro}}}
\qquad [\mathrm{bits/s}].
$$

- El numerador cuenta texto útil. No incluye preámbulo, acceso, longitudes ni CRC.
- El denominador incluye todos los envíos del lote, también los que se pierden o se rechazan.
- Las pausas del operador y el tiempo de cálculo de la computadora quedan fuera del denominador.
- La simulación no está limitada a tiempo real. El cronómetro de la interfaz no mide el tiempo de señal.
- La proporción de mensajes recuperados no es una BER, tasa de error de bits.
- `ruido_amplitud` tampoco es directamente una SNR, relación señal a ruido expresada en decibelios.

## Actividad 1. Seguir un mensaje completo { #actividad-1 }

**Propósito:** relacionar las representaciones del mensaje y justificar sus tamaños.

- **Cambia:** el texto enviado.
- **Permanece fijo:** la referencia integrada, incluido el preámbulo de 32 bytes.
- **Se observa:** el contenido de la trama, las cantidades de elementos y los tiempos asociados.

1. El estudiante envía `Hola` y después `¡Hola, Perú!`.
2. Identifica preámbulo, acceso, longitud externa duplicada, longitud interna, texto UTF-8 y CRC.
3. Reconstruye el orden de esos campos. Distingue qué cuenta cada longitud.
4. Calcula los símbolos BPSK, las muestras RRC de TX y las muestras que entran al canal.
5. Contrasta los cálculos con el montaje y explica cualquier diferencia entre puntos de observación.
6. Distingue duración del registro, retardo de los filtros y duración correspondiente al contenido útil.

El informe incluye esta tabla completada:

| Magnitud | Unidad | `Hola` | `¡Hola, Perú!` |
|---|---|---|---|
| Caracteres del texto | caracteres | | |
| Texto UTF-8 | bytes | | |
| Paquete protegido | bytes | | |
| Trama antes de `Bytes a bits` | bytes | | |
| Símbolos BPSK de la trama | símbolos | | |
| Salida de `Root Raised Cosine Filter` (`ID = pulso_rrc`) | muestras complejas | | |
| Entrada al canal, después de `sin_etiquetas` | muestras complejas | | |
| Tiempo del registro de entrada al canal | ms | | |
| Retardo conjunto de los dos filtros RRC | ms | | |

**Preguntas:** ¿por qué caracteres y bytes pueden ser cantidades diferentes?
¿Qué elementos aumentan la longitud transmitida sin añadir texto?
¿Por qué un byte que almacena un bit y un byte del texto tienen significados distintos?

## Actividad 2. Determinar cuándo hace falta cada corrección { #actividad-2 }

**Propósito:** relacionar una perturbación con la función receptora que la trata.

Cada fila es un experimento independiente. El estudiante compara el receptor completo con una modificación temporal.
Los demás parámetros del canal permanecen en cero y el preámbulo conserva 32 bytes.

| Caso | Perturbación | Modificación temporal |
|---|---|---|
| Frecuencia | `frecuencia_offset_hz = 10` | Comparar con y sin `Costas Loop` (`ID = recuperar_fase`), mediante el procedimiento de la sección 21. |
| Polaridad | `fase_grados = 120` | En `Map` (`ID = invertir_bits`), comparar `Map = [1, 0]` con `Map = [0, 1]`. |
| Tiempo | `retardo_muestras = 2` | Comparar `Symbol Sync` con `Keep M in N` (`ID = muestrear_stream`), mediante el control de selección fija de la sección 23. |

1. El estudiante escribe una predicción antes de ejecutar cada comparación.
2. Sigue los procedimientos de las [secciones 21](index.md#21-introducir-un-desajuste-de-frecuencia-y-recuperarlo-con-costas) y [23](index.md#23-recuperar-el-instante-de-simbolo-y-seguir-la-deriva-de-reloj) para cambiar las conexiones y los diagnósticos.
3. Envía primero el texto largo de 799 bytes de 23.7 y después `Hola`.
4. Registra `TX`, `DET`, `RX` y `OK`. Guarda una observación que permita localizar el fallo.
5. Restablece el receptor completo antes de comenzar la siguiente fila.

La tabla `[0, 1]` conserva los bits en la segunda ruta. Esa comparación se realiza únicamente en el caso de 120°.
Antes de abandonar el caso se restablece `Map = [1, 0]`.
El control de selección fija conserva `offset_muestreo = 0` y utiliza una sola ruta temporal activa.

**Preguntas:** ¿en qué etapa aparece la primera diferencia respecto de la referencia?
¿Qué indica que exista una detección sin entrega de texto?
Si una modificación todavía permite recibir, ¿qué condición explica ese resultado?

**Evidencia:** una tabla de predicciones y resultados, más una explicación basada en observaciones del enlace.

## Actividad 3. Encontrar un preámbulo suficiente { #actividad-3 }

**Propósito:** distinguir la adquisición del primer mensaje del seguimiento de los siguientes.

- **Cambia:** `preambulo_bytes`, con valores 0, 8, 16, 32 y 64.
- **Permanece fijo:** fase de 60°, frecuencia de +10 Hz, retardo de dos muestras, reloj de +1000 ppm y ruido cero.
- **Se observa:** recepción del primer texto y recepción del mensaje posterior.

1. El estudiante comprueba que `max_trama_bytes` incluya `preambulo_bytes`, como indica 24.3.
2. Inicia una ejecución nueva para cada longitud de preámbulo.
3. Envía el texto de 799 bytes de 23.7. Registra si aparece antes de enviar otro mensaje.
4. Envía `Hola` y conserva el resumen completo.
5. Identifica el menor valor probado que recuperó ambos textos en esta exploración.
6. Usa ese valor como candidato para el reto integrador.

El texto largo contiene 200 repeticiones de `SDR`, separadas por un espacio y sin espacio final.

| Preámbulo, bytes | Primer texto recuperado antes del segundo envío | `TX` | `DET` | `RX` | `OK` |
|---|---|---|---|---|---|
| 0 | | | | | |
| 8 | | | | | |
| 16 | | | | | |
| 32 | | | | | |
| 64 | | | | | |

**Preguntas:** ¿recibir el segundo mensaje demuestra que el primer envío adquirió correctamente?
¿Qué función cumple el preámbulo y qué función sigue cumpliendo el acceso?
¿Cuánto tiempo de señal añade cada candidato?

El resultado identifica un candidato en las condiciones ensayadas.
La validación con ruido y otras semillas corresponde al reto integrador.

## Actividad 4. Comparar longitudes y entrega útil { #actividad-4 }

**Propósito:** comparar el costo del formato con la entrega efectiva de texto.

- **Cambia:** el texto útil, con longitudes de 16, 128, 512 y 1024 bytes.
- **Permanece fijo:** preámbulo de 32 bytes, ruido de amplitud 1.0 y semilla 42. Los demás efectos del canal permanecen en cero.
- **Se observa:** mensajes recuperados exactamente, muestras utilizadas y tasa útil.

1. El estudiante prepara veinte textos distintos de cada longitud. Cuenta los bytes UTF-8, incluidos sus identificadores.
2. Inicia una ejecución nueva para cada longitud y envía su lote de veinte mensajes.
3. Registra todos los envíos y compara cada texto recibido con su referencia.
4. Calcula $G_{\mathrm{util}}$ para cada lote con la convención de medida de esta tarea.
5. Explica qué longitud produjo la mayor entrega útil en sus mediciones.

| Texto por mensaje, bytes | Enviados | Entregas exactas | Texto útil entregado, bytes | Muestras del lote | Tiempo del registro, s | Tasa útil, bits/s |
|---|---|---|---|---|---|---|
| 16 | 20 | | | | | |
| 128 | 20 | | | | | |
| 512 | 20 | | | | | |
| 1024 | 20 | | | | | |

**Preguntas:** ¿cómo cambia la fracción de texto útil al aumentar la longitud?
¿Qué ocurre con esa ventaja cuando se pierde o se rechaza un mensaje?
¿Por qué la mayor cantidad de bytes recibidos no garantiza la mayor tasa útil?

Estos lotes son una comparación exploratoria. Veinte envíos no establecen una tasa de error universal.
La amplitud 1.0 se utiliza en esta actividad; el reto integrador conserva sus propias condiciones.

## Actividad 5. Demostrar integridad y recepción desde la señal { #actividad-5 }

**Propósito:** distinguir pérdida de acceso, rechazo del paquete y ausencia de señal.

Cada control comienza con una ejecución nueva y la referencia integrada.
El estudiante anota la predicción antes de introducir la modificación.

| Control | Modificación |
|---|---|
| Texto alterado | Reutilizar `Alterar segundo paquete` después de `Construir paquete` y antes de `PDU Lambda` (`ID = envolver_trama`), como indica 16.8. |
| Acceso alterado | Cambiar un bit de la copia del acceso que `PDU Lambda` (`ID = envolver_trama`) publica en TX. |
| Señal anulada | En `Multiply Const` (`ID = rotar_fase`), establecer temporalmente `Constant = 0+0j` y conservar ruido cero. |

1. En el primer control, envía `Hola` tres veces. El auxiliar modifica únicamente el segundo paquete y conserva su CRC original.
2. En el segundo control, altera solo el acceso de TX. Conserva `sync_bits` y `Threshold = 0` en ambos detectores.
3. En el tercer control, envía `Hola` y comprueba el resultado mientras la señal transmitida permanece anulada.
4. Registra `TX`, `DET`, `RX`, `OK` y el texto observado en cada control.
5. Restablece el montaje, incluida la función de envoltura original, y demuestra otra vez la recepción de `Hola`.

La variable `sync_bytes` también se utiliza para definir la referencia del receptor.
Para el segundo control se modifica la copia transmitida, sin cambiar esa referencia compartida.
El preámbulo, las longitudes y el paquete protegido se conservan en ese control.

**Preguntas:** ¿por qué alterar el texto y alterar el acceso pueden afectar contadores diferentes?
¿Qué demuestra el control de señal anulada sobre las conexiones de mensajes?
¿Por qué recalcular el CRC después de alterar el texto cambiaría el experimento?

## Reto integrador. Defender una configuración del enlace { #reto-integrador }

El estudiante selecciona el menor preámbulo probado que cumpla los objetivos de esta validación.
Reutiliza la exploración de la actividad 3 y mantiene el receptor completo.

### Escenarios

| Escenario | Fase, grados | Frecuencia, Hz | Retardo, muestras | Reloj, ppm | Ruido, amplitud |
|---|---|---|---|---|---|
| Referencia | 0 | 0 | 0 | 0 | 0.0 |
| Desajustes combinados | 60 | +10 | 2 | +1000 | 0.0 |
| Combinación con ruido | 60 | +10 | 2 | +1000 | 0.1 |

Cada escenario se ejecuta con las semillas 17, 42 y 83.
Son nueve ejecuciones nuevas por candidato. En los casos sin ruido, las semillas funcionan como controles repetidos.
Cada ejecución conserva la misma configuración del canal durante todos sus mensajes.

### Lote común de diez mensajes

| Orden | Texto |
|---|---|
| 1 | Texto de 799 bytes de 23.7. |
| 2 | `Hola`. |
| 3 | `SDR`. |
| 4 | `¡Hola, Perú!`. |
| 5 | La letra `A` repetida 16 veces. |
| 6 | La letra `A` repetida 128 veces. |
| 7 | La letra `A` repetida 512 veces. |
| 8 | La letra `A` repetida 1024 veces. |
| 9 | La letra `A` repetida 5000 veces. |
| 10 | `␠␠texto␠␠`, con dos espacios iniciales y dos espacios finales. |

Las repeticiones se envían expandidas. La descripción de la tabla no forma parte del texto transmitido.
Cada marca `␠` representa un espacio y se reemplaza por ese carácter antes del envío.
El archivo de referencia debe conservar los espacios y la codificación UTF-8.
Los identificadores del registro se guardan por separado para conservar este lote común.

1. El estudiante ejecuta el lote en los nueve casos y conserva todas las evidencias.
2. Comprueba el primer texto antes de enviar el segundo.
3. Registra la entrega exacta de cada mensaje y cualquier pérdida, rechazo, duplicado o cambio de orden.
4. Calcula la tasa útil de cada ejecución y los resultados agregados de cada escenario.
5. Si el candidato no cumple los objetivos, prueba otro valor de la actividad 3. Conserva también los resultados anteriores.

### Objetivos medidos

- Recuperar el primer mensaje de las nueve ejecuciones sin necesitar un segundo envío.
- Recuperar exactamente al menos 29 de los 30 mensajes de cada escenario, agrupando sus tres semillas.
- Conservar los espacios y Unicode de los mensajes entregados correctamente.
- Justificar la selección del preámbulo mediante los candidatos realmente probados.
- Explicar qué controles de la actividad 5 permiten confiar en la interpretación del resultado.

Estos son objetivos de la tarea. El estudiante registra los resultados obtenidos, aunque no alcancen los objetivos.
Las nueve ejecuciones no prueban funcionamiento para cualquier canal ni permiten afirmar una probabilidad de error universal.
La calidad del diagnóstico y la reproducibilidad forman parte de la evaluación.

| Escenario | Semilla | Preámbulo, bytes | Primer mensaje exacto | `TX` | `DET` | `RX` | `OK` | Entregas exactas | Muestras del lote | Tasa útil, bits/s |
|---|---|---|---|---|---|---|---|---|---|---|
| Referencia | 17 | | | | | | | | | |
| Referencia | 42 | | | | | | | | | |
| Referencia | 83 | | | | | | | | | |
| Desajustes combinados | 17 | | | | | | | | | |
| Desajustes combinados | 42 | | | | | | | | | |
| Desajustes combinados | 83 | | | | | | | | | |
| Combinación con ruido | 17 | | | | | | | | | |
| Combinación con ruido | 42 | | | | | | | | | |
| Combinación con ruido | 83 | | | | | | | | | |

Para agregar tasas útiles se suman los bytes útiles y los tiempos de los lotes correspondientes.
No se promedian tasas de registros con duraciones diferentes sin justificar la ponderación.

## Entrega y criterios de evaluación

El estudiante entrega:

1. **Flowgraph reproducible:** archivo `.grc` con su `ID` exclusivo, configuración final y versiones de GNU Radio y Python declaradas.
2. **Informe PDF:** hipótesis, cálculos, tablas completas, diagnóstico de un fallo y justificación del preámbulo seleccionado.
3. **Resultados CSV:** caso, candidato, semilla, mensaje esperado, entrega exacta, contadores y muestras; incluye también los intentos fallidos.
4. **Referencias de texto y registros completos:** permiten verificar Unicode, espacios, orden y contenido sin depender de capturas.
5. **Capturas seleccionadas:** constelaciones, frecuencia, período y resumen de un caso representativo. Se añade la observación que sustenta el diagnóstico del fallo.

El informe distingue datos configurados, mediciones, cálculos e interpretación.
Los promedios de frecuencia y período deben proceder de datos numéricos.
Una lectura de una captura se identifica como aproximada.

Se evalúan la explicación de las funciones, el control de variables, la coherencia de unidades, la trazabilidad de los resultados y el diagnóstico.
Una conclusión debe indicar las condiciones que la sostienen.

## Referencias para resolver la tarea

- [Laboratorio 3: secciones 16 a 24](index.md#16-detectar-el-comienzo-y-la-longitud-desde-los-bits): formato, detección, canal, sincronización e integración.
- [Mapa visual de los 24 pasos](clase-enlace-digital.md): ubicación de cada función en el enlace.
- [Correlate Access Code - Tag Stream, implementación de GNU Radio](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-digital/lib/correlate_access_code_bb_ts_impl.cc): acceso, cabecera duplicada y longitud del paquete.
- [Burst Shaper, documentación de GNU Radio](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-digital/include/gnuradio/digital/burst_shaper.h): ceros añadidos y actualización de la longitud.
- [Costas Loop, detector BPSK de GNU Radio](https://github.com/gnuradio/gnuradio/blob/v3.10.12.0/gr-digital/lib/costas_loop_cc_impl.h#L63-L71): error de fase y ambigüedad de polaridad.

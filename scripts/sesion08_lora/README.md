# Sesión 08: LoRa y LoRaWAN

Ejecutar los comandos desde la raíz del repositorio `sdr`, con Radioconda
activo. Las rutas de muestras e informes parten de esa raíz.

| Archivo | Función |
|---|---|
| `inspeccionar_lora.py` | Sigue la señal I/Q hasta la cabecera, las matrices del cuerpo, los bytes y el CRC. |
| `extraer_mensaje.py` | Lee los 20 bytes del inspector y guarda la trama y el mensaje cifrado con los nombres de entrega. |
| `lora_presentacion.py` | Presenta las transiciones en tablas por bloque; lo utiliza el inspector. |
| `crc_lora.py` | Cálculo compartido del CRC físico para el inspector y la simulación de replay. |
| `simular_replay.py` | Compara un receptor vulnerable con otro que controla FCnt; simula repetición y alteraciones sobre bytes. |
| `verificar_lorawan_iq.py` | Genera el I/Q didáctico y comprueba la cadena de recepción y los controles de referencia. |
| `verificar_lorawan.py` | Interpreta tramas de datos LoRaWAN y verifica MIC y descifrado con claves conocidas. |
| `verificar_lorawan_brno.py` | Verifica el PCAP de Brno, incluido el material complementario de OTAA. |
| `verificar_lora_915.py` | Recibe las capturas I/Q reales de OSU o STU; comprueba la capa física LoRa. |

La práctica obligatoria y las diferencias entre las fuentes se explican en
[la lección de la sesión 08](../../docs/sessions/06/clase6.md).

## Preparar la muestra

```bash
python scripts/sesion08_lora/verificar_lorawan_iq.py --salida output/lorawan-iq
```

## Seguir las transiciones

```bash
python scripts/sesion08_lora/inspeccionar_lora.py --etapa simbolos
python scripts/sesion08_lora/inspeccionar_lora.py --etapa cabecera
python scripts/sesion08_lora/inspeccionar_lora.py --etapa gray
python scripts/sesion08_lora/inspeccionar_lora.py --etapa desentrelazado --bloque 1
python scripts/sesion08_lora/inspeccionar_lora.py --etapa fec --bloque 1
python scripts/sesion08_lora/inspeccionar_lora.py --etapa relleno --bloque 7
python scripts/sesion08_lora/inspeccionar_lora.py --etapa bytes
python scripts/sesion08_lora/inspeccionar_lora.py --etapa blanqueo
python scripts/sesion08_lora/inspeccionar_lora.py --etapa crc
python scripts/sesion08_lora/inspeccionar_lora.py --etapa phypayload
```

Cada comando recibe la muestra completa y muestra la transición elegida.
Se puede ejecutar independientemente de los anteriores. Quitar `--bloque`
para mostrar todos los bloques de esa transición. El filtro está disponible
en `gray`, `desentrelazado`, `fec` y `relleno`.

Los informes y los bytes recuperados se guardan en `output/lorawan-iq/traza/`.
`--etapa contenido` muestra todas las transiciones del cuerpo; `--etapa todo`
añade los símbolos y la cabecera. Las opciones completas se consultan con:

```bash
python scripts/sesion08_lora/inspeccionar_lora.py --help
```

Las verificaciones de capturas reales y descifrado son material complementario.
Sus comandos y descargas se detallan en los README de `gnuradio/samples/`.

## Obtener los archivos de entrega sin construir un flujograma

Después de preparar la muestra:

```bash
python scripts/sesion08_lora/inspeccionar_lora.py --etapa phypayload
python scripts/sesion08_lora/extraer_mensaje.py
```

El extractor lee `output/lorawan-iq/traza/03_phypayload.bin` y guarda
`output/lorawan-iq/trama_recibida.bin` (20 bytes) y
`output/lorawan-iq/mensaje_cifrado.bin` (7 bytes cifrados en esta muestra).
No verifica MIC ni descifra. El flujograma GRC de la sección 7 es opcional;
para extraer de su resultado, usar `--entrada output/lorawan-iq/trama_recibida.bin`.

## Replay: dos políticas de Network Server ante las mismas tramas

No requiere preparar I/Q. Genera las lecturas didácticas `temp=25` (FCnt=4) y
`temp=80` (FCnt=5), y repite íntegramente la primera después de la segunda.

```bash
python scripts/sesion08_lora/simular_replay.py --etapa tramas
python scripts/sesion08_lora/simular_replay.py --etapa replay
python scripts/sesion08_lora/simular_replay.py --etapa controles
python scripts/sesion08_lora/simular_replay.py
```

Cada ejecución parte de cero y guarda los tres PHYPayload de 20 bytes, un
informe JSON y la tabla de la etapa en `output/lorawan-replay/`. `--salida`
permite cambiar el directorio. Los CRC se registran en el JSON, separados de
los archivos `.bin`. Las operaciones criptográficas y el CRC se calculan;
no se asignan resultados de validación prefijados.

La clase `Receptor` agrupa el CRC del gateway, las decisiones de MIC/FCnt del
Network Server y el descifrado/estado del Application Server. La diferencia
vulnerable/con FCnt corresponde al servidor de red. El modelo usa una sola
sesión con la parte alta de FCnt en cero y no simula RF, OTAA, ACK/NbTrans ni
persistencia. El control de
FCnt evita entregar otra vez el dato; no modela todas las acciones de un
servidor LoRaWAN frente a retransmisiones legítimas. Las claves públicas del
laboratorio las utilizan el emisor y los receptores; la función de replay solo
copia el paquete y no utiliza claves.

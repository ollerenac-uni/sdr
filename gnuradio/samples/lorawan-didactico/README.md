# LoRaWAN: verificación previa con I/Q generado

Este ejemplo comprueba la recuperación de una trama LoRaWAN 1.0.x completa,
su MIC (*Message Integrity Code*, código de integridad) y su dato de aplicación.
**La señal I/Q se genera con GNU Radio. No procede de una recepción por aire.**
La referencia de frecuencia de 915 MHz no acredita una prueba de RF ni una red US915.

El profesor eligió este ejemplo para la preparación de la clase 6, junto con
la [captura real de LoRa de OSU](../lora-915-osu/README.md).
La captura real permite estudiar LoRa PHY. El ejemplo generado añade la
verificación del MIC y el descifrado de LoRaWAN.

## Procedencia de la trama

La trama original aparece en el paquete 258 de `03_Brno_join.pcap`, del conjunto
[LoRaWAN Traffic Analysis Dataset](https://zenodo.org/records/8090619), de
Ales Povalac y Jan Kral, Brno University of Technology.
Los autores publican las claves del nodo experimental.
El PCAP contiene paquetes ya demodulados, no muestras I/Q.

| Campo | Valor |
|---|---|
| PHYPayload | `80dc5de60190040001dbf5a4e31239d05321687b` |
| DevAddr | `01e65ddc` |
| FCnt | `4` |
| FPort | `1` |
| NwkSKey de prueba pública | `e2898779a03de59e2317b149abf00238` |
| AppSKey de prueba pública | `59ca1ac91922887093bc7b236bd1b07f` |
| MIC | `5321687b` |
| Dato descifrado | `timeout` |

La trama conserva sus bytes originales. El ejemplo genera nuevas muestras a
1 Msps, con SF7, BW de 125 kHz, CR 4/5 y sync word `0x34`.
Esos parámetros describen la señal generada. No sustituyen los parámetros de
la recepción original de Brno: el paquete 258 se recibió a 867,9 MHz con SF8.

## Repetir la comprobación

Desde la raíz del repositorio, con Radioconda activo:

```bash
python scripts/verificar_lorawan_iq.py --salida output/lorawan-iq
```

El programa usa bloques existentes de GNU Radio y
[gr-lora_sdr](https://github.com/tapparelj/gr-lora_sdr/tree/a8143cb):

- Generación: `Vector Source`, `Stream to Tagged Stream`, `Whitening`,
  `Add header`, `Add crc`, `Hamming enc`, `Interleaver`, `Gray demapping`,
  `Modulate` y `Vector Sink`.
- Recepción del archivo finito: `File Source`, `LoRa Rx` y `Vector Sink`.
- Verificación posterior: `scripts/verificar_lorawan.py`, con AES y CMAC de
  la biblioteca `cryptography`.

El programa termina con código 0 si todos los controles pasan.
Guarda `verificacion.json`, dos archivos `.sigmf-data` y sus metadatos.
Los archivos I/Q permanecen fuera de Git.

| Control | Resultado comprobado |
|---|---|
| Trama correcta | CRC correcto, MIC correcto y dato `timeout` |
| Contenido alterado antes de generar el CRC | CRC correcto; MIC incorrecto |
| NwkSKey incorrecta | MIC incorrecto; no se descifra |
| AppSKey incorrecta | MIC correcto; dato descifrado distinto |
| Sync word de recepción `0x12` | Ninguna trama recuperada |

El informe de referencia está en [verificacion.json](verificacion.json).
Cada archivo generado contiene 113 920 muestras complejas, incluidos ceros
de apertura y cierre. La duración del archivo es 113,92 ms; no equivale al
tiempo de transmisión del paquete.

La prueba se ejecutó con GNU Radio 3.10.12.0, Python 3.12.9 y
`gnuradio-lora_sdr` de Radioconda, revisión `a8143cb`.

## Límites para la clase

- El ejemplo aplica las secciones 4.3 y 4.4 de la
  [especificación LoRaWAN 1.0.4](https://resources.lora-alliance.org/technical-specifications/ts001-1-0-4-lorawan-l2-1-0-4-specification).
  No implementa LoRaWAN 1.1, OTAA, ventanas de recepción ni protección contra replay.
- El verificador necesita el contador completo de 32 bits.
  Sin `--fcnt`, supone cero en sus 16 bits superiores y lo indica en el informe.
- Un MIC válido comprueba integridad con NwkSKey. No confirma AppSKey.
- La captura real de OSU a 915 MHz sigue siendo un ejemplo de LoRa PHY.
  Su texto de fingerprinting no se convierte en LoRaWAN por usar sync word `0x34`.
- La [lección de LoRa](../../../docs/sessions/06/clase6.md) usa el I/Q generado para medir chirps, comprobar el CRC y extraer el mensaje cifrado.

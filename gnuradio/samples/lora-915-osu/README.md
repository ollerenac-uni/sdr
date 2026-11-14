# Captura real de LoRa a 915 MHz: verificación previa a la clase 6

La captura se descargó del conjunto de Oregon State University **LoRa Device
Fingerprinting in the Wild**, escenario indoor, día 1, dispositivo 1,
grabación `IQ_1`. Los metadatos originales describen una recepción por aire con
USRP B210, a 915 MHz, del 29 de mayo de 2021. La documentación del conjunto
identifica transmisores Pycom y un ancho LoRa de 125 kHz.

Esta comprobación usa las muestras recibidas originales. No genera la señal ni
reemplaza sus datos por una simulación. El nombre local `.sigmf-data` sustituye
la extensión original `.dat`; los bytes descargados se conservan.

## Procedencia

- [Directorio de la grabación](https://research.engr.oregonstate.edu/hamdaoui/RFFP-dataset/LoRa-Dataset/Diff_Days_Indoor_Setup/Day1/Device1/).
- [Datos originales: IQ_1.dat](https://research.engr.oregonstate.edu/hamdaoui/RFFP-dataset/LoRa-Dataset/Diff_Days_Indoor_Setup/Day1/Device1/IQ_1.dat).
- [Metadatos originales: IQ_1.sigmf-meta](https://research.engr.oregonstate.edu/hamdaoui/RFFP-dataset/LoRa-Dataset/Diff_Days_Indoor_Setup/Day1/Device1/IQ_1.sigmf-meta).
- [Documento de descripción del dataset](https://research.engr.oregonstate.edu/hamdaoui/sites/research.engr.oregonstate.edu.hamdaoui/files/release_note_2021.pdf).

El documento conserva enlaces antiguos que devuelven 404. Los enlaces de esta
carpeta incluyen el nivel `LoRa-Dataset/` y funcionaron durante la descarga.

Atribución solicitada por los autores: Abdurrahman Elmaghbub y Bechir Hamdaoui,
“LoRa Device Fingerprinting in the Wild: Disclosing RF Data-Driven Fingerprint
Sensitivity to Deployment Variability”, *IEEE Access*, vol. 9,
pp. 142893–142909, 2021.
Los datos de terceros conservan sus condiciones de uso originales.

## Archivo y parámetros comprobados

| Parámetro | Valor |
|---|---|
| Archivo local | `IQ_1.sigmf-data` |
| Tamaño | 160 000 000 bytes (160 MB; aproximadamente 152.6 MiB) |
| Muestras complejas | 20 000 000 |
| Duración | 20 segundos |
| Formato leído | I/Q float32 little endian intercalados, `cf32_le` |
| Frecuencia central | 915 MHz |
| Tasa de muestreo | 1 000 000 muestras complejas/s |
| Ancho del canal LoRa | 125 kHz |
| Spreading factor | SF7 |
| Coding rate de las cabeceras recuperadas | 4/5 |
| Cabecera | Explícita |
| CRC de payload | Presente |
| Sync word | `0x34` |

SHA-256 de los datos:

```text
3a6ef845f8af169419d71753bdd9936cf3eaf75a0f5b6e098e6a5e11228dbd95
```

`IQ_1.sigmf-meta` conserva sin editar los metadatos originales, que usan un
esquema SigMF antiguo. No se presupone compatibilidad de ese JSON con lectores
SigMF actuales. La prueba usa `File Source` con los parámetros de la tabla.
Al ser ya muestras complejas float32, no utiliza el conversor `.cu8`.

## Descargar y repetir

Desde la raíz del repositorio:

```bash
mkdir -p gnuradio/samples/lora-915-osu
curl --fail --location --retry 2 \
  'https://research.engr.oregonstate.edu/hamdaoui/RFFP-dataset/LoRa-Dataset/Diff_Days_Indoor_Setup/Day1/Device1/IQ_1.dat' \
  --output gnuradio/samples/lora-915-osu/IQ_1.sigmf-data
sha256sum gnuradio/samples/lora-915-osu/IQ_1.sigmf-data
```

Con Radioconda activo, comprobar que el módulo se importa desde `gnuradio`:

```bash
python -c "from gnuradio import lora_sdr; print(lora_sdr.__file__)"
python scripts/verificar_lora_915.py \
  --salida output/verificacion-lora-915/repeticion.json
```

El receptor ejecuta GNU Radio 3.10 y los bloques de `gr-lora_sdr`, sin hardware,
GUI ni Throttle. Lee el archivo una sola vez. La cadena es:

```text
File Source (Complex, 1 Msps)
    → LoRa Rx (SF7, BW 125 kHz, sync 0x34, soft decoding)
        → Vector Sink (bytes y etiquetas frame_info)
        → Message Debug, puerto store (mensajes)
```

El bloque jerárquico `LoRa Rx` realiza sincronización, demodulación FFT,
Gray mapping, desentrelazado, decodificación Hamming, recuperación de cabecera,
dewhitening y verificación CRC.

El programa cuenta como válido un paquete completo con CRC presente y etiqueta
`crc_valid = True`. No basta con que se publique un mensaje: el módulo también
puede publicar payloads cuyo CRC es incorrecto. Termina con código 0 si recupera
algún paquete con CRC válido, o 1 si no recupera ninguno.

## Resultado de la comprobación

Prueba del 3 de noviembre de 2026, con GNU Radio 3.10.12.0 y Python 3.12.9:

- **48 tramas recuperadas y 48 paquetes con CRC válido**.
- 0 tramas con CRC incorrecto y 0 errores de cabecera entre las recuperadas.
- Payload de 255 bytes: 12 240 bytes recuperados en total.
- Un único payload distinto, repetido 48 veces.
- Comienzo literal del texto: `RF fingerpring Project for Lora devic`, seguido
  de caracteres `n`. Se conserva la escritura de la transmisión original.

El informe completo, con hash, parámetros, payload y etiquetas de cada trama,
está en [verificacion.json](verificacion.json).
El resultado no determina cuántos paquetes se transmitieron en total; por tanto,
no equivale a una medición de tasa de error de paquetes.

La palabra de sincronización se identificó primero usando el modo diagnóstico
del receptor: `[0]` omite temporalmente su comprobación y mostró los símbolos
de red 24 y 32, correspondientes a `0x34`. La prueba final usa `0x34` y mantiene
activa esa comprobación.

Se ejecutó además un control con el archivo completo y sync word `0x12`:

```bash
python scripts/verificar_lora_915.py --sync-word 0x12 \
  --salida output/verificacion-lora-915/control-sync-incorrecto.json
```

El resultado fue 0 tramas y código de salida 1, como queda registrado en
[control-sync-incorrecto.json](control-sync-incorrecto.json).

## Alcance para la futura clase

Esta captura acredita la recuperación de **LoRa PHY** a partir de una recepción
real a 915 MHz. El payload recuperado es un texto de prueba de fingerprinting;
no se ha validado como una trama LoRaWAN. Usar `0x34` tampoco demuestra por sí
solo que el protocolo transportado sea LoRaWAN.

La [lección de LoRa](../../../docs/sessions/06/clase6.md) usa una señal I/Q
generada a partir de una trama de Brno para estudiar la estructura LoRaWAN.
El programa que genera esa señal está en `scripts/verificar_lorawan_iq.py`.

La grabación binaria permanece local y está excluida de Git por la regla
`*.sigmf-data`. El programa, los metadatos, los informes y este documento sí
pueden versionarse para repetir la descarga y la prueba en otra computadora.

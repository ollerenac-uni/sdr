# Continuación del curso SDR: preparación de la clase 6 sobre LoRaWAN

Trabaja en el repositorio `/home/user/Teaching/uni/2026/sdr`, rama `main`.
Comunícate con el usuario en español. Antes de modificar archivos, revisa
`git status` y los commits recientes: el curso se actualiza desde dos máquinas.
Conserva los cambios del usuario y consulta las instrucciones locales aplicables.

## Objetivo del usuario y alcance alcanzado

El usuario quiere dedicar la clase 6 a la decodificación de LoRaWAN. No tenía
capturas a 915 MHz, por lo que pidió primero descargar una captura real y
comprobar su decodificación con GNU Radio antes de preparar la clase.

**Esa comprobación ya se completó para LoRa PHY:** se descargó una recepción
real a 915 MHz y se recuperaron 48 paquetes con CRC válido. La carga es texto de
prueba de fingerprinting; no se ha validado como LoRaWAN. No presentes este
resultado como recuperación del MIC, descifrado o funcionamiento de una red
LoRaWAN. La clase 6 todavía no se ha creado ni se ha modificado el syllabus
para incorporarla.

El usuario pidió guardar estos avances con commit y push, y añadir este archivo
para que otro agente pueda retomar el trabajo. Consulta Git para identificar el
commit que contiene estos archivos y confirmar su sincronización con el remoto.

## Captura descargada y procedencia

Carpeta local:

`/home/user/Teaching/uni/2026/sdr/gnuradio/samples/lora-915-osu/`

- `IQ_1.sigmf-data`: datos originales descargados, 160 000 000 bytes.
- `IQ_1.sigmf-meta`: metadatos originales, conservados sin editar.
- `README.md`: procedencia, descarga, parámetros, reproducción y límites.
- `verificacion.json`: informe de la prueba completa con sync word correcto.
- `control-sync-incorrecto.json`: informe del control con sync word incorrecto.

Procedencia: Oregon State University, dataset de Abdurrahman Elmaghbub y Bechir
Hamdaoui, *LoRa Device Fingerprinting in the Wild*, escenario indoor, día 1,
dispositivo 1, grabación `IQ_1`. Los metadatos describen recepción por aire con
USRP B210 del 29 de mayo de 2021.

Directorio público vigente:

https://research.engr.oregonstate.edu/hamdaoui/RFFP-dataset/LoRa-Dataset/Diff_Days_Indoor_Setup/Day1/Device1/

El archivo original se llama `IQ_1.dat`; localmente se guardó como
`IQ_1.sigmf-data`, conservando exactamente sus bytes. Los enlaces antiguos del
PDF omiten el nivel `LoRa-Dataset/` y devuelven 404. Las instrucciones de descarga
vigentes y la referencia bibliográfica están en el README de la captura.

SHA-256 de los datos:

```text
3a6ef845f8af169419d71753bdd9936cf3eaf75a0f5b6e098e6a5e11228dbd95
```

La captura binaria está excluida de Git por `*.sigmf-data`. En otra máquina será
necesario descargarla con las instrucciones del README y comprobar el hash.
Los metadatos usan un esquema SigMF antiguo con un contenedor `_metadata`;
no presupongas compatibilidad con lectores SigMF modernos. La prueba utiliza
`File Source` con formato complejo float32 y parámetros explícitos.

## Entorno y receptor ya comprobados

Python utilizado: `/home/user/radioconda/bin/python`, versión 3.12.9.
GNU Radio: 3.10.12.0.

El módulo ya está instalado en Radioconda y se importa así:

```python
from gnuradio import lora_sdr
```

No confundas ese import con un módulo de nivel superior llamado `lora_sdr`.
No se instalaron paquetes ni se cambió el entorno para realizar esta prueba.

Parámetros:

| Parámetro | Valor |
|---|---|
| Frecuencia central | 915 MHz |
| Tasa de muestreo | 1 Msps |
| Duración | 20 segundos, 20 millones de muestras complejas |
| Formato | `cf32_le`, I/Q float32 intercalados |
| Ancho de canal | 125 kHz |
| Spreading factor | SF7 |
| Coding rate | 4/5 |
| Cabecera | Explícita |
| CRC de payload | Presente |
| Sync word | `0x34` |
| Soft decoding | Activado |
| LDRO mode | 2, automático |

Programa reproducible:

`/home/user/Teaching/uni/2026/sdr/scripts/verificar_lora_915.py`

Desde la raíz del repositorio:

```bash
/home/user/radioconda/bin/python scripts/verificar_lora_915.py \
  --salida output/verificacion-lora-915/repeticion.json
```

La cadena utiliza bloques reales de GNU Radio:

```text
File Source (Complex, sin repetición)
  → lora_sdr.lora_sdr_lora_rx
      → Vector Sink de bytes con etiquetas frame_info
      → Message Debug, puerto store
```

No usa hardware, GUI ni Throttle. El bloque jerárquico realiza sincronización,
demodulación FFT, Gray mapping, desentrelazado, Hamming, recuperación de cabecera,
dewhitening y comprobación CRC.

## Evidencia obtenida

En el archivo completo se recuperaron:

- 48 tramas, con cabeceras sin error.
- 48 paquetes con CRC válido, ninguno con CRC incorrecto entre los recuperados.
- 255 bytes por paquete: 12 240 bytes en total.
- Un único payload distinto, repetido 48 veces.
- Comienzo literal: `RF fingerpring Project for Lora devic`, seguido de `n`.
  No corrijas ese texto: así aparece en los bytes recibidos.

Para contar paquetes válidos, el programa comprueba presencia de CRC, etiqueta
`crc_valid = True` y longitud completa. **Recibir un mensaje no basta:**
`gr-lora_sdr` también puede publicar payloads cuyo CRC sea incorrecto.
Los 48 paquetes válidos no permiten afirmar una tasa de error de paquetes,
porque no se conoce el total transmitido en la ventana de captura.

La sincronización se identificó primero con `[0]`, modo diagnóstico que omite
su comprobación: mostró símbolos de red 24 y 32, correspondientes a `0x34`.
La prueba final sí exige `0x34`. Se hizo un control independiente con el mismo
archivo completo y `0x12`: produjo cero tramas y código de salida 1.
El caso correcto termina con código 0.

Comando del control, cuyo resultado esperado es código 1:

```bash
/home/user/radioconda/bin/python scripts/verificar_lora_915.py \
  --sync-word 0x12 \
  --salida output/verificacion-lora-915/control-sync-incorrecto.json
```

Los informes incluyen hash, versiones, parámetros y resultados. Los artefactos
exploratorios adicionales permanecen en `output/verificacion-lora-915/`, carpeta
ignorada por Git. Las pruebas completas, el control negativo, la compilación
de sintaxis del programa y la consistencia de los informes ya se verificaron.

## Continuación posible

Cuando el usuario pida continuar, resolver primero el alcance de LoRaWAN:
conseguir una captura de tramas LoRaWAN adecuada y claves conocidas cuando se
necesite descifrar, o construir tramas didácticas LoRaWAN completas. La captura
actual sirve para explicar chirps y recuperar paquetes LoRa, pero usar `0x34`
no demuestra por sí solo que la carga transportada sea LoRaWAN.

La clase 4 de referencia está en
`/home/user/Teaching/uni/2026/sdr/docs/sessions/04/clase4.md`: recepción FM y RDS,
bloques propios OOT, figuras y secciones desplegables. Revisa esa organización
antes de proponer el formato de una nueva clase. No crees ni publiques la clase
6 como si ya estuviera resuelta la parte LoRaWAN; conserva explícitamente la
distinción entre la validación física alcanzada y el trabajo que falta.

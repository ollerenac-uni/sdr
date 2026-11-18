# Continuación del curso SDR: sesión 8, Laboratorio #5 y verificaciones LoRaWAN

Trabaja en el repositorio `/home/user/Teaching/uni/2026/sdr`, rama `main`.
Comunícate con el usuario en español. Antes de modificar archivos, revisa
`git status` y los commits recientes: el curso se actualiza desde dos máquinas.
Conserva los cambios del usuario y consulta las instrucciones locales aplicables.

## Objetivo del usuario y alcance alcanzado

El usuario pidió inicialmente dedicar la «clase 6» a LoRaWAN; hoy figura como
sesión 8 y Laboratorio #5. No tenía
capturas a 915 MHz, por lo que pidió primero descargar una captura real y
comprobar su decodificación con GNU Radio antes de preparar la clase.

**La primera comprobación se completó para LoRa PHY:** se descargó una recepción
real a 915 MHz y se recuperaron 48 paquetes con CRC válido. La carga es texto de
prueba de fingerprinting; no se ha validado como LoRaWAN. No presentes este
resultado como recuperación del MIC, descifrado o funcionamiento de una red
LoRaWAN. Esta comprobación fue anterior a la creación de la lección actual.

**Actualización del 7 de noviembre de 2026:** el usuario pidió buscar una captura
real de LoRaWAN con claves conocidas y comprobar su decodificación y descifrado.
Se verificó LoRaWAN con claves publicadas en un PCAP real de Brno: MIC, OTAA,
derivación de claves y descifrado de `test message` y `timeout`. También se
descargó y decodificó con GNU Radio una captura I/Q real de LoRaWAN de STU,
pero las claves de esa otra sesión no se encontraron en sus materiales.
**Aún no hay una única captura I/Q real recibida por aire, con las claves de
su propia sesión, que permita verificar todo el recorrido hasta el texto claro.**
Sí existe ya un ejemplo I/Q generado con claves públicas y cadena completa.

## Estado integrado al 18 de noviembre de 2026

Se incorporó desde GitHub el commit `ae1d0e2`, que publicó la lección de LoRa
y la entrega. El archivo `docs/sessions/06/clase6.md` conserva el nombre
histórico, pero corresponde a la **sesión 08 y al Laboratorio #5** del índice.
La lección ya existe. El syllabus anterior está conservado como referencia
fuera del sitio publicado; la navegación vigente es `docs/sessions/index.md`.

La práctica obligatoria usa `output/lorawan-iq/correcto.sigmf-data`, generado
por GNU Radio desde el paquete 258 del PCAP de Brno. Sus bytes son reales,
pero esas muestras I/Q no proceden de una recepción por aire. Los 915 MHz son
una referencia de simulación; el paquete original fue recibido a 867.9 MHz,
con SF8, y el ejemplo se genera con SF7 y BW de 125 kHz.

La entrega exige un PDF, `trama_recibida.bin` de 20 bytes y
`mensaje_cifrado.bin` de 7 bytes, más el reto de FOpts resuelto en el PDF.
No exige descifrado, OTAA, claves de STU ni las descargas complementarias.
Conservar el plazo, el correo y el asunto de la convocatoria publicada.
`LoRa Rx` y `Tag Debug` verifican el CRC físico, no el MIC. La comparación de
MIC de la lección procede del verificador con claves públicas. La pregunta
de cierre se refiere al análisis de campos visibles sin utilizar esas claves.

El código común para MIC y descifrado de tramas de datos está en
`scripts/verificar_lorawan.py`. Tanto `verificar_lorawan_iq.py` como
`verificar_lorawan_brno.py` lo utilizan. El segundo conserva el lector de
PCAP/LoRaTap, OTAA y el formato original de su informe mediante un adaptador.
No volver a duplicar el cálculo del MIC ni el descifrado FRMPayload.

Las verificaciones reales de OSU, STU y Brno se conservan como material
complementario, con las diferencias de entrada y alcance documentadas en
la sección 11 de la lección y en los README de cada muestra.

El pedido actual es integrar y comprobar estos cambios y presentar un resumen
**antes de hacer commit**. Los avances de Brno/STU y esta integración están
pendientes de confirmación; no afirmar que están publicados sin consultar Git.

Comprobaciones de esta integración: 28 pruebas aprobadas de LoRaWAN, entrega,
numeración e índice; construcción estricta de MkDocs aprobada. El flowgraph
del alumno y el código literal de extracción producen los binarios de 20 y
7 bytes. El informe de Brno coincide con el anterior salvo la fecha: 809 MIC
válidos, 386 recepciones de aplicación descifradas y claves OTAA coincidentes.
Se repitieron además OSU (48 paquetes con CRC válido) y STU (2, con los mismos
PHYPayload del informe original). Los resultados de ejecución quedan en
`output/integracion-lorawan/`, fuera de Git.

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

## Actualización: LoRaWAN verificado en PCAP y en otra captura I/Q

### Brno: claves públicas, MIC, incorporación y texto claro

Carpeta: `/home/user/Teaching/uni/2026/sdr/gnuradio/samples/lorawan-brno/`.
Fuente: https://zenodo.org/records/8090619, LoRaWAN Traffic Analysis Dataset v2,
Ales Povalac y Jan Kral, Brno University of Technology.

Se descargó `pcap.zip` y se verificó su MD5 publicado:
`ad02cad7f3c697b56e30f3bd2090710e`. El ZIP queda en la carpeta ignorada
`output/verificacion-lorawan/`. Se extrajeron el PCAP `03_Brno_join.pcap` y los
archivos públicos `root_keys_lorawan` y `session_keys_lorawan`.
El PCAP tiene 3 128 888 bytes y SHA-256:
`185953b181a4e63bfbba2eec6b84f093de6cbe82c23062a33ca0dc0a30297a1e`.

Solo se analiza el nodo experimental de los autores, DevEUI
`70b3d5cee0000042`, DevAddr `01e65ddc`. Las claves están publicadas en Zenodo y
en los archivos del ZIP. No se realizó búsqueda de claves de otros nodos.

Programa: `/home/user/Teaching/uni/2026/sdr/scripts/verificar_lorawan_brno.py`.
Desde la raíz, con Radioconda activo:

```bash
python scripts/verificar_lorawan_brno.py \
  --salida output/verificacion-lorawan/brno-repeticion.json
```

Resultado guardado en `gnuradio/samples/lorawan-brno/verificacion.json`:

- 31 605 paquetes totales del PCAP; 857 recepciones con el DevAddr seleccionado.
- 809 recepciones con MIC válido, equivalentes a 471 PHYPayload distintos.
- 386 recepciones con payload de aplicación descifrado: 288 `timeout` y
  98 `test message`; equivalen a 246 PHYPayload de aplicación distintos.
- 15 tramas con estructura no admitida y 33 con MIC incorrecto, rechazadas.
- Se validaron los MIC de Join Request y Join Accept. Las dos claves derivadas
  del OTAA autenticado coinciden con las publicadas para esta sesión.

El script implementa LoRaWAN 1.0.x con FCnt32 alto cero para esta sesión,
observada desde su incorporación (contadores válidos 0 a 249). Usa
`cryptography`, ya disponible en Radioconda. No es un parser genérico de
LoRaWAN 1.1. Rechaza MIC incorrectos antes de entregar texto claro.
El informe incluye controles con NwkSKey incorrecta, ciphertext alterado y
AppSKey incorrecta. Esta última cambia el texto sin invalidar el MIC de datos;
la AppSKey correcta se comprueba además mediante la derivación OTAA.

Pruebas independientes guardadas en `tests/test_lorawan_crypto.py`:

```bash
python -m unittest discover -s tests -p test_lorawan_crypto.py -v
```

Cubren vectores AES-CMAC de RFC 4493, una trama pública de referencia, clave
incorrecta, alteración y tramas truncadas. El README de Brno explica la
descarga, los resultados y los límites. **Es PCAP con LoRaTap, no I/Q**: la
demodulación la hizo el sniffer de los autores.

### STU: LoRaWAN desde I/Q, claves de esa sesión pendientes

Carpeta: `/home/user/Teaching/uni/2026/sdr/gnuradio/samples/lorawan-stu/`.
Fuente: https://sites.google.com/view/benderisthegreatest/ddc-en/sdrlab-en.

Se descargó `lorawan_samples.dat`, una recepción real con USRP B210 entre un
nodo Arduino y un gateway Dragino. Localmente conserva los mismos bytes como
`lorawan_samples.sigmf-data`: 648 036 352 bytes, 81.004544 s a 1 Msps.
SHA-256: `f2b714f36c28481c3b0304aef5860b4836f8a984b54f650e9ba7e1c249009496`.
La frecuencia real es 868.1 MHz; no es una captura de 915 MHz.

Se amplió `scripts/verificar_lora_915.py` con `--frecuencia-central-hz`,
manteniendo los parámetros predeterminados de la comprobación original.
Para repetir el caso STU:

```bash
python scripts/verificar_lora_915.py \
  gnuradio/samples/lorawan-stu/lorawan_samples.sigmf-data \
  --frecuencia-central-hz 868100000 \
  --salida output/verificacion-lorawan/stu-repeticion.json
```

GNU Radio recuperó dos paquetes de 26 bytes con CRC válido, idénticos a los
publicados por el laboratorio: DevAddr `260b7848`, FPort 1, FCnt 2 y 3.
La fuente publica lecturas ya descifradas, pero no se encontraron las claves
de esa sesión en su página, flowgraph ni archivo de interpretación. **No se
descifró localmente STU ni se verificó su MIC**. Las claves de Brno pertenecen
a otra sesión. No uses los textos de referencia como prueba de descifrado local.

Los binarios I/Q y el PCAP permanecen locales e ignorados por Git. Los READMEs
permiten descargarlos en otra máquina. Estos avances se prepararon antes de
la lección que llegó con `ae1d0e2`; ahora se conservan como complemento de la
sesión 8. Consultar `git status` para distinguir archivos publicados y pendientes.

## Continuación posible

La cadena I/Q generado → LoRaWAN → MIC → texto claro ya está comprobada con
`scripts/verificar_lorawan_iq.py`, incluyendo los controles negativos. Para
probar esa misma cadena sobre una grabación recibida por aire, hace falta
obtener I/Q real con sus claves publicadas o conseguir del laboratorio STU
las claves de su sesión `260b7848`. No presentar las comprobaciones de STU
y Brno como si fueran una misma grabación ni describir el I/Q generado como
muestras reales recibidas.

La clase 4 de referencia está en
`/home/user/Teaching/uni/2026/sdr/docs/sessions/04/clase4.md`: recepción FM y RDS,
bloques propios OOT, figuras y secciones desplegables. Revisa esa organización
antes de proponer cambios de formato. La lección de LoRa ya existe: conservar
su práctica y su entrega, y distinguir el material obligatorio de las
verificaciones complementarias y de la captura real con claves aún pendiente.

# LoRaWAN real con claves públicas: Brno, incorporación OTAA y descifrado

Se descargó y comprobó la captura `03_Brno_join.pcap` del **LoRaWAN Traffic
Analysis Dataset**, publicado por Ales Povalac y Jan Kral, Brno University of
Technology: [Zenodo, versión v2, DOI 10.5281/zenodo.8090619](https://zenodo.org/records/8090619).
La captura comprende tráfico real del 30 de septiembre al 4 de octubre de 2022
en la banda EU868, e incluye un nodo experimental con claves publicadas.

**Entrada de esta prueba: paquetes PCAP con LoRaTap v1.** El sniffer ya realizó
la demodulación LoRa. Este archivo permite verificar y descifrar LoRaWAN, pero
no permite repetir la demodulación desde muestras I/Q ni observar sus chirps.
Esta comprobación lee el PCAP original. El ejemplo separado
[lorawan-didactico](../lorawan-didactico/README.md) genera I/Q a partir de una
de sus tramas para la práctica; esas muestras generadas no son la captura original.

## Descarga reproducible

Desde la raíz del curso:

```bash
mkdir -p output/verificacion-lorawan gnuradio/samples/lorawan-brno
curl --fail --location --retry 2 \
  'https://zenodo.org/records/8090619/files/pcap.zip?download=1' \
  --output output/verificacion-lorawan/pcap.zip
md5sum output/verificacion-lorawan/pcap.zip
```

El MD5 publicado por Zenodo y comprobado tras la descarga es
`ad02cad7f3c697b56e30f3bd2090710e`. El ZIP contiene 218 187 592 bytes.
Extraer únicamente los archivos necesarios:

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
destino = Path('gnuradio/samples/lorawan-brno')
with ZipFile('output/verificacion-lorawan/pcap.zip') as archivo:
    for nombre in ('03_Brno_join.pcap', 'root_keys_lorawan', 'session_keys_lorawan'):
        datos = archivo.read(nombre)
        if not nombre.endswith('.pcap'):
            datos = datos.replace(b'\r\n', b'\n')
        (destino / nombre).write_bytes(datos)
PY
```

El PCAP original mide 3 128 888 bytes y su SHA-256 es:

```text
185953b181a4e63bfbba2eec6b84f093de6cbe82c23062a33ca0dc0a30297a1e
```

Los archivos `root_keys_lorawan` y `session_keys_lorawan` conservan las claves
publicadas por los propios autores; solo se normalizan sus saltos de línea a LF.
La comprobación se limita al dispositivo
experimental y su sesión indicada; no intenta obtener claves de otros nodos.
El dataset y sus archivos conservan sus condiciones de uso originales.

## Claves y sesión comprobada

| Campo | Valor hexadecimal |
|---|---|
| DevEUI | `70b3d5cee0000042` |
| AppKey | `d494d49a7b4053302bdcf96f1defa65a` |
| DevAddr | `01e65ddc` |
| NwkSKey | `e2898779a03de59e2317b149abf00238` |
| AppSKey | `59ca1ac91922887093bc7b236bd1b07f` |

Estos valores corresponden al apartado `03_Brno_join` de la descripción de
Zenodo y a los archivos de claves incluidos en el ZIP.

## Repetir la comprobación

Con el Python de Radioconda, que ya contiene `cryptography` en la máquina usada:

```bash
python scripts/verificar_lorawan_brno.py \
  --salida output/verificacion-lorawan/brno-repeticion.json
```

El programa procesa el PCAP original sin modificarlo:

1. Extrae cada PHYPayload después de la cabecera LoRaTap.
2. Filtra el nodo experimental por DevEUI y DevAddr.
3. Verifica los MIC de Join Request y Join Accept con la AppKey publicada.
4. Abre Join Accept, deriva NwkSKey y AppSKey y las compara con las publicadas.
5. Verifica el MIC de cada trama de datos con NwkSKey.
6. Solo después de un MIC válido, descifra FRMPayload con AppSKey para FPort
   distinto de cero o con NwkSKey para FPort cero.

El análisis de tramas de datos, MIC y descifrado se comparte con
`scripts/verificar_lorawan.py`, también utilizado por el ejemplo I/Q generado.
`verificar_lorawan_brno.py` conserva la lectura LoRaTap y la verificación OTAA.
Su adaptador `descifrar_datos` mantiene los nombres de campos del informe
original para conservar los resultados y las herramientas que los consultan.

Se implementa LoRaWAN 1.0.x, con los 16 bits altos de FCnt32 iguales a cero para
esta sesión, observada desde su incorporación. Entre las tramas autenticadas
los contadores van de 0 a 249. No es un analizador general de sesiones LoRaWAN
1.1 ni de capturas con desbordamientos de contador.

La referencia del cálculo es la [especificación LoRaWAN 1.0.4](https://lora-alliance.org/wp-content/uploads/2021/11/LoRaWAN-Link-Layer-Specification-v1.0.4.pdf),
apartados 4.3.3, 4.4 y 6.2. El descifrado de Join Accept usa AES **encrypt**, ya
que el servidor lo cifra usando AES **decrypt**, como establece el protocolo.

## Resultado comprobado el 7 de noviembre de 2026

| Comprobación | Resultado |
|---|---:|
| Paquetes totales del PCAP | 31 605 |
| Recepciones con el DevAddr del nodo experimental | 857 |
| Tramas con estructura no admitida | 15 |
| Tramas con estructura admitida y MIC incorrecto | 33 |
| Recepciones con MIC válido | **809** |
| PHYPayload distintos con MIC válido | 471 |
| Recepciones con payload de aplicación descifrado | **386** |
| PHYPayload de aplicación distintos | 246 |
| Incorporación OTAA con claves derivadas coincidentes | **1** |

Las recepciones incluyen duplicados y retransmisiones: 809 no equivale a 809
mensajes distintos. Algunos paquetes válidos transportan comandos MAC o no
incluyen FRMPayload de aplicación.

Cargas de aplicación recuperadas:

| Texto ASCII | Hexadecimal | Recepciones |
|---|---|---:|
| `timeout` | `74696d656f7574` | 288 |
| `test message` | `74657374206d657373616765` | 98 |

Por ejemplo, para `test message`, el programa recupera:

```text
PHYPayload: 80dc5de60190060058a49a3565ea058c27a1785a0c8f741830
DevAddr:    01e65ddc
FCnt:       6
FPort:      88
MIC:        8f741830, recibido y calculado coinciden
Texto:      test message
```

El intercambio OTAA que produce las claves publicadas es:

```text
Join Request: 000000000000000000420000e0ced5b3707042eb21abc8
Join Accept:  20eb3f177794a1e9982152926b7fcadf6091c42e14835cba8b10fa02736418ee00
```

El informe con los resultados y ejemplos está en
[verificacion.json](verificacion.json).

## Controles realizados

- Una NwkSKey alterada invalida el MIC y el programa no entrega texto claro.
- Modificar un byte del ciphertext invalida el MIC.
- Una AppSKey alterada cambia el texto recuperado. El MIC de LoRaWAN 1.0.x
  protege el ciphertext con NwkSKey; por sí solo no valida AppSKey. Aquí se
  verifica además que AppSKey sea exactamente la derivada del OTAA autenticado.
- Las funciones se comprobaron contra vectores AES-CMAC de RFC 4493 y contra
  una trama de referencia de `nunomcruz/lora-packet-python` que descifra `test`.

Las pruebas de vectores y rechazo se pueden repetir sin descargar el PCAP:

```bash
python -m unittest discover -s tests -p test_lorawan_crypto.py -v
```

## Relación con las otras capturas del curso

La captura de OSU a 915 MHz valida LoRa PHY. La captura I/Q de STU a 868.1 MHz
permite recuperar dos tramas reales de LoRaWAN con GNU Radio, pero sus claves
de sesión no aparecen en los materiales consultados. Esta captura de Brno
valida la incorporación, la autenticación y el descifrado sobre paquetes PCAP
con claves públicas. Son evidencias de grabaciones diferentes; no constituyen
una sola cadena verificada desde I/Q hasta texto claro.

Para una práctica que exija completar todo el recorrido desde la misma
grabación, todavía falta una captura I/Q con las claves de su sesión.
La [sesión 8 y Laboratorio #5](../../../docs/sessions/06/clase6.md) ya existen.
La práctica obligatoria utiliza I/Q generado desde una trama de este PCAP y
se detiene en la extracción del mensaje cifrado. Esta verificación del PCAP
con OTAA y descifrado queda como material complementario, fuera de la entrega.

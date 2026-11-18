# Captura I/Q real de LoRaWAN: SDRLab, STU, 868.1 MHz

Se descargó `lorawan_samples.dat`, publicado por el laboratorio SDRLab de
IMICT FEI STU. La fuente describe tráfico entre un nodo Arduino y un gateway
Dragino conectado a The Things Network y una recepción con USRP B210.

Fuente: [SDRLab EN](https://sites.google.com/view/benderisthegreatest/ddc-en/sdrlab-en),
apartado “Virtual measurement - LoRa signal”.

## Descargar

Desde la raíz del curso:

```bash
mkdir -p gnuradio/samples/lorawan-stu
curl --fail --location --retry 2 \
  'https://drive.usercontent.google.com/download?id=1alY7cfrqMGfDEe-3C3owMWtmeK0nZtH4&export=download&confirm=t' \
  --output gnuradio/samples/lorawan-stu/lorawan_samples.sigmf-data
sha256sum gnuradio/samples/lorawan-stu/lorawan_samples.sigmf-data
```

El archivo local conserva los bytes del original; solo cambia la extensión.
Mide 648 036 352 bytes: 81 004 544 muestras complejas float32 intercaladas,
que a 1 Msps representan 81.004544 segundos. Su SHA-256 es:

```text
f2b714f36c28481c3b0304aef5860b4836f8a984b54f650e9ba7e1c249009496
```

La frecuencia central de **868.1 MHz**, el muestreo de **1 Msps**, el ancho de
**125 kHz** y **SF7** se obtuvieron del
[flowgraph original publicado por el laboratorio](https://drive.google.com/file/d/1RSRk8YFRijM09fCmSI7svZMNFW39jzln/view).
La prueba actual usa GNU Radio 3.10.12.0 y `gr-lora_sdr`, con sync word `0x34`,
cabecera explícita y soft decoding; no necesita ejecutar el flowgraph antiguo
de GNU Radio 3.7.

## Repetir la recuperación con GNU Radio

Con Radioconda activo:

```bash
python scripts/verificar_lora_915.py \
  gnuradio/samples/lorawan-stu/lorawan_samples.sigmf-data \
  --frecuencia-central-hz 868100000 \
  --salida output/verificacion-lorawan/stu-repeticion.json
```

Aunque el nombre del programa conserva la primera prueba a 915 MHz, el
argumento fija en esta ejecución la frecuencia real de la captura: 868.1 MHz.
No se ha desplazado ni reetiquetado la señal como una captura de 915 MHz.

El 7 de noviembre de 2026 se recuperaron **2 paquetes de 26 bytes, ambos con
CRC válido y cabecera sin error**. La cabecera LoRa informa CR 4/5.
Los PHYPayload recuperados fueron:

```text
4048780b2680020001c4e5094f5aec992259a6e6be173690cc51
4048780b2680030001f66577536aafb75415047a865054fe7466
```

Coinciden exactamente con los publicados por el laboratorio, después de retirar
de su salida antigua los tres bytes de cabecera LoRa y los dos del CRC físico.
Ambos corresponden a uplinks no confirmados del DevAddr `260b7848`, FPort 1,
con contadores 2 y 3. El informe está en [verificacion.json](verificacion.json).

## Límite de la comprobación

El laboratorio publica [un archivo de paquetes ya interpretados](https://drive.google.com/file/d/1jjkz4pudXvq-PwaCaKhAFbNeWcxR3Wk7/view)
con MIC y textos claros Cayenne LPP, pero las claves de esa sesión no aparecen
en la página, el flowgraph ni ese archivo. Esos textos claros de referencia
no sustituyen una ejecución local del descifrado.

Por tanto, con esta grabación se verificó localmente la recuperación I/Q →
PHYPayload con CRC válido; **no se verificó localmente su MIC ni su descifrado**.
Las claves de la captura de Brno pertenecen a otra sesión y no sirven para
esta grabación. El siguiente requisito para completar el recorrido con ella
es obtener del laboratorio las claves de la sesión `260b7848`.

El archivo I/Q se conserva localmente, excluido de Git. La captura y los
materiales de terceros conservan sus condiciones de uso originales.

Esta captura es material complementario de la
[sesión 8](../../../docs/sessions/06/clase6.md). La entrega del Laboratorio #5
usa el ejemplo generado `correcto.sigmf-data`; no exige descargar STU,
encontrar sus claves ni presentar un descifrado de esta sesión.

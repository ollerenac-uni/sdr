# Capturas RF verificadas antes de preparar las clases

Se descargaron capturas I/Q externas de cinco tecnologías y se comprobaron con
GNU Radio 3.10.12.0 y Python 3.12.9 de Radioconda. No se generaron señales
sintéticas ni se sustituyó la entrada por paquetes ya demodulados. Esta carpeta
conserva la verificación previa; ADS-B se desarrolla después en la
[sesión 9](../../../docs/sessions/09/clase9.md). La práctica de sensores OOK queda para el final.

El [catálogo](catalogo.json) fija las fuentes, formatos, tasas, frecuencias,
duraciones y SHA-256. El [informe](verificacion.json) conserva las tramas
recuperadas, campos interpretados, controles negativos y parámetros exactos.
Los binarios se guardan localmente y están excluidos de Git por las reglas
existentes de `*.cu8` y `*.sigmf-data`; las otras máquinas deben descargarlos.

## Reproducir

Desde la raíz del repositorio, usando el Python del entorno Radioconda que
contiene GNU Radio:

```bash
python scripts/descargar_capturas_rf.py
python scripts/verificar_capturas_rf.py todas
```

En la máquina donde se comprobó también se puede seleccionar el intérprete
explícitamente:

```bash
~/radioconda/bin/python scripts/descargar_capturas_rf.py
~/radioconda/bin/python scripts/verificar_capturas_rf.py todas
```

Para una sola tecnología:

```bash
python scripts/descargar_capturas_rf.py --solo ble
python scripts/verificar_capturas_rf.py ble --salida output/verificacion-ble.json
```

No se necesita SDR, Audio Sink, GUI ni Throttle: las pruebas son de archivos
finitos y se ejecutan tan rápido como permite el receptor. Se necesitan NumPy,
GNU Radio y, para el decodificador ADS-B de upstream, `colorama`, disponible en
el Radioconda comprobado. El descargador no instala paquetes ni cambia el entorno.

## Resultados y utilidad educativa

| Captura real | Entrada preparada | Resultado comprobado | Tema que permite trabajar |
|---|---|---|---|
| LaCrosse TX35DTH-IT | 868.2 MHz; 250 ksps; cu8; 0.262 s | Paquete `96a6412250`, CRC-8 válido; sensor 26, 24.1 °C, 34 % HR, coincidente con el JSON de referencia | Demodulación 2-FSK y recuperación de bits |
| NO-84 / PSAT, AX.25/APRS | 145.825 MHz; 24 ksps; I/Q complejo; 50.991 s | Cuatro tramas con CRC HDLC válido; posiciones, telemetría y mensaje de radioaficionado | Delimitadores, NRZI, bit stuffing y reconstrucción de tramas |
| AIS, canales A/B | 162 MHz; 250 ksps; I/Q complejo; 33.554 s | Más de 250 tramas con CRC HDLC válido en ambos canales; MMSI, posición, velocidad y rumbo | Campos de longitud fija, valores con signo y escalas |
| BLE, FCSC 2020 | 2461 MHz de referencia; 20 Msps; I/Q complejo; 59.4 ms | Seis anuncios, dos por canal 37/38/39, con CRC-24 válido | Whitening, orden de bits e integridad |
| ADS-B | 1090 MHz; 2.4 Msps; I/Q complejo; 3.495 s | Tramas DF17 con CRC-24 válido, sin corrección; identificadores ICAO, velocidad y altitud | Alternativa a AIS para interpretar campos y comprobar CRC |

Los conteos son resultados de estas cadenas y de los recortes indicados,
no inventarios de todos los mensajes transmitidos. La adquisición de reloj
y los bloques Python de upstream pueden cambiar algunos conteos según los
buffers del planificador. Para evaluar una práctica conviene exigir una trama
con CRC válido y campos concretos, no igualdad de un conteo total.

Una secuencia posible para las cinco clases es **2-FSK → AX.25/APRS → ADS-B →
BLE → OOK**. AIS queda como alternativa ya comprobada para la tercera clase.
ADS-B emplea modulación de posición de pulsos (PPM); este análisis de aeronaves
no adelanta la práctica final de sensores OOK.

## Procedencia y alcance de cada prueba

### LaCrosse

Fuente: [rtl_433_tests, TX29-IT y TX35DTH-IT](https://github.com/merbanan/rtl_433_tests/tree/1bd5af52f389f0150bda566437e7d5e17e11fc7f/tests/lacrosse/tx29-it_tx35dth-it).
El archivo contiene ambos sensores. La prueba se centra en el TX35 y compara
sus campos con el JSON publicado junto a la captura.

Cadena: File Source byte → conversor cu8 2:1 → Frequency Xlating FIR → Quadrature
Demod. Se prueban fases de muestreo dentro del período nominal de 105 μs y se
buscan sincronismo y CRC-8 en Python. Esto verifica la captura concreta;
todavía no es un receptor general con adquisición continua de reloj.

El README histórico del dataset dice OOK. Es una inconsistencia de esa fuente:
el [decodificador actual](https://github.com/merbanan/rtl_433/blob/3962dd97f9181f0dcd0e5bedd96ffd74060c19c3/src/devices/lacrosse_tx35.c)
declara `FSK_PULSE_PCM`, y aquí se recupera el paquete mediante discriminación
de frecuencia. No se utiliza esa mención histórica para clasificar la señal.

### AX.25/APRS y AIS

Fuente: [SDRangel, IQ Files](https://www.sdrangel.org/iq-files/), archivos
`no84.zip` y `ais.zip`. NO-84 se conserva completo; de AIS se extrae sólo el
prefijo fijado por el catálogo. El WAV de NO-84 tiene **dos canales I/Q**, no
audio AFSK previamente demodulado.

NO-84: File Source → FIR con desplazamiento de 1 kHz → Quadrature Demod para
FM → dos filtros centrados en 1200/2200 Hz → diferencia de potencias → Clock
Recovery MM → Binary Slicer → Differential Decoder → inversión NRZI → HDLC
Deframer. El último bloque elimina bit stuffing y sólo publica tramas con CRC
válido. El desplazamiento fijo ayuda con esta recepción satelital; no sustituye
un seguimiento general de Doppler.

AIS: File Source → dos FIR con desplazamiento ±25 kHz y decimación 5 → GMSK
Demod a 50 ksps, 9600 bit/s → Differential Decoder → inversión NRZI → HDLC
Deframer. No hace falta instalar `gr-ais` para esta prueba: la cadena utiliza
los bloques Core de GNU Radio. Los campos se interpretan sobre los octetos
restaurados, MSB primero, de acuerdo con el conversor NMEA de `gr-ais` y la
[descripción de mensajes AIS de NAVCEN](https://www.navcen.uscg.gov/ais-messages).

Ejemplo recuperado: MMSI `235093883`, latitud `51.458805`, longitud
`0.278396667`, velocidad `5.9 kn`, rumbo `276.4°`, compatible con la zona del
estuario del Támesis descrita para esta grabación.

### BLE

Fuente: [ANSSI, reto Bluetooth Low Energy de FCSC 2020](https://hackropole.fr/en/challenges/hardware/fcsc2020-hardware-bluetooth-low-energy/).
Se conserva el archivo `ble.sig` completo, renombrado como `.sigmf-data`, con
el mismo SHA-256 publicado por el organizador.

Es una captura especial: su autor desactiva el filtro antialias para que tres
canales separados aparezcan dentro de una sola grabación de 20 Msps. Sus
desplazamientos son +1 MHz, +5 MHz y −1 MHz para 37, 38 y 39. **No trasladar
estos desplazamientos a cualquier grabación BLE ni recomendar desactivar el
filtro como configuración normal de captura.**

Cadena: File Source complejo → Frequency Xlating FIR y decimación 5 → Quadrature
Demod → muestreo a 1 Mbit/s → búsqueda de Access Address → dewhitening por canal
→ extracción de PDU y comparación de CRC-24. La búsqueda y análisis binario se
realizan en Python después de la demodulación GNU Radio.

Seis anuncios pasan el CRC. Un bit alterado y una semilla de whitening
incorrecta fallan en los seis controles. Whitening no es cifrado y CRC no es
autenticación. No se han probado conexiones, salto de canal ni descifrado BLE.

Se conservan los bytes completos de los anuncios. Uno de los nombres UTF-8
tiene una longitud AD inconsistente en el material original: el analizador
señala el resto incompleto, aunque el CRC del paquete es correcto. No confundir
validez de CRC con validez de todos los campos de aplicación.

### ADS-B

Fuente: [SDRangel, IQ Files](https://www.sdrangel.org/iq-files/), `adsb.zip`,
grabación del 26 de noviembre de 2021. Se extrae un prefijo del WAV I/Q y se
convierte PCM16 a complex64 conservando la tasa original de 2.4 Msps.

Receptor: [mhostetter/gr-adsb, rama maint-3.10](https://github.com/mhostetter/gr-adsb/tree/b1b5b139c8849d0090319ba12140bdc88fce236f).
El descargador recupera tres bloques Python con versión y hashes fijados en
`tmp/rf-capturas/vendor/adsb/`. Conserva sus cabeceras GPL y no instala el módulo
globalmente ni modifica sus fuentes.

Cadena: File Source → Rational Resampler 10/3, a 8 Msps → Complex to Mag² →
promedio de potencia de cuatro muestras → ADS-B Framer, umbral 0.3 → ADS-B Demod
→ ADS-B Decoder. Se usa `Extended Squitter Only` y corrección de errores `None`.
Cada trama aceptada se comprueba además con una implementación independiente
del CRC Mode S; alterar un bit debe invalidarla.

Ejemplos recuperados: ICAO `4402f2`, `490d0b`, `3465d8`, `4ca92b`, `4ca809`.
El informe contiene los campos disponibles por mensaje. No se exige una pareja
CPR para producir coordenadas completas. Los tiempos del bloque upstream
corresponden a la reproducción, por lo que no se presentan como tiempos de
recepción de 2021.

**Ampliación para recuperar coordenadas:** se verificó después un prefijo más
largo de la misma grabación con una cadena que conserva las tramas en los
límites de bloque y calcula tiempos por índice de muestra. Produce **134 DF17
con CRC válido y 26 posiciones de nueve aeronaves**, contrastadas con pyModeS;
incluye un mapa interactivo. Véase [ADS-B: posiciones](../adsb-posiciones/README.md).
El conteo de mensajes publicados por el decodificador upstream anterior no
equivale al total de mensajes válidos presentes en las muestras: ese bloque
filtra resultados, incluidas primeras posiciones. La muestra corta también
contiene mensajes de posición; la ampliación proporciona más parejas CPR.

## Conversión, redistribución y límites

Los ZIP originales de AIS y ADS-B son grandes. El descargador descomprime
solamente el prefijo necesario, verifica su SHA-256 y convierte muestras
completas. No se verificó el CRC del ZIP completo para esos dos archivos.
Para NO-84 sí se comprueba el CRC32 del miembro completo. Los hashes de las
entradas convertidas permiten repetir exactamente el mismo recorte.

Se conservan las fuentes y atribuciones. La disponibilidad pública de una
grabación no establece por sí sola sus condiciones de redistribución. Este
repositorio publica el catálogo, metadatos, código y resultados; las muestras
se obtienen de los enlaces originales. Las dependencias descargadas se guardan
fuera de Git con sus avisos de licencia.

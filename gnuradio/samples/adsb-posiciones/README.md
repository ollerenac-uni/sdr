# ADS-B real: verificación de coordenadas y mapa

Verificación técnica que respalda la
[sesión 9 — Reverse Engineering a ADS-B](../../../docs/sessions/09/clase9.md).
Parte de muestras I/Q reales; no utiliza una lista de coordenadas como entrada.

## Muestra y procedencia

Fuente: [SDRangel, IQ Files](https://www.sdrangel.org/iq-files/), archivo
[`adsb.zip`](https://www.sdrangel.org/iq/adsb.zip). La fuente identifica la
grabación como paquetes ADS-B de aeronaves, a 2400 ksps, en WAV de 16 bits.
El miembro es `adsb.2021-11-26T15_03_30_573.wav`; su nombre indica el
26/11/2021, pero no especifica zona horaria.

Se descomprimen los primeros **134 217 728 bytes** del WAV y se convierten sus
pares I/Q PCM16 a complex64, dividiendo por 32768. No se generan ni remodulan
mensajes. El [catálogo de origen](origen.json) fija los hashes del prefijo y
del archivo convertido; no se afirma haber comprobado el CRC del ZIP completo.

| Propiedad | Valor |
|---|---|
| Archivo preparado | `adsb-sdrangel-posiciones.sigmf-data` |
| Frecuencia central | 1090 MHz |
| Tasa de muestras I/Q | 2.4 Msps |
| Formato | `cf32_le`, complejo de dos float32 little-endian |
| Muestras complejas | 33 554 378 |
| Duración según muestras/tasa | 13.980990833 s |
| Tamaño convertido | 268 435 024 bytes |
| SHA-256 convertido | `618f47716ba995438a9d997bb9aeb2053ad21c74014f4194dda982799ab21ff6` |

El binario está excluido de Git. En otra computadora se descarga desde la
fuente original con el comando siguiente; los metadatos SigMF se conservan
junto al archivo. La descarga del prefijo requiere menos transferencia que el
ZIP completo y necesita conexión a Internet.

## Repetir la verificación

Desde la raíz del repositorio, con el entorno Radioconda que contiene GNU Radio:

```bash
python scripts/sesion09_adsb/descargar_muestra.py
python scripts/sesion09_adsb/verificar_posiciones.py
```

Si `python` pertenece a otro entorno, usar `~/radioconda/bin/python` en ambos
comandos. Se comprobó con Python 3.12.9, GNU Radio 3.10.12.0 y NumPy de ese
entorno. No se requieren `gr-adsb`, hardware SDR, GUI ni Throttle. La prueba
usa aproximadamente 1 GB de espacio para la captura y la potencia intermedia,
además del espacio temporal de descarga.

La cadena ejecutada es:

1. **GNU Radio:** File Source complejo → Rational Resampler 10/3
   (2.4 → 8 Msps) → Complex to Mag² → archivo float32.
2. **Python/NumPy:** detectar los cuatro pulsos del preámbulo, integrar ambas
   mitades de cada bit PPM y comparar sus potencias; 8 muestras por bit.
3. Conservar únicamente DF17 de 112 bits con CRC-24 válido, **sin corregir bits**.
   Los bloques se solapan para conservar las tramas que cruzan sus límites.
4. Separar por ICAO, extraer campos CPR y combinar mensajes par/impar
   compatibles con separación de archivo de hasta 10 s. Se aplica CPR global
   sin introducir una posición conocida del receptor ni de las aeronaves.
5. Exportar las posiciones y representarlas en un mapa interactivo.

La salida predeterminada es `output/adsb-posiciones/`:

- `mapa.html`: filtro por aeronave, selección temporal y consulta de cada punto.
- `posiciones.csv` y `posiciones.geojson`: coordenadas y tramas par/impar de origen.
- `tramas.avr`: los mensajes recuperados completos en hexadecimal.
- `verificacion.json`: parámetros, controles, mensajes y posiciones.
- `potencia8.f32`: señal de potencia intermedia; ocupa unos 447 MB.

Para abrir el mapa, abrir `output/adsb-posiciones/mapa.html` con el navegador,
o ejecutar:

```bash
python -m http.server 8012 --bind 127.0.0.1 --directory output/adsb-posiciones
```

Luego visitar [el mapa local](http://127.0.0.1:8012/mapa.html). Leaflet 1.9.4
y los datos quedan incorporados en el HTML; el fondo de OpenStreetMap necesita
Internet. Los puntos y controles no dependen de un CDN de JavaScript.

## Resultado comprobado

| Resultado | Cantidad |
|---|---:|
| Tramas DF17 con CRC válido | 134 |
| Aeronaves detectadas por ICAO | 24 |
| Mensajes de posición aérea TC9–18 | 51 |
| Posiciones calculadas mediante CPR global | 26 |
| Aeronaves con coordenadas recuperadas | 9 |
| Controles de un bit alterado rechazados por CRC | 134 |

Ejemplo: ICAO `4402F2`, indicativo observado `EJU46DN`, produce una posición
`51.654968°, -0.949554°`, altitud barométrica 36 250 ft, a partir de:

```text
Par:   8d4402f258b9f270bbcdb62b2397
Impar: 8d4402f258bb25dcdbcf62e6e969
```

Las nueve aeronaves se ubican en el sur de Inglaterra, zona compatible con la
procedencia descrita por SDRangel. Esa información geográfica **no se usa para
calcular** las coordenadas. El [informe de referencia](verificacion.json)
conserva la evidencia completa de esta ejecución.

### Comprobación con otro decodificador

Se contrastaron todos los CRC y las 26 posiciones con **pyModeS 2.22.0**;
las coordenadas coinciden con tolerancia de `1e-9` grados. También se comparan
indicativos, altitud y velocidad/curso cuando esos campos están disponibles.
`rumbo_deg` en las exportaciones representa el curso sobre el suelo de TC19,
no el rumbo del fuselaje. La comparación de velocidad respeta el truncamiento
a nudos enteros que devuelve esa versión de pyModeS.

La dependencia es opcional y puede instalarse en una carpeta local ignorada
sin modificar el entorno principal:

```bash
python -m pip install --target tmp/adsb-posiciones/deps --no-deps 'pyModeS==2.22.0'
python scripts/sesion09_adsb/verificar_posiciones.py --pymodes-dir tmp/adsb-posiciones/deps
```

Referencias: [API de pyModeS](https://mode-s.org/pymodes/api/pyModeS.decoder.adsb.html),
[implementación CPR de pyModeS 2.22.0](https://github.com/junzis/pyModeS/blob/v2.22.0/src/pyModeS/decoder/bds/bds05.py)
y [explicación de CPR aéreo global, The 1090 MHz Riddle](https://mode-s.org/1090mhz/content/ads-b/3-airborne-position.html).

## Alcance y límites

- Es una captura histórica: el mapa no muestra vuelos actuales.
- Se comprueban DF17 y posiciones aéreas barométricas TC9–18; no se ha
  implementado aquí un receptor universal de todos los formatos Mode S.
- El tiempo se calcula por índice de muestra a la salida del remuestreador e
  incluye su retardo fijo. No es el reloj de reproducción ni una marca UTC
  original. No se ha validado la cadencia temporal original entre ráfagas:
  desplazamiento/tiempo de archivo no concuerda suficientemente con la
  velocidad TC19. Por eso no se deduce velocidad ni continuidad de vuelo a
  partir de esas diferencias. El mapa muestra puntos observados, sin interpolar.
- Las coordenadas se verificaron contra otra implementación de CPR; esto no
  constituye una comprobación externa contra radar o una trayectoria de referencia.
- Un CRC válido detecta errores de transmisión; no autentica al emisor.
- Se publican código, metadatos, hashes y resultados; la muestra se descarga
  del servidor original y no se incorpora al repositorio.

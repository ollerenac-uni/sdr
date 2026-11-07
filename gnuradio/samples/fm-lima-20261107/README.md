# Capturas FM/RDS de Lima — 7 de noviembre de 2026

Material del [Laboratorio #4: adaptación y diagnóstico FM/RDS](../../../docs/sessions/04/laboratorio-fm-rds.md).
Se adquirió con el RTL-SDR conectado a la computadora del profesor.
El dispositivo declaró Realtek RTL2838UHIDIR, RTL2832U y sintonizador R820T.

## Archivos

| Archivo | Centro RF | Tasa nominal | Ganancia | Duración nominal | Tamaño |
|---|---|---|---|---|---|
| `fm_lima_fc89p4MHz_2p048Msps_g20p7_30s.cu8` | 89.4 MHz | 2.048 Msps | 20.7 dB | 30 s | 122 880 000 bytes |
| `fm_lima_fc97p7MHz_2p048Msps_g29p7_30s.cu8` | 97.7 MHz | 2.048 Msps | 29.7 dB | 30 s | 122 880 000 bytes |
| `fm_lima_fc100p7MHz_2p048Msps_g29p7_30s.cu8` | 100.7 MHz | 2.048 Msps | 29.7 dB | 30 s | 122 880 000 bytes |
| `fm_lima_fc101p7MHz_2p048Msps_g29p7_30s.cu8` | 101.7 MHz | 2.048 Msps | 29.7 dB | 30 s | 122 880 000 bytes |

Cada muestra compleja ocupa dos bytes sin signo, en orden I, Q.
Cada archivo contiene 61 440 000 muestras complejas.
La duración se calcula con la tasa nominal; no se midió el error del oscilador del dongle.
Los archivos finales terminaron con código cero y tamaño exacto.
Eso no certifica que no existan pérdidas de muestras no notificadas por la herramienta.

Las grabaciones están excluidas de Git y se distribuyen desde la [carpeta de muestras del laboratorio 4](https://drive.google.com/drive/folders/18q_erbax0A_yiAJLknYfB9azaINqcDgJ?usp=sharing).
`capturas.json` registra comandos, parámetros y SHA-256.
`SHA256SUMS.txt` permite verificar las cuatro descargas; `LEEME-LAB04.txt` explica su ubicación y uso.
Las grabaciones cortas de exploración permanecen en `output/fm-peru-20261107/`, fuera de Git.

## Recepción comprobada

La validación con AGC, correspondiente al `fm.grc` vigente y al plan de tasas del laboratorio, produjo:

| Emisora | Frecuencia | Grupos en 30 s | PI | PS observado |
|---|---|---|---|---|
| Felicidad | 88.9 MHz | 273 | `F030` | Segmentos `FELICIDA`, `ICIDAD` y `DAD`. |
| Onda Cero | 98.1 MHz | 101 | `3F3F` | `ONDACERO`. |
| Panamericana | 101.1 MHz | 270 | `22FF` | `PANAMERI` y `....CANA`. |
| Oxígeno | 102.1 MHz | 44 | `F026` | `OXIGENO`. |

Los registros están en `felicidad-agc-30s.json`, `ondacero-agc-30s.json`, `panamericana-30s.json` y `oxigeno-30s.json`.
El alumno no necesita igualar esas cuentas para demostrar recepción válida.

Las primeras pruebas de las capturas A y B, realizadas antes de añadir el AGC, se conservan como antecedente:

| Archivo | Frecuencia seleccionada | Grupos válidos | PI | PS y RadioText |
|---|---|---|---|---|
| Centro 89.4 MHz | 88.9 MHz | 274 | `F030` | PS variable con segmentos de FELICIDAD; RT: `Me siento bien`. |
| Centro 89.4 MHz | 89.7 MHz | 0 | — | Sin campos RDS recuperados con esta cadena. |
| Centro 97.7 MHz | 98.1 MHz | 95–97 | `3F3F` | `ONDACERO`; RT: `Ozuna - Se preparo`. |
| Centro 97.7 MHz | 97.3 MHz | 12 | `956B` | Sin PS ni RT completos. |

Los resultados corresponden a GNU Radio 3.10.12.0 y a los parámetros del programa de validación.
Los textos identifican el instante grabado. No describen la programación actual.
Los PS parciales o cambiantes se conservan sin reemplazarlos por un nombre escrito manualmente.
La validación repetida de Onda Cero produjo 97 y 95 grupos, con los mismos campos recuperados.
El JSON conserva la ejecución más reciente. La evaluación no exige igualar un contador exacto.

El barrido espectral cubrió 87.5–108 MHz. Después se intentó decodificar 30 frecuencias candidatas durante ocho segundos cada una.
Se priorizaron RPP 89.7, Exitosa 95.5, Nacional 103.9 y PBO 91.9 MHz.
Ninguna de esas cuatro pruebas produjo grupos válidos con la cadena utilizada.
La prueba más larga de RPP tampoco produjo grupos válidos.

El barrido obtuvo 90 grupos en 88.9 MHz, 23 en 98.1 MHz, cinco en 97.3 MHz y uno en 102.1 MHz.
La detección de 102.1 MHz fue aislada y no incluyó un PS completo.
Ese barrido inicial no se utilizó para identificar la emisora.
La captura posterior dedicada de 30 segundos sí recuperó `OXIGENO`, como muestra la tabla con AGC.
`barrido-rds.json` conserva los resultados y los parámetros de las 30 pruebas.
El archivo registra el mejor resultado cuando se ensayó una frecuencia con dos ganancias.
Las potencias de `rtl_power` son relativas y no se presentan como medidas RF calibradas.

**Cero grupos recuperados no demuestra ausencia de RDS.** La antena, el nivel recibido, el intervalo y la adquisición afectan la prueba.
Este es un barrido local de Lima, no un inventario nacional de transmisores RDS.

## Reproducir la validación

Con Radioconda y los módulos `gnuradio.cbs33m`, `rds` y `satellites` instalados, desde la raíz:

```bash
python scripts/validar_captura_fm_rds.py gnuradio/samples/fm-lima-20261107/fm_lima_fc89p4MHz_2p048Msps_g20p7_30s.cu8 --center-freq 89400000 --station-freq 88900000
python scripts/validar_captura_fm_rds.py gnuradio/samples/fm-lima-20261107/fm_lima_fc97p7MHz_2p048Msps_g29p7_30s.cu8 --center-freq 97700000 --station-freq 98100000
```

Para repetir la validación del receptor vigente, el estudiante añade `--agc-rds`.
Las capturas C y D utilizan centros RF de `100700000` y `101700000` Hz, y emisoras objetivo de `101100000` y `102100000` Hz.

El programa procesa el archivo una sola vez y publica un resumen JSON.
No utiliza GUI, `Audio Sink` ni `Throttle`; procesa a la velocidad de la computadora.
La opción `--audio-wav` exporta audio mono PCM de 16 bits a 48 ksps, con factor de volumen 0.2.
El código de salida es cero si recupera al menos un grupo válido y uno si no recupera ninguno.
Un grupo aislado requiere más evidencia antes de identificar una emisora.

La referencia usa estas tasas y filtros:

| Etapa | Configuración | Salida |
|---|---|---|
| Canal FM | FIR, corte 100 kHz, transición 20 kHz, decimación 8. | 256 ksps Complex. |
| Audio | FIR, corte 16 kHz, transición 2 kHz, decimación 4. | 64 ksps Float. |
| Audio | `Rational Resampler`, interpolación 3, decimación 4. | 48 ksps Float. |
| RDS | Rotación −57 kHz a 256 ksps; FIR, corte 3 kHz, transición 1 kHz, decimación 16. | 16 ksps Complex. |
| RDS | Ganancia 20; Costas de orden 2; RRC, alpha 1 y 101 coeficientes. | 16 ksps Complex. |
| Chips | Gardner, muestras/chip `16000/2375`, ancho de lazo 0.01. | 2375 muestras/s. |
| Bits | Manchester, bloque 32; slicer; diferencial módulo 2. | 1187.5 bits/s nominales. |

El programa conserva el deénfasis de 75 μs del montaje de referencia.
Ese valor no constituye una medición del preénfasis de cada emisora recibida.
La longitud finita de los filtros y el cierre del procesamiento afectan el número final de muestras de audio.
La referencia produjo 1 439 967 muestras a 48 ksps por archivo.

Dos controles del reto se ejecutaron sobre el archivo A:

```bash
python scripts/validar_captura_fm_rds.py gnuradio/samples/fm-lima-20261107/fm_lima_fc89p4MHz_2p048Msps_g20p7_30s.cu8 --center-freq 89400000 --station-freq 88900000 --interp-rds 19 --remuestreo-decim-rds 16
python scripts/validar_captura_fm_rds.py gnuradio/samples/fm-lima-20261107/fm_lima_fc89p4MHz_2p048Msps_g20p7_30s.cu8 --center-freq 89400000 --station-freq 88900000 --tasa-declarada-rotador-rds 300000
```

- RDS remuestreado a 19 ksps, con RRC y reloj actualizados: **267 grupos**, PI `F030`, PS y RT coherentes.
- Tasa incorrecta de 300 ksps declarada solo en el rotador RDS: **cero grupos** y el mismo RMS de audio que la referencia.

Los JSON de esta carpeta registran cada comprobación.
La opción de tasa declarada incorrecta existe para reproducir el control negativo; el montaje normal usa la tasa real del canal.

## Fuentes primarias

- [RPP: frecuencias por ciudad](https://rpp.pe/audio/estaciones).
- [PBO: 91.9 FM en Lima](https://pbo.pe/audio/).
- [Radio Nacional: estaciones](https://www.radionacional.gob.pe/estaciones).
- [Osmocom: código de rtl_sdr](https://github.com/osmocom/rtl-sdr/blob/master/src/rtl_sdr.c).
- [Osmocom: código de rtl_power](https://github.com/osmocom/rtl-sdr/blob/master/src/rtl_power.c).
- [gr-rds: validación y publicación de grupos](https://github.com/bastibl/gr-rds/blob/maint-3.10/lib/decoder_impl.cc).

Las páginas de las emisoras orientan la sintonía. La presencia de RDS se comprobó en las muestras recibidas.

# Verificación previa de ADS-B

Estos programas comprueban una captura real y permiten seguir las etapas de la
[sesión 9](../../docs/sessions/09/clase9.md). La procedencia, los resultados y los límites están en
[`gnuradio/samples/adsb-posiciones/README.md`](../../gnuradio/samples/adsb-posiciones/README.md).

Desde la raíz del repositorio, con el Python de Radioconda:

```bash
python scripts/sesion09_adsb/descargar_muestra.py
python scripts/sesion09_adsb/verificar_posiciones.py
```

| Archivo | Función |
|---|---|
| `descargar_muestra.py` | Descargar el prefijo fijado por SHA-256 y preparar I/Q y metadatos SigMF |
| `receptor.py` | Procesar I/Q con GNU Radio, recuperar bits PPM, validar CRC e interpretar CPR |
| `verificar_posiciones.py` | Ejecutar controles, contrastar opcionalmente con pyModeS y exportar resultados |
| `mapa.html` | Plantilla del mapa; el programa incorpora datos y Leaflet en el HTML final |
| `inspeccionar_adsb.py` | Exponer muestras, medias PPM, bits, campos, pasos CRC y cálculos CPR de una trama real |
| `generar_figuras.py` | Regenerar las figuras, el explorador PPM y la copia del mapa de la sesión 9 |
| `ppm-interactivo.html` | Plantilla del explorador de medias de potencia y decisiones binarias |
| `muestras.py` | Catálogos de la lección y del recorte real del laboratorio 6 |
| `preparar_laboratorio.py` | Preparar mensajes, evidencias PPM y casos de CRC conservando el código del alumno |
| `plantilla_analisis.py` | Función de extracción de campos por completar y punto de entrada del alumno |
| `laboratorio.py` | Conectar los campos propios con CPR, validar resultados y generar el mapa |
| `vendor/leaflet-1.9.4/` | Leaflet con licencia BSD, fuente y hashes registrados en `origen.json` |

La salida se guarda en `output/adsb-posiciones/`. La carpeta de salida y los
binarios de muestras están ignorados por Git. La plantilla `mapa.html` de esta
carpeta no contiene datos; abrir el HTML generado en la carpeta de salida.

Pruebas automatizadas de PPM, límites entre bloques, CRC, CPR y exportación:

```bash
python -m pytest tests/test_adsb_posiciones.py -q
```

Estas pruebas requieren pytest y el entorno GNU Radio/NumPy. La verificación
de la captura real se realiza con el comando `verificar_posiciones.py` anterior.

Para seguir cada transición de la sesión 9:

```bash
python scripts/sesion09_adsb/inspeccionar_adsb.py --etapa todas
python scripts/sesion09_adsb/inspeccionar_adsb.py --etapa ppm --bloque 1
python scripts/sesion09_adsb/inspeccionar_adsb.py --etapa crc --bloque 7
```

Los grupos B1–B7 tienen 16 bits cada uno y sirven para presentar resultados;
no son bloques FEC del protocolo. Las tablas y `traza.json` se guardan en
`output/adsb-posiciones/traza/`. `--listar` muestra los mensajes de la captura
y `--hex` permite seleccionar uno de ellos.

Después de `--etapa todas` sobre la trama predeterminada, se pueden regenerar
las figuras con `python scripts/sesion09_adsb/generar_figuras.py` (requiere
Matplotlib). Ese comando actualiza los archivos generados de
`docs/sessions/09/figures/` y `docs/sessions/09/animaciones/`.

## Laboratorio 6

El laboratorio usa otro tramo del mismo WAV original, 14–27 s, sin
solapamiento con la lección. La guía y la rúbrica están en
[`laboratorio-adsb.md`](../../docs/sessions/09/laboratorio-adsb.md).

```bash
python scripts/sesion09_adsb/descargar_muestra.py --muestra laboratorio
python scripts/sesion09_adsb/preparar_laboratorio.py
python scripts/sesion09_adsb/preparar_laboratorio.py --inspeccionar 1 --etapa ppm --bloque 1
python scripts/sesion09_adsb/preparar_laboratorio.py --casos-crc
```

El alumno completa `extraer_campos(bits)` en la copia
`output/adsb-laboratorio/mi_analisis.py`. El soporte valida sus campos y
los utiliza para CPR y el mapa. No se completa automáticamente la función.
Repetir la preparación conserva el archivo del alumno; `--reprocesar` solo
regenera la recepción y sus datos.

La verificación de referencia es independiente de la carpeta del alumno:

```bash
python scripts/sesion09_adsb/verificar_posiciones.py --muestra laboratorio
```

Guarda la referencia en `output/adsb-laboratorio-referencia/`. Puede usarse con
`inspeccionar_adsb.py --directorio output/adsb-laboratorio-referencia`.
Los parámetros y resultados del nuevo recorte están en
[`adsb-laboratorio/`](../../gnuradio/samples/adsb-laboratorio/README.md).

```bash
python -m pytest tests/test_adsb_posiciones.py tests/test_adsb_laboratorio.py -q
```

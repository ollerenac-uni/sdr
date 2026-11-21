# Muestra real del laboratorio 6 — Radar bajo sospecha

La [tarea](../../../docs/sessions/09/laboratorio-adsb.md) utiliza los segundos
**14–27** del WAV `adsb.2021-11-26T15_03_30_573.wav`, publicado en
[SDRangel IQ Files](https://www.sdrangel.org/iq-files/). No se solapa con el
prefijo 0–13.981 s que se utiliza como ejemplo en la sesión 9.

El [catálogo](origen.json) fija el prefijo de 256 MiB del WAV, su SHA-256 y el
recorte por número de muestra. Se validan PCM16 I/Q, 2.4 Msps y 1090 MHz;
se normaliza por 32768 y se conserva el intervalo solicitado como `cf32_le`.
No se sintetizan ni remodulan las muestras de la tarea.

| Propiedad | Valor |
|---|---|
| Inicio en el WAV | Muestra compleja 33 600 000, tiempo de archivo 14 s |
| Longitud | 31 200 000 muestras complejas, 13 s a 2.4 Msps |
| Tamaño preparado | 249 600 000 bytes |
| SHA-256 preparado | `7638cfa9f6922516df993d079ee63526888fc55c578132bee086353938006ed4` |

El binario está ignorado por Git. Para prepararlo y comenzar la tarea, ejecutar
desde la raíz del repositorio, con el Python de Radioconda:

```bash
python scripts/sesion09_adsb/descargar_muestra.py --muestra laboratorio
python scripts/sesion09_adsb/preparar_laboratorio.py
```

La segunda orden deja una copia incompleta de la plantilla en
`output/adsb-laboratorio/mi_analisis.py` y los mensajes recuperados en
`mensajes.json`. La plantilla se conserva al repetir la preparación.

## Comprobación técnica del recorte

```bash
python scripts/sesion09_adsb/verificar_posiciones.py --muestra laboratorio
```

La referencia se guarda en `output/adsb-laboratorio-referencia/`, separada del
directorio del alumno. La [ejecución verificada](verificacion.json) obtuvo
**139 DF17 con CRC válido, 60 mensajes de posición y 30 posiciones CPR de diez
aeronaves**, sin corrección de bits. Los 139 CRC y las 30 coordenadas coinciden
con pyModeS 2.22.0, con tolerancia de `1e-9` grados para las coordenadas.

Con la dependencia opcional ya instalada en la carpeta local indicada:

```bash
python scripts/sesion09_adsb/verificar_posiciones.py --muestra laboratorio --pymodes-dir tmp/adsb-posiciones/deps
```

La fecha del nombre original no contiene zona horaria. Los tiempos de mensaje
son relativos al recorte e incluyen el retardo del remuestreador. No se ha
validado la cadencia original entre ráfagas para deducir velocidades; se usa
el contenido de TC19. Coincidir con otra implementación de CPR no equivale a
verificar las aeronaves mediante radar u otra fuente física independiente.

## Casos de integridad, separados del I/Q real

[`casos_integridad.json`](casos_integridad.json) contiene tres mensajes para
una comparación local de CRC. A procede de la captura, B altera un bit de A
sin actualizar el CRC y C es un vector sintético de identificación, con
indicativo `AULA06`. Este último es solamente una cadena binaria de prueba:
no se genera una forma de onda ni se realiza una transmisión RF.

El archivo documenta la procedencia como contexto externo. El CRC de A y C
es válido, pero esa coincidencia no acredita la identidad de sus emisores.
Estos casos no se añaden al conjunto real del mapa.

```bash
python scripts/sesion09_adsb/preparar_laboratorio.py --casos-crc
```

No se verificó el CRC del miembro ZIP completo: se descargó y comprobó el
prefijo fijado por hash. Se publican metadatos, código y resultados, y las
muestras se obtienen de la fuente original.

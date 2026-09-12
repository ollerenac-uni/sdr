# Guía de trabajo en este repositorio

Curso de pregrado de Radio Definida por Software (UNI). Sitio MkDocs Material publicado
en <https://ollerenac-uni.github.io/sdr/> mediante GitHub Actions en cada `push` a `main`.

## Figuras

**Cada vez que se añade una figura hay que verificar y asignar su número.** Es la regla que
más se ha incumplido, porque insertar una figura en medio de una sesión desplaza a todas
las posteriores y el error no produce ningún aviso.

El procedimiento, sin excepciones:

1. Toda figura de una sesión lleva pie inmediatamente debajo, con el formato
   `**Figura N.** Texto descriptivo terminado en punto.` Cuenta tanto una imagen `![...]`
   como un diagrama Mermaid.
2. Antes de insertar, comprueba qué números están en uso y cuál corresponde por posición.
3. Después de insertar, **renumera los pies posteriores** de la misma sesión y revisa si
   algún párrafo cita un número de figura por texto (por ejemplo «como muestra la Figura 10»).
4. Ejecuta `pytest tests/test_numeracion_figuras.py`, que comprueba que los pies de cada
   sesión van de 1 a N sin saltos ni repeticiones y que ninguna imagen queda sin pie.

Toda figura generada por código necesita su script en `docs/sessions/<sesión>/figures/gen_*.py`,
versionado y reproducible. Los PNG se commitean; los `.py` generados por GNU Radio Companion, no.

## Verificación antes de cada commit

```bash
mkdocs build --strict          # desde la RAÍZ del repositorio, nunca desde una subcarpeta
pytest tests/                  # con un intérprete que tenga pytest; radioconda no lo trae
```

`--strict` convierte en error los enlaces rotos y las entradas de `nav` que apuntan a archivos
inexistentes. Ejecutar `mkdocs` desde una subcarpeta falla con `exit 1` sin explicar por qué.

## Datos y archivos pesados

Las grabaciones I/Q se distribuyen por Google Drive, nunca por Git. `.gitignore` cubre `*.cu8`,
`*.cfile`, `gnuradio-flowgraphs/*.py`, `referencia/` y `.planning/research/`.

La grabación oficial de la Sesión 01 vive en `samples/` y se referencia así:

| Desde | Ruta |
|---|---|
| Comandos de terminal, ejecutados en la raíz | `samples/fm_99p1MHz_2p4Msps_g30.cu8` |
| Flowgraphs `.grc` | `../samples/fm_99p1MHz_2p4Msps_g30.cu8` |

La segunda es así porque GNU Radio Companion ejecuta cada grafo con el directorio del `.grc`
como directorio de trabajo. Nunca guardes rutas absolutas en un `.grc`: no existen en la
máquina del alumno.

## Flowgraphs

`gnuradio-flowgraphs/test.grc` **falla a propósito**: declara la muestra `.cu8` como
`complex64` para que el alumno diagnostique el error en la Parte B del laboratorio. No lo
arregles. `test2.grc` es la solución de referencia.

Cada `.grc` necesita un `id` distinto en sus opciones: con el mismo `id`, `grcc` genera el
mismo `.py` y un grafo sobrescribe al otro.

## Sesiones

Cada sesión nace con `status: draft` en su *frontmatter*. **No se empieza la sesión N+1
mientras la N siga en borrador.** Retirar esa línea es la aprobación del profesor.

Estructura establecida: objetivos, introducción, teoría por secciones numeradas, síntesis,
al menos cinco ejercicios con solución en bloques `??? example`, laboratorio y lecturas.

## Estilo

Español. Términos técnicos en inglés la primera vez, con glosa. Ecuaciones con `$...$` y
`$$...$$`. Cada figura va seguida de una lectura guiada que explica qué mirar.

Todo dato técnico que entre en una guía se verifica contra la fuente primaria antes de
escribirlo, y todo comando se ejecuta antes de publicarlo. Han llegado a publicarse comandos
inexistentes (`gnuradio.__version__`) y afirmaciones falsas sobre bloques de GNU Radio.

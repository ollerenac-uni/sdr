# Bloques Python del curso CBS33M

El módulo instala dos bloques en la categoría **CBS33M** de GNU Radio Companion:

- **Conversor de .cu8 a .c64**: consume dos bytes I/Q y produce un complejo normalizado.
- **Rotador de frecuencias**: multiplica por un oscilador complejo y conserva la fase entre lotes.

La implementación utiliza Python y NumPy. Instalarla requiere el Python que
ejecuta GNU Radio, como el de Radioconda.

## Instalar los bloques Python

Desde la raíz del repositorio, con Radioconda activo:

```bash
python gnuradio/gr-cbs33m/instalar.py
python gnuradio/gr-cbs33m/instalar.py --comprobar
```

Este instalador no necesita CMake. Obtiene las rutas del Python y GNU Radio
activos e instala tanto el paquete `gnuradio.cbs33m` como los `.block.yml`
de los bloques presentes en la biblioteca de GRC. También instala el manifiesto
del módulo. Admite instalar primero el conversor y añadir el rotador después,
como en la clase: cada bloque requiere su Python, su YAML y su exportación en
`__init__.py`. Antes de copiar, comprueba sintaxis, importaciones, creación de
instancias y puertos; una plantilla incompleta interrumpe la instalación.
Repetirlo actualiza los archivos
que hayan cambiado. `--comprobar` detecta archivos ausentes o desactualizados
sin modificarlos.

Cada computadora debe realizar esta instalación: `git pull` descarga el código,
pero no lo instala dentro de Radioconda. Ejecutar de nuevo el instalador después
de modificar los bloques o sus YAML. Usar el Python de Radioconda, sin activar
el `.venv` de MkDocs.

Después de instalar, guardar el flowgraph y reiniciar GRC desde el mismo
entorno Radioconda para actualizar la biblioteca.

## Construir los bloques durante la clase

La implementación de esta carpeta sirve de referencia. Para practicar sin
sobrescribirla, desde la raíz del repositorio:

```bash
mkdir -p tmp/clase4
cd tmp/clase4
gr_modtool newmod --scm-mode no cbs33m
cp ../../gnuradio/gr-cbs33m/instalar.py gr-cbs33m/
cd gr-cbs33m
gr_modtool add --scm-mode no -l python -t decimator --argument-list 'escala=127.5' cu8_a_c64
```

Responder el autor y `n` a la generación de QA. Completar el Python, el YAML y
la importación de las secciones 4.1–4.3 de la clase; ejecutar `python instalar.py`
y `python instalar.py --comprobar`. Todavía no se necesita el rotador.
En la sección 7, añadirlo al mismo módulo, completar sus archivos y repetir
ambos comandos. `instalar.py` se copia del curso: no lo genera `gr_modtool`.

## Si aparecen `Missing Block` en `fm.grc`

Las claves `cbs33m_cu8_a_c64` y `cbs33m_rotador_frecuencia` pertenecen a este
módulo OOT. Tener sus fuentes en el repositorio no hace que GRC los encuentre.
Un bloque ausente indica que su definición YAML no está en la biblioteca
cargada. Si falta el paquete Python, además fallará la ejecución del grafo.

Ejecutar los comandos de instalación anteriores desde una terminal de Radioconda
y recargar o reiniciar GRC. Los tres bloques del montaje (un conversor y dos
instancias del rotador) deben recuperar su nombre y sus puertos en la categoría
**CBS33M**. No hace falta sustituirlos ni volver a dibujar sus conexiones.

## Alternativa con CMake

También se conserva la instalación habitual del módulo OOT mediante CMake 3.16
o posterior. Esta configuración no compila código C++ ni busca Boost.
Esta alternativa se refiere al módulo completo publicado en esta carpeta.
La construcción por etapas utiliza `instalar.py`, que también funciona con
los `CMakeLists.txt` originales generados por `gr_modtool`.

Desde esta carpeta, con Radioconda activo:

```bash
cmake -S . -B build -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" -DPython3_EXECUTABLE="$CONDA_PREFIX/bin/python"
cmake --build build
ctest --test-dir build --output-on-failure
cmake --install build
python -c "from gnuradio import cbs33m; print(cbs33m.cu8_a_c64().name()); print(cbs33m.rotador_frecuencia().name())"
```

## Verificar el receptor

Después de instalar, comprobar la generación de `fm.grc` sin añadir rutas de
bloques del repositorio:

```bash
mkdir -p output/verificacion-fm
grcc -o output/verificacion-fm gnuradio/flowgraphs/fm.grc
```

Estos comandos se ejecutan desde la raíz del repositorio. En la carpeta del
módulo, las pruebas del procesamiento Python se pueden ejecutar sin CMake:

```bash
python -B python/cbs33m/qa_cbs33m.py
```

La comprobación completa de la clase se ejecuta desde la raíz del repositorio:

```bash
python gnuradio/gr-cbs33m/apps/verificar_fm_rds.py gnuradio/samples/fm_99p1MHz_2p4Msps_g30.cu8
```

Este programa procesa el archivo una vez, sin GUI, Throttle ni dispositivo de audio.
Comprueba el recorrido de audio y recupera los grupos y campos RDS de 98.1 MHz.
Las capturas se distribuyen por separado; no están incluidas en Git.

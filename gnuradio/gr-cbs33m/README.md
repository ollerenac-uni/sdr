# Bloques Python del curso CBS33M

El módulo instala dos bloques en la categoría **CBS33M** de GNU Radio Companion:

- **Conversor de .cu8 a .c64**: consume dos bytes I/Q y produce un complejo normalizado.
- **Rotador de frecuencias**: multiplica por un oscilador complejo y conserva la fase entre lotes.

La implementación utiliza Python y NumPy. Esta configuración de CMake no compila código C++ ni busca Boost.
Requiere un Python que importe GNU Radio, como el de Radioconda, y CMake 3.16 o posterior.

Desde esta carpeta, con Radioconda activo:

```bash
cmake -S . -B build -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" -DPython3_EXECUTABLE="$CONDA_PREFIX/bin/python"
cmake --build build
ctest --test-dir build --output-on-failure
cmake --install build
python -c "from gnuradio import cbs33m; print(cbs33m.cu8_a_c64().name()); print(cbs33m.rotador_frecuencia().name())"
```

Después de instalar, recargar la biblioteca de GRC o reiniciar GRC.
Al modificar Python o YAML, detener el programa, reinstalar y ejecutarlo de nuevo.

La comprobación completa de la clase se ejecuta desde la raíz del repositorio:

```bash
python gnuradio/gr-cbs33m/apps/verificar_fm_rds.py gnuradio/samples/fm_99p1MHz_2p4Msps_g30.cu8
```

Este programa procesa el archivo una vez, sin GUI, Throttle ni dispositivo de audio.
Comprueba el recorrido de audio y recupera los grupos y campos RDS de 98.1 MHz.
Las capturas se distribuyen por separado; no están incluidas en Git.

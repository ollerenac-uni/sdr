---
title: "Instalar GNU Radio con radioconda"
description: "Instalación de GNU Radio 3.10.12 y drivers SDR en Windows, Linux y macOS con radioconda 2025.03.14."
---

# Instalar GNU Radio con radioconda

[radioconda](https://github.com/radioconda/radioconda-installer) es una distribución basada en `conda` que instala en un solo paso GNU Radio 3.10.12, GNU Radio Companion, el driver `rtl-sdr` 2.0.2, `gr-osmosdr`, SoapySDR y varios módulos que usaremos en el curso (`gr-rds`, `gr-adsb`, `gr-lora_sdr`, `gr-satellites`). Funciona igual en Windows, Linux y macOS, así que profesor y alumnos trabajan con versiones idénticas.

!!! danger "Versión fijada para el curso: 2025.03.14"
    No ejecutes `mamba upgrade --all` ni actualices GNU Radio durante el semestre. Si lo haces por error, la sección *Problemas frecuentes* explica cómo volver a la versión fijada.

## Descarga

Todos los archivos están en la [página del release 2025.03.14](https://github.com/radioconda/radioconda-installer/releases/tag/2025.03.14).

| Sistema | Archivo | Tamaño |
|---|---|---:|
| Windows 10/11, 64 bits | `radioconda-2025.03.14-Windows-x86_64.exe` | 599 MB |
| Linux x86_64 | `radioconda-2025.03.14-Linux-x86_64.sh` | 648 MB |
| macOS Apple Silicon (M1/M2/M3/M4) | `radioconda-2025.03.14-MacOSX-arm64.pkg` | 400 MB |
| macOS Intel | `radioconda-2025.03.14-MacOSX-x86_64.pkg` | 413 MB |

Cada archivo tiene al lado un `.sha256`. Verifica la descarga antes de instalar:

=== "Windows"

    ```bat
    certutil -hashfile radioconda-2025.03.14-Windows-x86_64.exe SHA256
    ```

=== "Linux"

    ```bash
    sha256sum radioconda-2025.03.14-Linux-x86_64.sh
    ```

=== "macOS"

    ```bash
    shasum -a 256 radioconda-2025.03.14-MacOSX-arm64.pkg
    ```

El valor impreso debe coincidir con el contenido del archivo `.sha256`.

## Instalación

=== "Windows"

    1. Doble clic en el `.exe`. Si SmartScreen lo bloquea: **Más información → Ejecutar de todas formas**.
    2. Tipo de instalación: **Just Me**.
    3. Ruta por defecto: `C:\Users\<usuario>\radioconda`. Déjala así.
    4. **No** marques "Add radioconda to my PATH". Deja marcado "Register radioconda as my default Python" solo si no tienes otro Python instalado.
    5. Al terminar, en el menú Inicio aparece la carpeta **radioconda** con dos accesos: **radioconda Prompt** (terminal con el entorno activado) y **GNU Radio Companion**.

    Todo comando de este curso en Windows se ejecuta dentro de **radioconda Prompt**, no en `cmd` ni PowerShell normales.

=== "Linux"

    ```bash
    bash radioconda-2025.03.14-Linux-x86_64.sh
    ```

    1. Acepta la licencia.
    2. Ruta por defecto: `~/radioconda`. Déjala así.
    3. A la pregunta *"Do you wish to update your shell profile to automatically initialize conda?"* responde **yes**.
    4. Cierra la terminal y abre otra. El prompt debe empezar con `(base)`.

    Si no aparece `(base)`, activa el entorno a mano cada vez:

    ```bash
    source ~/radioconda/bin/activate
    ```

=== "macOS"

    1. Doble clic en el `.pkg` y sigue el asistente. Ruta por defecto: `~/radioconda`.
    2. Abre Terminal y activa el entorno:

    ```bash
    source ~/radioconda/bin/activate
    ```

    El prompt debe empezar con `(base)`.

## Verificar la instalación

Desde radioconda Prompt (Windows) o una terminal con `(base)` activo (Linux/macOS):

```bash
python -c "from gnuradio import gr; print(gr.version())"
```

Salida esperada:

```
3.10.12.0
```

El paquete `gnuradio` no tiene atributo `__version__`; la versión se lee con `gr.version()`. Equivalente desde la línea de comandos: `gnuradio-config-info --version`. No existe un comando llamado `gnuradio`; los ejecutables son `gnuradio-companion` y `gnuradio-config-info`.

!!! warning "Si ya tenías GNU Radio instalado con apt"
    Comprueba cuál se ejecuta: `which gnuradio-companion` debe devolver `~/radioconda/bin/gnuradio-companion` cuando `(base)` está activo. Si devuelve `/usr/bin/gnuradio-companion`, el entorno no está activado y estás usando la versión de apt (distinta a la del curso). Lo mismo con `which rtl_test`.

Confirma que el driver del RTL-SDR quedó instalado (no hace falta tener el dongle):

```bash
rtl_test -h
```

Debe imprimir la ayuda del programa (`Usage: rtl_test [-s samplerate] ...`). Por último, abre GNU Radio Companion:

```bash
gnuradio-companion
```

En Windows también puedes usar el acceso del menú Inicio.

## Primer flowgraph (sin hardware)

Un *flowgraph* (grafo de flujo) es un programa de GNU Radio dibujado como bloques conectados. Vamos a generar una señal y mirar su espectro.

1. En GRC, en el panel derecho busca (Ctrl+F) y arrastra al lienzo estos tres bloques:
    - **Signal Source**: `Sample Rate` = `samp_rate`, `Waveform` = Cosine, `Frequency` = `1000`, `Amplitude` = `1`, `Output Type` = Complex.
    - **Throttle**: `Sample Rate` = `samp_rate`.
    - **QT GUI Frequency Sink**: valores por defecto.
2. Conecta la salida de Signal Source a Throttle y la de Throttle al Frequency Sink (arrastra desde el puerto azul de uno al del otro).
3. El bloque **Variable** `samp_rate` ya existe en el lienzo con valor `32000`. Déjalo.
4. Guarda como `prueba.grc` (Ctrl+S) y ejecuta con **F6** (o el botón ▶).

Resultado esperado: una ventana con el espectro y **un solo pico en +1 kHz**. Haz una captura de pantalla: es parte del Reporte 0.

??? question "¿Por qué un solo pico en +1 kHz y no dos en ±1 kHz?"
    Elegiste salida *Complex*: la señal es $e^{j2\pi f t}$, no $\cos(2\pi f t)$. Una exponencial compleja tiene una sola frecuencia, positiva. Un coseno real es la suma de dos exponenciales, en $+f$ y $-f$, y por eso su espectro tiene dos picos. Cambia `Output Type` a *Float* y compruébalo. Este es el tema central de la Sesión 02.

El bloque **Throttle** no procesa nada: solo limita la velocidad a `samp_rate` muestras por segundo para que la simulación no consuma el 100 % de la CPU. Cuando la fuente sea el RTL-SDR real, el hardware marca el ritmo y Throttle **no** debe estar en el flowgraph.

## Problemas frecuentes

??? failure "Windows: `gnuradio-companion` no se reconoce como comando"
    Estás en `cmd` o PowerShell. Abre **radioconda Prompt** desde el menú Inicio y vuelve a intentarlo.

??? failure "Linux: `conda: command not found`"
    El instalador no modificó tu shell. Ejecuta `source ~/radioconda/bin/activate` y, si quieres que sea permanente, `~/radioconda/bin/conda init`.

??? failure "Linux: GRC arranca pero no aparece ninguna ventana (Wayland)"
    Fuerza el backend X11 antes de lanzar:

    ```bash
    export QT_QPA_PLATFORM=xcb
    gnuradio-companion
    ```

??? failure "El antivirus bloquea el instalador o borra archivos"
    Añade una excepción para la carpeta `radioconda` (en Windows `C:\Users\<usuario>\radioconda`). Los instaladores están firmados por el proyecto y publicados en GitHub.

??? failure "Actualicé por error y ahora tengo otra versión de GNU Radio"
    Vuelve a la versión fijada del curso instalando el archivo *lock* del release. En Windows (radioconda Prompt):

    ```bat
    mamba install --file https://github.com/radioconda/radioconda-installer/releases/download/2025.03.14/radioconda-win-64.lock
    ```

    En Linux x86_64:

    ```bash
    mamba install --file https://github.com/radioconda/radioconda-installer/releases/download/2025.03.14/radioconda-linux-64.lock
    ```

    En macOS: usa `radioconda-osx-arm64.lock` (Apple Silicon) o `radioconda-osx-64.lock` (Intel).

Si nada de esto resuelve tu caso, abre un [issue](https://github.com/ollerenac-uni/sdr/issues/new) con la salida completa del comando que falla.

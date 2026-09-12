---
title: "Configurar el RTL-SDR"
description: "Drivers, prueba con rtl_test y verificación de autenticidad del RTL-SDR Blog V3/V4 en Windows, Linux y macOS."
---

# Configurar el RTL-SDR

!!! info "Opcional"
    El dongle no es obligatorio: todos los laboratorios se califican con archivos IQ oficiales. Esta guía es para quienes lo tienen. Prerrequisito: [radioconda instalado](instalacion.md).

## Datos del hardware

| Parámetro | RTL-SDR Blog V4 | RTL-SDR Blog V3 |
|---|---|---|
| Demodulador / ADC | RTL2832U, 8 bits | RTL2832U, 8 bits |
| Tuner | Rafael Micro R828D | Rafael Micro R820T2 |
| Rango de frecuencia | 500 kHz – 1.766 GHz (HF con *upconverter* integrado) | 24 MHz – 1.766 GHz (HF por *direct sampling*) |
| Tasa de muestreo estable | 2.4 MS/s (2.56 con pérdidas ocasionales) | igual |
| Interfaz | USB 2.0 (no requiere USB 3.0) | USB 2.0 |
| Oscilador | TCXO 1 ppm | TCXO 1 ppm |
| Bias-tee | 4.5 V por software (para alimentar un LNA) | igual |
| Antena del kit | Dipolo telescópico ajustable con base imantada | igual |

## Driver

=== "Windows (Zadig)"

    Al conectar el dongle, Windows instala un driver de televisión (DVB-T) que impide usarlo como SDR. Hay que reemplazarlo por **WinUSB** con la herramienta Zadig.

    1. Conecta el dongle a un puerto USB directo de la laptop (evita hubs y adaptadores USB-C baratos).
    2. Descarga Zadig desde [zadig.akeo.ie](https://zadig.akeo.ie/). Es un ejecutable único; no se instala.
    3. Ejecuta Zadig **como administrador** (clic derecho → Ejecutar como administrador).
    4. Menú **Options → List All Devices**.
    5. En el desplegable elige **`Bulk-In, Interface (Interface 0)`**. Si en su lugar aparece `RTL2832UHIDIR` o `RTL2838UHIDIR`, también sirve. **No** elijas `Interface 1`.
    6. A la derecha de la flecha debe decir **WinUSB**. No uses `libusb-win32` ni `libusbK`.
    7. Pulsa **Replace Driver** (o **Install Driver**) y espera el mensaje de éxito. Cierra Zadig.

    ??? failure "Windows 11 rechaza instalar el driver"
        Ve a **Configuración → Privacidad y seguridad → Seguridad de Windows → Seguridad del dispositivo → Aislamiento del núcleo** y desactiva **Integridad de memoria**. Reinicia y repite Zadig. Después puedes volver a activarla: WinUSB es compatible.

    !!! warning "Windows Update puede devolver el driver de TV"
        Si el dongle deja de funcionar tras una actualización de Windows, repite Zadig. Para evitarlo, crea un archivo llamado `no-driver-updates.reg` con el contenido de abajo y ejecútalo con doble clic (pedirá permiso de administrador). **Aviso:** desactiva la búsqueda de drivers en Windows Update para **todos** los dispositivos. El segundo archivo lo revierte.

        ```ini title="no-driver-updates.reg"
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PolicyManager\current\device\Update]
        "ExcludeWUDriversInQualityUpdate"=dword:00000001

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PolicyManager\default\Update]
        "ExcludeWUDriversInQualityUpdate"=dword:00000001

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings]
        "ExcludeWUDriversInQualityUpdate"=dword:00000001

        [HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate]
        "ExcludeWUDriversInQualityUpdate"=dword:00000001

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PolicyManager\default\Update\ExcludeWUDriversInQualityUpdate]
        "value"=dword:00000001

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Device Metadata]
        "PreventDeviceMetadataFromNetwork"=dword:00000001

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching]
        "SearchOrderConfig"=dword:00000000
        "DontSearchWindowsUpdate"=dword:00000001
        ```

        ```ini title="driver-updates-on.reg (revertir)"
        Windows Registry Editor Version 5.00

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PolicyManager\current\device\Update]
        "ExcludeWUDriversInQualityUpdate"=-

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PolicyManager\default\Update]
        "ExcludeWUDriversInQualityUpdate"=-

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings]
        "ExcludeWUDriversInQualityUpdate"=-

        [HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate]
        "ExcludeWUDriversInQualityUpdate"=-

        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\DriverSearching]
        "SearchOrderConfig"=dword:00000001
        "DontSearchWindowsUpdate"=-
        ```

        Fuente: [rtl-sdr.com, registry hack para Windows 11](https://www.rtl-sdr.com/a-registry-hack-to-stop-windows-11-replacing-the-winusb-driver-installed-via-zadig/).

=== "Linux"

    El kernel carga un módulo de TV (`dvb_usb_rtl28xxu`) que reclama el dongle. Hay que bloquearlo y dar permisos de acceso al usuario. Con el entorno `(base)` de radioconda activo:

    ```bash
    sudo ln -s $CONDA_PREFIX/etc/modprobe.d/rtl-sdr-blacklist.conf /etc/modprobe.d/radioconda-rtl-sdr-blacklist.conf
    sudo modprobe -r $(cat $CONDA_PREFIX/etc/modprobe.d/rtl-sdr-blacklist.conf | sed -n -e 's/^blacklist //p')
    sudo ln -s $CONDA_PREFIX/lib/udev/rules.d/rtl-sdr.rules /etc/udev/rules.d/radioconda-rtl-sdr.rules
    sudo udevadm control --reload
    sudo udevadm trigger
    ```

    Desconecta y vuelve a conectar el dongle. Fuente: [README de radioconda, sección RTL-SDR](https://github.com/radioconda/radioconda-installer#rtl-sdr).

=== "macOS"

    No requiere driver. Conecta el dongle y pasa a la prueba.

## Prueba 1: detección

Desde radioconda Prompt o terminal con `(base)`:

```bash
rtl_test -t
```

Salida esperada con un **V4** auténtico:

```
Found 1 device(s):
  0:  RTLSDRBlog, Blog V4, SN: 00000001

Using device 0: Generic RTL2832U OEM
Found Rafael Micro R828D tuner
RTL-SDR Blog V4 Detected
Supported gain values (29): 0.0 0.9 1.4 2.7 3.7 7.7 8.7 12.5 14.4 15.7 16.6 19.7 20.7 22.9 25.4 28.0 29.7 32.8 33.8 36.4 37.2 38.6 40.2 42.1 43.4 43.9 44.5 48.0 49.6
```

Con un **V3** verás `Found Rafael Micro R820T tuner` y no aparece la línea "V4 Detected". La lista de ganancias es la misma.

??? failure "`usb_claim_interface error -6` (Linux)"
    El módulo de TV sigue cargado. Repite el paso de *blacklist* y reinicia.

??? failure "`No supported devices found` (Windows)"
    Zadig no se aplicó a la interfaz correcta. Ábrelo de nuevo con *List All Devices* y comprueba que `Bulk-In, Interface (Interface 0)` muestra `WinUSB` a la izquierda de la flecha.

??? failure "`No supported devices found` (Linux/macOS)"
    Prueba `lsusb` (Linux) o `system_profiler SPUSBDataType` (macOS): debe listar `Realtek Semiconductor Corp. RTL2838 DVB-T`. Si no aparece, cambia de cable o puerto.

## Prueba 2: pérdida de muestras

Esta prueba mide si tu laptop y tu puerto USB sostienen la tasa de muestreo del curso:

```bash
rtl_test -s 2400000
```

Déjalo correr **60 segundos** y detenlo con Ctrl+C. Salida esperada:

```
Found 1 device(s):
  0:  RTLSDRBlog, Blog V4, SN: 00000001

Using device 0: Generic RTL2832U OEM
Found Rafael Micro R828D tuner
RTL-SDR Blog V4 Detected
Supported gain values (29): ...
Sampling at 2400000 S/s.

Info: This tool will continuously read from the device, and report if
samples get lost. If you observe no further output, everything is fine.

Reading samples in async mode...
```

Si no aparece ninguna línea `lost at least N bytes`, todo está bien. Hasta 5 avisos en 60 s es aceptable. Con pérdidas continuas:

1. Cambia a otro puerto USB, sin hub ni adaptador.
2. Cierra navegador y programas pesados.
3. Prueba con `-s 2048000`; si así no pierde, usa esa tasa en tus flowgraphs.

Guarda la salida completa en un archivo de texto: forma parte del Reporte 0.

## Prueba 3: primer espectro en GNU Radio Companion

1. Abre el `prueba.grc` de la [guía de instalación](instalacion.md#primer-flowgraph-sin-hardware).
2. Borra **Signal Source** y **Throttle**.
3. Añade el bloque **RTL-SDR Source** (categoría *osmocom*): `Sample Rate (sps)` = `samp_rate`, `Ch0: Frequency (Hz)` = `99.1e6` (o la emisora FM que prefieras), `Ch0: RF Gain (dB)` = `30`.
4. Cambia la variable `samp_rate` a `2.4e6`.
5. Conecta RTL-SDR Source al QT GUI Frequency Sink y ejecuta.

Verás varias portadoras FM, cada una de unos 200 kHz de ancho, dentro de una ventana de 2.4 MHz. Captura de pantalla para el Reporte 0.

## Autenticidad y clones

Señales de que un dongle vendido como "RTL-SDR V4" es un clon:

- `rtl_test -t` no imprime `RTL-SDR Blog V4 Detected`.
- El tuner reportado es `FC0012`, `FC0013` o `E4000` en lugar de `R828D` (V4) o `R820T` (V3).
- No tiene bias-tee, o la carcasa es de plástico sin marca.
- Deriva de frecuencia grande: una emisora FM aparece desplazada varios kHz.

Referencia: [rtl-sdr.com, cómo identificar un dongle genuino](https://www.rtl-sdr.com/genuine/).

## Grabar muestras IQ

Los laboratorios y el proyecto usan grabaciones. Para grabar 10 segundos de una emisora FM:

```bash
rtl_sdr -f 99.1e6 -s 2400000 -g 30 -n 24000000 fm_99p1MHz_2p4Msps_g30.cu8
```

- `-f` frecuencia central en Hz, `-s` tasa de muestreo, `-g` ganancia en dB, `-n` número de muestras (24 M muestras a 2.4 MS/s = 10 s = 48 MB).
- Formato `.cu8`: bytes sin signo intercalados `I, Q, I, Q, …`, con el cero en 127.5.
- Convención de nombres del curso: `<señal>_<fc>_<fs>_g<ganancia>.cu8`.

Para leerlo en Python:

```python
import numpy as np

raw = np.fromfile("fm_99p1MHz_2p4Msps_g30.cu8", dtype=np.uint8)
iq = ((raw[0::2].astype(np.float32) - 127.5) + 1j * (raw[1::2].astype(np.float32) - 127.5)) / 127.5
```

Para reproducirlo en GNU Radio Companion hay dos opciones:

- **File Source** de tipo *Byte*, seguido de `UChar To Float`, `Add Const (-127.5)`, `Multiply Const (1/127.5)`, `Deinterleave` y `Float To Complex`. Es la cadena que construyes en la [Sesión 01](../sessions/01-introduccion-sdr/index.md#parte-c-la-lectura-correcta), y lee el `.cu8` sin convertirlo previamente.
- Convertir una vez a `complex64` y usar **File Source** (tipo *Complex*) seguido de **Throttle**. Un `File Source` de tipo *Complex* solo acepta archivos ya convertidos; apuntarlo a un `.cu8` produce valores sin sentido, no un error:

```python
iq.astype(np.complex64).tofile("fm_99p1MHz_2p4Msps_g30.cfile")
```

Los archivos oficiales del curso se publican semana a semana; el enlace se anuncia en cada sesión.

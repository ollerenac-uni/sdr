# Radio Definida por Software

### Curso de Pregrado · Acceso Abierto · CC BY 4.0

Un curso práctico de radio definida por software (SDR): desde las muestras I/Q y el procesamiento digital hasta la construcción guiada de un receptor QPSK sencillo. El curso comprende 16 sesiones, con tiempo de integración y consolidación. No se requiere hardware SDR individual: se utilizan archivos de muestras `.cu8` y señales generadas en Python o GNU Radio.

[Ver syllabus](syllabus.md){ .md-button .md-button--primary }
[Ver sesiones](sessions/index.md){ .md-button }
[Guías de instalación](setup/index.md){ .md-button }
[Exámenes](exams/index.md){ .md-button }
[Repositorio GitHub](https://github.com/ollerenac-uni/sdr){ .md-button }

---

## Arcos Temáticos

<div class="grid cards" markdown>

-   :material-sine-wave:{ .lg .middle } **Fundamentos y procesamiento de muestras**

    ---

    Sesiones 1–4

    Arquitectura SDR, muestras I/Q, espectro, sistemas, filtros y cambios de sampling rate.

-   :material-radio-tower:{ .lg .middle } **Enlace digital y sincronización**

    ---

    Sesiones 5–11

    BPSK/QPSK, pulse shaping, enlace ideal, ruido y recuperación de frecuencia, fase y timing con bloques preparados.

-   :material-access-point-network:{ .lg .middle } **Mensaje, integración y práctica**

    ---

    Sesiones 12–16

    Recuperación de tramas, integración del receptor QPSK, capturas reales, diagnóstico y consolidación. Multipath, equalization adaptativa y OFDM quedan como temas complementarios.

</div>

---

## Sesiones del Curso

El [syllabus](syllabus.md) describe el tema principal y el laboratorio de cada sesión.
El [pre-lab: instalar el entorno](setup/index.md) es una preparación previa, fuera de las 16 sesiones.

| # | Título | Estado |
|---|--------|:------:|
| 01 | [Introducción](sessions/01-introduccion-sdr/index.md) | En desarrollo |
| 02 | [Señales y espectro en SDR](sessions/02-tiempo-frecuencia-iq/index.md) | En desarrollo |
| 03 | Sistemas y filtros digitales | Próximamente |
| 04 | Selección de canal y decimación | Próximamente |
| 05 | De bits a símbolos: BPSK y QPSK | Próximamente |
| 06 | Pulse shaping y matched filtering | Próximamente |
| 07 | Enlace digital ideal | Próximamente |
| 08 | Ruido y medición de errores | Próximamente |
| 09 | Offset de frecuencia y fase | Próximamente |
| 10 | Corrección de frecuencia y fase | Próximamente |
| 11 | Symbol timing recovery | Próximamente |
| 12 | Tramas y recuperación del mensaje | Próximamente |
| 13 | Integración del receptor QPSK | Próximamente |
| 14 | Recepción desde una captura I/Q | Próximamente |
| 15 | Evaluación y diagnóstico del receptor | Próximamente |
| 16 | Síntesis y demostración del enlace | Próximamente |

---

## Prerrequisitos

| Área | Contenidos clave |
|------|-----------------|
| Señales y Sistemas | Transformada de Fourier, convolución, muestreo, filtrado |
| Programación | Python básico (NumPy, Matplotlib), cuadernos Jupyter |
| Comunicaciones Digitales (recomendado) | Modulación básica, SNR; puede cursarse en paralelo |

---

## Hardware y Software

| Herramienta | Uso en el curso |
|-------------|-----------------|
| radioconda 2025.03.14 (GNU Radio 3.10.12) | Flowgraphs de recepción en GNU Radio Companion; misma versión para todos |
| Archivos I/Q `.cu8` | Capturas para los laboratorios; no se requiere un dongle propio |
| USRP B210 y RTL-SDR del profesor | Demostraciones Tx–Rx y generación de capturas para el curso |
| Python (NumPy, SciPy, Matplotlib) | Análisis y prototipos en Google Colab |

---

## Cómo Usar Este Curso

=== "Sitio web"

    El [syllabus](syllabus.md) presenta el programa. Las sesiones disponibles incluyen teoría, ejercicios con soluciones desplegables y enlaces a sus laboratorios. Los snippets de Python pueden ejecutarse en Google Colab; los flowgraphs se utilizan en GNU Radio Companion.

=== "Clonar el repositorio"

    ```bash
    git clone https://github.com/ollerenac-uni/sdr.git
    cd sdr
    pip install -r requirements.txt
    mkdocs serve    # vista previa en http://127.0.0.1:8000
    ```

=== "GNU Radio"

    Los laboratorios usan GNU Radio Companion instalado con radioconda. Sigue las [guías de instalación](setup/index.md) antes de la primera sesión.

---

## Licencia

Todo el contenido se publica bajo [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Eres libre de compartir, adaptar y redistribuir este material, incluso con fines comerciales, siempre que se otorgue la atribución correspondiente.

> *Radio Definida por Software* por ollerenac-uni — [github.com/ollerenac-uni/sdr](https://github.com/ollerenac-uni/sdr)

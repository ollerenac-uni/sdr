# Radio Definida por Software

### Curso de Pregrado · Acceso Abierto · CC BY 4.0

Un curso práctico de radio definida por software (SDR): desde las muestras I/Q y el procesamiento digital hasta la construcción de un receptor QPSK y una introducción a OFDM. Cada sesión combina teoría con un laboratorio en Python o GNU Radio. No se requiere hardware individual: se utilizan archivos de muestras `.cu8` y señales generadas en software.

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

    BPSK/QPSK, pulse shaping, ruido, recuperación de fase, frecuencia y timing, y recuperación de tramas.

-   :material-access-point-network:{ .lg .middle } **Canal, equalization e integración**

    ---

    Sesiones 12–15

    Multipath, channel estimation, equalization adaptativa, introducción a OFDM y evaluación del receptor QPSK.

</div>

---

## Sesiones del Curso

El [syllabus](syllabus.md) describe el tema principal y el laboratorio de cada sesión.

| # | Título | Estado |
|---|--------|:------:|
| 00 | [Pre-lab: instalar el entorno](setup/index.md) | Disponible |
| 01 | [Introducción a la Radio Definida por Software](sessions/01-introduccion-sdr/index.md) | En desarrollo |
| 02 | [Señales y espectro en SDR](sessions/02-tiempo-frecuencia-iq/index.md) | En desarrollo |
| 03 | Sistemas y filtros digitales | Próximamente |
| 04 | Selección de canal y cambios de sampling rate | Próximamente |
| 05 | De bits a señales: BPSK y QPSK | Próximamente |
| 06 | Pulse shaping y matched filtering | Próximamente |
| 07 | Ruido y desempeño del enlace | Próximamente |
| 08 | PLL y sincronización de fase | Próximamente |
| 09 | Sincronización de frecuencia | Próximamente |
| 10 | Symbol timing recovery | Próximamente |
| 11 | Frame synchronization y recuperación del mensaje | Próximamente |
| 12 | Canal multipath y channel estimation | Próximamente |
| 13 | Equalization adaptativa | Próximamente |
| 14 | Introducción a OFDM | Próximamente |
| 15 | Integración y evaluación de un receptor SDR | Próximamente |

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

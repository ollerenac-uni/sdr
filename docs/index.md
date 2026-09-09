# Radio Definida por Software

### Curso de Pregrado · Acceso Abierto · CC BY 4.0

Un curso práctico de radio definida por software (SDR): desde las señales IQ y el procesamiento digital en banda base hasta la recepción y transmisión de sistemas de comunicación reales con GNU Radio y hardware de bajo costo. Cada sesión combina teoría con un laboratorio ejecutable en Google Colab o en GNU Radio Companion.

[Ver sesiones](sessions/index.md){ .md-button .md-button--primary }
[Guías de instalación](setup/index.md){ .md-button }
[Exámenes](exams/index.md){ .md-button }
[Repositorio GitHub](https://github.com/ollerenac-uni/sdr){ .md-button }

---

## Arcos Temáticos

<div class="grid cards" markdown>

-   :material-sine-wave:{ .lg .middle } **Fundamentos y hardware real**

    ---

    Sesiones 1–4

    Arquitectura de un receptor SDR y el RTL-SDR por dentro, señales IQ, ganancia y saturación a 8 bits, filtros y decimación, GNU Radio Companion a fondo.

-   :material-radio-tower:{ .lg .middle } **Señales reales: analógicas y digitales**

    ---

    Sesiones 5–10

    Receptor FM estéreo, presupuesto de enlace, modulación digital y sincronización, decodificación de RDS y ADS-B desde muestras reales.

-   :material-access-point-network:{ .lg .middle } **Espectro, sistemas y proyecto**

    ---

    Sesiones 11–16

    Sensado de espectro con el PNAF, OFDM e ISDB-Tb, IoT y LoRa en 915 MHz, satélites Meteor, proyecto final por hitos.

</div>

---

## Sesiones del Curso

| # | Título | Estado |
|---|--------|:------:|
| 00 | [Pre-lab: instalar el entorno](setup/index.md) | Disponible |
| 01 | [Introducción a la Radio Definida por Software](sessions/01-introduccion-sdr/index.md) | En desarrollo |
| 02 | [Del tiempo al espectro: señales, IQ y hardware real](sessions/02-tiempo-frecuencia-iq/index.md) | En desarrollo |
| 03 | DSP para SDR: filtros FIR, decimación, PSD y SNR | Próximamente |
| 04 | GNU Radio Companion a fondo | Próximamente |
| 05 | Modulación analógica: AM/FM, presupuesto de enlace, figura de ruido | Próximamente |
| 06 | Modulación digital I: símbolos, RRC, ISI, diagrama de ojo | Próximamente |
| 07 | Sincronización: reloj de símbolo, portadora, RDS real | Próximamente |
| 08 | Examen parcial | — |
| 09 | Modulación digital II: QAM, Eb/N0, BER | Próximamente |
| 10 | Trama y paquetes: RDS completo, ADS-B | Próximamente |
| 11 | Sensado de espectro, PNAF y RNF | Próximamente |
| 12 | OFDM en SDR e ISDB-Tb | Próximamente |
| 13 | IoT en banda ICM 915 MHz: sensores y LoRa | Próximamente |
| 14 | Satélites Meteor LRPT y panorama de SDR con transmisión | Próximamente |
| 15 | Integración y ensayo de demo | Próximamente |
| 16 | Presentaciones de proyecto | — |

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
| RTL-SDR Blog V4 o V3 (opcional) | Receptor de bajo costo; todo lab funciona también con archivos IQ oficiales |
| Python (NumPy, SciPy, Matplotlib) | Análisis y prototipos en Google Colab |
| rtl_433, SatDump | Herramientas externas para sensores ICM y satélites |

---

## Cómo Usar Este Curso

=== "Sitio web"

    Navega las sesiones directamente desde este sitio. Cada página incluye apuntes de teoría, ejercicios con soluciones desplegables y un botón **Abrir en Colab** para ejecutar el laboratorio sin instalar nada.

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

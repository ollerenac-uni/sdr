# Radio Definida por Software

### Curso de Pregrado · Acceso Abierto · CC BY 4.0

Un curso práctico de radio definida por software (SDR): desde las señales IQ y el procesamiento digital en banda base hasta la recepción y transmisión de sistemas de comunicación reales con GNU Radio y hardware de bajo costo. Cada sesión combina teoría con un laboratorio ejecutable en Google Colab o en GNU Radio Companion.

[Ver sesiones](sessions/index.md){ .md-button .md-button--primary }
[Exámenes](exams/index.md){ .md-button }
[Repositorio GitHub](https://github.com/ollerenac-uni/sdr){ .md-button }

---

## Arcos Temáticos

<div class="grid cards" markdown>

-   :material-sine-wave:{ .lg .middle } **Fundamentos de SDR y Señales IQ**

    ---

    Sesiones 1–4

    Arquitectura de un SDR, hardware (RTL-SDR, ADALM-Pluto, HackRF, USRP), señales en banda base compleja, muestreo y aliasing, filtros FIR, decimación e interpolación, GNU Radio Companion.

-   :material-radio-tower:{ .lg .middle } **Recepción y Transmisión de Señales**

    ---

    Sesiones 5–9

    Demodulación AM/FM, modulación digital (ASK, FSK, PSK, QAM), filtro conformador, sincronización de símbolo y portadora, ecualización y canal multipath.

-   :material-access-point-network:{ .lg .middle } **Sistemas y Protocolos Reales**

    ---

    Sesiones 10–14

    OFDM en SDR, decodificación de protocolos reales (ADS-B, AIS, RDS), sensado de espectro y radio cognitiva, LoRa e IoT, proyecto final de transceptor completo.

</div>

---

## Sesiones del Curso

| # | Título | Estado |
|---|--------|:------:|
| 01 | Introducción a SDR: arquitectura, hardware y ecosistema GNU Radio | Próximamente |
| 02 | Señales IQ: banda base compleja, mezcla y conversión de frecuencia | Próximamente |
| 03 | DSP para SDR: muestreo, filtros FIR, decimación e interpolación | Próximamente |
| 04 | GNU Radio Companion: flowgraphs, bloques y visualización | Próximamente |
| 05 | Modulación analógica: recepción de AM y FM broadcast | Próximamente |
| 06 | Modulación digital I: ASK, FSK, PSK y filtro conformador | Próximamente |
| 07 | Modulación digital II: QAM, constelaciones y BER en AWGN | Próximamente |
| 08 | Examen Parcial | — |
| 09 | Sincronización: reloj de símbolo, portadora y trama | Próximamente |
| 10 | Ecualización y canal multipath | Próximamente |
| 11 | OFDM en SDR | Próximamente |
| 12 | Decodificación de protocolos reales: ADS-B, AIS y RDS | Próximamente |
| 13 | Sensado de espectro y radio cognitiva | Próximamente |
| 14 | LoRa e IoT con SDR | Próximamente |
| 15 | Proyecto final: transceptor completo | Próximamente |
| 16 | Examen Final | — |

---

## Prerrequisitos

| Área | Contenidos clave |
|------|-----------------|
| Señales y Sistemas | Transformada de Fourier, convolución, muestreo, filtrado |
| Comunicaciones | Modulación analógica y digital básica, SNR |
| Programación | Python básico (NumPy, Matplotlib), cuadernos Jupyter |

---

## Hardware y Software

| Herramienta | Uso en el curso |
|-------------|-----------------|
| GNU Radio Companion | Diseño de flowgraphs de recepción y transmisión |
| RTL-SDR | Receptor de bajo costo para laboratorios de recepción |
| ADALM-Pluto / HackRF / USRP | Transmisión y laboratorios de transceptor |
| Python (NumPy, SciPy, Matplotlib) | Laboratorios en Google Colab |

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

    Los laboratorios con hardware usan GNU Radio Companion. Instálalo desde [gnuradio.org](https://wiki.gnuradio.org/index.php/InstallingGR) o usa una imagen preconfigurada como [DragonOS](https://sourceforge.net/projects/dragonos-focal/).

---

## Licencia

Todo el contenido se publica bajo [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Eres libre de compartir, adaptar y redistribuir este material, incluso con fines comerciales, siempre que se otorgue la atribución correspondiente.

> *Radio Definida por Software* por ollerenac-uni — [github.com/ollerenac-uni/sdr](https://github.com/ollerenac-uni/sdr)

# Radio Definida por Software

### Curso de Pregrado · Acceso Abierto · CC BY 4.0

Curso práctico de radio definida por software (SDR). Se estudian muestras I/Q, se construye un enlace digital y se analizan señales FM, RDS y LoRa. Las prácticas usan capturas y señales generadas en Python o GNU Radio.

[Ver sesiones](sessions/index.md){ .md-button .md-button--primary }
[Guías de instalación](setup/index.md){ .md-button }
[Exámenes](exams/index.md){ .md-button }
[Repositorio GitHub](https://github.com/ollerenac-uni/sdr){ .md-button }

---

## Arcos Temáticos

<div class="grid cards" markdown>

-   :material-sine-wave:{ .lg .middle } **Fundamentos y procesamiento de muestras**

    ---

    Sesiones 01–05

    Arquitectura SDR, muestras I/Q, espectro, sistemas, filtros y cambios de sampling rate.

-   :material-radio-tower:{ .lg .middle } **Enlace digital y sincronización**

    ---

    Sesión 06

    Enlace BPSK, conformación de pulsos, recuperación de frecuencia, fase y temporización.

-   :material-access-point-network:{ .lg .middle } **Recepción FM, RDS y LoRa**

    ---

    Sesiones 07–08

    Recuperación de audio FM y datos RDS. Medición de chirps LoRa y análisis de una trama LoRaWAN.

</div>

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

    El [índice de sesiones](sessions/index.md) reúne las clases y los laboratorios. Los ejemplos de Python pueden ejecutarse en Google Colab. Los *flowgraphs* se usan en GNU Radio Companion.

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

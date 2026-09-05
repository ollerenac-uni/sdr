# Diseño del curso de Radio Definida por Software (SDR)

Fecha: 2026-09-05. Estado: aprobado por el profesor tras dos rondas de revisión adversaria.

## Contexto

- Curso de pregrado, Universidad Nacional de Ingeniería (Lima). 16 semanas, 4 h académicas/semana (2 h teoría + 2 h lab en aula).
- Sitio del curso: https://ollerenac-uni.github.io/sdr/ (MkDocs Material, GitHub Pages vía `mkdocs gh-deploy` en Actions). Pestañas: Inicio, Sesiones, Exámenes (+ Setup).
- Hardware del alumno: RTL-SDR Blog V3 o V4 (RTL2832U, solo recepción, 8 bits, ≤2.4 MS/s, 24 MHz–1.7 GHz; V4 con HF desde 500 kHz). No todos lo tendrán.
- Alumnos mayoritariamente en Windows con laptops de gama media/baja. Profesor en Linux, sin laptop Windows 11 propia.
- Prerrequisito: Señales y Sistemas. Comunicaciones Digitales puede ser simultáneo.

## Principios transversales

1. **Todo laboratorio se califica desde un archivo IQ oficial.** El dongle es la variante "en vivo", opcional y nunca exigida por la rúbrica.
2. **Versiones fijadas.** GNU Radio 3.10.12 vía radioconda 2025.03.14 para todos. GNU Radio 4 fuera del semestre. `mkdocs-material==9.7.*` (proyecto en modo mantenimiento desde 9.7.0, nov-2025).
3. **Solo recepción y solo servicios públicos.** Radiodifusión, RDS, ADS-B, AIS, satélites, sensores ICM. Voz aeronáutica limitada a ATIS/VOLMET desde archivo; prohibido publicar contenido de voz. Prohibido celular, trunking y cualquier servicio no destinado al público (DS 013-93-TCC art. 4; Reglamento DS 06-94-TCC art. 10; Código Penal 162).

## A. Entorno de trabajo

**Ruta principal: radioconda nativo** en Windows / Linux / macOS. Incluye gnuradio 3.10.12, rtl-sdr 2.0.2 (con soporte V4), gnuradio-osmosdr 0.2.6, SoapySDR, y en el canal `ryanvolz`: gnuradio-rds, gnuradio-adsb, gnuradio-lora_sdr, gnuradio-satellites, gnuradio-ieee802_11. rtl_433 se instala como binario de GitHub (no existe en conda).

Guía única `docs/setup/instalacion.md` con pestañas por OS:

- Común: instalador radioconda, GRC, flowgraph de prueba (Signal Source → QT GUI Frequency Sink), sin dongle.
- Windows: Zadig → WinUSB en "Bulk-In, Interface 0"; desactivar Memory Integrity (Core Isolation); hack de registro contra Windows Update restaurando el driver DVB-T; SmartScreen/antivirus.
- Criterio de aprobado con dongle: `rtl_test -t` detecta el dispositivo (y para V4 imprime "RTL-SDR Blog V4 Detected", criterio anti-clon); `rtl_test -s 2400000` 60 s con pérdidas ≈ 0. La salida va en el Reporte 0.

**Ruta secundaria (documentada, soporte limitado), diferida hasta después de la clínica de S01:** VirtualBox ≥ 7.0 (EHCI/xHCI ya en el paquete base; el Extension Pack no es necesario para USB) + Ubuntu 24.04 + radioconda vía script. Sin OVA. Dongle por passthrough xHCI medido con `rtl_test`; si pierde muestras, `rtl_tcp` desde el host (10.0.2.2 en NAT). Linux nativo: nota "bajo tu responsabilidad" apuntando a la misma guía.

**Archivos IQ:** raw uint8 I/Q de `rtl_sdr` (`.cu8`), clips de 10–30 s. Cada archivo publicado con `fs`, `fc`, ganancia, antena, fecha, SHA256 y "salida esperada". Alojados en GitHub Releases de un repo `sdr-datasets`. ADS-B grabado a 2.0 MS/s (gr-adsb exige múltiplo entero de 2 MS/s).

**Mitigación sin laptop Windows 11:** (1) validar Zadig + `rtl_test` en una VM Windows 11 de evaluación sobre Linux (valida pasos, no throughput); (2) "clínica de drivers" en S01 con 2–3 voluntarios Windows; (3) issue template "instalación" con salida de `rtl_test` obligatoria.

**Dongle:** recomendar RTL-SDR Blog V4 o V3 de tienda oficial o compra colectiva. No es requisito para aprobar.

## B. Sitio de reportes del alumno

- Repo plantilla mínimo `ollerenac-uni/sdr-reportes-template` (marcado "Template repository"): mismo tema y workflow que el curso; pestañas Inicio / Reportes; `docs/index.md` (perfil), `docs/reportes/index.md` (tabla índice), `docs/reportes/00-plantilla.md` (título, fecha, objetivo, procedimiento, resultados, conclusiones, referencias); `requirements.txt` fijado.
- Tutorial `docs/setup/sitio-reportes.md`: cuenta GitHub → "Use this template" → repo público con nombre fijo `sdr-reportes` (URL predecible `https://<usuario>.github.io/sdr-reportes/`) → esperar Action → Settings → Pages → rama `gh-pages` → verificar. Luego flujo local: `git clone`, editar, `commit`, `push`. Al menos un reporte se hace con git local.
- Tarea 0 (S01, vence S02): sitio en línea + Reporte 0 "Instalación y prueba del entorno" con captura del flowgraph de prueba y salida de `rtl_test` (o nota "sin dongle").
- Omitido a propósito: plugin blog de Material (frontmatter `date` obligatorio rompe builds), script de recolección de URLs, OVA.

## C. Syllabus

### Resultados de aprendizaje

1. Explicar la arquitectura de un receptor SDR y los parámetros que limitan su desempeño (fs, bits, ganancia, ancho de banda, rango dinámico, figura de ruido).
2. Representar y manipular señales en banda base compleja (IQ) con Python y GNU Radio.
3. Diseñar cadenas de procesamiento (filtrado, decimación, demodulación) en GNU Radio Companion.
4. Demodular señales analógicas (AM/FM) y digitales reales (PSK/FSK/PPM) y simuladas (QAM), incluyendo sincronización de símbolo, portadora y trama.
5. Decodificar al menos un protocolo real del espectro (RDS, ADS-B o similar) desde muestras IQ.
6. Medir y reportar ocupación espectral y relacionarla con el PNAF 2023 y el RNF del MTC.
7. Documentar y publicar trabajo técnico reproducible (reportes en sitio propio, repositorio con flowgraphs y código).

### Secuencia

| S | Teoría (2 h) | Lab (2 h; desde archivo IQ, dongle opcional) | Entrega |
|---|---|---|---|
| 00 | Pre-lab: video de instalación, instaladores en USB/servidor local | — | — |
| 01 | Qué es SDR, arquitectura RX, RTL2832U por dentro, marco legal | Validar: `rtl_test`, GRC hola mundo, primer espectro FM | R0 (vence S02) |
| 02 | Señales IQ + hardware real: ganancia manual vs AGC, saturación a 8 bits, DC spike, ppm, antena del kit | Archivo FM a 3 ganancias; leer IQ en NumPy | R1 |
| 03 | DSP: FIR, decimación, resampler, PSD y RBW, SNR, aliasing real | Canalizar una emisora FM del archivo, medir SNR | — |
| 04 | GRC a fondo: tasas, streams vs mensajes, QT GUI, bloque Python, hier blocks | Receptor parametrizado + bloque Python de potencia | R2 |
| 05 | AM/FM, de-énfasis, FM estéreo, presupuesto de enlace, figura de ruido | Receptor FM estéreo con audio; ATIS desde archivo | — |
| 06 | Digital I (simulado): símbolos, RRC, ISI, ojo, constelación | TX→AWGN→RX en GRC, diagrama de ojo | R3 |
| 07 | Sincronización: reloj de símbolo, Costas/FLL, ambigüedad, diferencial | BPSK simulado con sync → constelación RDS real enganchada | — |
| 08 | Examen parcial (S01–S07) | — | — |
| 09 | Digital II: QAM, Eb/N0, BER teórico vs Monte Carlo (curvas en pre-lab Colab) | Medición de BER en GRC | Propuesta de proyecto |
| 10 | Trama y paquetes: preámbulo, correlación, CRC, scrambling | RDS grupos completos vs gr-rds; preámbulo + CRC ADS-B con esqueleto Python (pyModeS) | R4 |
| 11 | Sensado de espectro: detección de energía, Pfa/Pd, PNAF 2023, RNF | Barrido `rtl_power`, mapa de ocupación, identificar servicios | R5 |
| 12 | OFDM: IFFT/FFT, CP, pilotos, Schmidl-Cox; multipath como motivación (30 min) | TX/RX OFDM (material propio); ISDB-Tb real, canal 16 UHF, vista parcial | Hito 1 |
| 13 | IoT: ICM 915–928 MHz, OOK/FSK de sensores, LoRa CSS/SF/BW, plan AU915 | rtl_433 desde archivo; LoRa TX→RX simulado en gr-lora_sdr + un archivo real | — |
| 14 | Satélites (Meteor M2-4 LRPT, gr-satellites) + panorama TX (Pluto, HackRF, USRP, srsRAN) 45 min | Meteor LRPT con SatDump desde archivo | Hito 2 |
| 15 | Integración y ensayo de demo | Asesoría | — |
| 16 | Presentaciones de proyecto | — | Proyecto |

### Evaluación

- Parcial: 30 %.
- Reportes: 30 % = R0–R5, 5 % cada uno. Rúbrica: reproducibilidad, análisis, claridad. Exige resultados sobre el archivo oficial.
- Proyecto: 40 % = propuesta 5 + hito 1 10 + hito 2 10 + demo y reporte final 15. Grupos de 2–3.
- Temas de proyecto: ADS-B con mapa, RDS completo, Meteor LRPT, dashboard rtl_433, LoRa AU915, ACARS, AIS Callao (requiere antena VHF en azotea; sin verificar), sensado de banda con reporte PNAF.

### Fuera del curso

NOAA APT (satélites desactivados en 2025), radiosondas SENAMHI (no verificable), ecualización como semana propia, Wi-Fi/DVB/QAM real (fuera del alcance del RTL-SDR), GNU Radio 4, plugin blog, OVA.

## Evidencia de las revisiones adversarias

- RTL2832U es USB 2.0; 2.4 MS/s × 2 B = 4.8 MB/s ≈ 38 Mbit/s. https://www.rtl-sdr.com/about-rtl-sdr/
- VirtualBox 7.0: "The EHCI and XHCI USB controller devices are now part of the open source base package". https://www.virtualbox.org/wiki/Changelog-7.0
- Passthrough USB de VirtualBox con pérdidas incluso con USB2 bien configurado. https://lists.gnu.org/archive/html/discuss-gnuradio/2018-01/msg00207.html
- Windows 11 reemplaza WinUSB por el driver DVB-T. https://www.rtl-sdr.com/a-registry-hack-to-stop-windows-11-replacing-the-winusb-driver-installed-via-zadig/
- radioconda 2025.03.14 y sus paquetes. https://github.com/radioconda/radioconda-installer/releases/tag/2025.03.14
- rtl-sdr upstream con soporte V4 desde v2.0.0; Ubuntu 24.04 trae 2.0.1. https://github.com/osmocom/rtl-sdr
- GNU Radio 4 RC1 (mar-2026). https://www.gnuradio.org/news/2026-03-22-gr4-release-candidate-1/
- mkdocs-material en modo mantenimiento. https://squidfunk.github.io/mkdocs-material/blog/2025/11/11/insiders-now-free-for-everyone/
- NOAA-15/18/19 desactivados en 2025. https://www.ospo.noaa.gov/data/messages/2025/08/MSG_20250820_1410.html
- Meteor M2-4 activo. https://db.satnogs.org/satellite/VSVI-4798-5613-4587-2414/
- ISDB-Tb Lima, apagón analógico 2025-01-01. https://www.concortv.gob.pe/apagon-analogico-para-lima-y-callao/
- PNAF 2023, RM 597-2023-MTC/01.03. https://www.gob.pe/institucion/mtc/normas-legales/4243339-0597-2023-mtc-01-03 · RNF: https://rnf.mtc.gob.pe/
- ICM 915–928 MHz, exento ≤1 W (RM 1685-2023-MTC). https://www.gob.pe/institucion/mtc/normas-legales/4900290-1685-2023-mtc-01-03
- gr-adsb exige múltiplo de 2 MS/s. https://github.com/mhostetter/gr-adsb · pyModeS: https://mode-s.org/1090mhz/
- rtl_433 binarios. https://github.com/merbanan/rtl_433/releases
- Ley de Telecomunicaciones (TUO DS 013-93-TCC). https://www.osiptel.gob.pe/media/kbejkkkk/ds013-93-tcc-tuo-ley-de-telecomunicaciones.pdf
- Reglamento (DS 06-94-TCC). https://www.osiptel.gob.pe/media/wvidghyb/ds06-94-tcc-reg-general-ley-de-telecomunicaciones.pdf

## Riesgos abiertos

- Pérdida de muestras con dongle en Windows sin validar por el profesor: se resuelve en la clínica de S01.
- Saturación por transmisores cercanos al campus (Rímac): lab de ganancia en S02 lo convierte en contenido.
- AIS Callao sin verificar: solo como tema de proyecto con advertencia.
- Grabaciones IQ: el profesor debe grabar FM (3 ganancias), ATIS, ADS-B a 2.0 MS/s, barrido rtl_power, ISDB-T, sensores ICM, LoRa AU915, Meteor LRPT. Sin estas grabaciones los labs sin dongle no existen.

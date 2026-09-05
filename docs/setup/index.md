# Guías de instalación

!!! warning "Antes de la semana 1"
    Instala todo en casa durante la semana 0. El laboratorio de la Sesión 01 solo **valida** la instalación; no hay tiempo para instalar en clase. La descarga es de unos 600 MB: hazla con buena conexión.

## Qué necesitas

| Componente | Obligatorio | Notas |
|---|:---:|---|
| Laptop de 64 bits, 8 GB de RAM, 5 GB libres | Sí | Windows 10/11, Ubuntu 22.04 o superior, macOS 12 o superior |
| radioconda 2025.03.14 | Sí | GNU Radio 3.10.12 + drivers SDR. Guía: [Instalar GNU Radio](instalacion.md) |
| Cuenta de GitHub y sitio de reportes | Sí | Tutorial disponible antes de la semana 2 |
| RTL-SDR Blog V4 (o V3) | No | Todo laboratorio funciona con archivos IQ. Guía: [Configurar el RTL-SDR](rtl-sdr.md) |

## Rutas soportadas

- **Principal (con soporte del curso):** radioconda instalado de forma nativa en Windows, Linux o macOS. Misma versión de GNU Radio para todos.
- **Secundaria (soporte limitado):** máquina virtual Ubuntu 24.04 en VirtualBox 7.x con radioconda dentro. Se publicará una guía corta después de la semana 1 solo si hace falta.
- **Linux nativo con dual-boot:** bajo tu responsabilidad. Usa la pestaña *Linux* de la guía de instalación.

## Si compras el dongle

Recomendado: **RTL-SDR Blog V4** (o V3) comprado en la [tienda oficial](https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/) o en la compra colectiva del curso. En el mercado local abundan clones que no funcionan igual. Criterio de autenticidad: `rtl_test -t` imprime `RTL-SDR Blog V4 Detected` (en el V3 no aparece esa línea, pero el tuner debe ser `Rafael Micro R820T`).

El dongle **no** es obligatorio: ningún reporte ni examen exige hardware. Todos los laboratorios se califican con los archivos IQ oficiales del curso.

## Marco legal (resumen)

- En este curso solo se **recibe**. El RTL-SDR no puede transmitir.
- Solo se reciben y analizan servicios **destinados al público**: radiodifusión FM/AM y su RDS, ADS-B de aviones, AIS de barcos, satélites meteorológicos, sensores en banda ICM, y difusiones aeronáuticas automáticas (ATIS, VOLMET).
- **Prohibido en el curso:** telefonía celular, sistemas troncalizados, y cualquier comunicación no destinada al público. Prohibido publicar contenido de voz.
- Base legal: TUO de la Ley de Telecomunicaciones ([DS 013-93-TCC](https://www.osiptel.gob.pe/media/kbejkkkk/ds013-93-tcc-tuo-ley-de-telecomunicaciones.pdf), art. 4), su Reglamento ([DS 06-94-TCC](https://www.osiptel.gob.pe/media/wvidghyb/ds06-94-tcc-reg-general-ley-de-telecomunicaciones.pdf), art. 10) y el Código Penal (art. 162). Detalle en la [Sesión 01](../sessions/01-introduccion-sdr/index.md#6-marco-legal-del-curso).

## Problemas

Abre un [issue en el repositorio del curso](https://github.com/ollerenac-uni/sdr/issues/new) con: sistema operativo, paso donde falla y la **salida completa** del comando (texto, no captura). Revisa antes la sección *Problemas frecuentes* de cada guía.

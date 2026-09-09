---
title: "Sesión 01 — Introducción a la Radio Definida por Software"
session: 1
description: "Qué es un SDR, cómo funciona un receptor RTL-SDR por dentro, qué limita su desempeño y qué se puede recibir legalmente en Perú."
status: draft
---

# Sesión 01 — Introducción a la Radio Definida por Software

## Objetivos de aprendizaje

Al finalizar esta sesión, el estudiante será capaz de:

1. Explicar qué es un *software-defined radio* (radio definida por software) y qué funciones del receptor pasan del hardware al software
2. Describir la cadena de recepción del RTL-SDR (tuner → ADC → DDC → USB) y el papel de cada bloque
3. Relacionar los parámetros $f_c$, $f_s$, ganancia y resolución en bits con el ancho de banda observable y el rango dinámico
4. Verificar una instalación de GNU Radio y un dongle con `rtl_test`, interpretando su salida
5. Identificar qué señales del espectro peruano se pueden recibir y publicar dentro del marco legal del curso

---

## Introducción

Antes de la adopción masiva del procesamiento digital, una radio convencional se diseñaba para un solo sistema. Cada función —filtrado, mezcla y demodulación— correspondía a un circuito fijo. Cambiar de estándar exigía cambiar el hardware.

La radio definida por software (*software-defined radio*, SDR) cambia ese enfoque: digitaliza la señal tan pronto como resulta técnica y económicamente viable, y traslada al software el procesamiento posterior.

Una misma plataforma puede recibir FM, señales aeronáuticas, satélites o sensores con solo cambiar el programa.

Joseph Mitola acuñó el término en 1995. Durante la primera década, la tecnología se concentró en entornos militares y de laboratorio.

En una radio convencional, cada aplicación determina una cadena de circuitos. En un SDR, varias aplicaciones reutilizan el mismo *front-end* y digitalizador; la selección, el filtrado y la demodulación pasan al software.

![Comparación entre tres radios convencionales con hardware dedicado y una plataforma SDR cuyo hardware alimenta varias aplicaciones definidas por software](figures/radio-convencional-vs-sdr.png)

**Figura 1.** Comparación entre radios convencionales de hardware dedicado y una plataforma SDR reutilizable.

El SDR no elimina necesariamente el hardware analógico. Desplaza hacia el dominio digital una frontera que depende del costo, el consumo y la frecuencia de operación del equipo.

En 2012, Antti Palosaari descubrió que el RTL2832U de ciertos sintonizadores USB de televisión digital podía entregar muestras I/Q crudas al computador. El proyecto Osmocom desarrolló `librtlsdr` y dio origen al **RTL-SDR** de bajo costo.

El curso utiliza ese dongle, o grabaciones realizadas con él, para construir receptores completos en GNU Radio y Python.

La sesión responde tres preguntas: ¿qué contiene el dongle?, ¿qué limita su funcionamiento? y ¿qué señales pueden recibirse legalmente?

---

## Teoría

### 1. Del superheterodino al SDR

El receptor *superheterodino* dominó la radio durante gran parte del siglo XX. Su nombre describe la generación de «otra frecuencia» mediante la mezcla de la señal recibida con un oscilador local.

Fessenden introdujo el término en 1901. El método consiste en **multiplicar** la señal recibida, de frecuencia $f_{RF}$, por una senoide local de frecuencia $f_{LO}$. El producto contiene dos frecuencias nuevas: la suma y la diferencia.

$$
\cos(2\pi f_{RF} t)\cos(2\pi f_{LO} t) = \tfrac{1}{2}\cos\!\big(2\pi (f_{RF}-f_{LO})\,t\big) + \tfrac{1}{2}\cos\!\big(2\pi (f_{RF}+f_{LO})\,t\big).
$$

Un filtro conserva la diferencia y traslada la señal a una frecuencia elegida por el diseño. En el superheterodino de Armstrong (1918), esa diferencia se sitúa en una frecuencia intermedia (IF) fija, como 455 kHz en AM o 10.7 MHz en FM.

Un mismo filtro estrecho y un amplificador trabajan en esa IF para cualquier emisora. La sintonización se logra modificando $f_{LO}$.

```mermaid
flowchart LR
    ANT[Antena] -->|①| PRE[Filtro RF<br/>preselector]
    PRE -->|②| LNA[Amplificador<br/>de bajo ruido]
    LNA -->|③| MIX((×))
    LO[Oscilador local<br/>f_LO] --> MIX
    MIX -->|④| IFF[Filtro IF<br/>paso banda]
    IFF -->|⑤| IFA[Amplificador IF]
    IFA -->|⑥| DEM[Demodulador]
    DEM -->|⑦| AF[Amplificador<br/>de audio]
```

**Figura 2.** Cadena funcional de un receptor superheterodino y puntos de observación de la señal.

Puntos de observación del espectro:

- ① en la antena,
- ② tras el preselector,
- ③ tras el LNA,
- ④ a la salida del mezclador, donde aparecen suma y diferencia,
- ⑤ tras el filtro IF,
- ⑥ tras el amplificador IF,
- ⑦ banda base tras el demodulador.

<!-- TODO (profesor): explicar aquí las transformaciones del espectro de la señal en los puntos ① a ⑦. -->

Cada bloque es un circuito diseñado para una IF y una modulación concretas. El **SDR ideal** reduce la cadena a antena, ADC y software.

Sin embargo, digitalizar directamente a 1 GHz con buena resolución exige un ADC rápido, costoso y de alto consumo.

Por ello, los SDR prácticos conservan un *front-end* analógico. Su función es acondicionar y, cuando resulta necesario, trasladar la señal a una frecuencia que pueda muestrear un ADC más modesto.

Según dónde queda la señal antes del ADC hay tres familias:

| Arquitectura | Señal antes del ADC | Ejemplos | Costo típico |
|---|---|---|---|
| *RF sampling* | En RF, sin mezcla | Convertidores RF de laboratorio | miles de US$ |
| *Zero-IF* (conversión directa) | En banda base, I y Q separados | ADALM-Pluto, HackRF, LimeSDR | 100–400 US$ |
| *Low-IF* | En una IF baja, señal real | **RTL-SDR** | 30–40 US$ |

![Comparación de las cadenas de recepción de muestreo directo de RF, Zero-IF y Low-IF, indicando dónde aparece el ADC y dónde se forman I y Q](figures/arquitecturas-receptores-sdr.png)

**Figura 3.** Comparación entre muestreo directo de RF, conversión directa (*Zero-IF*) y frecuencia intermedia baja (*Low-IF*).

La diferencia decisiva es **qué señal ve el ADC**. En muestreo directo ve RF; en *Zero-IF* dos ADC reciben los voltajes I y Q producidos por mezcladores analógicos; en *Low-IF* un ADC recibe una IF real y un DDC forma I/Q digitalmente.

La figura sintetiza las comparaciones publicadas por [Analog Devices](https://www.analog.com/en/resources/technical-articles/a-review-of-wideband-rf-receiver-architecture-options.html).

También considera el informe de arquitecturas de recepción de [Texas Instruments](https://www.ti.com/kr/lit/pdf/snaa329).

Como ejemplo verificable de *Zero-IF*, el [ADALM-Pluto](https://wiki.analog.com/university/tools/pluto/users/understanding) emplea conversión directa dentro del AD9363.

El RTL-SDR es *Low-IF*: el tuner deja la señal en una IF de pocos megahercios y el ADC la muestrea como señal real.

La separación en componentes I y Q ocurre después, en el dominio digital. Para comprender el proceso, resulta necesario examinar el interior del receptor.

### 2. Cadena de recepción del RTL-SDR

![Diagrama técnico simplificado del interior de un RTL-SDR Blog V4, con el triplexor, el tuner R828D, el RTL2832U, el TCXO y las rutas de señal](figures/rtl-sdr-v4-interior.png)

**Figura 4.** Representación funcional de los componentes principales de un RTL-SDR Blog V4.

La ilustración es funcional, no fotográfica: identifica los componentes necesarios para seguir la señal, pero no reproduce su posición exacta sobre la placa.

Su contenido se basa en la [hoja de datos oficial del V4](https://www.rtl-sdr.com/wp-content/uploads/2024/12/RTLSDR_V4_Datasheet_V_1_0.pdf).

**V3** y **V4** son generaciones comerciales del dongle RTL-SDR Blog, no versiones del estándar USB ni del chip RTL2832U. El V3 emplea el tuner R820T2; el V4 lo reemplaza por el R828D y añade filtrado de entrada y un *upconverter* para HF.

El dongle contiene dos circuitos integrados principales en la cadena de recepción:

- El **tuner** es el *front-end* analógico: Rafael Micro R820T2 en el V3 y R828D en el V4.

  Ambos pertenecen a la misma familia y utilizan el mismo driver. El R828D sustituyó al R820T2 y ofrece tres entradas de RF, utilizadas por el V4 para los filtros de banda y el *upconverter* de HF.
- El **RTL2832U** es un demodulador de televisión reconvertido en digitalizador: contiene el ADC, el conversor descendente digital y el controlador USB.

```mermaid
flowchart LR
    ANT[Antena] -->|①| TUN[Tuner R828D / R820T2<br/>LNA · mezclador · filtro IF 5 MHz · VGA]
    TUN -->|② IF real<br/>3.57 MHz| ADC[ADC 8 bits<br/>28.8 MS/s]
    ADC -->|③| DDC[Mezcla digital<br/>× cos, × −sin a 3.57 MHz]
    DDC -->|④ I/Q| LPF[Filtro paso bajo<br/>+ decimación → f_s]
    LPF -->|⑤| USB[Control USB<br/>bytes I,Q,I,Q…]
    USB -->|⑥ USB 2.0| PC[PC: librtlsdr<br/>→ GNU Radio / Python]
    XTAL[Cristal 28.8 MHz<br/>TCXO 1 ppm] -.-> TUN
    XTAL -.-> ADC
```

**Figura 5.** Cadena completa de recepción del RTL-SDR, desde la antena hasta el computador.

Todo el procesamiento comprendido entre los puntos ② y ⑤ ocurre dentro del RTL2832U.

La exposición siguiente recorre la señal punto por punto y muestra su espectro. Cada diagrama resalta en ámbar el bloque activo. El ejemplo corresponde a la sección 7: una emisora objetivo en $f_c = 99.1$ MHz y una tasa $f_s = 2.4$ MS/s.

Las figuras son esquemáticas: lóbulos de 200 kHz para cada emisora de FM, sin escala de potencia.

#### 2.1. Punto ① — En la antena: banda de RF

```mermaid
flowchart LR
    ANT[Antena] -->|①| TUN[Tuner R828D / R820T2<br/>LNA · mezclador · filtro IF 5 MHz · VGA]
    TUN -->|② IF real<br/>3.57 MHz| ADC[ADC 8 bits<br/>28.8 MS/s]
    ADC -->|③| DDC[Mezcla digital<br/>× cos, × −sin a 3.57 MHz]
    DDC -->|④ I/Q| LPF[Filtro paso bajo<br/>+ decimación → f_s]
    LPF -->|⑤| USB[Control USB<br/>bytes I,Q,I,Q…]
    USB -->|⑥ USB 2.0| PC[PC: librtlsdr<br/>→ GNU Radio / Python]
    XTAL[Cristal 28.8 MHz<br/>TCXO 1 ppm] -.-> TUN
    XTAL -.-> ADC
    classDef activo fill:#fde68a,stroke:#d97706,stroke-width:3px,color:#111827;
    class ANT activo;
```

![Espectro en la antena: emisoras de FM cada 400 kHz alrededor de la emisora objetivo en 99.1 MHz y el oscilador local del tuner en 95.53 MHz](figures/cadena-rx-1-antena.png)

**Figura 6.** Punto ①: banda de RF en la antena y ubicación del bloque observado en la cadena RTL-SDR.

- Cada lóbulo gris representa una emisora de FM; el azul identifica la emisora objetivo en $f_c = 99.1$ MHz.
- La línea verde punteada representa el oscilador local del tuner, situado por el driver en $f_{LO} = f_c - 3.57$ MHz.
- **Sintonizar equivale a elegir $f_{LO}$**: la emisora ubicada 3.57 MHz por encima del LO cae en el centro de la IF.
- El LNA (*Low Noise Amplifier*) eleva el nivel de toda la banda con la ganancia configurada en el dongle.

#### 2.2. Punto ② — Tras el tuner: señal real en la IF

- El mezclador multiplica la banda completa por el LO y, por la identidad de la sección 1, produce suma y diferencia.
- La diferencia traslada la banda en bloque: la emisora en $f_c$ cae en 3.57 MHz, y cada vecina en $3.57 + (f - f_c)$ MHz, conservando sus separaciones.
- La suma cae cerca de 194 MHz y el filtro IF la elimina.
- El filtro tiene 5 MHz de ancho por defecto y está centrado en 3.57 MHz. Por tanto, deja pasar de 1.07 a 6.07 MHz, equivalentes a unos ±2.5 MHz alrededor de $f_c$.
- El VGA (Variable Gain Amplifier) ajusta el nivel antes del ADC.

```mermaid
flowchart LR
    ANT[Antena] -->|①| TUN[Tuner R828D / R820T2<br/>LNA · mezclador · filtro IF 5 MHz · VGA]
    TUN -->|② IF real<br/>3.57 MHz| ADC[ADC 8 bits<br/>28.8 MS/s]
    ADC -->|③| DDC[Mezcla digital<br/>× cos, × −sin a 3.57 MHz]
    DDC -->|④ I/Q| LPF[Filtro paso bajo<br/>+ decimación → f_s]
    LPF -->|⑤| USB[Control USB<br/>bytes I,Q,I,Q…]
    USB -->|⑥ USB 2.0| PC[PC: librtlsdr<br/>→ GNU Radio / Python]
    XTAL[Cristal 28.8 MHz<br/>TCXO 1 ppm] -.-> TUN
    XTAL -.-> ADC
    classDef activo fill:#fde68a,stroke:#d97706,stroke-width:3px,color:#111827;
    class TUN activo;
```

![Espectro real en la IF: lóbulo de la señal en +3.57 MHz, su espejo en −3.57 MHz, vecinas trasladadas y la máscara del filtro IF de 5 MHz](figures/cadena-rx-2-if.png)

**Figura 7.** Punto ②: bloque tuner resaltado y espectro real resultante en la IF de 3.57 MHz.

Hay un hecho que el diagrama no dice y que decide todo lo que viene después: **la señal en la IF es real**.

Aquí *real* no significa «física» en oposición a «simulada». Significa que, en cada instante, la IF está representada por un único valor real de tensión en un cable.

La señal de RF que llega a la antena también es físicamente real. Los números complejos son una representación matemática que permite describir su amplitud y su fase. El espectro de una señal real es simétrico:

$$
x(t) = \mathrm{Re}\{m(t)\,e^{j2\pi f_{IF} t}\}
\quad\Longrightarrow\quad
X(f) = \tfrac{1}{2}M(f - f_{IF}) + \tfrac{1}{2}M^*(-f - f_{IF}).
$$

El espectro contiene un lóbulo en $+3.57$ MHz y su espejo conjugado en $-3.57$ MHz. No representan dos señales, sino las dos mitades de una señal real, del mismo modo que un coseno puede expresarse como la suma de dos exponenciales.

El primer *flowgraph* de la guía muestra el mismo efecto: la salida *Complex* presenta un pico en $+1$ kHz, mientras que la salida *Float* presenta dos picos en $\pm 1$ kHz.

La señal azul aparece en $+3.57$ MHz y las emisoras vecinas, en gris, permanecen a sus lados. El lóbulo rojo rayado corresponde al espejo en $-3.57$ MHz. La respuesta simétrica del filtro IF se representa con una línea negra punteada.

En 0 Hz permanecen el desplazamiento de continua, la fuga del LO y el ruido 1/f. La arquitectura *Low-IF* aleja esos defectos 3.57 MHz de la señal útil, aunque exige un ADC más rápido.

#### 2.3. Punto ③ — ADC: 28.8 millones de muestras reales por segundo

La frecuencia más alta que entra al ADC es $3.57 + 2.5 = 6.07$ MHz. Nyquist exige una tasa superior a $2 \times 6.07 = 12.1$ MS/s. El RTL2832U muestrea a 28.8 MS/s, la frecuencia de su cristal, y ofrece margen suficiente.

Su zona de Nyquist abarca de $-14.4$ a $+14.4$ MHz. El filtro IF también actúa como filtro *anti-aliasing*: cualquier componente que superase 14.4 MHz reaparecería plegada dentro de esa zona.

Muestrear tiene una consecuencia sobre el espectro: lo hace **periódico**. El espectro entero se copia cada $f_s = 28.8$ MHz. Basta mirar un período.

```mermaid
flowchart LR
    ANT[Antena] -->|①| TUN[Tuner R828D / R820T2<br/>LNA · mezclador · filtro IF 5 MHz · VGA]
    TUN -->|② IF real<br/>3.57 MHz| ADC[ADC 8 bits<br/>28.8 MS/s]
    ADC -->|③| DDC[Mezcla digital<br/>× cos, × −sin a 3.57 MHz]
    DDC -->|④ I/Q| LPF[Filtro paso bajo<br/>+ decimación → f_s]
    LPF -->|⑤| USB[Control USB<br/>bytes I,Q,I,Q…]
    USB -->|⑥ USB 2.0| PC[PC: librtlsdr<br/>→ GNU Radio / Python]
    XTAL[Cristal 28.8 MHz<br/>TCXO 1 ppm] -.-> TUN
    XTAL -.-> ADC
    classDef activo fill:#fde68a,stroke:#d97706,stroke-width:3px,color:#111827;
    class ADC activo;
```

![Espectro tras el ADC: los dos lóbulos de la IF intactos dentro de la zona de Nyquist de ±14.4 MHz y sus copias periódicas en ±28.8 MHz](figures/cadena-rx-3-adc.png)

**Figura 8.** Punto ③: ADC resaltado, zona de Nyquist y copias periódicas producidas por el muestreo.

La franja azul claro representa la zona de Nyquist. Dentro de ella se mantiene el espectro del punto ②: la banda gris de 5 MHz, la emisora objetivo en azul y su espejo en rojo.

Las copias en $\pm 28.8$ MHz son una consecuencia del muestreo y no contienen información nueva. No se solapan porque la señal termina en 6.07 MHz, muy por debajo de 14.4 MHz. La señal conserva su información, ahora codificada con 8 bits.

#### 2.4. Punto ④ — Del voltaje real a las muestras complejas I/Q

El ADC no produce números complejos. En cada instante $n$ entrega un único número real $x[n]$, proporcional al voltaje de la IF. La cuadratura aparece en el bloque digital siguiente: el DDC.

El DDC envía la misma secuencia $x[n]$ por dos ramas. Una se multiplica por un coseno y la otra por un seno con un desfase de $90^\circ$:

$$
I_{\mathrm{raw}}[n]=x[n]\cos\!\left(2\pi f_{IF}\frac{n}{f_{ADC}}\right),
\qquad
Q_{\mathrm{raw}}[n]=-x[n]\sin\!\left(2\pi f_{IF}\frac{n}{f_{ADC}}\right).
$$

Los filtros paso bajo eliminan los productos de alta frecuencia y dejan $I[n]$ y $Q[n]$. No son dos mediciones independientes: son la misma señal comparada con dos referencias separadas $90^\circ$.

El par conserva la amplitud y la fase de la señal. Por conveniencia, GNU Radio lo transporta como un solo número complejo:

$$
z[n]=I[n]+jQ[n].
$$

Para una sinusoide didáctica, ignorando una ganancia común, $I(t)=\cos(2\pi f_0t)$ y $Q(t)=\sin(2\pi f_0t)$. Cada una es una señal real; juntas trazan la hélice de $z(t)=e^{j2\pi f_0t}$.

![Una sinusoide compleja representada como una hélice cuyas proyecciones son las dos señales reales I y Q, separadas noventa grados](figures/iq-cuadratura-tiempo.png)

**Figura 9.** Representación conjunta de una sinusoide compleja y sus componentes reales I y Q en cuadratura.

Cada componente real tiene dos copias espectrales, en $+f_0$ y $-f_0$. Al formar $I+jQ$, el factor $j$ cambia sus fases: las copias positivas se suman y las negativas se cancelan.

No se cancela «la parte imaginaria» para obtener una señal real. El resultado sigue siendo complejo, pero ya permite distinguir una frecuencia positiva de una negativa respecto a la frecuencia central.

![Espectros de I, jQ e I más jQ: las componentes se suman en frecuencia positiva y se cancelan en frecuencia negativa](figures/iq-cancelacion-espectral.png)

**Figura 10.** Formación de $I+jQ$: suma de las componentes positivas y cancelación de las copias negativas.

!!! info "¿Qué significa `Complex Float 32` en GNU Radio?"
    Una muestra contiene dos números `float32`: uno para I y otro para Q. Cada componente ocupa 32 bits, de modo que la muestra compleja completa ocupa 64 bits u 8 bytes.

    Las fuentes SDR y la cadena de procesamiento I/Q suelen usar este tipo. No todos los bloques de GNU Radio son complejos: después de demodular, por ejemplo, el audio normalmente se representa como `Float 32`.

    Esto tampoco es el formato `.cu8` del cable USB. Allí I y Q ocupan un byte cada uno; el bloque fuente de GNU Radio los centra, normaliza y entrega al *flowgraph* como componentes de punto flotante.

##### 2.4.1. Mezcla digital y desplazamiento del espectro

En el RTL2832U, los multiplicadores usan $\cos(2\pi \cdot 3.57\,\text{MHz}\cdot t)$ y $-\sin(2\pi \cdot 3.57\,\text{MHz}\cdot t)$.

Juntas, las dos ramas equivalen a multiplicar por $e^{-j2\pi \cdot 3.57\,\text{MHz}\cdot t}$.

Multiplicar por esa exponencial compleja **desplaza todo el espectro** en $-3.57$ MHz. La señal que estaba en $+3.57$ MHz cae en 0 Hz; su espejo, situado en $-3.57$ MHz, cae en $-7.14$ MHz.

```mermaid
flowchart LR
    ANT[Antena] -->|①| TUN[Tuner R828D / R820T2<br/>LNA · mezclador · filtro IF 5 MHz · VGA]
    TUN -->|② IF real<br/>3.57 MHz| ADC[ADC 8 bits<br/>28.8 MS/s]
    ADC -->|③| DDC[Mezcla digital<br/>× cos, × −sin a 3.57 MHz]
    DDC -->|④ I/Q| LPF[Filtro paso bajo<br/>+ decimación → f_s]
    LPF -->|⑤| USB[Control USB<br/>bytes I,Q,I,Q…]
    USB -->|⑥ USB 2.0| PC[PC: librtlsdr<br/>→ GNU Radio / Python]
    XTAL[Cristal 28.8 MHz<br/>TCXO 1 ppm] -.-> TUN
    XTAL -.-> ADC
    classDef activo fill:#fde68a,stroke:#d97706,stroke-width:3px,color:#111827;
    class DDC activo;
```

![Espectro tras la mezcla digital: la señal centrada en 0 Hz, la imagen en −7.14 MHz y la máscara del filtro paso bajo digital de ±1.2 MHz](figures/cadena-rx-4-ddc.png)

**Figura 11.** Punto ④: DDC resaltado y desplazamiento de la señal útil a 0 Hz y de su imagen a $-7.14$ MHz.

La flecha negra indica el desplazamiento de $-3.57$ MHz. La señal azul queda en 0 Hz y pasa a ser compleja: el multiplicador por coseno produce I y el multiplicador por seno produce Q. El lóbulo rayado en $-7.14$ MHz es la imagen.

El coseno y el seno digitales mantienen un desfase exacto de 90° y amplitudes idénticas. Por ello, esta generación de cuadratura evita el desbalance I/Q propio de mezcladores analógicos.

#### 2.5. Punto ⑤ — Filtro paso bajo y decimación

Un filtro paso bajo digital conserva $|f| < f_s^{\text{out}}/2$: ±1.2 MHz para una salida de 2.4 MS/s. El filtro elimina la imagen de $-7.14$ MHz y las emisoras que quedan fuera de la ventana.

Después, un *downsampler* reduce la tasa de 28.8 a 2.4 MS/s, lo que equivale a conservar una de cada 12 muestras. Cuando la razón no es entera, el chip utiliza un *resampler* fraccional.

El registro de razón se gobierna mediante $28.8\,\text{MHz} \cdot 2^{22} / f_s$. Por ello, el dispositivo admite tasas como 1.024 MS/s, aunque no dividan exactamente 28.8 MHz, con una ligera cuantización de la tasa real.

```mermaid
flowchart LR
    ANT[Antena] -->|①| TUN[Tuner R828D / R820T2<br/>LNA · mezclador · filtro IF 5 MHz · VGA]
    TUN -->|② IF real<br/>3.57 MHz| ADC[ADC 8 bits<br/>28.8 MS/s]
    ADC -->|③| DDC[Mezcla digital<br/>× cos, × −sin a 3.57 MHz]
    DDC -->|④ I/Q| LPF[Filtro paso bajo<br/>+ decimación → f_s]
    LPF -->|⑤| USB[Control USB<br/>bytes I,Q,I,Q…]
    USB -->|⑥ USB 2.0| PC[PC: librtlsdr<br/>→ GNU Radio / Python]
    XTAL[Cristal 28.8 MHz<br/>TCXO 1 ppm] -.-> TUN
    XTAL -.-> ADC
    classDef activo fill:#fde68a,stroke:#d97706,stroke-width:3px,color:#111827;
    class LPF activo;
```

![Espectro tras filtrar y decimar: la emisora objetivo en 0 Hz y sus vecinas dentro de la ventana de ±1.2 MHz; el ancho observable es fs = 2.4 MHz](figures/cadena-rx-5-decimacion.png)

**Figura 12.** Punto ⑤: filtro y decimador resaltados, con la señal útil dentro de la ventana de ±1.2 MHz.

El eje representa frecuencia respecto a $f_c$. Solo permanecen la emisora objetivo y las vecinas comprendidas dentro de ±1.2 MHz. La señal compleja no requiere una copia espectral redundante; por eso, el ancho de banda observable es $f_s$.

El filtro digital fija el ancho de banda mostrado por GNU Radio, mientras que el filtro IF protege al ADC. Las muestras I y Q vuelven a recortarse a 8 bits para el enlace USB, y los bordes del filtro reducen la zona útil a cerca del 80 %.

#### 2.6. Punto ⑥ — USB: bytes I, Q, I, Q…

```mermaid
flowchart LR
    ANT[Antena] -->|①| TUN[Tuner R828D / R820T2<br/>LNA · mezclador · filtro IF 5 MHz · VGA]
    TUN -->|② IF real<br/>3.57 MHz| ADC[ADC 8 bits<br/>28.8 MS/s]
    ADC -->|③| DDC[Mezcla digital<br/>× cos, × −sin a 3.57 MHz]
    DDC -->|④ I/Q| LPF[Filtro paso bajo<br/>+ decimación → f_s]
    LPF -->|⑤| USB[Control USB<br/>bytes I,Q,I,Q…]
    USB -->|⑥ USB 2.0| PC[PC: librtlsdr<br/>→ GNU Radio / Python]
    XTAL[Cristal 28.8 MHz<br/>TCXO 1 ppm] -.-> TUN
    XTAL -.-> ADC
    classDef activo fill:#fde68a,stroke:#d97706,stroke-width:3px,color:#111827;
    class USB activo;
```

![Salida USB: muestras I y Q como bytes sin signo de 0 a 255, con el cero en 127.5, intercalados](figures/cadena-rx-6-usb.png)

**Figura 13.** Punto ⑥: interfaz USB resaltada y representación de las muestras I/Q como bytes intercalados.

Cada muestra compleja sale como dos bytes sin signo, primero I y luego Q, con el cero en 127.5. A 2.4 MS/s, el caudal alcanza 4.8 MB/s. GNU Radio o NumPy convierten la secuencia al intervalo de $-1$ a $+1$ mediante $(x-127.5)/127.5$.

La [guía del RTL-SDR](../../setup/rtl-sdr.md#grabar-muestras-iq) desarrolla esa conversión. El mismo enlace USB transporta las órdenes de frecuencia, ganancia y tasa hacia los registros del RTL2832U, que programa el tuner por I²C.

El cristal de 28.8 MHz, representado con una línea discontinua, sirve como referencia del PLL del tuner y como reloj del ADC. Un error de $p$ ppm desplaza $f_c$ y $f_s$ en la misma proporción; una sola corrección compensa ambos errores.


??? note "Muestreo directo en el V3, y por qué el V4 lo cambió"
    El V3 dispone de un modo *direct sampling* para HF. Un puente conduce la señal de la antena, a través de un filtro paso bajo, directamente a la entrada Q del ADC y evita el tuner.

    En este modo, la zona de Nyquist abarca de 0 a 14.4 MHz. Una señal de HF por encima de 14.4 MHz se pliega dentro de esa zona y aparece como una imagen, sin la protección del filtro IF.

    El V4 reemplazó ese modo por un *upconverter*. Este bloque traslada la banda de 0–24 MHz a una frecuencia que el tuner puede recibir, por lo que las señales de HF recorren la cadena normal.

El tuner y el ADC constituyen la etapa previa al procesamiento por software. Las operaciones del curso —filtrado, demodulación FM, sincronización BPSK y decodificación ADS-B— actúan sobre la secuencia I/Q del punto ⑥.

Esa secuencia queda sujeta a los límites descritos a continuación.

### 3. Los cuatro parámetros y sus límites

**Frecuencia central $f_c$.** El tuner sintoniza de 24 MHz a 1.766 GHz. El V4 incorpora un *upconverter* que traslada la banda de 500 kHz a 24 MHz, por lo que también recibe onda corta y media.

Por debajo de 24 MHz, el V3 solo puede utilizar *direct sampling* —muestreo directo sin tuner—, con menor sensibilidad.

**Tasa de muestreo $f_s$.** `librtlsdr` acepta 225–300 kS/s y 900 kS/s–3.2 MS/s. Con muestreo complejo, el ancho de banda observable es igual a $f_s$.

Los filtros del DDC atenúan los bordes, por lo que en la práctica se aprovecha cerca del 80 % central.

Por encima de 2.4 MS/s, el enlace USB puede perder muestras. Por ello, el curso adopta 2.4 MS/s como tasa de referencia. El caudal resultante es

$$
R = f_s \times 2\ \text{bytes} = 2.4 \times 10^6 \times 2 = 4.8\ \text{MB/s} \approx 38.4\ \text{Mbit/s},
$$

Este caudal queda por debajo de los 480 Mbit/s de USB 2.0 y por encima de los 12 Mbit/s de USB 1.1. El dongle no requiere USB 3.0, pero sí un puerto USB 2.0 real.

Una máquina virtual mal configurada o un concentrador deficiente pueden ocasionar pérdidas de muestras.

**Resolución: 8 bits.** Un ADC de $N$ bits tiene una relación señal a ruido de cuantización máxima

$$
\text{SQNR} \approx 6.02\,N + 1.76\ \text{dB},
$$

Con $N = 8$, el resultado es 49.9 dB. En la práctica, el rango dinámico útil ronda los 45 dB. Si dos señales dentro de la ventana difieren más que ese valor, la débil desaparece bajo el ruido de cuantización o la fuerte satura el ADC.

Esta limitación explica la importancia de ajustar correctamente la ganancia.

**Ganancia.** Los 29 pasos de 0 a 49.6 dB distribuyen la ganancia entre el LNA, el mezclador y el VGA.

Con poca ganancia domina el ruido del ADC. Con demasiada, una señal fuerte lleva el ADC a sus extremos, produce recorte y genera espurias.

El modo AGC (*automatic gain control*) se ajusta según la señal más fuerte presente. Esto puede ocultar señales débiles cerca de un transmisor de FM o TV. La Sesión 02 mide el efecto mediante grabaciones con tres niveles de ganancia.

Otros dos límites condicionan el desempeño:

- **Exactitud de frecuencia.** El cristal de 28.8 MHz presenta un error en partes por millón: $\Delta f = f_c \times \text{ppm} \times 10^{-6}$.

  Los V3 y V4 incorporan un TCXO de 1 ppm, equivalente a 1.09 kHz de error a 1090 MHz. Un cristal de 50–100 ppm se desvía entre 55 y 110 kHz a esa frecuencia.
- **Figura de ruido.** El tuner añade unos 3.5 dB de ruido propio. Para señales muy débiles (satélites) se antepone un LNA alimentado por el bias-tee. Se cuantifica en la Sesión 05 con el presupuesto de enlace.

### 4. El ecosistema de software

| Capa | Herramienta | Qué hace |
|---|---|---|
| Driver | `librtlsdr` (`rtl_test`, `rtl_sdr`, `rtl_fm`, `rtl_power`, `rtl_tcp`) | Habla con el dongle; utilidades de línea de comandos para probar, grabar, demodular FM, barrer espectro y servir muestras por red |
| Abstracción | SoapySDR, `gr-osmosdr` | Interfaz común para muchos SDR; el bloque **RTL-SDR Source** de GNU Radio viene de `gr-osmosdr` |
| Framework | GNU Radio 3.10 | Bloques de procesamiento conectados en *flowgraphs*; GNU Radio Companion (GRC) es su editor gráfico |
| Aplicaciones | SDR++, GQRX, SDR# | Receptores de propósito general con interfaz gráfica; útiles para explorar, no para el curso |
| Distribución | radioconda 2025.03.14 | Instala todo lo anterior con versiones fijas en Windows, Linux y macOS |

El curso utiliza GNU Radio para los *flowgraphs* y Python con NumPy para el análisis y los prototipos. Las aplicaciones de la última fila permiten explorar el espectro, pero no muestran el funcionamiento interno de un receptor.

### 5. Qué se puede recibir en Lima

Con el dongle y su antena telescópica, desde una ventana o azotea:

| Señal | Frecuencia | Qué se ve | Sesión |
|---|---|---|---|
| Radiodifusión FM y su RDS | 88–108 MHz | Audio estéreo; texto y hora en RDS (BPSK a 1187.5 bit/s) | 02–10 |
| Difusiones aeronáuticas automáticas (ATIS, VOLMET) | 118–137 MHz, AM | Reportes meteorológicos de voz sintetizada | 05 |
| ADS-B | 1090 MHz | Posición y altitud de aviones (Jorge Chávez) | 10 |
| AIS | 161.975 / 162.025 MHz | Posición de barcos (Callao; requiere antena en altura) | proyecto |
| Televisión digital ISDB-Tb | UHF, p. ej. canal 16 (482–488 MHz) | Espectro OFDM de 6 MHz, visible solo en parte a 2.4 MS/s | 12 |
| Satélite Meteor M2-4 (LRPT) | 137.9 MHz | Imágenes meteorológicas digitales | 14 |
| Sensores y LoRa en banda ICM | 915–928 MHz | Telemetría OOK/FSK; chirps LoRa (plan AU915) | 13 |
| Radioaficionados | 144–148 y 430–440 MHz | Voz NBFM, APRS | proyecto |

Fuera de alcance: Wi-Fi y Bluetooth (2.4 GHz, fuera del rango del tuner y con 20 MHz de ancho), telefonía celular (ilegal en el curso, ver abajo), GPS (posible con antena activa pero fuera del programa).

### 6. Marco legal del curso

La recepción técnica no autoriza el acceso a cualquier comunicación. La legislación peruana protege la inviolabilidad de las telecomunicaciones:

- El [TUO de la Ley de Telecomunicaciones](https://www.osiptel.gob.pe/media/kbejkkkk/ds013-93-tcc-tuo-ley-de-telecomunicaciones.pdf), DS 013-93-TCC, art. 4, declara inviolable el secreto de las telecomunicaciones.

  También tipifica como infracción muy grave la interceptación de servicios no destinados al uso libre del público y la divulgación de su contenido.
- El [Reglamento General](https://www.osiptel.gob.pe/media/wvidghyb/ds06-94-tcc-reg-general-ley-de-telecomunicaciones.pdf), DS 06-94-TCC, art. 10, considera violación intentar conocer una comunicación ajena.
- El Código Penal (art. 162 y 162-A) sanciona la interceptación de comunicaciones telefónicas o similares y la posesión de equipos destinados a interceptarlas.

La recepción de radiodifusión, señales de navegación y emisiones destinadas al público no requiere una licencia de receptor. De este marco se derivan las reglas del curso:

1. **Solo recepción.** El RTL-SDR no puede transmitir; ningún trabajo del curso transmite.
2. **Solo servicios destinados al público:** radiodifusión y RDS, ADS-B, AIS, satélites, sensores en banda ICM, difusiones automáticas ATIS y VOLMET.
3. **Prohibido** sintonizar, decodificar o publicar telefonía celular, sistemas troncalizados o cualquier comunicación privada. La voz de controladores y pilotos no se graba ni se publica.
4. En los reportes se publican espectros, constelaciones, datos de aviones y barcos, imágenes de satélite y telemetría de sensores. Nunca audio de voz.

El [Plan Nacional de Atribución de Frecuencias](https://www.gob.pe/institucion/mtc/normas-legales/4243339-0597-2023-mtc-01-03) y el [Registro Nacional de Frecuencias](https://rnf.mtc.gob.pe/) identifican el servicio asignado a cada banda.

Ambas fuentes se estudian en la Sesión 11.

### 7. Ejemplo end-to-end: planificar una captura

El ejemplo plantea la grabación de 10 s de una emisora en 99.1 MHz para las Sesiones 02 y 03.

1. **Tasa.** Con $f_s = 2.4$ MS/s la ventana va de 97.9 a 100.3 MHz; el 80 % útil (1.92 MHz) cubre unas 9 emisoras de 200 kHz. Suficiente para ver la emisora objetivo y sus vecinas.
2. **Ganancia.** Se parte de 30 dB, sin AGC. Cerca de la UNI existen transmisores potentes de FM y TV; el AGC se ajustaría a la señal más fuerte y ocultaría las vecinas débiles.

   Un piso de ruido elevado o picos repetidos indican saturación y exigen reducir la ganancia.
3. **Exactitud.** 1 ppm a 99.1 MHz son 99 Hz. Frente a un canal de 200 kHz, despreciable.
4. **Tamaño.** $10\ \text{s} \times 2.4 \times 10^6\ \text{muestras/s} \times 2\ \text{bytes} = 48$ MB. El archivo no debe almacenarse en el repositorio Git, porque cada versión aumenta el historial.

   Por ello, los archivos del curso se distribuyen como *releases* independientes.
5. **Legalidad.** Radiodifusión FM: servicio destinado al público. Sin restricción.

El comando resultante es el de la [guía del RTL-SDR](../../setup/rtl-sdr.md#grabar-muestras-iq):

```bash
rtl_sdr -f 99.1e6 -s 2400000 -g 30 -n 24000000 fm_99p1MHz_2p4Msps_g30.cu8
```

!!! info "¿Qué describe la extensión `.cu8`?"
    El nombre abrevia **c**omplejo, **u**nsigned (sin signo), **8** bits por componente. Cada muestra contiene un byte `uint8` para I y otro para Q: 16 bits o 2 bytes en total, intercalados como `I,Q,I,Q,…`.

    | Representación | Componente I | Componente Q | Total por muestra |
    |---|---:|---:|---:|
    | `.cu8` | `uint8`, 1 byte | `uint8`, 1 byte | 2 bytes |
    | GNU Radio `Complex Float 32` | `float32`, 4 bytes | `float32`, 4 bytes | 8 bytes |

    `.cu8` es una convención descriptiva, no una extensión que `rtl_sdr` interprete. La utilidad escribe los bytes crudos en el archivo cuyo nombre recibe; podría llamarse `.bin`, pero entonces el tipo no quedaría indicado.

    [SigMF](https://sigmf.org/sigmf-spec.pdf) formaliza el nombre de tipo `cu8` y permite acompañar los datos con metadatos.

    El [código de `rtl_sdr`](https://github.com/osmocom/rtl-sdr/blob/master/src/rtl_sdr.c) confirma que la utilidad graba un búfer `uint8_t` y utiliza dos bytes por muestra compleja.

---

## Síntesis

| Concepto | Implicación de diseño | Se profundiza en |
|---|---|---|
| Arquitectura *low-IF* con DDC digital | I y Q nacen en el RTL2832U; toda la selectividad fina se hace en software | S02, S03 |
| $f_c$ (tuner) y $f_s$ (RTL2832U) son independientes | $f_s$ fija el ancho de banda visible; $f_c$ dónde se mira | S02 |
| 8 bits → ~45 dB de rango dinámico | La ganancia se elige por la señal más fuerte presente, no por la que interesa | S02 |
| 2.4 MS/s → 38 Mbit/s por USB 2.0 | Sin USB 3.0; sí puerto directo y sin virtualización descuidada | guía RTL-SDR |
| Error de cristal en ppm | 1 ppm es despreciable en FM; 50 ppm rompe un canal NBFM | S07 |
| Figura de ruido ≈ 3.5 dB | Señales de satélite exigen LNA alimentado por bias-tee | S05, S14 |
| Solo recepción de servicios públicos | Define qué señales entran en labs y proyectos | S05, S10, S11 |

---

## Ejercicios

### Ejercicio 1: Caudal por USB

Un estudiante configura el dongle a 2.56 MS/s. Se debe calcular el caudal en MB/s y Mbit/s, determinar si funcionaría en un puerto USB 1.1 de 12 Mbit/s y hallar la tasa máxima teórica de ese puerto.

??? example "Solución"
    Cada muestra son 2 bytes (I y Q de 8 bits):

    $$
    R = 2.56 \times 10^6 \times 2 = 5.12\ \text{MB/s} = 40.96\ \text{Mbit/s}.
    $$

    USB 1.1 ofrece 12 Mbit/s, por lo que no alcanza. La tasa máxima teórica sería $12 \times 10^6 / 16 = 0.75$ MS/s; en la práctica, la sobrecarga del protocolo la reduce a unos 0.25–0.5 MS/s.

    Una máquina virtual limitada a USB 1.1 presenta el síntoma característico: `rtl_test` informa pérdidas incluso con tasas bajas.

### Ejercicio 2: Rango dinámico y bits

Se debe calcular la SQNR máxima para 8 bits (RTL-SDR), 12 bits (ADALM-Pluto) y 14 bits (USRP B210). Si dos señales dentro de una misma ventana difieren en 60 dB, se debe determinar el mínimo de bits necesario para observar ambas.

??? example "Solución"
    Con $\text{SQNR} \approx 6.02N + 1.76$ dB:

    | Bits | SQNR |
    |---|---|
    | 8 | 49.9 dB |
    | 12 | 74.0 dB |
    | 14 | 86.0 dB |

    Para 60 dB de separación se necesita $N \geq (60 - 1.76)/6.02 = 9.7$, es decir, un mínimo de 10 bits.

    Con el RTL-SDR, la señal débil queda bajo el ruido de cuantización. Si se reduce la ganancia para evitar saturación, también se pierde la señal débil. La solución requiere un filtro analógico previo al ADC.

### Ejercicio 3: Error de frecuencia

Se debe calcular el desplazamiento para 1 ppm a 99.1 MHz y 1090 MHz, y para un clon de 60 ppm a 1090 MHz. Después se debe determinar si ese clon resulta adecuado para un receptor NBFM de 435 MHz con canales de 12.5 kHz.

??? example "Solución"
    $\Delta f = f_c \times \text{ppm} \times 10^{-6}$:

    - 1 ppm, 99.1 MHz: 99 Hz.
    - 1 ppm, 1090 MHz: 1.09 kHz.
    - 60 ppm, 1090 MHz: 65.4 kHz. Para ADS-B, cuyo receptor abarca unos 2 MHz, sigue dentro de la ventana; se decodifica.
    - 60 ppm, 435 MHz: 26.1 kHz, más de dos canales de 12.5 kHz. El clon sintoniza el canal equivocado. Habría que calibrar el ppm con una señal de referencia conocida, como el piloto de 19 kHz de FM estéreo (Sesión 05).

### Ejercicio 4: Ancho de banda y canales

Para $f_s = 2.4$ MS/s y $f_c = 96.0$ MHz, se debe hallar el rango observado y la cantidad de canales FM de 200 kHz que caben en el 80 % útil.

También se debe determinar cuántas capturas cubren 88–108 MHz y qué herramienta automatiza el proceso.

??? example "Solución"
    La ventana abarca $96.0 \pm 1.2$ MHz, es decir, de 94.8 a 97.2 MHz. La parte útil mide 1.92 MHz y admite nueve canales de 200 kHz.

    La banda completa mide 20 MHz. Como $20 / 1.92 \approx 10.4$, se necesitan 11 capturas solapadas. `rtl_power` automatiza el barrido en pasos de $f_s$ y entrega el espectro promedio en un archivo CSV.

### Ejercicio 5: Planificar una captura de ATIS (integrador)

El ATIS del aeropuerto Jorge Chávez emite en AM dentro de 118–137 MHz. Para el ejercicio se adopta 128.8 MHz. A 4 km existe un transmisor de FM comercial cuya señal en la antena supera al ATIS en 30 dB.

Se debe planificar una grabación de 30 s: seleccionar $f_s$, ganancia y nombre de archivo; calcular el tamaño; y determinar si la captura y su publicación en el reporte son legales.

??? example "Solución"
    - **$f_s$.** El canal AM aeronáutico ocupa 8.33 o 25 kHz, por lo que no requiere 2.4 MS/s. Con $f_s = 1.024$ MS/s, la ventana abarca de 128.29 a 129.31 MHz.

      La banda de FM queda fuera y el transmisor fuerte no alcanza el ADC. El filtro del tuner, de unos 6 MHz, también rechaza una emisora situada a 20 MHz.
    - **Ganancia.** Sin una señal fuerte en la ventana, la ganancia puede elevarse a 40 dB. Si el espectro muestra saturación, debe reducirse.
    - **Tamaño.** $30 \times 1.024 \times 10^6 \times 2 = 61.4$ MB.
    - **Nombre.** `atis_128p8MHz_1p024Msps_g40.cu8`.
    - **Legalidad.** ATIS es una difusión automática de información meteorológica destinada a cualquier aeronave que la sintonice. Por ello, se considera un servicio dirigido al público y su recepción está permitida.

      Las reglas del curso permiten publicar el espectro y el reporte meteorológico. No permiten publicar la voz de la torre ni de los pilotos en canales de control, porque esas comunicaciones no están destinadas al público.

    El ejercicio combina cuatro conceptos de la sesión: ancho de banda observable ($f_s$), rango dinámico (evitado por selección de ventana), tamaño de archivo y marco legal.

---

## Laboratorio

El laboratorio valida el entorno de trabajo. Cada estudiante debe asistir con las herramientas instaladas según las guías:

- [Instalar GNU Radio con radioconda](../../setup/instalacion.md)
- [Configurar el RTL-SDR](../../setup/rtl-sdr.md) (solo para quien disponga del dongle)

### En clase (2 h)

| # | Paso | Evidencia para el Reporte 0 | Sin dongle |
|---|---|---|:---:|
| 1 | `python -c "from gnuradio import gr; print(gr.version())"` imprime `3.10.12.0` | Texto de la salida | ✓ |
| 2 | `prueba.grc` (Signal Source → Throttle → Frequency Sink) muestra un pico en +1 kHz | Captura de pantalla del flowgraph y de la ventana | ✓ |
| 3 | Cambiar `Output Type` de Signal Source a *Float* y explicar en dos líneas el cambio del espectro | Captura y explicación | ✓ |
| 4 | `rtl_test -t` detecta el dongle y muestra el tuner | Texto completo de la salida | — |
| 5 | `rtl_test -s 2400000` corre 60 s | Texto completo; cuenta de líneas `lost at least` | — |
| 6 | Obtener el primer espectro FM con **RTL-SDR Source** a 2.4 MS/s y 30 dB de ganancia | Captura que identifique al menos tres emisoras por su frecuencia | — |
| 7 | Repetir el paso 6 con ganancias de 0 dB y 49.6 dB; comparar el piso de ruido y los picos | Dos capturas y tres líneas de análisis | — |

Los alumnos sin dongle completan los pasos 1–3 y, para los pasos 6–7, analizan las capturas que el profesor proyecta en clase.

La clínica de instalación se desarrolla en paralelo. Quien encuentre problemas con Zadig, el módulo DVB de Linux o `rtl_test` puede resolverlos con el profesor y los voluntarios. El Reporte 0 debe registrar el problema y su solución.

### Reporte 0: instalación y prueba del entorno

- **Vence:** al inicio de la Sesión 02; debe publicarse en el sitio de reportes del estudiante.
- **Contenido:** sistema operativo y versión; evidencias de la tabla anterior; problemas encontrados y solución; salida de `rtl_test` o la frase "sin dongle".
- **Rúbrica (5 puntos):** evidencias completas y legibles (2), explicación del paso 3 correcta (1), análisis del paso 7 o, sin dongle, del espectro proyectado (1), reporte publicado a tiempo y con la estructura de la plantilla (1).

---

## Lecturas recomendadas

1. M. Lichtman, *PySDR: A Guide to SDR and DSP using Python*: [introducción](https://pysdr.org/content/intro.html) y [RTL-SDR](https://pysdr.org/content/rtlsdr.html). Lectura gratuita de referencia del curso.
2. rtl-sdr.com, *About RTL-SDR*. Especificaciones, historia y límites del dongle. [rtl-sdr.com/about-rtl-sdr](https://www.rtl-sdr.com/about-rtl-sdr/)
3. Osmocom, *rtl-sdr wiki*. Documentación del driver y de las utilidades `rtl_*`. [osmocom.org/projects/rtl-sdr/wiki](https://osmocom.org/projects/rtl-sdr/wiki)
4. GNU Radio Wiki, *Tutorials: Your First Flowgraph* y *Python Variables in GRC*. [wiki.gnuradio.org/index.php/Tutorials](https://wiki.gnuradio.org/index.php/Tutorials)
5. J. Mitola, "The software radio architecture", *IEEE Communications Magazine*, vol. 33, n.º 5, 1995. El artículo que dio nombre al campo.
6. TUO de la Ley de Telecomunicaciones (DS 013-93-TCC) y Reglamento General (DS 06-94-TCC), artículos citados en la sección 6.

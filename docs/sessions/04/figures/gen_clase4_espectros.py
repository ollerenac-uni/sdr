"""Genera las figuras calculadas de FFT y traslación de la clase 4.

Desde la raíz: python docs/sessions/04/figures/gen_clase4_espectros.py
Los demás SVG de esta carpeta son esquemas editables, no mediciones.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CARPETA = Path(__file__).resolve().parent
FS = 2.4e6
FC = 99.1e6
FRECUENCIAS = np.array([-600e3, 0, 400e3])
AMPLITUDES = np.array([0.8, 0.5, 0.65])
COLORES = ["#2166ac", "#b35806", "#1b7837"]
plt.rcParams.update({"font.size": 10, "svg.hashsalt": "sdr-clase4", "svg.fonttype": "none"})


def guardar(figura, nombre):
    figura.savefig(CARPETA / f"{nombre}.png", dpi=170, facecolor="white")
    svg = CARPETA / f"{nombre}.svg"
    figura.savefig(svg, metadata={"Date": None}, facecolor="white")
    svg.write_text("\n".join(linea.rstrip() for linea in svg.read_text().splitlines()) + "\n")
    plt.close(figura)


def tiempo_y_fft():
    n = np.arange(2400)
    x = np.sum(
        AMPLITUDES[:, None] * np.exp(2j * np.pi * FRECUENCIAS[:, None] * n / FS),
        axis=0,
    )
    f = np.fft.fftshift(np.fft.fftfreq(len(n), 1 / FS))
    espectro = np.abs(np.fft.fftshift(np.fft.fft(x))) / len(n)
    figura, (ax_t, ax_f) = plt.subplots(2, 1, figsize=(10, 6), layout="constrained")
    figura.suptitle("Ejemplo sintético: una señal compleja, tres tonos")
    ax_t.plot(n[:25] / FS * 1e6, x[:25].real, ".-", label="I")
    ax_t.plot(n[:25] / FS * 1e6, x[:25].imag, ".-", label="Q")
    ax_t.set(xlabel="Tiempo (µs)", ylabel="Componente", title="Primeras 25 muestras de x[n] = I[n] + jQ[n]")
    ax_t.legend(ncols=2)
    ax_f.plot(f / 1e3, espectro, color="#444444", linewidth=0.8)
    for frecuencia, amplitud, color in zip(FRECUENCIAS, AMPLITUDES, COLORES):
        ax_f.plot(frecuencia / 1e3, amplitud, "o", color=color)
        ax_f.annotate(f"{frecuencia / 1e3:+.0f} kHz", (frecuencia / 1e3, amplitud),
                      xytext=(0, 10), textcoords="offset points", ha="center", color=color)
    ax_f.set(xlim=(-1200, 1200), ylim=(0, 1), xlabel="Frecuencia relativa a 99.1 MHz (kHz)",
             ylabel="|FFT(x)| / N", title="FFT de 2400 muestras · separación de bins: 1 kHz")
    superior = ax_f.secondary_xaxis("top", functions=(lambda f: FC / 1e6 + f / 1000,
                                                     lambda rf: (rf - FC / 1e6) * 1000))
    superior.set_xlabel("Frecuencia RF de origen (MHz)")
    for ax in (ax_t, ax_f):
        ax.grid(alpha=0.25)
    guardar(figura, "10-iq-a-espectro")


def centrar_bandas():
    f = np.linspace(-1200, 1200, 2401)
    figura, ejes = plt.subplots(3, 1, figsize=(10, 7), sharex=True, layout="constrained")
    mezclas = [0, 600, -400]
    titulos = ["A · Entrada: centro de captura en 99.1 MHz",
               "B · Mezcla +600 kHz: la banda de 98.5 MHz queda en cero",
               "C · Mezcla −400 kHz: la banda de 99.5 MHz queda en cero"]
    for ax, mezcla, titulo in zip(ejes, mezclas, titulos):
        for frecuencia, amplitud, color in zip(FRECUENCIAS / 1000, AMPLITUDES, COLORES):
            centro = (frecuencia + mezcla + 1200) % 2400 - 1200
            distancia = (f - centro + 1200) % 2400 - 1200
            banda = np.zeros_like(f)
            dentro = np.abs(distancia) <= 60
            banda[dentro] = amplitud * 0.5 * (1 + np.cos(np.pi * distancia[dentro] / 60))
            ax.fill_between(f[dentro], banda[dentro], color=color, alpha=0.25)
            ax.plot(f[dentro], banda[dentro], color=color, linewidth=1)
            ax.text(centro, amplitud + 0.045, f"{99.1 + frecuencia / 1000:.1f} MHz",
                    color=color, ha="center")
        ax.axvline(0, color="#555555", linestyle="--", linewidth=0.8)
        ax.set(title=titulo, ylabel="Nivel ilustrativo", ylim=(0, 1), xlim=(-1200, 1200))
        ax.grid(alpha=0.2)
    ejes[-1].set_xlabel("Frecuencia de banda base después de mezclar (kHz)")
    figura.suptitle("Bandas ilustrativas de 120 kHz · no son medidas de la captura")
    guardar(figura, "11-centrar-emisoras")


if __name__ == "__main__":
    tiempo_y_fft()
    centrar_bandas()

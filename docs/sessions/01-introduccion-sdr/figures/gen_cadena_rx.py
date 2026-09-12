"""Figuras esquemáticas de la cadena de recepción del RTL-SDR (Sesión 01, §2).

Genera seis PNG a 300 DPI con fondo blanco, una por punto de observación ①–⑥.
Ejecutar desde cualquier directorio: python gen_cadena_rx.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

OUT = Path(__file__).parent
plt.rcParams.update(
    {
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.facecolor": "white",
    }
)

BLUE, GRAY, RED, GREEN, DARK = "#1e40af", "#9ca3af", "#dc2626", "#047857", "#111827"

FC = 99.1  # emisora objetivo, MHz
FIF = 3.57  # IF del tuner, MHz
FLO = FC - FIF  # oscilador local del tuner, MHz
FS_ADC = 28.8  # MS/s
FS_OUT = 2.4  # MS/s pedidos por el usuario
IF_BW = 5.0  # filtro IF por defecto, MHz
ST_BW = 0.2  # ancho de una emisora FM, MHz

STATIONS = np.arange(96.1, 102.0, 0.4)  # emisoras cada 400 kHz
rng = np.random.default_rng(3)
AMP = {round(s, 1): (1.0 if abs(s - FC) < 1e-6 else rng.uniform(0.35, 0.8)) for s in STATIONS}


def lobe(f, center, bw=ST_BW):
    """Lóbulo de tope plano (super-gaussiana) centrado en `center`."""
    return np.exp(-(((f - center) / (bw / 2.4)) ** 8))


def if_mask(f):
    """Filtro IF del tuner: 5 MHz centrado en ±3.57 MHz (respuesta simétrica)."""
    return 1.0 / (1.0 + ((np.abs(f) - FIF) / (IF_BW / 2)) ** 12)


def lpf_mask(f, cutoff=FS_OUT / 2):
    """Filtro paso bajo digital del RTL2832U para la tasa de salida pedida."""
    return 1.0 / (1.0 + (f / cutoff) ** 16)


def rf_spectrum(f):
    """Espectro en la antena: solo frecuencias positivas, en MHz de RF."""
    return sum(a * lobe(f, s) for s, a in AMP.items())


def if_spectrum(f, filtered=True):
    """Espectro real en la IF: lóbulos en +(3.57 + Δ) y espejos en −(3.57 + Δ)."""
    y = np.zeros_like(f)
    for s, a in AMP.items():
        d = s - FC
        y += a * lobe(f, FIF + d) + a * lobe(f, -(FIF + d))
    return y * if_mask(f) if filtered else y


def if_target_only(f, mirror=False):
    c = -FIF if mirror else FIF
    return lobe(f, c) * if_mask(f)


def sampled(spec_fn, f, fs=FS_ADC, k=(-1, 0, 1)):
    return sum(spec_fn(f - i * fs) for i in k)


def ddc_spectrum(f):
    """Tras la mezcla digital: espectro muestreado desplazado −3.57 MHz."""
    return sampled(if_spectrum, f + FIF)


def ddc_target(f, mirror=False):
    return sampled(lambda g: if_target_only(g, mirror), f + FIF)


def new_fig(w=7.2, h=2.6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_ylim(0, 1.25)
    ax.set_yticks([])
    ax.set_ylabel("|X(f)|  (esquemático)")
    ax.set_xlabel("Frecuencia (MHz)")
    ax.axhline(0, color=DARK, lw=0.8)
    return fig, ax


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name)
    plt.close(fig)
    print("ok", name)


# ---------------------------------------------------------------- ① antena
f = np.linspace(94, 104, 6000)
fig, ax = new_fig()
ax.fill_between(f, 0, rf_spectrum(f) - lobe(f, FC), color=GRAY, alpha=0.8, lw=0)
ax.fill_between(f, 0, lobe(f, FC), color=BLUE, lw=0)
ax.axvline(FLO, color=GREEN, ls="--", lw=1.2)
ax.text(FLO + 0.12, 1.02, f"LO del tuner\n$f_{{LO}} = f_c - 3.57 = {FLO:.2f}$ MHz", ha="left", color=GREEN)
ax.annotate(
    f"emisora objetivo\n$f_c = {FC}$ MHz",
    xy=(FC, 1.02),
    xytext=(FC + 1.2, 1.08),
    color=BLUE,
    arrowprops=dict(arrowstyle="->", color=BLUE),
)
ax.text(100.5, 0.86, "emisoras vecinas\n(200 kHz cada una)", color=GRAY, fontsize=8)
ax.set_title("① En la antena: banda de FM alrededor de $f_c$")
save(fig, "cadena-rx-1-antena.png")

# ---------------------------------------------------------------- ② IF real
f = np.linspace(-8, 8, 8000)
fig, ax = new_fig()
ax.fill_between(f, 0, if_spectrum(f) - if_target_only(f) - if_target_only(f, True), color=GRAY, alpha=0.8, lw=0)
ax.fill_between(f, 0, if_spectrum(f, filtered=False) * (1 - if_mask(f)), color=GRAY, alpha=0.25, lw=0)
ax.fill_between(f, 0, if_target_only(f), color=BLUE, lw=0)
ax.fill_between(f, 0, if_target_only(f, True), facecolor="none", edgecolor=RED, hatch="////", lw=0.8)
ax.plot(f, 1.15 * if_mask(f), color=DARK, ls="--", lw=1)
ax.text(FIF, 1.17, "filtro IF, 5 MHz", ha="center", color=DARK)
ax.text(-FIF, 1.17, "filtro IF (espejo)", ha="center", color=DARK)
ax.annotate("señal: $f_c \\to +3.57$ MHz", xy=(FIF, 1.0), xytext=(5.3, 0.75), color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE))
ax.annotate("espejo: la señal es real,\nsu espectro es simétrico", xy=(-FIF, 1.0), xytext=(-7.9, 0.7), color=RED, arrowprops=dict(arrowstyle="->", color=RED))
ax.text(0.0, 0.62, "0 Hz: offset DC, fuga del LO\ny ruido 1/f quedan aquí,\nlejos de la señal", ha="center", fontsize=7.5, color=DARK, bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))
ax.set_title("② Tras el tuner: señal real en la IF de 3.57 MHz")
save(fig, "cadena-rx-2-if.png")

# ---------------------------------------------------------------- ③ ADC
f = np.linspace(-44, 44, 12000)
fig, ax = new_fig()
ax.axvspan(-FS_ADC / 2, FS_ADC / 2, color="#dbeafe", alpha=0.6, lw=0)
# A esta escala una emisora de 200 kHz es una línea: se dibuja la banda de 5 MHz
# que dejó pasar el filtro IF como bloque gris, y la emisora objetivo como línea.
for k in (-1, 0, 1):
    a = 1.0 if k == 0 else 0.35
    for sign in (1, -1):
        ax.fill_between(f, 0, 0.8 * lobe(f, sign * FIF + k * FS_ADC, bw=IF_BW), color=GRAY, alpha=0.5 * a, lw=0)
    ax.vlines(FIF + k * FS_ADC, 0, 1.0, color=BLUE, lw=2.5, alpha=a)
    ax.vlines(-FIF + k * FS_ADC, 0, 1.0, color=RED, lw=2.5, alpha=a, linestyles=(0, (2, 1)))
for x, lab in ((-FS_ADC, "$-f_s$"), (FS_ADC, "$+f_s$")):
    ax.axvline(x, color=DARK, ls=":", lw=0.8)
    ax.text(x, 1.12, lab, ha="center")
ax.text(0, 1.12, "zona de Nyquist: $\\pm f_s/2 = \\pm 14.4$ MHz", ha="center", color=BLUE)
ax.text(-FS_ADC, 0.9, "copia (k = −1)", ha="center", color=GRAY, fontsize=8)
ax.text(FS_ADC, 0.9, "copia (k = +1)", ha="center", color=GRAY, fontsize=8)
ax.annotate("señal, +3.57 MHz", xy=(FIF, 1.0), xytext=(7.5, 1.0), color=BLUE, fontsize=8, arrowprops=dict(arrowstyle="->", color=BLUE))
ax.annotate("espejo, −3.57 MHz", xy=(-FIF, 1.0), xytext=(-13.8, 1.0), color=RED, fontsize=8, arrowprops=dict(arrowstyle="->", color=RED))
ax.text(FIF, 0.3, "banda IF\n5 MHz", ha="center", fontsize=7, color=DARK)
ax.text(-FIF, 0.3, "espejo de\nla banda", ha="center", fontsize=7, color=DARK)
ax.set_title("③ Tras el ADC (28.8 MS/s, 8 bits): el espectro se repite cada $f_s$")
save(fig, "cadena-rx-3-adc.png")

# ---------------------------------------------------------------- ④ DDC
f = np.linspace(-16, 16, 12000)
fig, ax = new_fig()
ax.fill_between(f, 0, ddc_spectrum(f) - ddc_target(f) - ddc_target(f, True), color=GRAY, alpha=0.8, lw=0)
ax.fill_between(f, 0, ddc_target(f), color=BLUE, lw=0)
ax.fill_between(f, 0, ddc_target(f, True), facecolor="none", edgecolor=RED, hatch="////", lw=0.8)
ax.plot(f, 1.15 * lpf_mask(f), color=GREEN, ls="--", lw=1.2)
ax.text(0, 1.18, f"filtro paso bajo digital, $\\pm {FS_OUT/2}$ MHz", ha="center", color=GREEN)
ax.annotate("señal → 0 Hz\n(ya compleja: I y Q)", xy=(0, 1.0), xytext=(3.5, 0.8), color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE))
ax.annotate("imagen → $-2 \\times 3.57 = -7.14$ MHz\n(el filtro la elimina)", xy=(-2 * FIF, 1.0), xytext=(-15.8, 1.0), va="bottom", color=RED, arrowprops=dict(arrowstyle="->", color=RED))
ax.annotate("", xy=(-4.6, 0.86), xytext=(-2.6, 0.86), arrowprops=dict(arrowstyle="->", color=DARK, lw=1.2))
ax.text(-3.6, 0.9, "todo se desplaza\n−3.57 MHz", ha="center", va="bottom", fontsize=7.5, color=DARK)
ax.set_title("④ Tras la mezcla digital por $e^{-j2\\pi\\,3.57\\,\\mathrm{MHz}\\,t}$")
save(fig, "cadena-rx-4-ddc.png")

# ---------------------------------------------------------------- ⑤ LPF + decimación
f = np.linspace(-1.3, 1.3, 6000)
fig, ax = new_fig()
ax.axvspan(-FS_OUT / 2, FS_OUT / 2, color="#dcfce7", alpha=0.6, lw=0)
y_all = ddc_spectrum(f) * lpf_mask(f)
y_t = ddc_target(f) * lpf_mask(f)
ax.fill_between(f, 0, y_all - y_t, color=GRAY, alpha=0.8, lw=0)
ax.fill_between(f, 0, y_t, color=BLUE, lw=0)
for x in (-FS_OUT / 2, FS_OUT / 2):
    ax.axvline(x, color=GREEN, ls="--", lw=1.2)
ax.annotate("", xy=(-FS_OUT / 2, 1.12), xytext=(FS_OUT / 2, 1.12), arrowprops=dict(arrowstyle="<->", color=GREEN))
ax.text(0, 1.15, f"ancho observable = $f_s$ = {FS_OUT} MHz (no $f_s/2$: la señal es compleja)", ha="center", color=GREEN)
ax.text(0, 0.5, "$f_c$", ha="center", color="white", fontweight="bold")
ax.set_xlabel("Frecuencia respecto a $f_c$ (MHz)")
ax.set_title(f"⑤ Tras filtrar y decimar (28.8 → {FS_OUT} MS/s, ÷12): la ventana que pediste")
save(fig, "cadena-rx-5-decimacion.png")

# ---------------------------------------------------------------- ⑥ USB
n = np.arange(40)
tone = np.exp(1j * 2 * np.pi * 0.05 * n) * 0.8
I = np.clip(np.round(127.5 + 127.5 * tone.real), 0, 255).astype(int)
Q = np.clip(np.round(127.5 + 127.5 * tone.imag), 0, 255).astype(int)
fig, ax = plt.subplots(figsize=(7.2, 2.6))
ax.axhline(127.5, color=DARK, ls="--", lw=0.8)
ax.text(39.5, 131, "127.5 = cero", ha="right", fontsize=8)
ax.stem(n - 0.15, I, linefmt=BLUE, markerfmt="o", basefmt=" ", label="I (byte par)")
ax.stem(n + 0.15, Q, linefmt=RED, markerfmt="s", basefmt=" ", label="Q (byte impar)")
ax.set_ylim(0, 300)
ax.set_yticks([0, 64, 127.5, 191, 255])
ax.set_xlabel("índice de muestra n")
ax.set_ylabel("valor del byte (uint8)")
ax.legend(loc="upper right", ncol=2, frameon=False)
bytes_txt = " ".join(f"{i} {q}" for i, q in zip(I[:6], Q[:6]))
ax.set_title(f"⑥ Salida USB: I, Q, I, Q… un byte cada uno; a {FS_OUT} MS/s son 4.8 MB/s\nprimeros bytes en el cable: {bytes_txt} …", fontsize=9)
save(fig, "cadena-rx-6-usb.png")



# ---------------------------------------------------------------- ④b ramas I y Q
# Demostración en el dominio del tiempo de por qué hacen falta DOS ramas.
# Se sintetiza una señal de paso banda real con emisoras SOLO por encima de la
# frecuencia central, se multiplica por cos y por -sin, y se comparan los tres
# espectros. Cada rama por sí sola muestra el doble de emisoras de las que hay.

def _escena_iq(n_muestras=32768, fs_adc=28.8e6, f_if=FIF * 1e6, semilla=11):
    """Señal real en la IF con emisoras solo en offsets positivos."""
    t = np.arange(n_muestras) / fs_adc
    rng_local = np.random.default_rng(semilla)
    offsets = np.array([0.2, 0.5, 0.9]) * 1e6
    amplitudes = np.array([1.0, 0.65, 0.45])
    banda = sum(
        a * np.exp(2j * np.pi * o * t + 1j * rng_local.uniform(0, 2 * np.pi))
        for o, a in zip(offsets, amplitudes)
    )
    x = np.real(banda * np.exp(2j * np.pi * f_if * t))
    i_rama = x * np.cos(2 * np.pi * f_if * t)
    q_rama = -x * np.sin(2 * np.pi * f_if * t)
    freqs = np.fft.fftshift(np.fft.fftfreq(n_muestras, 1 / fs_adc)) / 1e6

    def espectro(s):
        return np.fft.fftshift(np.fft.fft(s * np.hanning(n_muestras))) / n_muestras

    E = {"x": espectro(x), "I": espectro(i_rama),
         "Q": espectro(q_rama), "z": espectro(i_rama + 1j * q_rama)}
    return freqs, offsets / 1e6, {k: np.abs(v) for k, v in E.items()}, E


def fig_ramas_iq():
    f, offsets, S, E = _escena_iq()
    tope = max(v.max() for v in S.values())
    filas = [
        ("x[n]", "x", GRAY, "(a) Entrada real en la IF: dos lóbulos simétricos en $\\pm 3.57$ MHz"),
        ("I", "I", BLUE, "(b) Rama I = x·cos: seis emisoras aparentes, pero solo tres existen"),
        ("Q", "Q", RED, "(c) Rama Q = −x·sen: magnitud idéntica a la de I. Lo que cambia es la fase"),
        ("z = I+jQ", "z", GREEN, "(d) Al combinar: los espejos se cancelan; quedan las tres reales"),
    ]
    fig, ax = plt.subplots(5, 2, figsize=(8.4, 10.4),
                           gridspec_kw={"width_ratios": [1.9, 1]})
    for r, (nombre, clave, color, titulo) in enumerate(filas):
        y = 20 * np.log10(S[clave] / tope + 1e-12)
        for c, (lim, paso) in enumerate(((14.4, None), (1.5, 0.5))):
            a = ax[r, c]
            a.plot(f, y, color=color, lw=0.8)
            a.set_xlim(-lim, lim); a.set_ylim(-70, 5)
            a.axvline(0, color="#bbb", lw=0.6, zorder=0)
            if c == 1:
                for o in offsets:
                    a.axvline(+o, color=GREEN, ls=":", lw=0.9)
                    if clave in ("I", "Q"):
                        a.axvline(-o, color=RED, ls=":", lw=0.9)
                a.set_yticklabels([])
            else:
                a.set_ylabel("dB")
        ax[r, 0].set_title(titulo, fontsize=9, loc="left")
        ax[r, 1].set_title("ampliación de la banda base", fontsize=8, loc="left", color="#666")
    # (a) todavía no hay nada en banda base: la señal sigue en la IF
    ax[0, 1].text(0, -32, "todavía nada aquí:\nla señal está en $\\pm 3.57$ MHz",
                  ha="center", fontsize=8, color=GRAY)
    ax[1, 1].text(-0.95, -6, "espejo", color=RED, fontsize=8, ha="center")
    ax[1, 1].text(+0.95, -6, "real", color=GREEN, fontsize=8, ha="center")
    ax[3, 1].text(-0.75, -30, "nada:\nse cancelaron", color=GREEN, fontsize=8, ha="center")
    # las réplicas en ±2·f_IF, que el filtro paso bajo eliminará después
    for fila in (1, 2, 3):
        for signo in (-1, 1):
            if fila == 3 and signo > 0:
                continue
            ax[fila, 0].annotate("", xy=(signo * 7.7, -14), xytext=(signo * 7.7, -4),
                                 arrowprops=dict(arrowstyle="->", color=DARK, lw=0.8))
    ax[1, 0].text(0, -4, "réplicas en $\\pm 2f_{IF}$", ha="center", fontsize=7.5, color=DARK)
    ax[3, 0].text(-7.7, -2, "solo queda la de $-7.14$", ha="center", fontsize=7.5, color=DARK)
    # (e) las DOS fases por separado, una por rama: donde coinciden se suman,
    # donde difieren 180 grados se anulan. No es una resta: son dos cantidades,
    # cada una perteneciente a uno de los paneles de arriba.
    fase_I = np.degrees(np.angle(E["I"]))
    fase_jQ = np.degrees(np.angle(1j * E["Q"]))
    visible = S["I"] > 0.02 * S["I"].max()
    for c, lim in enumerate((14.4, 1.5)):
        a = ax[4, c]
        a.plot(f[visible], fase_I[visible], "o", color=BLUE, ms=4.5, label="fase de I, panel (b)")
        a.plot(f[visible], fase_jQ[visible], "x", color=RED, ms=5, mew=1.4, label="fase de jQ, panel (c)")
        a.set_xlim(-lim, lim); a.set_ylim(-260, 260)
        a.set_yticks([-180, -90, 0, 90, 180])
        a.axvline(0, color="#bbb", lw=0.6, zorder=0)
        if c == 0:
            a.set_ylabel("grados")
            a.legend(fontsize=7.5, frameon=False, loc="lower left", ncol=2)
        else:
            a.set_yticklabels([])
            for o in offsets:
                a.axvline(+o, color=GREEN, ls=":", lw=0.9)
                a.axvline(-o, color=RED, ls=":", lw=0.9)
            a.text(+0.55, 215, "coinciden\n→ se suman", color=GREEN, fontsize=7, ha="center")
            a.text(-0.55, 215, "opuestas\n→ se anulan", color=RED, fontsize=7, ha="center")
    ax[4, 0].set_title("(e) La fase de cada rama: el dato que (b) y (c) no dibujan",
                       fontsize=9, loc="left")
    ax[4, 1].set_title("ampliación de la banda base", fontsize=8, loc="left", color="#666")
    for c in range(2):
        ax[4, c].set_xlabel("Frecuencia (MHz)")
    fig.tight_layout(h_pad=1.1)
    save(fig, "cadena-rx-4b-ramas-iq.png")


fig_ramas_iq()


# ---------------------------------------------------------------- fasores
# El puente entre "el espectro vale tanto a esta frecuencia" y "las ramas se suman
# o se anulan": dibujar esos dos valores como flechas y encadenarlas punta con cola.

def fig_fasores():
    from matplotlib.lines import Line2D

    f, offsets, S, E = _escena_iq()
    fig, ax = plt.subplots(1, 2, figsize=(7.8, 4.4))
    ref = max(abs(E["I"][int(np.argmin(np.abs(f - v)))]) for v in (+0.5, -0.5))
    for col, (freq, titulo, color) in enumerate((
        (+0.5, "En $+0.5$ MHz: emisora real", GREEN),
        (-0.5, "En $-0.5$ MHz: espejo", RED),
    )):
        k = int(np.argmin(np.abs(f - freq)))
        a, b = E["I"][k] / ref, 1j * E["Q"][k] / ref
        fin = a + b
        p_ = ax[col]
        p_.axhline(0, color="#ddd", lw=0.8, zorder=0)
        p_.axvline(0, color="#ddd", lw=0.8, zorder=0)

        # 1) F{I} desde el origen; 2) jF{Q} desde donde terminó la anterior
        p_.annotate("", xy=(a.real, a.imag), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2.6,
                                    shrinkA=0, shrinkB=0, mutation_scale=19))
        p_.annotate("", xy=(fin.real, fin.imag), xytext=(a.real, a.imag),
                    arrowprops=dict(arrowstyle="-|>", color=RED, lw=2.6,
                                    shrinkA=0, shrinkB=0, mutation_scale=19))
        p_.plot(0, 0, "o", color=DARK, ms=5, zorder=6)
        p_.plot(fin.real, fin.imag, "o", color=color, ms=13, zorder=6)

        p_.text(0.5, 0.16,
                "la cadena acaba lejos del origen:\npanel (d), el doble de largo"
                if abs(fin) > 0.05 else
                "la cadena vuelve al origen:\npanel (d), cero",
                transform=p_.transAxes, ha="center", fontsize=8.5,
                color=color, fontweight="bold")
        p_.text(0.5, 0.05, "las dos flechas miden lo mismo: $|I| = |Q|$",
                transform=p_.transAxes, ha="center", fontsize=7.5, color=DARK)

        p_.set_xlim(-2.5, 2.5); p_.set_ylim(-2.1, 2.1)
        p_.set_aspect("equal"); p_.set_xticks([]); p_.set_yticks([])
        p_.set_xlabel("parte real"); p_.set_ylabel("parte imaginaria")
        p_.set_title(titulo, fontsize=9.5, color=color)

    fig.legend(handles=[
        Line2D([], [], color=BLUE, lw=2.6, label="$\\mathcal{F}\\{I\\}$, del panel (b)"),
        Line2D([], [], color=RED, lw=2.6, label="$j\\,\\mathcal{F}\\{Q\\}$, del panel (c)"),
    ], loc="lower center", ncol=2, frameon=False, fontsize=8.5)
    fig.suptitle("Las mismas dos longitudes, dos resultados opuestos", fontsize=10)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save(fig, "cadena-rx-4c-fasores.png")


fig_fasores()

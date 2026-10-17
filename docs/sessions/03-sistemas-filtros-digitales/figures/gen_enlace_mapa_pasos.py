"""Genera 24 mapas funcionales del laboratorio BPSK con posiciones estables.

Desde la raíz del repositorio:
    python3 docs/sessions/03-sistemas-filtros-digitales/figures/gen_enlace_mapa_pasos.py
Requiere Matplotlib. --salida permite verificar la reproducción fuera de docs/.
Los colores indican el tema de estudio, no el estado activo del flowgraph.
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

PASOS = [
    {
        "numero": 1,
        "titulo": "Preparar el entorno de la simulación",
        "foco": ["entorno"],
        "apoyo": [],
    },
    {
        "numero": 2,
        "titulo": "Definir la entrada de texto",
        "foco": ["t1"],
        "apoyo": ["entorno"],
    },
    {
        "numero": 3,
        "titulo": "Comprobar la interfaz antes de continuar",
        "foco": ["t1", "entorno"],
        "apoyo": [],
    },
    {
        "numero": 4,
        "titulo": "Observar mensajes con Message Debug",
        "foco": ["observacion"],
        "apoyo": ["t1"],
    },
    {
        "numero": 5,
        "titulo": "Codificar el texto como bytes UTF-8",
        "foco": ["t1"],
        "apoyo": ["observacion"],
    },
    {
        "numero": 6,
        "titulo": "Comprobar la conversión inversa",
        "foco": ["r6"],
        "apoyo": ["t1"],
    },
    {
        "numero": 7,
        "titulo": "Construir un paquete que pueda comprobarse",
        "foco": ["t2"],
        "apoyo": ["t1"],
    },
    {
        "numero": 8,
        "titulo": "Validar antes de entregar el texto",
        "foco": ["r6"],
        "apoyo": ["t2"],
    },
    {
        "numero": 9,
        "titulo": "Introducir un error deliberado",
        "foco": ["t2", "r6", "ensayo"],
        "apoyo": [],
    },
    {
        "numero": 10,
        "titulo": "Separar cada byte en ocho bits",
        "foco": ["t4"],
        "apoyo": ["t2"],
    },
    {
        "numero": 11,
        "titulo": "Mapear los bits a símbolos BPSK",
        "foco": ["t5"],
        "apoyo": ["t4", "observacion"],
    },
    {
        "numero": 12,
        "titulo": "Construir muestras con un pulso rectangular",
        "foco": ["rectangular"],
        "apoyo": ["t5"],
    },
    {
        "numero": 13,
        "titulo": "Dar forma RRC y cerrar la ráfaga",
        "foco": ["t6"],
        "apoyo": ["rectangular", "t5"],
    },
    {
        "numero": 14,
        "titulo": "Recibir con filtro y tiempo conocidos",
        "foco": ["r1", "r2"],
        "apoyo": ["t6"],
    },
    {
        "numero": 15,
        "titulo": "Recuperar bits, bytes y el paquete",
        "foco": ["r4", "r5", "r6"],
        "apoyo": ["r1", "r2"],
    },
    {
        "numero": 16,
        "titulo": "Detectar acceso y longitud desde los bits",
        "foco": ["t3", "r5"],
        "apoyo": ["r6"],
    },
    {
        "numero": 17,
        "titulo": "Recibir muestras sin etiquetas del transmisor",
        "foco": ["r2", "r5"],
        "apoyo": ["t6", "ensayo"],
    },
    {
        "numero": 18,
        "titulo": "Añadir ruido y contar cada etapa",
        "foco": ["c5", "ensayo"],
        "apoyo": ["r1", "r5", "r6"],
    },
    {
        "numero": 19,
        "titulo": "Introducir fase y observar Costas",
        "foco": ["c1", "r3"],
        "apoyo": ["r4", "r5"],
    },
    {
        "numero": 20,
        "titulo": "Resolver la polaridad con el protocolo",
        "foco": ["r4", "r5"],
        "apoyo": ["r3", "r6"],
    },
    {
        "numero": 21,
        "titulo": "Seguir una diferencia de frecuencia",
        "foco": ["c2", "r3"],
        "apoyo": ["r4", "r5"],
    },
    {
        "numero": 22,
        "titulo": "Separar retardo y fase de muestreo",
        "foco": ["c3", "r2"],
        "apoyo": ["r3"],
    },
    {
        "numero": 23,
        "titulo": "Adquirir el instante y seguir el reloj",
        "foco": ["c4", "r2"],
        "apoyo": ["c3", "r1", "observacion"],
    },
    {
        "numero": 24,
        "titulo": "Dar tiempo de adquisición e integrar",
        "foco": ["t3"],
        "apoyo": ["c1", "c2", "c3", "c4", "c5", "r2", "r3", "r4", "r5", "r6", "ensayo"],
    },
]

# id, posición, ancho, título y lectura breve. Las posiciones nunca cambian.
BLOQUES = [
    ("t1", 0.8, 10.85, 3.25, "T1 · Texto", "UTF-8 → bytes"),
    ("t2", 4.65, 10.85, 3.25, "T2 · Paquete", "Longitud y CRC"),
    ("t3", 8.5, 10.85, 3.25, "T3 · Trama", "Acceso y cabecera\nPreámbulo en 24"),
    ("t4", 12.35, 10.85, 3.25, "T4 · Bits", "MSB first"),
    ("t5", 16.2, 10.85, 3.25, "T5 · BPSK", "0 → −1; 1 → +1"),
    ("t6", 20.05, 10.85, 3.25, "T6 · Pulso TX", "Filtro RRC"),
    ("c1", 19.45, 7.85, 3.85, "C1 · Fase", "Rotación fija"),
    ("c2", 14.8, 7.85, 3.85, "C2 · Frecuencia", "Giro de fase"),
    ("c3", 10.15, 7.85, 3.85, "C3 · Retardo", "Delay"),
    ("c4", 5.5, 7.85, 3.85, "C4 · Reloj", "Remuestreo"),
    ("c5", 0.85, 7.85, 3.85, "C5 · Ruido", "Suma gaussiana"),
    ("r1", 0.8, 4.85, 3.25, "R1 · RRC RX", "Filtro adaptado"),
    ("r2", 4.65, 4.85, 3.25, "R2 · Tiempo", "Ideal / fijo /\nSymbol Sync"),
    ("r3", 8.5, 4.85, 3.25, "R3 · Costas", "Portadora"),
    ("r4", 12.35, 4.85, 3.25, "R4 · Bits", "Decisión y\npolaridad"),
    ("r5", 16.2, 4.85, 3.25, "R5 · Paquete", "Acceso y bytes"),
    ("r6", 20.05, 4.85, 3.25, "R6 · Validar", "CRC → UTF-8"),
    ("entorno", 0.8, 1.85, 5.1, "E · Entorno", "Options y Qt"),
    ("observacion", 6.55, 1.85, 5.1, "O · Observar", "Debug y visores"),
    ("ensayo", 12.3, 1.85, 5.1, "X · Ensayar", "Auxiliar y contadores"),
    ("rectangular", 18.05, 1.85, 5.1, "P · Rectangular", "Repeat · comparación"),
]
H = 1.3
ESTILOS = {
    "foco": ("#fff0ca", "#a34f00", "#5b2c00", 2.8),
    "apoyo": ("#e3f0fa", "#25618d", "#164967", 1.65),
    "contexto": ("#f4f5f6", "#b9c2c9", "#50606b", 0.9),
}


def flecha(ax, puntos):
    for a, b in zip(puntos[:-2], puntos[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], c="#677783", lw=1.5, zorder=2)
    ax.add_patch(
        FancyArrowPatch(
            puntos[-2],
            puntos[-1],
            arrowstyle="-|>",
            mutation_scale=14,
            lw=1.5,
            color="#677783",
            shrinkA=0,
            shrinkB=2,
            zorder=2,
        )
    )


def panel(ax, y, titulo):
    ax.add_patch(
        FancyBboxPatch(
            (0.35, y),
            23.3,
            2.45,
            boxstyle="round,pad=0.03,rounding_size=0.15",
            facecolor="#ffffff",
            edgecolor="#d9e0e5",
            lw=1.1,
            zorder=0,
        )
    )
    ax.text(
        0.65, y + 2.12, titulo, va="center", fontsize=13, weight="bold", c="#253947"
    )


def generar(paso, salida):
    with plt.rc_context({"font.family": "DejaVu Sans"}):
        fig, ax = plt.subplots(figsize=(13, 8.35))
        fig.subplots_adjust(left=0.012, right=0.988, top=0.99, bottom=0.02)
        ax.set(xlim=(0, 24), ylim=(0, 15))
        ax.axis("off")
        ax.text(
            12,
            14.65,
            f"Paso {paso['numero']:02d} · {paso['titulo']}",
            ha="center",
            va="center",
            fontsize=16,
            weight="bold",
            c="#1d3344",
        )
        ax.text(
            12,
            14.13,
            "Mapa funcional TX → canal → RX · BPSK en banda base",
            ha="center",
            fontsize=12,
            c="#50606b",
        )
        for x, clave, texto in [
            (1, "foco", "Foco del paso"),
            (8.4, "apoyo", "Funciones relacionadas"),
            (17.4, "contexto", "Contexto global"),
        ]:
            fc, ec, tc, lw = ESTILOS[clave]
            ax.add_patch(Rectangle((x, 13.43), 0.45, 0.30, fc=fc, ec=ec, lw=lw))
            ax.text(x + 0.62, 13.58, texto, va="center", fontsize=11, c=tc)
        panel(ax, 10.5, "TX  →  Texto · bytes · bits · símbolos · muestras")
        panel(ax, 7.5, "CANAL SIMULADO  ←  Muestras I/Q")
        panel(ax, 4.5, "RX  →  Muestras · símbolos · bits · bytes · texto")
        panel(ax, 1.5, "ENTORNO, OBSERVADORES Y RAMA DE COMPARACIÓN")
        for clave, x, y, w, titulo, texto in BLOQUES:
            estado = (
                "foco"
                if clave in paso["foco"]
                else ("apoyo" if clave in paso["apoyo"] else "contexto")
            )
            fc, ec, tc, lw = ESTILOS[estado]
            ax.add_patch(
                FancyBboxPatch(
                    (x, y),
                    w,
                    H,
                    boxstyle="round,pad=0.015,rounding_size=0.10",
                    facecolor=fc,
                    edgecolor=ec,
                    lw=lw,
                    zorder=3,
                )
            )
            ax.text(
                x + w / 2,
                y + 0.98,
                titulo,
                ha="center",
                va="center",
                fontsize=12.5,
                weight="bold",
                color=tc,
                zorder=4,
            )
            ax.text(
                x + w / 2,
                y + 0.43,
                texto,
                ha="center",
                va="center",
                fontsize=11.5,
                color=tc,
                linespacing=1.12,
                zorder=4,
            )
        for grupo in (BLOQUES[:6], BLOQUES[6:11], BLOQUES[11:17]):
            for a, b in zip(grupo[:-1], grupo[1:]):
                _, x, y, w, *_ = a
                _, xb, yb, wb, *_ = b
                if xb > x:
                    flecha(ax, [(x + w, y + H / 2), (xb, yb + H / 2)])
                else:
                    flecha(ax, [(x, y + H / 2), (xb + wb, yb + H / 2)])
        flecha(ax, [(21.675, 10.85), (21.675, 10.15), (21.375, 10.15), (21.375, 9.15)])
        flecha(
            ax, [(2.775, 7.85), (2.775, 7.12), (0.10, 7.12), (0.10, 5.5), (0.8, 5.5)]
        )
        ax.text(
            12,
            0.95,
            "El color indica qué se estudia; no confirma que todo el mapa esté activo.",
            ha="center",
            fontsize=11.5,
            weight="bold",
            c="#3b4b56",
        )
        ax.text(
            12,
            0.45,
            "La guía define las conexiones de cada paso. Los instrumentos no sustituyen el recorrido por muestras.",
            ha="center",
            fontsize=10.3,
            c="#50606b",
        )
        archivo = salida / f"enlace-mapa-paso-{paso['numero']:02d}.png"
        fig.savefig(
            archivo, dpi=160, facecolor="white", metadata={"Software": "Matplotlib"}
        )
        plt.close(fig)
        return archivo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--paso", type=int, choices=range(1, 25))
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    for paso in PASOS:
        if args.paso is None or paso["numero"] == args.paso:
            print(generar(paso, args.salida))


if __name__ == "__main__":
    main()

"""Diagramas del replay a partir de las decisiones reales de simular_replay.py."""

from pathlib import Path
import sys

from gen_cabecera_bits_lora import Lienzo

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from scripts.sesion08_lora.simular_replay import ejecutar_experimento


def flecha(f, x1, y1, x2, y2, color="#47617d"):
    f.nodo("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=color, stroke_width=2)
    dx, dy = x2-x1, y2-y1
    largo = (dx*dx+dy*dy)**0.5
    ux, uy = dx/largo, dy/largo
    f.nodo("path", d=f"M {x2-8*ux-5*uy},{y2-8*uy+5*ux} L {x2},{y2} "
           f"L {x2-8*ux+5*uy},{y2-8*uy-5*ux}",
           fill="none", stroke=color, stroke_width=2)


def secuencia(r):
    f = Lienzo(920, "Replay: gateway, Network Server y Application Server en dos caminos simulados")
    f.texto(30, 35, "Una lectura antigua puede ocultar la alarma", 25, peso="bold")
    f.texto(30, 65, "Mismo tráfico; dos políticas de Network Server y sus aplicaciones independientes.", 18)
    nombres = ["t1 · Sensor: trama A", "t2 · Sensor: trama B", "t3 · Atacante: copia de A"]
    for i, (e, t) in enumerate(zip(r["eventos"], r["tramas"])):
        y = 85 + i*255
        f.caja(30, y, 940, 245, "#f6f8fb", "#d1dce7")
        f.caja(50, y+10, 325, 44, "#eef3ff")
        f.texto(212, y+29, nombres[i], 17, peso="bold", ancla="middle")
        f.texto(212, y+47, f"FCnt={t['fcnt']} · contenido cifrado", 15, ancla="middle")
        flecha(f, 377, y+32, 413, y+32)
        f.caja(415, y+10, 535, 44, "#eef3ff")
        f.texto(682, y+29, "Gateway: comprueba CRC físico", 17, peso="bold", ancla="middle")
        f.texto(682, y+47, "CRC válido → reenvía el PHYPayload cifrado", 15, ancla="middle")
        flecha(f, 580, y+55, 265, y+82)
        flecha(f, 785, y+55, 735, y+82)
        for tipo, x, cabecera in (("vulnerable", 50, "Network Server vulnerable"),
                                 ("con_fcnt", 520, "Network Server con FCnt")):
            a = e[tipo]
            color = "#fff0ea" if i == 2 and tipo == "vulnerable" else "#e5f6ee"
            f.caja(x, y+84, 430, 64, color)
            f.texto(x+215, y+109, cabecera, 18, peso="bold", ancla="middle")
            detalle = ("MIC válido; omite el control de FCnt" if tipo == "vulnerable"
                       else f"MIC válido; guarda FCnt={a['ultimo_fcnt_despues']}" if a["entregado"]
                       else "MIC válido; 4 ≤ 5: bloquea el reenvío")
            f.texto(x+215, y+134, detalle, 16, ancla="middle")
            if a["entregado"]:
                flecha(f, x+215, y+150, x+215, y+176)
            else:
                f.nodo("line", x1=x+215, y1=y+150, x2=x+215, y2=y+165,
                       stroke="#b04747", stroke_width=2)
                f.nodo("path", d=f"M {x+210},{y+160} l 10,10 m -10,0 l 10,-10",
                       fill="none", stroke="#b04747", stroke_width=2)
            f.caja(x, y+178, 430, 57, color)
            f.texto(x+215, y+200, "Application Server", 18, peso="bold", ancla="middle")
            accion = "Descifra → estado" if a["entregado"] else "Sin entrega; conserva"
            f.texto(x+215, y+223, f"{accion} {a['estado_aplicacion']}", 17, ancla="middle")
    f.texto(30, 874, "MIC y FCnt: Network Server. Descifrado con AppSKey y lectura: Application Server.", 18)
    f.texto(30, 904, "El atacante solo guarda y reproduce A; no necesita claves ni modificar los bytes.", 18)
    f.guardar("replay-secuencia.svg")


def verificacion(r):
    f = Lienzo(890, "Gateway comprueba CRC; Network Server verifica MIC y FCnt; Application Server descifra")
    f.texto(30, 35, "Mismo replay de A · FCnt recibido=4 · último válido=5", 24, peso="bold")
    f.texto(30, 68, "El control que cambia está en el servidor de red; el cifrado es el mismo en ambos caminos.", 18)
    f.caja(150, 90, 700, 88, "#eef3ff")
    f.texto(500, 118, "GATEWAY", 22, peso="bold", ancla="middle")
    f.texto(500, 145, "Comprueba CRC físico: válido → reenvía la trama", 18, ancla="middle")
    f.texto(500, 168, "No verifica el MIC ni controla FCnt", 16, ancla="middle")
    flecha(f, 350, 180, 255, 232)
    flecha(f, 650, 180, 745, 232)
    for x, tipo, titulo in ((30, "vulnerable", "Network Server vulnerable"),
                            (520, "con_fcnt", "Network Server con FCnt")):
        a = r["eventos"][-1][tipo]
        f.caja(x, 235, 450, 365, "#f6f8fb", "#d1dce7")
        f.texto(x+225, 268, titulo, 21, peso="bold", ancla="middle")
        f.caja(x+20, 285, 410, 75, "#e5f6ee")
        f.texto(x+225, 314, "1. Verifica MIC con NwkSKey", 18, peso="bold", ancla="middle")
        f.texto(x+225, 343, "Válido: la trama sigue siendo auténtica", 17, ancla="middle")
        flecha(f, x+225, 362, x+225, 392)
        fondo = "#fff0ea" if tipo == "vulnerable" else "#fff2cf"
        f.caja(x+20, 395, 410, 80, fondo)
        if tipo == "vulnerable":
            lineas = ["No consulta el historial de FCnt", "Trata la trama como un dato nuevo"]
        else:
            lineas = ["2. ¿FCnt recibido > último válido?", "4 > 5 es falso → bloquea el reenvío"]
        f.texto(x+225, 425, lineas[0], 18, peso="bold", ancla="middle")
        f.texto(x+225, 454, lineas[1], 17, ancla="middle")
        flecha(f, x+225, 477, x+225, 512)
        f.caja(x+20, 515, 410, 62, "#fff0ea" if tipo == "vulnerable" else "#e5f6ee")
        f.texto(x+225, 541, "REENVÍA A OTRA VEZ" if a["entregado"] else "NO REENVÍA A LA APLICACIÓN",
                18, peso="bold", ancla="middle")
        f.texto(x+225, 565, "Contenido de aplicación aún cifrado" if a["entregado"]
                else "Conserva último FCnt válido = 5", 16, ancla="middle")
        if a["entregado"]:
            flecha(f, x+225, 602, x+225, 658)
        else:
            f.nodo("line", x1=x+225, y1=602, x2=x+225, y2=627, stroke="#b04747", stroke_width=2)
            f.nodo("path", d=f"M {x+219},622 l 12,12 m -12,0 l 12,-12",
                   fill="none", stroke="#b04747", stroke_width=2)
            f.texto(x+225, 649, "Sin nueva entrega", 16, color="#b04747", ancla="middle")
        f.caja(x+20, 660, 410, 100, "#fff0ea" if tipo == "vulnerable" else "#e5f6ee")
        f.texto(x+225, 688, "APPLICATION SERVER", 20, peso="bold", ancla="middle")
        f.texto(x+225, 717, "Descifra A con AppSKey" if a["entregado"] else "No recibe A: no actualiza la lectura",
                17, ancla="middle")
        f.texto(x+225, 746, f"Estado de la aplicación: {a['estado_aplicacion']}", 18, ancla="middle")
    f.caja(30, 792, 940, 72, "#eef3ff")
    f.texto(50, 822, "Si el MIC falla, el Network Server no reenvía ni avanza el contador.", 19, peso="bold")
    f.texto(50, 849, "La aplicación solo puede actualizar su estado cuando el servidor de red le entrega un dato.", 18)
    f.guardar("replay-verificacion.svg")


if __name__ == "__main__":
    resultado = ejecutar_experimento()
    if not resultado["comprobaciones_aprobadas"]:
        raise SystemExit("El experimento no pasó sus comprobaciones")
    secuencia(resultado)
    verificacion(resultado)

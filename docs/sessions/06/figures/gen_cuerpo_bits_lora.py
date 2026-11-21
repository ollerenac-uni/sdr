"""Dibuja todos los símbolos, bloques FEC y bytes extraídos de la muestra LoRa."""

import argparse
import json
from pathlib import Path

from gen_cabecera_bits_lora import Lienzo


def flecha(f, x1, y, x2):
    f.nodo("line", x1=x1, y1=y, x2=x2, y2=y, stroke="#47617d", stroke_width=2)
    f.nodo("path", d=f"M {x2-7},{y-5} L {x2},{y} L {x2-7},{y+5}",
           fill="none", stroke="#47617d", stroke_width=2)


def indices_completos(c):
    alto = 155 + len(c["bloques"])*172
    f = Lienzo(alto, "Los 245 bits del cuerpo: 35 filas de siete bits y sus valores después de Gray")
    f.texto(30, 35, "35 símbolos × 7 bits: recorrer todas las filas", 25, peso="bold")
    f.texto(30, 67, "u = (índice − 1) mod 128;  g = u XOR (u >> 1). Aquí no se divide entre cuatro.", 18)
    for x, titulo in ((30, "Bloque"), (140, "Símbolo"), (290, "Índice recibido"),
                      (530, "u: restar uno"), (765, "g: fila tras Gray")):
        f.texto(x, 106, titulo, 17, peso="bold")
    for b in c["bloques"]:
        y = 125+(b["numero"]-1)*172
        f.caja(25, y, 950, 158, "#f6f8fb" if b["numero"] % 2 else "#edf5fc")
        f.texto(45, y+35, f"B{b['numero']}", 23, peso="bold")
        for i, (s, indice, u, gray) in enumerate(zip(b["simbolos"], b["indices"],
                                                   b["indices_ajustados"], b["filas_gray"])):
            yy = y+27+i*28
            for x, texto in ((140, f"S{s:02d}"), (300, f"{indice:07b}"),
                              (540, f"{u:07b}"), (775, gray)):
                f.texto(x, yy, texto, 20, mono=True)
    f.texto(30, alto-12, "Las filas de siete bits son etiquetas de símbolos; todavía no son las palabras FEC.", 18)
    f.guardar("cuerpo-35-filas.svg")


def bloque_completo(b):
    numero = b["numero"]
    f = Lienzo(425, f"Bloque B{numero}: cinco filas de siete bits se desentrelazan en siete palabras de cinco bits")
    f.texto(25, 32, f"B{numero} · S{b['simbolos'][0]:02d}–S{b['simbolos'][-1]:02d}: 5 × 7 = 7 × 5 = 35 bits", 23, peso="bold")
    f.texto(25, 67, "5 filas tras Gray", 19, peso="bold")
    f.texto(410, 67, "7 palabras FEC", 19, peso="bold")
    f.texto(720, 67, "7 grupos decodificados", 18, peso="bold")
    for j in range(7):
        f.texto(95+j*28, 100, str(j+1), 14, color="#60748a", ancla="middle")
    for i, (s, fila) in enumerate(zip(b["simbolos"], b["filas_gray"])):
        yy = 120+i*42
        f.texto(25, yy+22, f"S{s:02d}", 16, mono=True)
        for j, bit in enumerate(fila):
            marcado = j == (i-1) % 7
            f.caja(82+j*28, yy, 25, 29, "#ffe2ab" if marcado else "#edf3fc")
            f.texto(95+j*28, yy+21, bit, 18, mono=True, ancla="middle")
    f.texto(300, 187, "Reubicar", 15)
    f.texto(300, 208, "los bits", 15)
    flecha(f, 306, 226, 393)
    for i, p in enumerate(b["palabras"]):
        yy = 92+i*36
        fondo = {"contenido": "#edf3fc", "CRC": "#def4e8", "relleno": "#fff0d3"}[p["rol"]]
        f.caja(407, yy, 225, 29, fondo)
        f.texto(418, yy+21, f"P{p['numero']:02d}", 17, mono=True)
        f.texto(474, yy+21, p["bits"][:4]+" | "+p["bits"][4], 19, mono=True)
        f.caja(718, yy, 105, 29, fondo)
        f.texto(737, yy+21, f"{p['nibble']:04b}", 20, mono=True)
        f.texto(838, yy+21, p["rol"], 16)
    f.texto(650, 187, "FEC", 14)
    f.texto(650, 208, "4/5", 14)
    flecha(f, 643, 226, 703)
    primera = b["palabras"][0]
    f.texto(25, 365, f"Amarillo: un bit de cada fila forma P{primera['numero']:02d} = {primera['bits']}.", 18)
    f.texto(25, 393, "En cada palabra: cuatro datos | una paridad; el decodificador restaura el orden de los datos.", 17)
    f.guardar(f"cuerpo-bloque-{numero}.svg")


def bytes_completos(c):
    alto = 180+len(c["bytes"])*33
    f = Lienzo(alto, "Formación de los 22 bytes: parejas de nibbles, máscara y resultado del desblanqueo")
    f.texto(25, 33, "De las palabras FEC a los bytes: ver todas las parejas", 24, peso="bold")
    f.texto(25, 67, "Llega primero el nibble bajo. Se escribe alto|bajo y se aplica XOR con la máscara.", 18)
    cabeceras = ((30, "Byte"), (102, "Palabras"), (259, "Bajo"), (355, "Alto"),
                 (452, "Alto|bajo"), (615, "Máscara"), (790, "Resultado"))
    for x, texto in cabeceras:
        f.texto(x, 105, texto, 17, peso="bold")
    for i, b in enumerate(c["bytes"]):
        yy = 120+i*33
        fondo = "#def4e8" if b["rol"] == "CRC" else "#f3f6fb" if i % 2 == 0 else "white"
        f.caja(25, yy, 950, 30, fondo, fondo)
        mascara = f"{b['mascara']:08b}" if b["mascara"] is not None else "sin XOR"
        valores = ((33, f"{b['numero']:02d}"), (102, f"P{b['palabra_baja']:02d}/P{b['palabra_alta']:02d}"),
                   (262, f"{b['nibble_bajo']:04b}"), (358, f"{b['nibble_alto']:04b}"),
                   (452, f"{b['antes_blanqueo']:08b}"), (615, mascara),
                   (790, f"{b['recuperado']:08b} = {b['recuperado']:02x}"))
        for x, texto in valores:
            f.texto(x, yy+22, texto, 17, mono=True)
    f.texto(25, alto-18, "Las dos últimas filas son CRC: se reagrupan sin blanqueo y se separan del PHYPayload.", 18)
    f.guardar("cuerpo-bytes-blanqueo.svg")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traza", type=Path, default=Path("output/lorawan-iq/traza/traza.json"))
    args = parser.parse_args()
    c = json.loads(args.traza.read_text())["contenido"]
    indices_completos(c)
    for bloque in c["bloques"]:
        bloque_completo(bloque)
    bytes_completos(c)


if __name__ == "__main__":
    main()

"""Dibuja la cabecera con valores extraídos de la señal por inspeccionar_lora.py."""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traza", type=Path, default=Path("output/lorawan-iq/traza/traza.json"))
    args = parser.parse_args()
    h = json.loads(args.traza.read_text())["cabecera"]
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    raiz = ET.Element(f"{{{ns}}}svg", {"viewBox": "0 0 1000 690", "role": "img",
                         "aria-labelledby": "titulo descripcion"})
    ET.SubElement(raiz, f"{{{ns}}}title", {"id": "titulo"}).text = "De 56 bits de índices a los campos de la cabecera LoRa"
    ET.SubElement(raiz, f"{{{ns}}}desc", {"id": "descripcion"}).text = (
        "Ocho índices de siete bits pasan por ajuste, reducción y Gray. La matriz de ocho "
        "filas de cinco bits se desentrelaza en cinco palabras de ocho bits. La decodificación "
        "FEC 4/8 recupera veinte bits: longitud, CR, indicador CRC, bits fijos y comprobación.")

    def nodo(tag, **attrs):
        return ET.SubElement(raiz, f"{{{ns}}}{tag}", {k.replace('_', '-'): str(v) for k, v in attrs.items()})

    def texto(x, y, cadena, tam=18, color="#172d45", mono=False, peso="normal", ancla="start"):
        nodo("text", x=x, y=y, font_size=tam, fill=color, font_weight=peso,
             font_family="DejaVu Sans Mono, monospace" if mono else "DejaVu Sans, sans-serif",
             text_anchor=ancla).text = cadena

    def caja(x, y, w, alto, fondo="#eef3ff", borde="#a0b3d4"):
        nodo("rect", x=x, y=y, width=w, height=alto, rx=9, fill=fondo, stroke=borde)

    def flecha(x1, y1, x2, y2):
        nodo("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke="#47617d", stroke_width=2)
        nodo("path", d=f"M {x2-7},{y2-5} L {x2},{y2} L {x2-7},{y2+5}",
             fill="none", stroke="#47617d", stroke_width=2)

    nodo("rect", width=1000, height=690, fill="white")
    texto(30, 33, "Cabecera observada en la señal: 8 índices × 7 = 56 bits", 21, peso="bold")
    for i, v in enumerate(h["indices"]):
        x, y = 30 + (i % 4)*242, 52 + (i//4)*47
        caja(x, y, 224, 37)
        texto(x+12, y+25, f"S{i+1}  {v:07b}", 19, mono=True)
    caja(30, 155, 950, 64, "#f6f8fb")
    texto(50, 180, "Ajustar el índice, reducir el primer bloque y aplicar Gray", 18, peso="bold")
    texto(50, 204, "u = ((índice − 1) mod 128) // 4;     g = u XOR (u >> 1)", 17, mono=True)

    texto(30, 254, "8 filas de 5 bits", 19, peso="bold")
    texto(414, 254, "5 palabras FEC de 8 bits", 19, peso="bold")
    texto(820, 254, "5 grupos de 4", 18, peso="bold")
    for i, fila in enumerate(h["filas_desentrelazador"]):
        y = 272+i*27
        texto(35, y+18, f"S{i+1}", 16, color="#60748a")
        for j, bit in enumerate(fila):
            caja(84+j*32, y, 29, 24, "#edf6fc")
            texto(98+j*32, y+18, bit, 17, mono=True, ancla="middle")
    texto(265, 343, "Desentrelazar", 16)
    texto(265, 365, "Usar las 8 filas", 14, color="#60748a")
    flecha(274, 383, 397, 383)
    for i, (palabra, nibble) in enumerate(zip(h["palabras_fec"], h["nibbles"])):
        y = 287+i*37
        caja(414, y, 205, 29, "#edf6fc")
        texto(431, y+21, palabra, 20, mono=True)
        caja(820, y, 150, 29, "#e5f6ee", "#92bfa8")
        texto(846, y+21, f"{nibble:04b}", 20, mono=True)
    texto(644, 343, "Decodificar", 16)
    texto(644, 365, "FEC 4/8", 16)
    texto(644, 387, "Paridad y orden", 14, color="#60748a")
    flecha(654, 405, 797, 405)
    texto(30, 520, "Separar los campos después de decodificar", 20, peso="bold")
    b = h["bits_decodificados"]
    campos = [("Longitud · 8", b[:8], 275, "#e0edff"),
              ("CR · 3", b[8:11], 130, "#e6f1e2"),
              ("CRC · 1", b[11], 120, "#fff0cd"),
              ("Fijos · 3", b[12:15], 140, "#f0f1f5"),
              ("Comprobación · 5", b[15:], 245, "#f1e9fa")]
    x = 30
    for etiqueta, contenido, w, color in campos:
        caja(x, 540, w, 75, color)
        texto(x+w/2, 566, etiqueta, 16, ancla="middle")
        texto(x+w/2, 598, contenido, 23, mono=True, ancla="middle")
        x += w+10
    texto(30, 655, f"Resultado: {h['longitud_bytes']} bytes; CR = {h['cr_indice']} (4/5); "
          "CRC presente; comprobación de cabecera válida.", 19, peso="bold")
    destino = Path(__file__).with_name("cabecera-bits-lora.svg")
    ET.ElementTree(raiz).write(destino, encoding="utf-8", xml_declaration=True)
    print(destino)
    dibujar_detalles(h)


class Lienzo:
    """Figuras de detalle con los mismos datos que el esquema general."""

    def __init__(self, alto, titulo):
        self.ns = "http://www.w3.org/2000/svg"
        self.raiz = ET.Element(f"{{{self.ns}}}svg", {
            "viewBox": f"0 0 1000 {alto}", "role": "img", "aria-label": titulo})
        self.nodo("title").text = titulo
        self.nodo("rect", width=1000, height=alto, fill="white")

    def nodo(self, tag, **attrs):
        return ET.SubElement(self.raiz, f"{{{self.ns}}}{tag}",
                             {k.replace("_", "-"): str(v) for k, v in attrs.items()})

    def texto(self, x, y, cadena, tam=18, mono=False, color="#172d45", peso="normal", ancla="start"):
        self.nodo("text", x=x, y=y, font_size=tam, fill=color, font_weight=peso,
                  text_anchor=ancla,
                  font_family="DejaVu Sans Mono, monospace" if mono else "DejaVu Sans, sans-serif").text = cadena

    def caja(self, x, y, ancho, alto, fondo="#eef3ff", borde="#a0b3d4"):
        self.nodo("rect", x=x, y=y, width=ancho, height=alto, rx=9, fill=fondo, stroke=borde)

    def guardar(self, nombre):
        destino = Path(__file__).with_name(nombre)
        ET.ElementTree(self.raiz).write(destino, encoding="utf-8", xml_declaration=True)
        print(destino)


def dibujar_detalles(h):
    fila = h["filas_desentrelazador"][0]
    paridad = fila.count("1") % 2
    ampliada = fila + str(paridad) + "0"
    prefijo, inversa = 0, ""
    for bit in ampliada:
        prefijo ^= int(bit)
        inversa += str(prefijo)
    indice, u = h["indices"][0], h["indices_ajustados"][0]

    f = Lienzo(735, "Origen y recuperación del primer índice: transmisor y receptor separados")
    f.texto(30, 35, "Primer índice: separar transmisión y recepción", 24, peso="bold")
    f.caja(30, 55, 940, 355, "#f6f8fb")
    f.texto(50, 88, "TRANSMISOR · Explica de dónde sale el índice recibido", 20, peso="bold")
    f.texto(50, 120, f"Fila del entrelazador   {fila}", 21, mono=True)
    f.texto(50, 151, f"Paridad XOR = {paridad}; cero fijo = 0 → {fila} | {paridad} | 0 = {ampliada}", 20, mono=True)
    f.texto(50, 184, "Inversa Gray: copiar el primer bit y acumular XOR de izquierda a derecha", 18)
    for j in range(7):
        x = 330+j*71
        f.texto(x, 216, str(j+1), 16, color="#60748a", ancla="middle")
        f.caja(x-26, 228, 52, 40, "#e8eefb")
        f.texto(x, 256, ampliada[j], 23, mono=True, ancla="middle")
        f.caja(x-26, 280, 52, 40, "#e5f6ee")
        f.texto(x, 308, inversa[j], 23, mono=True, ancla="middle")
    f.texto(50, 255, "Entrada Gray", 19)
    f.texto(50, 307, "Binario acumulado", 19)
    f.texto(50, 356, f"{ampliada} → {inversa} = {int(inversa,2)}; sumar 1 → {indice:07b} = {indice}", 21, mono=True)
    f.texto(50, 388, "Las dos posiciones adicionales son paridad y cero antes de este mapeo.", 18)

    f.caja(30, 430, 940, 275, "#f0f8f4", "#92bfa8")
    f.texto(50, 465, "RECEPTOR · Recorrido que seguimos en la práctica", 20, peso="bold")
    lineas = [f"Índice {indice:07b} ({indice}) − 1 = {(indice-1)%128:07b} ({(indice-1)%128})",
              f"Dividir entre 4: {(indice-1)%128:05b} >> 2 = {u:07b} = {u:05b}",
              f"Gray: u XOR (u >> 1) = {u:05b} XOR {u>>1:05b} = {fila}"]
    for i, linea in enumerate(lineas):
        f.texto(50, 504+i*39, linea, 21, mono=True)
    f.texto(50, 638, "El desplazamiento quita los dos ceros de la derecha del índice ajustado.", 18)
    f.texto(50, 671, f"{u:07b} y {u:05b} representan el mismo valor: {u}; los ceros de la izquierda son formato.", 18)
    f.guardar("cabecera-primer-indice.svg")

    f = Lienzo(810, "Desentrelazado de la primera palabra y decodificación FEC 4/8")
    f.texto(30, 35, "De las ocho filas a la primera palabra FEC", 24, peso="bold")
    f.texto(30, 66, "Cada casilla resaltada aporta un bit; la numeración de bits empieza en 1.", 18)
    for j in range(5):
        f.texto(135+j*47, 105, str(j+1), 16, color="#60748a", ancla="middle")
    for i, fila_actual in enumerate(h["filas_desentrelazador"]):
        y, j = 120+i*39, (i-1) % 5
        f.texto(45, y+25, f"S{i+1}", 18, mono=True)
        for col, bit in enumerate(fila_actual):
            f.caja(114+col*47, y, 42, 31,
                   "#ffdfad" if col == j else "#f0f3f8", "#cb8b34" if col == j else "#c4cfdb")
            f.texto(135+col*47, y+23, bit, 20, mono=True, ancla="middle")
        f.texto(400, y+24, f"S{i+1}, bit {j+1} → {fila_actual[j]}", 19, mono=True)
    primera = h["palabras_fec"][0]
    f.caja(650, 156, 315, 195, "#fff4df", "#cb8b34")
    f.texto(675, 193, "Leer de S1 a S8", 20, peso="bold")
    f.texto(675, 239, primera, 31, mono=True)
    f.texto(675, 279, "Ocho bits, una palabra", 18)
    f.texto(675, 314, "De S1 se toma su bit 5", 17)
    f.texto(30, 463, "S1 reparte sus cinco bits entre cinco palabras: no se convierte sola en una palabra.", 18)
    f.caja(30, 490, 940, 285, "#f0f8f4", "#92bfa8")
    f.texto(50, 526, "FEC 4/8 · Comprobar paridad y recuperar el orden de los datos", 20, peso="bold")
    f.texto(50, 569, f"Palabra: {primera[:4]} | {primera[4:]} = cuatro bits de datos | cuatro de paridad", 20, mono=True)
    a, b, c, d = map(int, primera[:4])
    calculada = f"{a^b^c}{b^c^d}{a^b^d}{a^c^d}"
    f.texto(50, 610, f"Datos: {primera[:4]}; paridad calculada: {calculada}; recibida: {primera[4:]}", 20, mono=True)
    f.texto(50, 648, "La palabra de esta muestra es válida: no requiere corregir bits.", 18)
    f.texto(50, 690, f"Datos en orden del codificador: {primera[:4]} → orden original: {primera[:4][::-1]}", 20, mono=True)
    f.texto(50, 736, f"Resultado del decodificador: {h['nibbles'][0]:04b}", 22, peso="bold")
    f.guardar("cabecera-desentrelazado-fec.svg")


if __name__ == "__main__":
    main()

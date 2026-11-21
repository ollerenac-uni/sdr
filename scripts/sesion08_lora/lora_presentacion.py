"""Tablas por transición a partir de los valores observados en el receptor LoRa.

Este módulo solo presenta los datos. La recepción y las comprobaciones de cada
transformación se realizan en inspeccionar_lora.py sobre las muestras I/Q.
"""


def tabla(cabeceras, filas):
    filas = [[str(v) for v in fila] for fila in filas]
    anchos = [max(len(str(h)), *(len(f[i]) for f in filas))
              for i, h in enumerate(cabeceras)] if filas else [len(h) for h in cabeceras]
    def linea(fila):
        return " | ".join(str(v).ljust(a) for v, a in zip(fila, anchos))
    return "\n".join([linea(cabeceras), "-+-".join("-"*a for a in anchos)]
                     + [linea(f) for f in filas])


def bloques(r, numero=None):
    return [b for b in r["contenido"]["bloques"] if numero is None or b["numero"] == numero]


def titulo_bloque(b):
    return (f"[B{b['numero']} | S{b['simbolos'][0]:02d}-S{b['simbolos'][-1]:02d} | "
            f"P{b['palabras'][0]['numero']:02d}-P{b['palabras'][-1]['numero']:02d}]")


def gray(r, numero=None):
    secciones = ["3.5.1 | INDICES -> RESTAR UNO -> GRAY\n"
                 "Cada grupo es una matriz de cinco filas. Se conservan siete bits por fila; sin dividir entre cuatro."]
    for b in bloques(r, numero):
        filas = [(f"S{s:02d}", f"{indice:07b}", f"{u:07b}", f"{u>>1:07b}", g)
                 for s, indice, u, g in zip(b["simbolos"], b["indices"],
                                            b["indices_ajustados"], b["filas_gray"])]
        secciones += [titulo_bloque(b), tabla(
            ["Simbolo", "Indice (7 bits)", "u=(indice-1)%128", "u>>1", "g=u XOR (u>>1)"], filas)]
    return "\n\n".join(secciones)


def desentrelazado(r, numero=None):
    secciones = ["3.5.2 | MATRIZ 5 x 7 -> MATRIZ 7 x 5\n"
                 "En cada palabra se lee un bit de cada fila. El numero de columna empieza en uno."]
    for b in bloques(r, numero):
        secciones += [titulo_bloque(b), "ENTRADA: cinco filas de siete bits tras Gray", tabla(
            ["Fila local", "Simbolo", "Bits c1..c7"],
            [(i+1, f"S{s:02d}", " ".join(g))
             for i, (s, g) in enumerate(zip(b["simbolos"], b["filas_gray"]))])]
        filas = []
        for k, p in enumerate(b["palabras"], 1):
            columnas = [(i-k) % 7 for i in range(5)]
            seleccion = [b["filas_gray"][i][j] for i, j in enumerate(columnas)]
            filas.append((f"P{p['numero']:02d}", " ".join(str(j+1) for j in columnas),
                          " ".join(seleccion), p["bits"]))
        secciones += ["SALIDA: siete palabras de cinco bits; c(r,k)=((r-k-1)%7)+1", tabla(
            ["Palabra", "Columnas en las 5 filas", "Bits seleccionados", "Palabra FEC"], filas),
            "Balance del bloque: 5 x 7 = 7 x 5 = 35 bits; solo se cambia su posicion."]
    return "\n\n".join(secciones)


def fec(r, numero=None):
    secciones = ["3.5.2 | FEC 4/5: PALABRA -> DATOS Y PARIDAD -> NIBBLE\n"
                 "Se muestran tambien las palabras de relleno; se excluyen en la etapa relleno."]
    for b in bloques(r, numero):
        filas = []
        for p in b["palabras"]:
            dato, paridad = p["bits"][:4], p["bits"][4]
            calculada = str(dato.count("1") % 2)
            filas.append((f"P{p['numero']:02d}", p["bits"], dato, paridad, calculada,
                          "SI" if calculada == paridad else "NO", f"{p['nibble']:04b}", p["rol"]))
        secciones += [titulo_bloque(b), tabla(
            ["Palabra", "FEC (5)", "Datos (4)", "p RX", "p XOR", "Igual", "Orden original", "Uso"], filas)]
    total = sum(len(b["palabras"]) for b in bloques(r, numero))
    secciones.append(f"Seleccion mostrada: {total} palabras de cinco bits -> {total} nibbles de cuatro bits. "
                     "Las paridades de esta muestra coinciden.")
    return "\n\n".join(secciones)


def relleno(r, numero=None):
    c, h = r["contenido"], r["cabecera"]
    secciones = ["3.5.3 | CLASIFICAR PALABRAS Y EXCLUIR RELLENO\n"
                 f"Cabecera recibida: {h['longitud_bytes']} bytes de contenido + 2 bytes de CRC. "
                 "Cada byte necesita dos palabras FEC."]
    for b in bloques(r, numero):
        filas = [(f"P{p['numero']:02d}", p["bits"], f"{p['nibble']:04b}", p["rol"],
                  "EXCLUIR" if p["rol"] == "relleno" else "CONSERVAR") for p in b["palabras"]]
        secciones += [titulo_bloque(b), tabla(
            ["Palabra", "FEC (5 bits)", "Nibble (4 bits)", "Uso por posicion", "Decision"], filas)]
    todas = sum(len(b["palabras"]) for b in c["bloques"])
    secciones += ["TOTALES DE LA TRAMA (aunque se haya seleccionado un solo bloque)",
                  tabla(["Region", "Palabras", "Bits codificados", "Bits tras FEC"], [
                      ("Contenido", h["longitud_bytes"]*2, h["longitud_bytes"]*10, h["longitud_bytes"]*8),
                      ("CRC", 4, 20, 16),
                      ("Relleno excluido", c["palabras_relleno"], c["bits_relleno"], c["palabras_relleno"]*4),
                      ("Conservado", c["palabras_reales"], c["palabras_reales"]*5, c["palabras_reales"]*4)]),
                  f"{todas} palabras totales - {c['palabras_relleno']} de relleno = {c['palabras_reales']} utiles. "
                  "Un cero dentro de las palabras utiles se conserva."]
    return "\n\n".join(secciones)


def origen_byte(b):
    bajo, alto = (b["palabra_baja"]-1)//7+1, (b["palabra_alta"]-1)//7+1
    return f"B{bajo}" if bajo == alto else f"B{bajo}/B{alto}"


def grupos_bytes(r, incluir_crc=True):
    """Cada pareja se presenta una vez, en el bloque de su nibble bajo."""
    for bloque in r["contenido"]["bloques"]:
        filas = [b for b in r["contenido"]["bytes"]
                 if (b["palabra_baja"]-1)//7+1 == bloque["numero"]
                 and (incluir_crc or b["rol"] == "contenido")]
        if filas:
            yield bloque, filas


def bytes_reagrupados(r, numero=None):
    secciones = ["3.5.4 | PAREJAS DE NIBBLES -> BYTES\n"
                 "Cada pareja aparece en el bloque de su nibble bajo. La columna Origen avisa si cruza de bloque.\n"
                 "Llega bajo y luego alto; se escribe alto|bajo. No se descartan las parejas que cruzan."]
    for bloque, grupo in grupos_bytes(r):
        filas = [(f"{b['numero']:02d}", origen_byte(b),
                  f"P{b['palabra_baja']:02d}={b['nibble_bajo']:04b}",
                  f"P{b['palabra_alta']:02d}={b['nibble_alto']:04b}",
                  f"{b['antes_blanqueo']:08b}", f"{b['antes_blanqueo']:02x}", b["rol"]) for b in grupo]
        secciones += [titulo_bloque(bloque), tabla(
            ["Byte", "Origen", "Nibble bajo", "Nibble alto", "Alto|bajo", "Hex", "Uso"], filas)]
    n = len(r["contenido"]["bytes"])
    secciones.append(f"Resultado: {n*2} nibbles x 4 = {n} bytes x 8 = {n*8} bits. "
                     "El contenido sigue blanqueado; el CRC no lleva blanqueo.")
    return "\n\n".join(secciones)


def blanqueo(r, numero=None):
    secciones = ["3.5.5 | BYTE REAGRUPADO XOR MASCARA -> BYTE RECUPERADO\n"
                 "La mascara procede del LFSR de LoRa. Las filas de CRC se conservan sin aplicar XOR."]
    for bloque, grupo in grupos_bytes(r):
        filas = [(f"{b['numero']:02d}", origen_byte(b), f"{b['antes_blanqueo']:08b}",
                  f"{b['mascara']:08b}" if b["mascara"] is not None else "sin XOR",
                  f"{b['recuperado']:08b}", f"{b['recuperado']:02x}", b["rol"]) for b in grupo]
        secciones += [titulo_bloque(bloque), tabla(
            ["Byte", "Origen", "Entrada (8 bits)", "Mascara", "Salida (8 bits)", "Hex", "Uso"], filas)]
    return "\n\n".join(secciones)


def crc(r, pasos):
    c = r["contenido"]
    secciones = ["3.5.6 | RECUPERAR LOS DOS BYTES DE CRC Y COMPARAR\n"
                 "Se utiliza todo el contenido recuperado para recalcular el CRC; no solo un bloque."]
    for b in c["bloques"]:
        palabras = [p for p in b["palabras"] if p["rol"] == "CRC"]
        if palabras:
            secciones += [titulo_bloque(b), tabla(["Palabra CRC", "FEC (5)", "Datos", "p RX", "Nibble original"],
                [(f"P{p['numero']:02d}", p["bits"], p["bits"][:4], p["bits"][4], f"{p['nibble']:04b}")
                 for p in palabras])]
    secciones += ["Parejas de nibbles que forman los dos bytes recibidos", tabla(
        ["Byte", "Origen", "Bajo", "Alto", "Byte recibido", "Hex"],
        [(b["numero"], f"P{b['palabra_baja']:02d}/P{b['palabra_alta']:02d}",
          f"{b['nibble_bajo']:04b}", f"{b['nibble_alto']:04b}", f"{b['recuperado']:08b}",
          f"{b['recuperado']:02x}") for b in c["bytes"] if b["rol"] == "CRC"]),
        "Recalculo CRC-16: polinomio 1021, estado inicial 0000; se procesan los primeros N-2 bytes",
        tabla(["Byte de contenido", "Entrada hex", "CRC antes", "CRC despues"],
              [(p["numero"], f"{p['byte']:02x}", f"{p['antes']:04x}", f"{p['despues']:04x}") for p in pasos])]
    calculo = c["crc_calculo"]
    secciones += [tabla(["Operacion final", "Valor"], [
        ("CRC sobre N-2 bytes", f"{calculo['sobre_primeros_n_menos_2']:04x}"),
        ("Ultimos dos bytes del contenido (penultimo en parte alta)", f"{calculo['ultimos_dos_contenido']:04x}"),
        ("XOR: CRC calculado", f"{calculo['calculado']:04x}"),
        ("CRC recibido (valor de 16 bits)", f"{calculo['recibido']:04x}"),
        ("Comparacion", "VALIDO" if c["crc_valido"] else "INVALIDO")]),
        f"Bytes de CRC separados: {c['crc_hex']}. El MIC de LoRaWAN permanece dentro del PHYPayload."]
    return "\n\n".join(secciones)


def phypayload(r, numero=None):
    secciones = ["3.5.7 | PHYPAYLOAD FINAL, SIN LOS DOS BYTES DE CRC FISICO"]
    for bloque, grupo in grupos_bytes(r, incluir_crc=False):
        filas = [(b["numero"], origen_byte(b), f"{b['recuperado']:08b}", f"{b['recuperado']:02x}") for b in grupo]
        secciones += [titulo_bloque(bloque), tabla(["Byte", "Origen", "Bits recuperados", "Hex"], filas)]
    h = r["cabecera"]
    secciones += [f"Total: {h['longitud_bytes']} bytes = {h['longitud_bytes']*8} bits.",
                  r["contenido"]["payload_hex"]]
    return "\n\n".join(secciones)

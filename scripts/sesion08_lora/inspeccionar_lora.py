"""Sigue una trama SF7 desde sus muestras I/Q hasta la cabecera y el contenido.

Ejecutar con el Python de Radioconda. Usa el receptor de gr-lora_sdr en modo
explícito y observa sus etapas; no utiliza los bytes conocidos del transmisor.
La representación de 301 bits corresponde a la muestra de la sección 3.
Fuentes de las convenciones de índice, Gray, entrelazado y cabecera:
https://github.com/tapparelj/gr-lora_sdr/tree/a8143cb/lib
"""

import argparse
import json
from pathlib import Path

from gnuradio import blocks, gr, lora_sdr
import numpy as np
import pmt

if __package__:
    from . import lora_presentacion as presentacion
    from .crc_lora import crc_lora, pasos_crc
else:
    import lora_presentacion as presentacion
    from crc_lora import crc_lora, pasos_crc


def bits(valores, ancho):
    return " ".join(f"{int(valor):0{ancho}b}" for valor in valores)


def secuencia_blanqueo(longitud):
    """LFSR x^8+x^6+x^5+x^4+1, estado inicial ff; una máscara por byte."""
    estado, secuencia = 0xff, []
    for _ in range(longitud):
        secuencia.append(estado)
        nuevo = ((estado >> 7) ^ (estado >> 5) ^ (estado >> 4) ^ (estado >> 3)) & 1
        estado = ((estado << 1) & 0xff) | nuevo
    return secuencia


def detallar_cuerpo(indices, valores, longitud, reales):
    """Expone y comprueba todos los bloques y bytes frente a las etapas reales."""
    filas = [f"{v:07b}" for v in valores["gray"][8:]]
    palabras_rx = valores["palabras"][5:]
    nibbles_rx = valores["nibbles"][5:]
    bloques = []
    for inicio in range(0, len(filas), 5):
        matriz = filas[inicio:inicio+5]
        palabras = [["0"]*5 for _ in range(7)]
        for i in range(5):
            for j in range(7):
                palabras[(i-j-1) % 7][i] = matriz[i][j]
        palabras = ["".join(p) for p in palabras]
        base = (inicio//5)*7
        if [int(p, 2) for p in palabras] != palabras_rx[base:base+7]:
            raise ValueError("Un bloque de cuerpo no coincide con el desentrelazado real.")
        grupos = []
        for j, palabra in enumerate(palabras):
            numero = base+j+1
            nibble = int(palabra[:4][::-1], 2)
            if nibble != nibbles_rx[base+j] or palabra.count("1") % 2:
                raise ValueError("La paridad u orden de una palabra de cuerpo no coincide.")
            rol = "contenido" if numero <= 2*longitud else "CRC" if numero <= reales else "relleno"
            grupos.append({"numero": numero, "bits": palabra, "nibble": nibble,
                           "paridad_valida": True, "rol": rol})
        bloques.append({"numero": inicio//5+1,
                        "simbolos": list(range(inicio+9, inicio+14)),
                        "indices": indices[inicio+8:inicio+13],
                        "indices_ajustados": valores["indices_ajustados"][inicio+8:inicio+13],
                        "filas_gray": matriz, "palabras": grupos})

    nibbles = valores["sin_cabecera_relleno"]
    reagrupados = [(nibbles[2*i+1] << 4) | nibbles[2*i] for i in range(longitud+2)]
    mascaras = secuencia_blanqueo(longitud)
    desblanqueados = [b ^ m for b, m in zip(reagrupados, mascaras)] + reagrupados[-2:]
    if desblanqueados != valores["bytes_con_crc"]:
        raise ValueError("El desblanqueo ilustrado difiere del receptor real.")
    pares = [{"numero": i+1, "palabra_baja": 2*i+1, "palabra_alta": 2*i+2,
              "nibble_bajo": nibbles[2*i], "nibble_alto": nibbles[2*i+1],
              "antes_blanqueo": reagrupados[i],
              "mascara": mascaras[i] if i < longitud else None,
              "recuperado": desblanqueados[i], "rol": "contenido" if i < longitud else "CRC"}
             for i in range(longitud+2)]
    parcial, calculado = crc_lora(bytes(desblanqueados[:longitud]))
    recibido = desblanqueados[-2] | (desblanqueados[-1] << 8)
    if calculado != recibido:
        raise ValueError("La comprobación ilustrada del CRC difiere del receptor real.")
    return {"bloques": bloques, "filas_desentrelazador": filas,
            "palabras_fec": [f"{v:05b}" for v in palabras_rx],
            "nibbles_con_relleno": nibbles_rx, "bytes": pares,
            "crc_calculo": {"sobre_primeros_n_menos_2": parcial,
                            "ultimos_dos_contenido": (desblanqueados[longitud-2] << 8)
                                                        | desblanqueados[longitud-1],
                            "calculado": calculado, "recibido": recibido}}


def observar(archivo):
    """Recibe una sola trama SF7/BW125k con cabecera explícita."""
    meta = json.loads(archivo.with_suffix(".sigmf-meta").read_text())
    if meta["global"]["core:datatype"] != "cf32_le":
        raise ValueError("Se requiere el formato cf32_le de la práctica.")
    fs = int(meta["global"]["core:sample_rate"])
    frecuencia = int(meta["captures"][0]["core:frequency"])
    if fs % 125000:
        raise ValueError("La tasa de muestreo debe ser un múltiplo de 125000.")

    tb = gr.top_block("Inspección de las etapas de recepción LoRa")
    fuente = blocks.file_source(gr.sizeof_gr_complex, str(archivo), False)
    receptor = lora_sdr.lora_sdr_lora_rx(
        center_freq=frecuencia, bw=125000, sf=7, samp_rate=fs,
        sync_word=[0x34], impl_head=False, soft_decoding=False,
        # Son valores iniciales: la cabecera recibida los reemplaza.
        # Se eligen distintos de los conocidos de la muestra didáctica.
        cr=4, has_crc=False, pay_len=255, ldro_mode=2,
        print_rx=[False, False],
    )
    destinos = {"payload": blocks.vector_sink_b()}
    tb.connect(fuente, receptor, destinos["payload"])
    etapas = (
        ("iq_sincronizado", "frame_sync", blocks.vector_sink_c),
        ("indices_ajustados", "fft_demod", blocks.vector_sink_s),
        ("gray", "gray_mapping", blocks.vector_sink_s),
        ("palabras", "deinterleaver", blocks.vector_sink_b),
        ("nibbles", "hamming_dec", blocks.vector_sink_b),
        ("sin_cabecera_relleno", "header_decoder", blocks.vector_sink_b),
        ("bytes_con_crc", "dewhitening", blocks.vector_sink_b),
    )
    for nombre, bloque, constructor in etapas:
        destinos[nombre] = constructor()
        tb.connect(getattr(receptor, f"lora_sdr_{bloque}_0"), destinos[nombre])
    tb.run()

    etiquetas = [pmt.to_python(t.value) for t in destinos["payload"].tags()
                 if pmt.symbol_to_string(t.key) == "frame_info"]
    if len(etiquetas) != 1:
        raise ValueError(f"Se esperaba una trama válida; se recibieron {len(etiquetas)}.")
    info = etiquetas[0]
    if info.get("err") != 0 or info.get("crc_valid") is not True:
        raise ValueError("La comprobación de cabecera o CRC físico no fue válida.")
    if info["cr"] != 1 or info["crc"] != 1:
        raise ValueError("Este recorrido didáctico requiere tasa 4/5 y CRC físico.")
    valores = {k: [int(v) for v in d.data()] for k, d in destinos.items()
               if k != "iq_sincronizado"}

    # Repetir el dechirp y la FFT sobre las muestras ya sincronizadas permite
    # observar los índices completos (7 bits), antes de la reducción de cabecera
    # que fft_demod aplica internamente. No se regeneran símbolos del transmisor.
    sincronizado = destinos["iq_sincronizado"]
    inicio = [pmt.to_python(t.value) for t in sincronizado.tags()
              if pmt.symbol_to_string(t.key) == "frame_info"
              and pmt.to_python(t.value).get("is_header") is True]
    if len(inicio) != 1:
        raise ValueError("No se pudo identificar el inicio de la trama sincronizada.")
    n = np.arange(128, dtype=float)
    indice = int(inicio[0]["cfo_int"]) % 128
    fase = n*n/(2*128) + (indice/128 - 0.5)*n
    fase -= np.where(n >= 128-indice, n, 0)
    referencia = np.exp(2j*np.pi*fase)
    downchirp = referencia.conj() * np.exp(-2j*np.pi*inicio[0]["cfo_frac"]*n/128)
    muestras = np.asarray(sincronizado.data()).reshape(-1, 128)
    indices = np.abs(np.fft.fft(muestras*downchirp, axis=1)).argmax(axis=1).tolist()
    ajustados = [(v-1) % 128 for v in indices]
    ajustados[:8] = [v//4 for v in ajustados[:8]]
    if ajustados != valores["indices_ajustados"]:
        raise ValueError("La FFT observada no coincide con la del receptor.")
    if [v ^ (v >> 1) for v in ajustados] != valores["gray"]:
        raise ValueError("El mapeo Gray no coincide con el del receptor.")

    # Mostrar explícitamente la permutación inversa de la matriz 8 x 5.
    filas = [f"{v:05b}" for v in valores["gray"][:8]]
    palabras = [["0"]*8 for _ in range(5)]
    for i in range(8):
        for j in range(5):
            palabras[(i-j-1) % 5][i] = filas[i][j]
    palabras = ["".join(p) for p in palabras]
    if [int(p, 2) for p in palabras] != valores["palabras"][:5]:
        raise ValueError("El desentrelazado mostrado difiere del receptor.")
    cabecera = valores["nibbles"][:5]
    longitud = (cabecera[0] << 4) | cabecera[1]
    cr, crc = cabecera[2] >> 1, cabecera[2] & 1
    if (longitud, cr, crc) != (info["pay_len"], info["cr"], info["crc"]):
        raise ValueError("Los campos mostrados difieren de la cabecera recibida.")
    if len(valores["payload"]) != longitud:
        raise ValueError("La cantidad de bytes recibidos no coincide con la cabecera.")
    reales = (longitud*8+16)//4
    relleno = valores["palabras"][5+reales:]
    if any(relleno):
        raise ValueError("El relleno de esta muestra no consiste en palabras de ceros.")
    return {
        "archivo": str(archivo), "sf": 7, "bw_hz": 125000,
        "simbolos": indices, "bits_simbolos": "".join(f"{v:07b}" for v in indices),
        "cabecera": {
            "indices": indices[:8], "indices_ajustados": ajustados[:8],
            "filas_desentrelazador": filas, "palabras_fec": palabras,
            "nibbles": cabecera, "bits_decodificados": bits(cabecera, 4).replace(" ", ""),
            "longitud_bytes": longitud, "cr_indice": cr, "crc_presente": bool(crc),
            "checksum": ((cabecera[3] & 1) << 4) | cabecera[4], "checksum_valido": True,
        },
        "contenido": {
            "simbolos": len(indices)-8, "bits_codificados": (len(indices)-8)*7,
            "palabras_reales": reales, "bits_paridad": reales,
            "palabras_relleno": len(relleno), "bits_relleno": len(relleno)*5,
            "nibbles_con_crc": valores["sin_cabecera_relleno"],
            "bytes_con_crc_hex": bytes(valores["bytes_con_crc"]).hex(" "),
            "crc_hex": bytes(valores["bytes_con_crc"][-2:]).hex(" "),
            "crc_valido": True, "payload_hex": bytes(valores["payload"]).hex(" "),
            **detallar_cuerpo(indices, valores, longitud, reales),
        },
    }


def mostrar_simbolos(r):
    indices = r["simbolos"]
    lineas = [f"Símbolos demodulados: {len(indices)}; SF7: {len(indices)*7} bits de índices.",
              "Cada grupo representa un índice de chirp, de mayor a menor peso.",
              "01-08 (cabecera): " + bits(indices[:8], 7)]
    for i in range(8, len(indices), 7):
        lineas.append(f"{i+1:02d}-{min(i+7, len(indices)):02d} (cuerpo):   "
                      + bits(indices[i:i+7], 7))
    return "\n".join(lineas)


def mostrar_cabecera(r):
    h = r["cabecera"]
    lineas = ["Cabecera recibida: 8 índices x 7 = 56 bits", bits(h["indices"], 7),
              "\nÍndice (7 bits) -> ajuste y reducción (5 bits) -> Gray (5 bits)",
              presentacion.tabla(["Símbolo", "Índice (7)", "Restar 1 (7)", "u: dividir 4 (5)", "u>>1", "Gray (5)"],
                  [(f"S{i+1:02d}", f"{indice:07b}", f"{(indice-1)%128:07b}", f"{u:05b}",
                    f"{u>>1:05b}", g) for i, (indice, u, g) in enumerate(zip(
                        h["indices"], h["indices_ajustados"], h["filas_desentrelazador"]))])]
    indice, u = h["indices"][0], h["indices_ajustados"][0]
    fila = h["filas_desentrelazador"][0]
    paridad = fila.count("1") % 2
    ampliada = fila + str(paridad) + "0"
    anterior, inversa, pasos_inversa = 0, "", []
    for i, bit in enumerate(ampliada, 1):
        operacion = "copiar" if i == 1 else f"{anterior} XOR {bit}"
        anterior ^= int(bit)
        inversa += str(anterior)
        pasos_inversa.append((i, bit, operacion, anterior, inversa))
    lineas += ["\nOrigen del primer índice en el transmisor:",
               f"Fila {fila} + paridad {paridad} + cero 0 = {ampliada}.",
               f"Inversa Gray acumulada: {ampliada} -> {inversa}; "
               f"sumar 1 -> {indice:07b} ({indice}).",
               presentacion.tabla(["Posición", "Bit Gray", "Operación", "Bit binario", "Acumulado"], pasos_inversa),
               "Recuperación de la fila en el receptor:",
               f"{indice:07b} - 1 = {(indice-1)%128:07b}; "
               f"dividir entre 4 = {u:07b} = {u:05b}.",
               f"Gray: {u:05b} XOR {u>>1:05b} = {fila}.",
               "\nPrimera palabra desentrelazada: un bit de cada fila (bits desde 1):"]
    lineas.append(presentacion.tabla(["Fila", "Bits tras Gray", "Columna", "Bit seleccionado"],
        [(f"S{i+1:02d}", f, (i-1)%5+1, f[(i-1)%5])
         for i, f in enumerate(h["filas_desentrelazador"])]))
    primera = h["palabras_fec"][0]
    datos = [int(bit) for bit in primera[:4]]
    a, b, c, d = datos
    paridades = f"{a^b^c}{b^c^d}{a^b^d}{a^c^d}"
    lineas += [f"Resultado: {primera} = datos {primera[:4]} + paridad {primera[4:]}.",
               f"FEC 4/8: paridad calculada {paridades}; "
               f"paridad recibida {primera[4:]}; "
               f"datos en orden original {primera[:4][::-1]}."]
    lineas += ["\nDesentrelazado: cinco palabras FEC de ocho bits -> cinco grupos de cuatro"]
    lineas.append(presentacion.tabla(["Palabra", "FEC (8 bits)", "Datos", "Paridad RX", "Nibble original"],
        [(f"H{i+1}", p, p[:4], p[4:], f"{n:04b}")
         for i, (p, n) in enumerate(zip(h["palabras_fec"], h["nibbles"]))]))
    b = h["bits_decodificados"]
    lineas += ["\nCabecera decodificada (20 bits): " + bits(h["nibbles"], 4),
               f"Longitud | CR  | CRC | Fijos | Comprobación\n"
               f"{b[:8]} | {b[8:11]} | {b[11]}   | {b[12:15]}   | {b[15:]}",
               f"Longitud: {h['longitud_bytes']} bytes; CR: {h['cr_indice']} "
               f"(tasa 4/{4+h['cr_indice']}); CRC presente: {int(h['crc_presente'])}.",
               "Comprobación de cabecera: válida."]
    return "\n".join(lineas)


ETAPAS_CUERPO = (
    ("gray", presentacion.gray, "05_gray.txt"),
    ("desentrelazado", presentacion.desentrelazado, "06_desentrelazado.txt"),
    ("fec", presentacion.fec, "07_fec.txt"),
    ("relleno", presentacion.relleno, "08_relleno.txt"),
    ("bytes", presentacion.bytes_reagrupados, "09_bytes.txt"),
    ("blanqueo", presentacion.blanqueo, "10_blanqueo.txt"),
    ("crc", lambda r, numero=None: presentacion.crc(
        r, pasos_crc(bytes.fromhex(r["contenido"]["payload_hex"]))), "11_crc.txt"),
    ("phypayload", presentacion.phypayload, "12_phypayload.txt"),
)
ETAPAS_FILTRABLES = {"gray", "desentrelazado", "fec", "relleno"}


def mostrar_contenido(r):
    return "\n\n".join(funcion(r) for _, funcion, _ in ETAPAS_CUERPO)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Recorrido de la seccion 3.5:
  --etapa gray              Indices, resta de uno y Gray, por bloque
  --etapa desentrelazado    Matrices de entrada, columnas seleccionadas y palabras FEC
  --etapa fec               Datos, paridad recibida/calculada y orden de cada nibble
  --etapa relleno           Palabras conservadas y excluidas segun la longitud
  --etapa bytes             Parejas de nibbles y bytes reagrupados
  --etapa blanqueo          Byte XOR mascara y byte recuperado
  --etapa crc               Palabras de CRC, bytes y estados del CRC recalculado
  --etapa phypayload        Bytes finales en binario y hexadecimal

Usar --bloque 1 o --bloque 7 con gray, desentrelazado, fec o relleno.
Cada ejecucion recibe la trama completa desde I/Q; --bloque filtra la tabla mostrada.
--etapa contenido muestra todas las transiciones del cuerpo; --etapa todo incluye la cabecera.
""")
    parser.add_argument("--archivo", type=Path, default=Path("output/lorawan-iq/correcto.sigmf-data"))
    parser.add_argument("--salida", type=Path, default=Path("output/lorawan-iq/traza"))
    parser.add_argument("--etapa", choices=("simbolos", "cabecera", "contenido", "todo")
                        + tuple(nombre for nombre, _, _ in ETAPAS_CUERPO), default="todo")
    parser.add_argument("--bloque", type=int, help="Mostrar solo Bn en gray, desentrelazado, fec o relleno")
    args = parser.parse_args()
    if args.bloque is not None and args.etapa not in ETAPAS_FILTRABLES:
        parser.error("--bloque se usa con gray, desentrelazado, fec o relleno. "
                     "Las parejas de bytes y el CRC se presentan completos.")
    try:
        r = observar(args.archivo)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"No se pudo completar la inspección: {exc}\n")
    if args.bloque is not None and not 1 <= args.bloque <= len(r["contenido"]["bloques"]):
        parser.error(f"--bloque debe estar entre 1 y {len(r['contenido']['bloques'])}.")
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "01_simbolos_bits.txt").write_text(r["bits_simbolos"] + "\n")
    (args.salida / "02_cabecera.txt").write_text(mostrar_cabecera(r) + "\n", encoding="utf-8")
    (args.salida / "03_phypayload.bin").write_bytes(bytes.fromhex(r["contenido"]["payload_hex"]))
    (args.salida / "04_cuerpo.txt").write_text(mostrar_contenido(r) + "\n", encoding="utf-8")
    (args.salida / "traza.json").write_text(json.dumps(r, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    informes = {}
    for nombre, funcion, archivo in ETAPAS_CUERPO:
        texto = funcion(r)
        (args.salida / archivo).write_text(texto + "\n", encoding="utf-8")
        informes[nombre] = (texto, archivo)
    if args.etapa in informes:
        texto, archivo = informes[args.etapa]
        if args.bloque is not None:
            funcion = next(f for n, f, _ in ETAPAS_CUERPO if n == args.etapa)
            texto = funcion(r, args.bloque)
            archivo = f"{Path(archivo).stem}_B{args.bloque}.txt"
            (args.salida / archivo).write_text(texto + "\n", encoding="utf-8")
        print(texto)
        print(f"\nTabla guardada: {args.salida / archivo}")
    for nombre, funcion in (("simbolos", mostrar_simbolos), ("cabecera", mostrar_cabecera),
                            ("contenido", mostrar_contenido)):
        if args.etapa in (nombre, "todo"):
            print(funcion(r))
            print()
    print(f"Archivos de la inspección: {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

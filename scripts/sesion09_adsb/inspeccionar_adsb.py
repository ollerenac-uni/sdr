"""Expone muestras, decisiones PPM, bits, campos, CRC y CPR de la captura real.

Primero ejecutar verificar_posiciones.py. Todas las etapas usan la misma
ráfaga recuperada; los bloques B1-B7 son grupos de presentación de 16 bits.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np

if __package__:
    from .receptor import ROOT, FS, mode_s_residue, nl, sha256
else:
    from receptor import ROOT, FS, mode_s_residue, nl, sha256


def tabla(cabeceras, filas):
    filas = [[str(c) for c in fila] for fila in filas]
    anchos = [max([len(h)]+[len(f[i]) for f in filas]) for i, h in enumerate(cabeceras)]
    def linea(f):
        return " | ".join(c.ljust(a) for c, a in zip(f, anchos))
    return "\n".join([linea(cabeceras), "-+-".join("-"*a for a in anchos)] + [linea(f) for f in filas])


def pasos_crc(bits):
    estado, filas = 0, []
    for i, bit in enumerate(bits, 1):
        previo = estado
        alto = bool(estado & 0x800000)
        estado = ((estado << 1) | int(bit)) & 0xffffff
        if alto:
            estado ^= 0xfff409
        filas.append({"bit": i, "entrada": int(bit), "antes": previo,
                      "xor_polinomio": alto, "despues": estado})
    return filas


def detallar_cpr(par, impar):
    ye, yo = par["cpr_lat"]/131072, impar["cpr_lat"]/131072
    xe, xo = par["cpr_lon"]/131072, impar["cpr_lon"]/131072
    j = math.floor(59*ye-60*yo+.5)
    le, lo = 6*((j % 60)+ye), (360/59)*((j % 59)+yo)
    le = le-360 if le >= 270 else le
    lo = lo-360 if lo >= 270 else lo
    ultimo = max((par, impar), key=lambda f: f["tiempo_s"])
    f = ultimo["cpr_impar"]
    lat = lo if f else le
    zonas = nl(lat)
    ni = max(zonas-f, 1)
    m = math.floor(xe*(zonas-1)-xo*zonas+.5)
    lon = (360/ni)*((m % ni)+(xo if f else xe))
    if lon >= 180:
        lon -= 360
    return {"par": par, "impar": impar, "ye": ye, "yo": yo, "xe": xe, "xo": xo,
            "j": j, "lat_par": le, "lat_impar": lo, "nl_par": nl(le), "nl_impar": nl(lo),
            "ultimo_impar": f, "ni": ni, "m": m, "latitud": lat, "longitud": lon}


def construir_traza(informe, potencia, hexadecimal=None):
    por_hex = {f["hex"]: f for f in informe["tramas"]}
    if hexadecimal is None:
        hexadecimal = informe["posiciones"][0]["hex_par"]
    if hexadecimal not in por_hex:
        raise ValueError("El hexadecimal no aparece entre las tramas recuperadas de esta captura.")
    frame = por_hex[hexadecimal]
    n0 = frame["muestra_8msps"]
    p = np.memmap(potencia, dtype="<f4", mode="r")
    if n0+960 > len(p):
        raise ValueError("El archivo de potencia esta incompleto: repetir verificar_posiciones.py.")
    decisiones = []
    for i in range(112):
        n = n0+64+8*i
        primera, segunda = float(p[n:n+4].mean()), float(p[n+4:n+8].mean())
        decisiones.append({"simbolo": i+1, "muestra_inicio": n,
                           "inicio_us": 8+i, "primera": primera, "segunda": segunda,
                           "bit": int(primera > segunda)})
    bits = "".join(str(d["bit"]) for d in decisiones)
    if f"{int(bits,2):028x}" != hexadecimal or mode_s_residue(map(int, bits)):
        raise ValueError("Las muestras de potencia no coinciden con la trama del informe.")
    definiciones = [("DF", 1, 5), ("CA", 6, 8), ("ICAO", 9, 32),
                    ("ME", 33, 88), ("CRC", 89, 112)]
    campos = [{"nombre": nombre, "inicio": a, "fin": b, "bits": bits[a-1:b],
               "decimal": int(bits[a-1:b], 2),
               "hex": f"{int(bits[a-1:b],2):0{math.ceil((b-a+1)/4)}x}"}
              for nombre, a, b in definiciones]
    me = []
    if 9 <= frame["tc"] <= 18:
        for nombre, a, b in [("TC",33,37),("SS",38,39),("SAF/NICsb",40,40),("ALT",41,52),
                             ("T",53,53),("F",54,54),("LAT-CPR",55,71),("LON-CPR",72,88)]:
            me.append({"nombre": nombre, "inicio": a, "fin": b,
                       "bits": bits[a-1:b], "decimal": int(bits[a-1:b],2)})
    pareja = next((p for p in informe["posiciones"]
                   if hexadecimal in (p["hex_par"],p["hex_impar"])), None)
    cpr = detallar_cpr(por_hex[pareja["hex_par"]], por_hex[pareja["hex_impar"]]) if pareja else None
    if cpr and max(abs(cpr["latitud"]-pareja["latitud"]),
                   abs(cpr["longitud"]-pareja["longitud"])) > 1e-10:
        raise ValueError("El desglose CPR no coincide con las coordenadas verificadas.")
    return {"trama": frame, "bits": bits, "decisiones": decisiones, "campos": campos,
            "me": me, "crc_calculado": mode_s_residue([int(b) for b in bits[:88]]+[0]*24),
            "crc_recibido": int(bits[88:], 2), "crc_pasos": pasos_crc(bits), "cpr": cpr}


def preparar_ventana(informe, traza, destino):
    """Recorta I/Q nativo y remuestrea una ventana corta para Inspectrum.

    El índice estimado incluye el retardo del remuestreador de la cadena larga;
    el margen de 100 us conserva la ráfaga completa. Se verifica otra vez el
    mensaje por PPM/CRC sobre la ventana producida, con su propio origen local.
    """
    from gnuradio import blocks, filter, gr
    if __package__:
        from .receptor import recuperar_tramas
    else:
        from receptor import recuperar_tramas
    origen = informe["origen"]
    archivo = ROOT / "gnuradio/samples/adsb-posiciones" / origen["archivo"]
    entrada = np.memmap(archivo, dtype="<c8", mode="r")
    inicio = max(0, math.floor((traza["trama"]["tiempo_s"]-.0001)*origen["fs"]))
    ventana = entrada[inicio:inicio+math.ceil(.0004*origen["fs"])]
    tb = gr.top_block("Ventana I/Q ADS-B para Inspectrum")
    fuente = blocks.vector_source_c(ventana.tolist(), False)
    rr = filter.rational_resampler_ccc(interpolation=10, decimation=3)
    sink = blocks.vector_sink_c()
    tb.connect(fuente, rr, sink)
    tb.run()
    iq = np.asarray(sink.data(), dtype="<c8")
    nombre = destino / "ventana-8msps.sigmf-data"
    iq.tofile(nombre)
    potencia = destino / "ventana-potencia.f32"
    (np.abs(iq)**2).astype("<f4").tofile(potencia)
    frames, _ = recuperar_tramas(potencia)
    frame = next((f for f in frames if f["hex"] == traza["trama"]["hex"]), None)
    if frame is None:
        raise ValueError("La ventana corta no recupero la trama seleccionada.")
    meta = {"global": {"core:datatype":"cf32_le", "core:sample_rate":FS,"core:version":"1.0.0",
                       "core:dataset":nombre.name,
                       "core:description":"Ventana I/Q real remuestreada 10/3; no es una señal sintetizada."},
            "captures":[{"core:sample_start":0,"core:frequency":origen["fc"]}],
            "annotations":[{"core:sample_start":frame["muestra_8msps"],"core:sample_count":960,
                            "core:description":"DF17 recuperado: "+frame["hex"]}]}
    nombre.with_suffix(".sigmf-meta").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    ventana_info = {"archivo":nombre.name,"fs":FS,"inicio_nativo":inicio,
                    "muestra_preambulo_local":frame["muestra_8msps"],
                    "preambulo_local_us":frame["muestra_8msps"]/8,
                    "hex":frame["hex"]}
    (destino / "ventana.json").write_text(json.dumps(ventana_info,indent=2)+"\n")
    return ventana_info


def presentar(traza, etapa, bloque=None):
    f, bits = traza["trama"], traza["bits"]
    lineas = [f"TRAMA REAL: {f['hex']} | ICAO {f['icao']} | TC {f['tc']}",
              f"Inicio de preambulo: muestra {f['muestra_8msps']} a 8 Msps; t_archivo={f['tiempo_s']:.8f} s."]
    if etapa == "preambulo":
        lineas += ["8 us = 64 muestras. Los datos comienzan en n0 + 64.",tabla(
            ["Pulso", "Inicio us", "Fin us", "Inicio muestra relativa", "Muestras de pulso"],
            [(i+1,t,t+.5,n,4) for i,(t,n) in enumerate(zip((0,1,3.5,4.5),(0,8,28,36)))])]
    elif etapa == "ppm":
        lineas += ["Un simbolo de 1 us representa un bit: primera mitad > segunda => 1; en otro caso => 0.",
                   "B1-B7 agrupan 16 simbolos para presentar resultados; no son bloques FEC."]
        for k in range(7):
            if bloque and bloque != k+1:
                continue
            filas = traza["decisiones"][k*16:(k+1)*16]
            lineas += [f"B{k+1}: S{k*16+1:03d}-S{k*16+16:03d}",tabla(
                ["Simbolo", "Muestra inicio", "t relativo us", "Media H1 (4)", "Media H2 (4)", "H1-H2", "Bit"],
                [(f"S{d['simbolo']:03d}",d["muestra_inicio"],d["inicio_us"],f"{d['primera']:.8f}",
                  f"{d['segunda']:.8f}",f"{d['primera']-d['segunda']:+.8f}",d["bit"]) for d in filas])]
    elif etapa == "bits":
        lineas += ["112 simbolos PPM = 112 bits = 14 bytes. Se lee MSB primero.",tabla(
            ["Grupo visual", "Bits", "Byte impar", "Byte par", "Hex"],
            [(f"B{k+1}",f"{16*k+1:03d}-{16*k+16:03d}",bits[16*k:16*k+8],bits[16*k+8:16*k+16],
              f["hex"][4*k:4*k+4]) for k in range(7) if not bloque or bloque==k+1]),
            "BLOQUE COMPLETO (112 bits):",bits,"BYTES (14):"," ".join(f["hex"][i:i+2] for i in range(0,28,2))]
    elif etapa == "campos":
        lineas += ["Posiciones numeradas desde 1; no se permutan ni invierten los bits.",tabla(
            ["Campo", "Rango", "Ancho", "Bits recibidos", "Hex", "Decimal"],
            [(c["nombre"],f"{c['inicio']}-{c['fin']}",c["fin"]-c["inicio"]+1,c["bits"],c["hex"],c["decimal"])
             for c in traza["campos"]])]
        if traza["me"]:
            lineas += ["ME DE POSICION AEREA (56 bits)",tabla(
                ["Campo", "Rango global", "Bits", "Decimal"],
                [(c["nombre"],f"{c['inicio']}-{c['fin']}",c["bits"],c["decimal"]) for c in traza["me"]]),
                f"Altitud de esta trama: {f.get('altitud_ft')} ft; F=0 par, F=1 impar."]
        elif "callsign" in f:
            lineas += ["CARACTERES DEL INDICATIVO (codigos de 6 bits, no ASCII)",tabla(
                ["Caracter", "Rango", "Bits", "Valor"],
                [(i+1,f"{41+6*i}-{46+6*i}",bits[40+6*i:46+6*i],int(bits[40+6*i:46+6*i],2)) for i in range(8)]),
                "Indicativo: "+f["callsign"]]
    elif etapa == "crc":
        alterado = list(map(int,bits))
        alterado[40] ^= 1
        lineas += ["Polinomio completo: 0x1FFF409; sin termino x^24: 0xFFF409. Estado inicial 0.",
                   f"CRC calculado sobre 88 bits seguidos de 24 ceros: {traza['crc_calculado']:06x}",
                   f"CRC recibido, bits 89-112: {traza['crc_recibido']:06x}",
                   "Division de los 112 bits recibidos (registro de 24 bits):",tabla(
            ["Paso/bit", "Entrada", "Estado antes", "XOR FFF409", "Estado despues"],
            [(p["bit"],p["entrada"],f"{p['antes']:06x}","SI" if p["xor_polinomio"] else "NO",f"{p['despues']:06x}")
             for p in traza["crc_pasos"] if not bloque or (p["bit"]-1)//16==bloque-1]),
            f"Resto final: {traza['crc_pasos'][-1]['despues']:06x}",
            f"Control: invertir solo el bit 41 -> resto {mode_s_residue(alterado):06x} (rechazado)."]
    elif etapa == "cpr":
        c = traza["cpr"]
        if c is None:
            return "\n".join(lineas+["Esta trama no dispone de una pareja CPR compatible en el informe."])
        lineas += ["Dos mensajes del mismo ICAO; paridades opuestas y diferencia de archivo <= 10 s.",tabla(
            ["Mensaje", "Hex", "F", "LAT-CPR", "LON-CPR", "Tiempo archivo s"],
            [(nombre,c[nombre]["hex"],c[nombre]["cpr_impar"],c[nombre]["cpr_lat"],c[nombre]["cpr_lon"],
              f"{c[nombre]['tiempo_s']:.8f}") for nombre in ("par","impar")]),
            tabla(["Paso", "Expresion", "Resultado"], [
                (1,"ye = LATpar / 131072",f"{c['ye']:.12f}"),
                (2,"yo = LATimpar / 131072",f"{c['yo']:.12f}"),
                (3,"j = floor(59*ye - 60*yo + 0.5)",c["j"]),
                (4,"lat_par = 6*((j mod 60)+ye)",f"{c['lat_par']:.12f}"),
                (5,"lat_impar = (360/59)*((j mod 59)+yo)",f"{c['lat_impar']:.12f}"),
                (6,"NL(lat_par), NL(lat_impar)",f"{c['nl_par']}, {c['nl_impar']}"),
                (7,"Ultima paridad F; ni=max(NL-F,1)",f"F={c['ultimo_impar']}; ni={c['ni']}"),
                (8,"xe = LONpar / 131072",f"{c['xe']:.12f}"),
                (9,"xo = LONimpar / 131072",f"{c['xo']:.12f}"),
                (10,"m = floor(xe*(NL-1) - xo*NL + 0.5)",c["m"]),
                (11,"lon = (360/ni)*((m mod ni) + x_ultimo)",f"{c['longitud']:.12f} (ajustada a -180..180)"),
            ]),f"POSICION FINAL: {c['latitud']:.12f}, {c['longitud']:.12f}",
            "No se usa una coordenada conocida como entrada. Los tiempos son relativos al archivo."]
    return "\n\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etapa", choices=("senal","preambulo","ppm","bits","campos","crc","cpr","mapa","todas"), default="bits")
    parser.add_argument("--directorio",type=Path,default=ROOT / "output/adsb-posiciones")
    parser.add_argument("--hex",help="Selecciona una trama presente en la captura")
    parser.add_argument("--bloque",type=int,choices=range(1,8),help="Muestra un grupo visual de 16 bits")
    parser.add_argument("--listar",action="store_true",help="Lista mensajes recuperados y sus tipos")
    args = parser.parse_args()
    try:
        informe = json.loads((args.directorio / "verificacion.json").read_text())
        potencia = args.directorio / "potencia8.f32"
        origen = informe["origen"]
        archivo = ROOT / "gnuradio/samples/adsb-posiciones" / origen["archivo"]
        if sha256(archivo) != origen["sha256"]:
            raise ValueError("La captura no coincide con su hash verificado.")
        if args.listar:
            print(tabla(["Hex", "ICAO", "TC", "Tiempo archivo s", "Indicativo"],
                [(f["hex"],f["icao"],f["tc"],f"{f['tiempo_s']:.8f}",f.get("callsign","")) for f in informe["tramas"]]))
            return 0
        traza = construir_traza(informe,potencia,args.hex.lower() if args.hex else None)
        destino = args.directorio / "traza"
        destino.mkdir(parents=True,exist_ok=True)
        (destino / "traza.json").write_text(json.dumps(traza,ensure_ascii=False,indent=2)+"\n")
        (destino / "112_bits.txt").write_text(traza["bits"]+"\n")
        etapas = ("senal","preambulo","ppm","bits","campos","crc","cpr","mapa") if args.etapa=="todas" else (args.etapa,)
        for etapa in etapas:
            if etapa == "senal":
                ventana = preparar_ventana(informe,traza,destino)
                texto = f"Ventana I/Q real: {destino / ventana['archivo']}\nTasa: 8 Msps, formato cf32.\nPreámbulo local en {ventana['preambulo_local_us']:.3f} us.\nDatos desde {ventana['preambulo_local_us']+8:.3f} us; fin {ventana['preambulo_local_us']+120:.3f} us."
            elif etapa == "mapa":
                texto = f"Mapa generado por verificar_posiciones.py: {args.directorio / 'mapa.html'}\nPosiciones: {len(informe['posiciones'])}; aeronaves: {len(informe['resumen']['aeronaves_con_posicion'])}.\nCada punto conserva las dos tramas CPR de origen en posiciones.csv y verificacion.json."
            else:
                texto = presentar(traza,etapa,args.bloque)
            (destino / f"{etapa}.txt").write_text(texto+"\n")
            print(texto+"\n")
        return 0
    except (OSError,ValueError,KeyError) as exc:
        parser.exit(1,f"{exc}\nPreparar antes: python scripts/sesion09_adsb/verificar_posiciones.py\n")


if __name__ == "__main__":
    raise SystemExit(main())

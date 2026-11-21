"""Soporte del laboratorio 6: recepción compartida, exportación y casos locales.

La extracción de los campos principales se delega a la función del alumno.
Los casos de integridad son mensajes binarios locales; no se genera ni emite RF.
"""

import json
from numbers import Integral
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from .receptor import (ROOT, FS, interpretar, recuperar_posiciones, resumen,
                       mode_s_residue)
from .verificar_posiciones import guardar_resultados


def bits_trama(hexadecimal):
    h = hexadecimal.strip().lower()
    if len(h) != 28 or any(c not in "0123456789abcdef" for c in h):
        raise ValueError("Se requieren 28 dígitos hexadecimales: una trama de 112 bits")
    return f"{int(h,16):0112b}"


def analizar_crc(hexadecimal):
    bits = bits_trama(hexadecimal)
    recibido = int(bits[88:],2)
    calculado = mode_s_residue([int(b) for b in bits[:88]]+[0]*24)
    resto = mode_s_residue(map(int,bits))
    return {"hex":hexadecimal.lower(),"crc_recibido":f"{recibido:06x}",
            "crc_calculado":f"{calculado:06x}","resto":f"{resto:06x}",
            "crc_valido":recibido==calculado and resto==0}


def comprobar_casos(casos):
    return [{"id":c["id"],**analizar_crc(c["hex"])} for c in casos["casos"]]


def guardar_grafico_potencia(traza,archivo,destino):
    """Grafica muestras observadas, sin exigir Matplotlib al alumno."""
    ns="http://www.w3.org/2000/svg"
    ET.register_namespace("",ns)
    raiz=ET.Element(f"{{{ns}}}svg",{"viewBox":"0 0 1120 550","role":"img"})
    def nodo(tag,**attrs):
        return ET.SubElement(raiz,f"{{{ns}}}{tag}",{k.replace("_","-"):str(v) for k,v in attrs.items()})
    def texto(x,y,s,tam=16):
        nodo("text",x=x,y=y,font_family="DejaVu Sans, sans-serif",font_size=tam,fill="#17314a").text=s
    nodo("title").text="Potencia real del preámbulo y dieciséis símbolos PPM"
    nodo("rect",width=1120,height=550,fill="white")
    f=traza["trama"]
    texto(30,30,f"Trama {f['hex']} · preámbulo en muestra {f['muestra_8msps']}",19)
    p=np.memmap(archivo,dtype="<f4",mode="r")
    n=f["muestra_8msps"]
    for panel,(base,cantidad,intervalo,titulo) in enumerate([
            (n,73,9,"Preámbulo observado: cuatro pulsos; datos desde 8 µs"),
            (n+64,128,16,"Primeros 16 símbolos PPM: un bit por intervalo de 1 µs")]):
        y0=85+255*panel
        valores=p[base:base+cantidad]
        pico=max(float(np.max(valores)),1e-12)
        texto(70,y0-20,titulo,18)
        spans=[(a,a+.5) for a in (0,1,3.5,4.5)] if not panel else [
            (i if d["bit"] else i+.5, i+.5 if d["bit"] else i+1)
            for i,d in enumerate(traza["decisiones"][:16])]
        for a,b in spans:
            nodo("rect",x=70+a/intervalo*1000,y=y0,width=(b-a)/intervalo*1000,height=135,fill="#deeee7")
        puntos=" ".join(f"{70+(i/8)/intervalo*1000:.3f},{y0+135-float(v)/pico*116:.3f}" for i,v in enumerate(valores))
        nodo("polyline",points=puntos,fill="none",stroke="#1c7794",stroke_width=1.7)
        nodo("line",x1=70,y1=y0+135,x2=1070,y2=y0+135,stroke="#72889b")
        paso=1 if not panel else 2
        for x in range(0,intervalo+1,paso):
            texto(65+x/intervalo*1000,y0+157,str(x),14)
        texto(70,y0+184,"Tiempo desde el primer pulso (µs)" if not panel else "Tiempo desde el comienzo de los datos (µs)",16)
        texto(775,y0-20,f"Máximo de potencia: {pico:.5f}",15)
        if panel:
            for i,d in enumerate(traza["decisiones"][:16]):
                texto(70+(i+.5)/16*1000-5,y0+15,str(d["bit"]),15)
    ET.ElementTree(raiz).write(destino,encoding="utf-8",xml_declaration=True)


def validar_campos(c):
    """Detecta errores de tipo/rango sin corregir el resultado del alumno."""
    base={"df","ca","icao","tc"}
    if not isinstance(c,dict) or not base.issubset(c):
        raise ValueError("extraer_campos debe devolver df, ca, icao y tc")
    if any(not isinstance(c[k],Integral) for k in ("df","ca","tc")):
        raise ValueError("DF, CA y TC deben ser enteros")
    if c["df"] != 17 or not 0 <= c["ca"] <= 7 or not 0 <= c["tc"] <= 31:
        raise ValueError("Revisar los rangos y la numeración de DF, CA y TC")
    if not isinstance(c["icao"],str) or len(c["icao"])!=6 or any(
            b not in "0123456789abcdefABCDEF" for b in c["icao"]):
        raise ValueError("ICAO debe tener seis dígitos hexadecimales, incluidos ceros iniciales")
    if 9 <= c["tc"] <= 18:
        if not {"cpr_impar","cpr_lat","cpr_lon","altitud_ft"}.issubset(c):
            raise ValueError("Para TC9–18 faltan cpr_impar, cpr_lat, cpr_lon o altitud_ft")
        if any(not isinstance(c[k],Integral) for k in ("cpr_impar","cpr_lat","cpr_lon")):
            raise ValueError("F y los campos CPR deben ser enteros")
        if c["cpr_impar"] not in (0,1) or not 0 <= c["cpr_lat"] < 131072 or not 0 <= c["cpr_lon"] < 131072:
            raise ValueError("Revisar F y los dos campos CPR de 17 bits")


def ejecutar_analisis(extraer_campos, entrada, salida):
    """Construye el mapa usando los campos obtenidos por la función del alumno."""
    datos=json.loads(Path(entrada).read_text(encoding="utf-8"))
    tramas=[]
    for mensaje in datos["mensajes"]:
        bits=bits_trama(mensaje["hex"])
        if not analizar_crc(mensaje["hex"])["crc_valido"]:
            raise ValueError("Se alteró un mensaje de entrada: el CRC ya no es válido")
        propios=extraer_campos(bits)
        validar_campos(propios)
        r={**propios,"icao":propios["icao"].lower(),"hex":mensaje["hex"],
           "muestra_8msps":mensaje["muestra_8msps"],"tiempo_s":mensaje["muestra_8msps"]/FS,
           "contraste_preambulo":mensaje["contraste_preambulo"],"crc24_valido":True}
        # Se facilita únicamente el contenido de identificación y velocidad.
        # DF, CA, ICAO, TC, ALT y CPR del alumno no se sustituyen por una referencia.
        opcionales=interpretar(mensaje["hex"],mensaje["muestra_8msps"],mensaje["contraste_preambulo"])
        referencia={**opcionales,"ca":int(bits[5:8],2)}
        claves=["df","ca","icao","tc"]
        if 9<=opcionales["tc"]<=18:
            claves += ["cpr_impar","cpr_lat","cpr_lon","altitud_ft"]
        for k in claves:
            valor=propios[k].lower() if k=="icao" else propios.get(k)
            if valor!=referencia[k]:
                raise ValueError(f"Revisar {k} en el mensaje {mensaje.get('numero',mensaje['hex'])}: no coincide con los bits recibidos")
        for k in ("callsign","velocidad_kt","rumbo_deg"):
            if k in opcionales:
                r[k]=opcionales[k]
        tramas.append(r)
    posiciones=recuperar_posiciones(tramas)
    if not posiciones:
        raise ValueError("No se obtuvieron coordenadas: revisar TC, F, LAT-CPR y LON-CPR")
    informe={"origen":datos["origen"],"cadena":["I/Q real","PPM y CRC del curso", "Extracción de campos del alumno","CPR global"],
             "tiempo":"Tiempo relativo al recorte; no es una marca UTC original.",
             "resumen":resumen(tramas,posiciones),"tramas":tramas,"posiciones":posiciones,
             "limites":["No se deduce velocidad mediante desplazamiento/tiempo del archivo.",
                        "CRC válido no autentica al emisor.","Los casos sintéticos se analizan aparte de la captura real."]}
    salida=Path(salida)
    salida.mkdir(parents=True,exist_ok=True)
    guardar_resultados(informe,salida)
    return informe

"""Figuras de la sesión 9 a partir de decisiones PPM y campos de I/Q real."""

import json
from pathlib import Path
from shutil import copyfile
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if __package__:
    from .receptor import ROOT, mode_s_residue
else:
    from receptor import ROOT, mode_s_residue

DESTINO = ROOT / "docs/sessions/09/figures"
TRAZA = ROOT / "output/adsb-posiciones/traza"
COLORES = ["#dceafa", "#eadff9", "#d9f1e7", "#fff0d4", "#f9dfe5"]
TINTA = "#17314a"


class Figura:
    def __init__(self, alto, titulo):
        self.ns = "http://www.w3.org/2000/svg"
        ET.register_namespace("",self.ns)
        self.raiz = ET.Element(f"{{{self.ns}}}svg", {"viewBox":f"0 0 1120 {alto}","role":"img"})
        self.nodo("title").text = titulo
        self.nodo("rect",width=1120,height=alto,fill="white")
        self.texto(30,37,titulo,24,peso="bold")

    def nodo(self,tag,**attrs):
        return ET.SubElement(self.raiz,f"{{{self.ns}}}{tag}",
                             {k.replace("_","-"):str(v) for k,v in attrs.items()})

    def texto(self,x,y,s,tam=18,peso="normal",mono=False,color=TINTA,ancla="start"):
        self.nodo("text",x=x,y=y,font_size=tam,fill=color,font_weight=peso,text_anchor=ancla,
                  font_family="DejaVu Sans Mono, monospace" if mono else "DejaVu Sans, sans-serif").text = str(s)

    def caja(self,x,y,w,h,fondo="#edf3fa"):
        self.nodo("rect",x=x,y=y,width=w,height=h,rx=8,fill=fondo,stroke="#a9bccf")

    def flecha(self,x1,y1,x2,y2):
        self.nodo("line",x1=x1,y1=y1,x2=x2,y2=y2,stroke="#47617d",stroke_width=2)
        self.nodo("path",d=f"M{x2-8},{y2-6} L{x2},{y2} L{x2-8},{y2+6}",fill="none",stroke="#47617d",stroke_width=2)

    def guardar(self,nombre):
        ET.ElementTree(self.raiz).write(DESTINO/nombre,encoding="utf-8",xml_declaration=True)


def avion_y_torre(t):
    """Esquema conceptual de difusión y recepción; panel con datos de la captura."""
    reporte=json.loads((ROOT/"output/adsb-posiciones/verificacion.json").read_text())
    p=next(p for p in reporte["posiciones"] if p["icao"]==t["trama"]["icao"])
    identificacion=next((m["callsign"] for m in reporte["tramas"]
                         if m["icao"]==p["icao"] and m.get("callsign")),"Sin indicativo recibido")
    f=Figura(770,"ADS-B: el avión transmite y la estación muestra sus datos")
    f.texto(30,72,"1090ES · Difusión automática por radio · Esquema conceptual, sin escala",18,color="#526b81")
    defs=f.nodo("defs")
    grad=ET.SubElement(defs,f"{{{f.ns}}}linearGradient",{"id":"cielo","x1":"0","y1":"0","x2":"0","y2":"1"})
    ET.SubElement(grad,f"{{{f.ns}}}stop",{"offset":"0%","stop-color":"#edf6ff"})
    ET.SubElement(grad,f"{{{f.ns}}}stop",{"offset":"100%","stop-color":"#ffffff"})
    f.nodo("rect",x=20,y=92,width=1080,height=487,rx=16,fill="url(#cielo)")
    f.nodo("path",d="M 20,550 Q 180,515 340,549 T 660,548 L 695,579 L 20,579 Z",fill="#e1ede7")

    # Aeronave: dibujo vectorial propio, visto desde arriba y sin escala.
    f.nodo("path",d="M 108,227 L 235,227 L 180,165 L 207,165 L 285,227 L 336,227 Q 360,229 378,241 Q 360,253 336,255 L 285,255 L 207,316 L 180,316 L 235,255 L 137,255 L 110,276 L 87,276 L 105,241 L 87,205 L 110,205 L 137,227 Z",fill="#e7edf4",stroke="#45667f",stroke_width=2.5,stroke_linejoin="round")
    f.nodo("path",d="M 330,230 L 347,233 L 355,241 L 334,241 Z",fill="#3f6e8d")
    f.nodo("line",x1=151,y1=241,x2=314,y2=241,stroke="#93a9ba",stroke_width=2)
    f.caja(55,108,326,55,"#ffffff")
    f.texto(72,132,"Datos calculados a bordo",19,peso="bold")
    f.texto(72,151,"Posición GNSS · altitud · velocidad",16)
    f.texto(70,355,"Aeronave con ADS-B Out",22,peso="bold")
    f.texto(70,385,"Transmite sin una interrogación previa",17)
    f.texto(70,411,"del receptor en tierra.",17)
    for x,y,w in [(396,217,14),(421,201,23),(451,185,32)]:
        f.nodo("path",d=f"M {x},{y} Q {x+w*2},{241} {x},{482-y}",fill="none",stroke="#2e927c",stroke_width=4,stroke_linecap="round")
    f.texto(401,160,"1090 MHz",20,peso="bold",color="#267968")

    # Antena y torre como estación receptora en tierra.
    f.nodo("line",x1=578,y1=221,x2=578,y2=284,stroke="#45667f",stroke_width=4)
    f.nodo("circle",cx=578,cy=219,r=6,fill="#2e927c")
    f.nodo("path",d="M 564,210 Q 551,222 564,234 M 592,210 Q 605,222 592,234",fill="none",stroke="#2e927c",stroke_width=3)
    f.nodo("path",d="M 512,286 L 644,286 L 630,330 L 526,330 Z",fill="#a8c8df",stroke="#45667f",stroke_width=2)
    for x in (542,578,614):
        f.nodo("line",x1=x,y1=289,x2=x,y2=327,stroke="#45667f",stroke_width=2)
    f.nodo("rect",x=550,y=330,width=57,height=206,fill="#d2e0ea",stroke="#45667f",stroke_width=2)
    for y in (363,411,459):
        f.nodo("rect",x=569,y=y,width=18,height=26,rx=2,fill="#82a9c4")
    f.nodo("rect",x=514,y=536,width=130,height=15,rx=3,fill="#66859c")
    f.texto(578,185,"Antena receptora",18,peso="bold",ancla="middle")
    f.nodo("path",d="M 625,360 L 681,360",fill="none",stroke="#426a8b",stroke_width=3)
    f.nodo("path",d="M 672,352 L 681,360 L 672,368",fill="none",stroke="#426a8b",stroke_width=3)
    f.texto(578,572,"Estación en tierra",19,peso="bold",ancla="middle")

    # Pantalla con mapa esquemático y campos extraídos de varios mensajes.
    f.nodo("rect",x=702,y=110,width=380,height=424,rx=15,fill="#17314a")
    f.nodo("rect",x=716,y=154,width=352,height=365,rx=5,fill="#ffffff")
    f.texto(892,139,"Visualización del tráfico aéreo",19,color="white",peso="bold",ancla="middle")
    f.nodo("rect",x=728,y=165,width=328,height=128,rx=5,fill="#eaf4f7")
    f.nodo("path",d="M 731,208 L 792,176 L 851,205 L 840,250 L 785,283 L 741,258 Z M 908,169 L 984,188 L 1039,238 L 1002,286 L 936,264 Z",fill="#d2e4d5")
    for x in (780,834,888,942,996):
        f.nodo("line",x1=x,y1=166,x2=x,y2=292,stroke="#cadde8",stroke_width=1)
    for y in (195,229,263):
        f.nodo("line",x1=729,y1=y,x2=1056,y2=y,stroke="#cadde8",stroke_width=1)
    f.nodo("path",d="M 815,214 L 842,228 L 867,238 L 885,245",fill="none",stroke="#328c78",stroke_width=2,stroke_dasharray="5 4")
    f.nodo("circle",cx=885,cy=245,r=8,fill="#dc8a32",stroke="white",stroke_width=3)
    f.texto(902,243,p["icao"].upper(),17,peso="bold")
    f.texto(902,264,"Mapa esquemático",12,color="#526b81")
    datos=[("ICAO",p["icao"].upper()),("Indicativo",identificacion),
           ("Latitud",f"{p['latitud']:.6f}°"),("Longitud",f"{p['longitud']:.6f}°"),
           ("Altitud barométrica",f"{p['altitud_ft']:,} ft".replace(","," ")),
           ("Velocidad TC19",f"{p['velocidad_kt']:.1f} kt")]
    for i,(etiqueta,valor) in enumerate(datos):
        y=321+i*33
        f.texto(736,y,etiqueta,16,color="#526b81")
        f.texto(1049,y,valor,18,mono=True,peso="bold",ancla="end")
    f.nodo("rect",x=862,y=534,width=59,height=19,fill="#45667f")
    f.nodo("rect",x=811,y=552,width=160,height=10,rx=4,fill="#45667f")

    pasos=[("1. TRANSMITIR","El avión difunde mensajes","de distintos tipos por radio."),
           ("2. RECIBIR Y DECODIFICAR","La estación recupera bits,","comprueba CRC y lee campos."),
           ("3. ASOCIAR Y REPRESENTAR","El software reúne mensajes","con la misma dirección ICAO.")]
    for i,(a,b,c) in enumerate(pasos):
        x=25+365*i
        f.caja(x,598,345,105,COLORES[i])
        f.texto(x+14,628,a,17,peso="bold")
        f.texto(x+14,657,b,17)
        f.texto(x+14,682,c,17)
    f.texto(30,736,"La pantalla reúne varios mensajes de la captura de 2021; no todos los campos viajan en una sola trama.",18)
    f.guardar("00-adsb-avion-torre.svg")


def recorrido():
    f=Figura(340,"De la señal de radio a la posición en el mapa")
    pasos=[("I + jQ","2.4 Msps","Muestras reales"),("|x[n]|²","8 Msps","Potencia"),
           ("Preámbulo","8 µs","Alinear tiempos"),("PPM","112 símbolos","112 bits"),
           ("DF17 + CRC","14 bytes","Campos válidos"),("CPR global","Par + impar","Latitud / longitud")]
    for i,(a,b,c) in enumerate(pasos):
        x=25+183*i
        f.caja(x,85,165,130,COLORES[i%5])
        for j,t in enumerate((a,b,c)):
            f.texto(x+82,119+j*31,t,17 if j else 19,peso="bold" if j==0 else "normal",ancla="middle")
        if i<5:
            f.flecha(x+166,151,x+181,151)
    f.texto(30,257,"GNU Radio: remuestreo 10/3 y potencia. Python: sincronismo, PPM, CRC y CPR.",21)
    f.texto(30,294,"8 muestras por símbolo ≠ 8 bits: las muestras permiten decidir un único bit.",21,peso="bold")
    f.guardar("01-recorrido.svg")


def flujo_laboratorio():
    f=Figura(340,"Laboratorio 6: del recorte real al mapa con evidencia")
    pasos=[("Muestras I/Q","Recorte 14–27 s","2.4 Msps"),
           ("Recepción","PPM + CRC","Facilitada"),
           ("112 bits / trama","extraer_campos","Código del alumno"),
           ("CPR global","Par + impar","Facilitado"),
           ("Mapa","Tres aeronaves","Con evidencias")]
    for i,(a,b,c) in enumerate(pasos):
        x=25+220*i
        f.caja(x,90,195,130,COLORES[3] if i==2 else COLORES[2 if i==4 else 0])
        for j,texto in enumerate((a,b,c)):
            f.texto(x+97,124+j*31,texto,17 if j else 19,
                    peso="bold" if j==0 else "normal",ancla="middle",mono=i==2 and j==1)
        if i<4:
            f.flecha(x+196,155,x+216,155)
    f.texto(30,264,"La función del alumno entrega los campos que se utilizan para calcular las coordenadas.",20)
    f.texto(30,303,"Los tres casos de CRC se estudian aparte: no se mezclan con la captura I/Q del mapa.",20,peso="bold")
    f.guardar("09-flujo-laboratorio.svg")


def senales(t):
    carpeta=ROOT/"output/adsb-posiciones"
    p=np.memmap(carpeta/"potencia8.f32",dtype="<f4",mode="r")
    n=t["trama"]["muestra_8msps"]
    plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
                         "svg.fonttype":"none","figure.facecolor":"white","axes.labelcolor":TINTA})
    iq=np.fromfile(TRAZA/"ventana-8msps.sigmf-data",dtype="<c8")
    v=json.loads((TRAZA/"ventana.json").read_text())
    fig,axes=plt.subplots(3,1,figsize=(12,8.6),layout="constrained")
    axes[0].specgram(iq,NFFT=32,Fs=8e6,noverlap=28,cmap="magma",vmin=-100,vmax=-55)
    axes[0].set(xlabel="Tiempo local de ventana (s)",ylabel="Frecuencia relativa (Hz)",
                title="A. Espectrograma de la ventana I/Q real remuestreada · las ráfagas son breves")
    axes[0].set_ylim(-1.2e6,1.2e6)
    axes[1].plot(np.arange(len(iq))/8,np.abs(iq)**2,color="#1c7794",lw=1)
    axes[1].axvspan(v["preambulo_local_us"],v["preambulo_local_us"]+120,color="#e6b04e",alpha=.15)
    axes[1].set(xlabel="Tiempo local de ventana (µs)",ylabel="Potencia |I+jQ|²",
                title="B. Pasar a potencia hace visibles los pulsos; la zona sombreada contiene la trama")
    axes[2].plot(np.arange(960)/8,p[n:n+960],color="#1c7794",lw=1)
    axes[2].axvspan(0,8,color="#8496bd",alpha=.25,label="Preámbulo: 8 µs")
    axes[2].axvspan(8,120,color="#e6b04e",alpha=.15,label="112 símbolos de 1 µs")
    axes[2].set(xlabel="Tiempo desde el primer pulso (µs)",ylabel="Potencia",
                title="C. Ampliación de la trama seleccionada · 8 + 112 = 120 µs",xlim=(-1,121))
    axes[2].legend(loc="upper right",fontsize=9)
    fig.savefig(DESTINO/"02-senal-real.png",dpi=160)
    plt.close(fig)

    fig,axes=plt.subplots(2,1,figsize=(12,6.3),layout="constrained")
    x=np.arange(80)/8
    axes[0].plot(x,p[n:n+80],marker=".",ms=4,lw=1,color="#1c7794",label="Potencia observada")
    for a in (0,1,3.5,4.5):
        axes[0].axvspan(a,a+.5,color="#9cafd4",alpha=.35)
    axes[0].axvline(8,color="#a04c29",ls="--",label="Inicio de datos")
    axes[0].set(xlim=(-.3,9),xlabel="Tiempo desde el primer pulso (µs)",ylabel="Potencia",
                title="Cuatro pulsos de referencia: 0, 1, 3.5 y 4.5 µs · datos desde 8 µs")
    axes[0].legend(fontsize=9)
    axes[1].plot(np.arange(128)/8,p[n+64:n+64+128],marker=".",ms=3,lw=1,color="#1c7794")
    pico=float(np.max(p[n+64:n+64+128]))
    for i,d in enumerate(t["decisiones"][:16]):
        axes[1].axvspan(i if d["bit"] else i+.5,i+.5 if d["bit"] else i+1,color="#80bc9e",alpha=.27)
        axes[1].axvline(i,color="#abc0d2",lw=.7)
        axes[1].text(i+.5,pico*1.08,str(d["bit"]),ha="center",fontweight="bold")
    axes[1].set(xlim=(0,16),xlabel="Tiempo desde el comienzo de los datos (µs)",ylabel="Potencia",
                title="Primeros 16 símbolos: gana la primera mitad → 1; gana la segunda → 0",xticks=range(17),ylim=(-.05,pico*1.2))
    fig.savefig(DESTINO/"03-preambulo-ppm.png",dpi=160)
    plt.close(fig)


def ppm(t):
    f=Figura(505,"PPM: elegir la posición del pulso dentro de un símbolo")
    for k,bit in enumerate((1,0)):
        x=50+k*535
        f.texto(x,81,f"Esquema ideal · símbolo que representa {bit}",21,peso="bold")
        for j in range(8):
            alto=(j<4)==bool(bit)
            f.caja(x+j*53,100,48,77,"#d9f1e7" if alto else "#f2f5f8")
            f.texto(x+j*53+24,145,"A" if alto else "b",20,mono=True,ancla="middle")
        f.texto(x,207,"0 µs",17)
        f.texto(x+212,207,"0.5 µs",17,ancla="middle")
        f.texto(x+424,207,"1 µs",17,ancla="end")
        f.texto(x+106,242,"H1: 4 muestras",18,ancla="middle")
        f.texto(x+318,242,"H2: 4 muestras",18,ancla="middle")
    f.caja(35,272,1050,66)
    f.texto(55,301,"P1 = promedio(p[n:n+4]);    P2 = promedio(p[n+4:n+8])",22,mono=True)
    f.texto(55,325,"Decisión: bit = 1 si P1 > P2; bit = 0 en otro caso. A=alto, b=bajo.",18)
    f.texto(35,376,"Ejemplos observados, no pulsos ideales:",21,peso="bold")
    for k,d in enumerate(t["decisiones"][:2]):
        f.texto(55,411+k*33,f"S{k+1:03d}: P1={d['primera']:.6f} | P2={d['segunda']:.6f} | bit={d['bit']}",21,mono=True)
    f.texto(35,485,"Remuestrear a 8 Msps facilita la cuadrícula; no añade información a la captura original.",18)
    f.guardar("04-decision-ppm.svg")


def bloques(t):
    f=Figura(625,"Los 112 bits recuperados, en siete filas de 16 bits")
    f.texto(30,72,"B1–B7 son grupos visuales: cada fila contiene dos bytes. No hay desentrelazado.",19)
    def color(pos):
        return next(COLORES[i] for i,c in enumerate(t["campos"]) if c["inicio"]<=pos<=c["fin"])
    for j in range(16):
        f.texto(155+j*35,111,str(j+1),14,ancla="middle",color="#60748a")
    for k in range(7):
        y=127+52*k
        f.texto(30,y+25,f"B{k+1} {16*k+1:03d}–{16*k+16:03d}",16,mono=True)
        for j,b in enumerate(t["bits"][k*16:k*16+16]):
            x=140+j*35
            f.caja(x,y,30,34,color(k*16+j+1))
            f.texto(x+15,y+24,b,21,mono=True,ancla="middle")
        f.texto(726,y+24,t["trama"]["hex"][k*4:k*4+2]+" "+t["trama"]["hex"][k*4+2:k*4+4],21,mono=True)
    for i,c in enumerate(t["campos"]):
        y=139+62*i
        f.caja(855,y-18,230,45,COLORES[i])
        f.texto(870,y+9,f"{c['nombre']}: {c['inicio']}–{c['fin']}",19)
    f.texto(30,530,"Primer byte: 10001101 = 0x8D. DF usa los 5 primeros bits; CA, los 3 siguientes.",19)
    f.texto(30,566,"112 bits = 14 bytes = 88 bits de campos + 24 bits de CRC.",22,peso="bold")
    f.texto(30,600,"El preámbulo de 8 µs alinea la recepción y queda fuera de estos 112 bits.",19)
    f.guardar("05-bloque-112-bits.svg")


def campos(t):
    f=Figura(690,"Segmentar la trama: campos generales y contenido ME de posición")
    f.texto(30,75,t["trama"]["hex"].upper(),26,mono=True)
    x=30
    for i,c in enumerate(t["campos"]):
        ancho=(c["fin"]-c["inicio"]+1)*9.4
        f.caja(x,101,ancho,56,COLORES[i])
        f.texto(x+ancho/2,135,c["nombre"],14 if ancho<45 else 20,ancla="middle")
        x+=ancho
    f.texto(30,191,"DF 5 + CA 3 + ICAO 24 + ME 56 + CRC 24 = 112 bits",23,peso="bold")
    f.texto(30,230,"ME ocupa los bits 33–88. Su Type Code determina cómo leer el resto.",20)
    for i,c in enumerate(t["me"]):
        x=30+(i%4)*275
        y=255+(i//4)*128
        f.caja(x,y,255,108,COLORES[3] if c["nombre"] not in ("LAT-CPR","LON-CPR") else COLORES[2])
        f.texto(x+12,y+25,f"{c['nombre']} · bits {c['inicio']}–{c['fin']}",17,peso="bold")
        f.texto(x+12,y+55,c["bits"],16,mono=True)
        f.texto(x+12,y+84,f"Valor entero: {c['decimal']}",17)
    f.texto(30,545,"F=0: mensaje par. LAT-CPR y LON-CPR son fracciones codificadas, no grados.",20)
    alt=next(c["decimal"] for c in t["me"] if c["nombre"]=="ALT")
    n=((alt & 0xfe0)>>1) | (alt & 0x0f)
    f.texto(30,583,f"ALT → Q=1 → quitar Q → N={n} → 25×{n} − 1000 = {t['trama']['altitud_ft']} ft.",19)
    f.texto(30,621,"TC=11 selecciona posición aérea con altitud barométrica; no contiene el indicativo.",19)
    f.texto(30,659,"Los mensajes de identificación y velocidad se asocian por el mismo ICAO.",19)
    f.guardar("06-campos-trama.svg")


def crc(t):
    f=Figura(390,"CRC: comprobar los campos recibidos sin corregir los bits")
    f.caja(30,80,690,70,COLORES[3]);f.caja(750,80,335,70,COLORES[4])
    f.texto(50,108,"Bits 1–88: DF, CA, ICAO y ME",22,peso="bold")
    f.texto(50,137,t["trama"]["hex"][:22],23,mono=True)
    f.texto(770,108,"Bits 89–112: CRC RX",21,peso="bold")
    f.texto(770,137,f"{t['crc_recibido']:06x}",23,mono=True)
    f.texto(30,196,"88 bits + 24 ceros → división XOR por 0x1FFF409",23)
    f.flecha(640,188,755,188)
    f.texto(778,196,f"{t['crc_calculado']:06x} = CRC RX",23,mono=True)
    f.texto(30,246,"También: dividir los 112 bits recibidos → resto 0x000000 → aceptar.",23)
    alterado=list(map(int,t["bits"]))
    alterado[40]^=1
    f.texto(30,292,f"Cambiar el bit 41 → resto 0x{mode_s_residue(alterado):06X} → rechazar esta trama alterada.",22)
    f.texto(30,346,"El CRC comprueba errores; no prueba quién transmitió ni cifra el mensaje.",21,peso="bold")
    f.guardar("07-crc.svg")


def cpr(t):
    c=t["cpr"]
    f=Figura(600,"CPR global: dos mensajes compatibles permiten recuperar una posición")
    for k,nombre in enumerate(("par","impar")):
        a=c[nombre];x=30+550*k
        f.caja(x,75,520,152,COLORES[2] if not k else COLORES[0])
        for j,s in enumerate((f"Mensaje {nombre} · F={a['cpr_impar']} · ICAO {a['icao']}",
                              a["hex"],f"LAT-CPR={a['cpr_lat']} · LON-CPR={a['cpr_lon']}",
                              f"t_archivo={a['tiempo_s']:.8f} s")):
            f.texto(x+17,108+j*32,s,17 if j==1 else 19,mono=j==1,peso="bold" if not j else "normal")
    f.texto(30,271,"1. Normalizar los enteros: dividir cada coordenada CPR por 2¹⁷ = 131072.",20)
    f.texto(30,309,f"2. Combinar rejillas de latitud de 6° y 360/59°: j={c['j']}.",20)
    f.texto(30,347,f"3. Candidatas: par {c['lat_par']:.6f}°; impar {c['lat_impar']:.6f}°. NL={c['nl_par']} en ambas.",20)
    f.texto(30,385,f"4. El mensaje más reciente es impar: elegir su latitud; ni={c['nl_impar']}−1={c['ni']} para longitud.",20)
    f.caja(30,416,1050,75,"#d9f1e7")
    f.texto(55,448,f"LATITUD {c['latitud']:.9f}°     LONGITUD {c['longitud']:.9f}°",25,mono=True,peso="bold")
    f.texto(55,477,"Posición correspondiente al mensaje impar; no es el promedio de las dos latitudes.",18)
    delta=abs(c['par']['tiempo_s']-c['impar']['tiempo_s'])
    f.texto(30,533,f"Mismo ICAO · CRC válidos · F opuestos · separación de archivo {delta:.6f} s ≤ 10 s",20)
    f.texto(30,572,"No se introduce una ubicación conocida. La comparación con pyModeS verifica el cálculo.",19)
    f.guardar("08-cpr-global.svg")


def animacion(t):
    template=Path(__file__).with_name("ppm-interactivo.html").read_text()
    (DESTINO.parent/"animaciones").mkdir(exist_ok=True)
    (DESTINO.parent/"animaciones/ppm.html").write_text(template.replace("__TRAZA__",json.dumps(t,ensure_ascii=False).replace("<","\\u003c")))


def main():
    DESTINO.mkdir(parents=True,exist_ok=True)
    t=json.loads((TRAZA/"traza.json").read_text())
    avion_y_torre(t);recorrido();flujo_laboratorio();senales(t);ppm(t);bloques(t);campos(t);crc(t);cpr(t);animacion(t)
    # Copias generadas para que el mapa y sus descargas funcionen en MkDocs.
    for origen,nombre in [("mapa.html","mapa-adsb.html"),("posiciones.csv","posiciones.csv"),
                          ("posiciones.geojson","posiciones.geojson"),("verificacion.json","verificacion.json")]:
        copyfile(ROOT/"output/adsb-posiciones"/origen,DESTINO.parent/"animaciones"/nombre)
    print("Figuras y explorador PPM creados en",DESTINO.parent)


if __name__=="__main__":
    main()

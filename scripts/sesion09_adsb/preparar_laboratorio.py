"""Prepara mensajes reales y la plantilla del laboratorio 6 sin completarla.

El lector, demodulador PPM y comprobador CRC se facilitan. El alumno implementa
la extracción de campos y justifica los resultados de su mapa.
"""

import argparse
import json
from pathlib import Path
from shutil import copyfile
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.sesion09_adsb.muestras import cargar_muestra
from scripts.sesion09_adsb.receptor import crear_potencia, recuperar_tramas, sha256, interpretar
from scripts.sesion09_adsb.inspeccionar_adsb import construir_traza, presentar
from scripts.sesion09_adsb.laboratorio import comprobar_casos, guardar_grafico_potencia


def preparacion_valida(datos,origen,potencia):
    """La salida finita de un FIR puede perder muestras de cola: usar el conteo real."""
    n=datos.get("muestras_potencia",0)
    return (datos["origen"]["sha256"]==origen["sha256"] and n>0
            and potencia.stat().st_size==n*4
            and all(0<=m["muestra_8msps"]<=n-960 for m in datos["mensajes"]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida",type=Path,default=ROOT/"output/adsb-laboratorio")
    parser.add_argument("--reprocesar",action="store_true",help="Regenera potencia y mensajes, sin sobrescribir el script del alumno")
    parser.add_argument("--inspeccionar",type=int,metavar="N",help="Selecciona un mensaje por número, comenzando en 1")
    parser.add_argument("--etapa",choices=("preambulo","ppm","bits","crc"),default="ppm")
    parser.add_argument("--bloque",type=int,choices=range(1,8))
    parser.add_argument("--casos-crc",action="store_true",help="Comprueba los tres mensajes del caso local, separados de I/Q")
    args=parser.parse_args()
    carpeta,origen=cargar_muestra("laboratorio")
    archivo=carpeta/origen["archivo"]
    if not archivo.exists() or sha256(archivo)!=origen["sha256"]:
        parser.error("Preparar primero: python scripts/sesion09_adsb/descargar_muestra.py --muestra laboratorio")
    salida=args.salida
    salida.mkdir(parents=True,exist_ok=True)
    entrada=salida/"mensajes.json"
    potencia=salida/"potencia8.f32"
    if args.reprocesar or not entrada.exists() or not potencia.exists():
        print("GNU Radio: recorte real I/Q 2.4 Msps -> potencia 8 Msps...",flush=True)
        n=crear_potencia(archivo,potencia)
        frames,_=recuperar_tramas(potencia)
        datos={"origen":origen,"fs_potencia":8000000,"muestras_potencia":n,
               "mensajes":[{"numero":i+1,"hex":f["hex"],"muestra_8msps":f["muestra_8msps"],
                            "contraste_preambulo":f["contraste_preambulo"]} for i,f in enumerate(frames)]}
        entrada.write_text(json.dumps(datos,ensure_ascii=False,indent=2)+"\n")
    else:
        datos=json.loads(entrada.read_text())
        if not preparacion_valida(datos,origen,potencia):
            parser.error("La preparación anterior no coincide con la muestra. Usar --reprocesar.")
    plantilla=salida/"mi_analisis.py"
    if not plantilla.exists():
        copyfile(Path(__file__).with_name("plantilla_analisis.py"),plantilla)
    casos=json.loads((carpeta/"casos_integridad.json").read_text())
    copyfile(carpeta/"casos_integridad.json",salida/"casos_integridad.json")
    print(f"Preparados {len(datos['mensajes'])} mensajes DF17 con CRC válido.")
    print("Plantilla del alumno (conservada si ya existía):",plantilla)
    print("Entrada para el análisis propio:",entrada)
    if args.inspeccionar is not None:
        if not 1<=args.inspeccionar<=len(datos["mensajes"]):
            parser.error("Número de mensaje fuera de rango")
        m=datos["mensajes"][args.inspeccionar-1]
        frame=interpretar(m["hex"],m["muestra_8msps"],m["contraste_preambulo"])
        traza=construir_traza({"tramas":[frame],"posiciones":[]},potencia,m["hex"])
        texto=presentar(traza,args.etapa,args.bloque)
        destino=salida/"evidencias"
        destino.mkdir(exist_ok=True)
        guardar_grafico_potencia(traza,potencia,destino/f"mensaje_{args.inspeccionar:03d}_potencia.svg")
        (destino/f"mensaje_{args.inspeccionar:03d}_{args.etapa}.txt").write_text(texto+"\n")
        print(texto)
    if args.casos_crc:
        resultado=comprobar_casos(casos)
        (salida/"resultado_casos_crc.json").write_text(json.dumps(resultado,indent=2)+"\n")
        for c in resultado:
            print(f"{c['id']}: recibido={c['crc_recibido']}; calculado={c['crc_calculado']}; resto={c['resto']}; CRC válido={c['crc_valido']}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

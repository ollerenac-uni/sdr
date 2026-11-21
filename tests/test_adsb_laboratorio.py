"""Recorte real reproducible, CRC de los casos y uso efectivo del parser del alumno."""

import json
from pathlib import Path
import struct

import numpy as np
import pytest

from scripts.descargar_capturas_rf import wav_iq
from scripts.sesion09_adsb.laboratorio import analizar_crc, bits_trama, ejecutar_analisis
from scripts.sesion09_adsb.muestras import cargar_muestra, ruta_captura
from scripts.sesion09_adsb.receptor import interpretar
from scripts.sesion09_adsb.preparar_laboratorio import preparacion_valida

ROOT=Path(__file__).resolve().parents[1]
PAR="8d40621d58c382d690c8ac2863a7"
IMPAR="8d40621d58c386435cc412692ad6"


def wav_pequeno():
    fs,fc=2400000,1090000000
    valores=np.asarray([[0,32767],[-32768,0],[123,-456]],dtype="<i2")
    aux=bytearray(36)
    struct.pack_into("<I",aux,32,fc)
    fmt=struct.pack("<HHIIHH",1,2,fs,fs*4,4,16)
    chunks=b"fmt "+struct.pack("<I",len(fmt))+fmt+b"auxi"+struct.pack("<I",len(aux))+aux
    chunks+=b"data"+struct.pack("<I",valores.nbytes)+valores.tobytes()
    return b"RIFF"+struct.pack("<I",4+len(chunks))+b"WAVE"+chunks,valores


def test_recorte_wav_conserva_iq_normalizacion_y_tasa():
    wav,valores=wav_pequeno()
    completo=np.frombuffer(wav_iq(wav,2400000,1090000000),dtype="<c8")
    assert completo.shape==(3,)
    np.testing.assert_allclose(completo,(valores[:,0]+1j*valores[:,1])/32768)
    recorte=np.frombuffer(wav_iq(wav,2400000,1090000000,start_sample=1,sample_count=1),dtype="<c8")
    np.testing.assert_array_equal(recorte,completo[1:2])
    with pytest.raises(ValueError,match="no está completo"):
        wav_iq(wav,2400000,1090000000,start_sample=2,sample_count=2)


def test_laboratorio_es_otro_intervalo_y_tiene_procedencia_fijada():
    _,leccion=cargar_muestra("leccion")
    carpeta,lab=cargar_muestra("laboratorio")
    assert lab["inicio_archivo_original_s"]>=leccion["duracion_archivo_s"]
    assert lab["muestras"]==13*lab["fs"]
    assert lab["bytes"]==lab["muestras"]*8
    assert ruta_captura(lab)==carpeta/lab["archivo"]
    assert lab["sha256"]!=leccion["sha256"]


def test_casos_crc_capturado_y_sintetico_pasan_alteracion_falla():
    c=json.loads((ROOT/"gnuradio/samples/adsb-laboratorio/casos_integridad.json").read_text())
    resultados={x["id"]:analizar_crc(x["hex"]) for x in c["casos"]}
    assert {k:v["crc_valido"] for k,v in resultados.items()}=={"A":True,"B":False,"C":True}
    a,b=(bits_trama(c["casos"][i]["hex"]) for i in (0,1))
    assert [i for i,(x,y) in enumerate(zip(a,b),1) if x!=y]==[41]
    assert a[88:]==b[88:]
    sintetico=c["casos"][2]["hex"]
    assert interpretar(sintetico,0,1)["callsign"]=="AULA06"


@pytest.mark.parametrize("h",["0"*27,"g"*28,"0"*29])
def test_no_se_comprueba_crc_de_longitud_o_formato_incorrecto(h):
    with pytest.raises(ValueError):
        analizar_crc(h)


def entrada_de_prueba(tmp_path):
    datos={"origen":{"archivo":"prueba.sigmf-data","duracion_archivo_s":2,
                     "descarga":{"miembro":"prueba.wav"}},
           "mensajes":[{"numero":i+1,"hex":h,"muestra_8msps":i*8000000,"contraste_preambulo":2}
                       for i,h in enumerate((PAR,IMPAR))]}
    p=tmp_path/"mensajes.json"
    p.write_text(json.dumps(datos))
    return p


def extractor_de_referencia(bits):
    # Verifica el contrato de la función inyectada; no completa la plantilla.
    c=interpretar(f"{int(bits,2):028x}",0,1)
    return {**c,"ca":int(bits[5:8],2)}


def test_exportacion_utiliza_parser_y_preserva_evidencia_cpr(tmp_path):
    entrada=entrada_de_prueba(tmp_path)
    recibidos=[]
    def parser(bits):
        recibidos.append(bits)
        return extractor_de_referencia(bits)
    r=ejecutar_analisis(parser,entrada,tmp_path/"resultado")
    assert len(recibidos)==2 and all(len(b)==112 for b in recibidos)
    assert r["posiciones"][0]["latitud"]==pytest.approx(52.26578017412606,abs=1e-10)
    assert r["posiciones"][0]["hex_par"]==PAR
    assert (tmp_path/"resultado/mapa.html").exists()
    def incorrecto(bits):
        return {**extractor_de_referencia(bits),"cpr_lat":0}
    with pytest.raises(ValueError,match="cpr_lat"):
        ejecutar_analisis(incorrecto,entrada,tmp_path/"incorrecto")


def test_preparacion_reutiliza_conteo_real_sin_exigir_cola_ideal_del_fir(tmp_path):
    origen={"sha256":"entrada","muestras":3001}
    potencia=tmp_path/"potencia.f32"
    potencia.write_bytes(bytes(9998*4))
    datos={"origen":origen,"muestras_potencia":9998,"mensajes":[{"muestra_8msps":8000}]}
    assert preparacion_valida(datos,origen,potencia)
    potencia.write_bytes(bytes(9997*4))
    assert not preparacion_valida(datos,origen,potencia)

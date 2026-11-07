"""Instala los bloques Python CBS33M en el mismo entorno que ejecuta GNU Radio.

No requiere CMake para este módulo Python. Ejecutar con el Python de Radioconda,
no con el entorno .venv usado para MkDocs. --comprobar no modifica archivos.
"""

import argparse
import importlib
import importlib.util
from pathlib import Path
import shutil
import sys

import yaml


MODULO = Path(__file__).resolve().parent
BLOQUES = {
    "cu8_a_c64": (1, 8, 0.5, "byte"),
    "rotador_frecuencia": (8, 8, 1.0, "complex"),
}


def bloques_presentes():
    """Permite instalar el conversor antes de crear el rotador en la clase."""
    presentes = []
    for nombre in BLOQUES:
        fuente = MODULO / f"python/cbs33m/{nombre}.py"
        descripcion = MODULO / f"grc/cbs33m_{nombre}.block.yml"
        if fuente.is_file() != descripcion.is_file():
            raise RuntimeError(f"{nombre}: hacen falta tanto el Python como su .block.yml")
        if fuente.is_file():
            presentes.append(nombre)
    if not presentes:
        raise RuntimeError("Todavía no hay bloques. Completa primero el conversor de la sección 4.")
    return presentes


def rutas_instalacion(nombres):
    try:
        import gnuradio
        from gnuradio import gr
    except ImportError as error:
        raise RuntimeError(
            "Este Python no importa GNU Radio. Ejecuta instalar.py con el Python de Radioconda."
        ) from error
    prefijo_python = Path(sys.prefix).resolve()
    paquete = Path(gnuradio.__file__).resolve().parent
    prefijo_gr = Path(gr.prefix()).resolve()
    if not paquete.is_relative_to(prefijo_python) or not prefijo_gr.is_relative_to(prefijo_python):
        raise RuntimeError(
            f"GNU Radio está fuera del entorno Python {prefijo_python}. "
            "Usa directamente el Python de Radioconda, sin activar .venv."
        )
    archivos = [(MODULO / "python/cbs33m" / nombre, paquete / "cbs33m" / nombre)
                for nombre in ["__init__.py", *(f"{n}.py" for n in nombres)]]
    archivos += [(MODULO / "grc" / nombre, prefijo_gr / "share/gnuradio/grc/blocks" / nombre)
                 for nombre in (f"cbs33m_{n}.block.yml" for n in nombres)]
    archivos.append((MODULO / "MANIFEST.yml", prefijo_gr / "share/gnuradio/manifests/cbs33m/MANIFEST.yml"))
    return archivos


def comprobar_bloques(paquete, nombres):
    for nombre in nombres:
        bloque = getattr(paquete, nombre)()
        entrada, salida, tasa, _ = BLOQUES[nombre]
        if (bloque.relative_rate() != tasa
                or bloque.input_signature().sizeof_stream_item(0) != entrada
                or bloque.output_signature().sizeof_stream_item(0) != salida):
            raise RuntimeError(f"{nombre}: los puertos o la relación de procesamiento son incorrectos")
        if nombre == "rotador_frecuencia" and not callable(bloque.set_frecuencia_mezcla):
            raise RuntimeError("El rotador debe definir set_frecuencia_mezcla")


def comprobar_fuentes(archivos, nombres):
    """Rechaza plantillas pendientes antes de tocar una instalación que funciona."""
    for origen, _ in archivos:
        contenido = origen.read_bytes()
        if origen.suffix == ".py":
            compile(contenido, str(origen), "exec")
    for nombre in nombres:
        descripcion = MODULO / f"grc/cbs33m_{nombre}.block.yml"
        datos = yaml.safe_load(descripcion.read_text())
        if (not isinstance(datos, dict) or datos.get("id") != f"cbs33m_{nombre}"
                or datos.get("inputs", [{}])[0].get("dtype") != BLOQUES[nombre][3]
                or datos.get("outputs", [{}])[0].get("dtype") != "complex"):
            raise RuntimeError(f"Completa la descripción de GRC: {descripcion}")
    inicializador = MODULO / "python/cbs33m/__init__.py"
    nombre_temporal = "_cbs33m_preinstalacion"
    spec = importlib.util.spec_from_file_location(nombre_temporal, inicializador)
    paquete = importlib.util.module_from_spec(spec)
    sys.modules[nombre_temporal] = paquete
    sin_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(paquete)
        comprobar_bloques(paquete, nombres)
    finally:
        sys.dont_write_bytecode = sin_bytecode
        for nombre in list(sys.modules):
            if nombre == nombre_temporal or nombre.startswith(nombre_temporal + "."):
                del sys.modules[nombre]


def comprobar(archivos, nombres):
    problemas = []
    for origen, destino in archivos:
        if not destino.is_file():
            problemas.append(f"Falta: {destino}")
        elif destino.read_bytes() != origen.read_bytes():
            problemas.append(f"Versión distinta a la del repositorio: {destino}")
    if not problemas:
        importlib.invalidate_caches()
        from gnuradio import cbs33m
        if Path(cbs33m.__file__).resolve() != archivos[0][1].resolve():
            raise RuntimeError(f"Otro paquete oculta la instalación: {cbs33m.__file__}")
        comprobar_bloques(cbs33m, nombres)
        print(f"Paquete Python: {cbs33m.__file__}")
    for problema in problemas:
        print(problema, file=sys.stderr)
    return not problemas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comprobar", action="store_true", help="Comprobar la instalación sin modificarla")
    argumentos = parser.parse_args()
    try:
        nombres = bloques_presentes()
        archivos = rutas_instalacion(nombres)
        comprobar_fuentes(archivos, nombres)
        if not argumentos.comprobar:
            for origen, destino in archivos:
                if destino.is_file() and destino.read_bytes() == origen.read_bytes():
                    continue
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origen, destino)
                # Eliminar solo la caché generada de los archivos reemplazados.
                if destino.suffix == ".py":
                    Path(importlib.util.cache_from_source(str(destino))).unlink(missing_ok=True)
                print(f"Instalado: {destino}")
        if not comprobar(archivos, nombres):
            print("Ejecuta este programa sin --comprobar para instalar o actualizar los bloques.", file=sys.stderr)
            return 1
    except (ImportError, OSError, RuntimeError, SyntaxError, AttributeError,
            ValueError, TypeError, IndexError, yaml.YAMLError) as error:
        print(f"No se pudo preparar CBS33M: {error}", file=sys.stderr)
        return 1
    print(f"CBS33M listo: {', '.join(nombres)}. Reinicia GRC para actualizar su biblioteca.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

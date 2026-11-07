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


MODULO = Path(__file__).resolve().parent
PYTHON_ARCHIVOS = ("__init__.py", "cu8_a_c64.py", "rotador_frecuencia.py")
GRC_ARCHIVOS = ("cbs33m_cu8_a_c64.block.yml", "cbs33m_rotador_frecuencia.block.yml")


def rutas_instalacion():
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
                for nombre in PYTHON_ARCHIVOS]
    archivos += [(MODULO / "grc" / nombre, prefijo_gr / "share/gnuradio/grc/blocks" / nombre)
                 for nombre in GRC_ARCHIVOS]
    archivos.append((MODULO / "MANIFEST.yml", prefijo_gr / "share/gnuradio/manifests/cbs33m/MANIFEST.yml"))
    return archivos


def comprobar(archivos):
    problemas = []
    for origen, destino in archivos:
        if not destino.is_file():
            problemas.append(f"Falta: {destino}")
        elif destino.read_bytes() != origen.read_bytes():
            problemas.append(f"Versión distinta a la del repositorio: {destino}")
    if not problemas:
        importlib.invalidate_caches()
        from gnuradio import cbs33m
        conversor = cbs33m.cu8_a_c64()
        rotador = cbs33m.rotador_frecuencia()
        if (conversor.relative_rate() != 0.5
                or conversor.input_signature().sizeof_stream_item(0) != 1
                or conversor.output_signature().sizeof_stream_item(0) != 8
                or not callable(rotador.set_frecuencia_mezcla)):
            problemas.append("Los bloques importados no tienen los puertos o callbacks esperados")
        print(f"Paquete Python: {cbs33m.__file__}")
    for problema in problemas:
        print(problema, file=sys.stderr)
    return not problemas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comprobar", action="store_true", help="Comprobar la instalación sin modificarla")
    argumentos = parser.parse_args()
    try:
        archivos = rutas_instalacion()
        if not argumentos.comprobar:
            # Detectar fuentes incompletas antes de modificar la instalación.
            for origen, _ in archivos:
                contenido = origen.read_bytes()
                if origen.suffix == ".py":
                    compile(contenido, str(origen), "exec")
            for origen, destino in archivos:
                if destino.is_file() and destino.read_bytes() == origen.read_bytes():
                    continue
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origen, destino)
                # Eliminar solo la caché generada de los archivos reemplazados.
                if destino.suffix == ".py":
                    Path(importlib.util.cache_from_source(str(destino))).unlink(missing_ok=True)
                print(f"Instalado: {destino}")
        if not comprobar(archivos):
            print("Ejecuta este programa sin --comprobar para instalar o actualizar los bloques.", file=sys.stderr)
            return 1
    except (ImportError, OSError, RuntimeError, SyntaxError) as error:
        print(f"No se pudo preparar CBS33M: {error}", file=sys.stderr)
        return 1
    print("CBS33M listo. En GRC, pulsa Reload Blocks en la barra de herramientas o reinicia GRC.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Los laboratorios mantienen su número en el menú, el título y el índice."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("numero,carpeta,archivo", [
    (1, "01-introduccion-sdr", "laboratorio-muestreo.md"),
    (2, "02-tiempo-frecuencia-iq", "laboratorio-receptor-fm.md"),
])
def test_laboratorio_numerado_en_navegacion_y_documentos(numero, carpeta, archivo):
    # BaseLoader lee las etiquetas sin ejecutar los tags de las extensiones.
    config = yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    sesiones = next(entrada["Sesiones"] for entrada in config["nav"] if "Sesiones" in entrada)
    seccion = next(entrada for entrada in sesiones if isinstance(entrada, dict) and next(iter(entrada)).startswith(f"{numero:02d} —"))
    paginas = next(iter(seccion.values()))
    ruta = f"sessions/{carpeta}/{archivo}"
    etiqueta = next(titulo for pagina in paginas if isinstance(pagina, dict) for titulo, destino in pagina.items() if destino == ruta)
    assert etiqueta.startswith(f"Laboratorio #{numero}:")
    assert (ROOT / "docs" / ruta).is_file()

    laboratorio = (ROOT / "docs" / ruta).read_text(encoding="utf-8")
    metadatos = yaml.safe_load(laboratorio.split("---", 2)[1])
    prefijo = f"Laboratorio #{numero} — "
    assert metadatos["title"].startswith(prefijo)
    assert any(linea.startswith(f"# {prefijo}") for linea in laboratorio.splitlines())

    sesion = (ROOT / "docs/sessions" / carpeta / "index.md").read_text(encoding="utf-8")
    assert any(linea.startswith(f"## {prefijo}") for linea in sesion.splitlines())

"""Descarga el prefijo real ADS-B identificado en origen.json y verifica sus hashes."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.descargar_capturas_rf import archive_prefix, save_checked, wav_iq

CARPETA = ROOT / "gnuradio/samples/adsb-posiciones"


def main():
    config = json.loads((CARPETA / "origen.json").read_text())
    archivo = CARPETA / config["archivo"]
    save_checked(archivo, config["sha256"], lambda: wav_iq(
        archive_prefix(config["descarga"]), config["fs"], config["fc"]))
    meta = {"global": {"core:datatype": config["formato"], "core:sample_rate": config["fs"],
                       "core:version": "1.0.0", "core:dataset": config["archivo"],
                       "core:description": config["nota"], "core:recorder": config["fuente"]},
            "captures": [{"core:sample_start": 0, "core:frequency": config["fc"]}], "annotations": []}
    archivo.with_suffix(".sigmf-meta").write_text(json.dumps(meta, ensure_ascii=False, indent=2)+"\n")
    print(f"Muestra lista: {config['muestras']} muestras; {config['duracion_archivo_s']:.6f} s de archivo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

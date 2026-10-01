"""La reorganización no debe exponer documentos personales ni PDFs locales."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_protege_archivos_locales_sin_ocultar_los_flowgraphs(tmp_path):
    # Un repo temporal evita depender del índice o las exclusiones del usuario.
    subprocess.run(["git", "init", "--quiet", "--template=", str(tmp_path)], check=True, capture_output=True, text=True)
    (tmp_path / ".gitignore").write_text((ROOT / ".gitignore").read_text(encoding="utf-8"), encoding="utf-8")
    excluidos = {
        "burocracia/documentos-contratacion/documento-personal.pdf",
        "burocracia/notas.md",
        "sdr-reference-courses/SDR4Engineers.pdf",
        "sdr-reference-courses/sdr-course/Lesson_1/referencia.pdf",
        "referencia/libro.pdf",
        "backups/sesion-anterior.md",
        "samples/grabacion.cu8",
        "gnuradio-flowgraphs/generado.py",
    }
    publicables = {
        "sdr-reference-courses/sdr-course/Lesson_1/ejercicio.grc",
        "sdr-reference-courses/sdr-course/Project/in.txt",
        "gnuradio-flowgraphs/test2.grc",
        "docs/sessions/01-introduccion-sdr/index.md",
    }
    resultado = subprocess.run(["git", "-C", str(tmp_path), "-c", "core.excludesFile=/dev/null", "check-ignore", "--no-index", "--stdin"], input="\n".join(sorted(excluidos | publicables)) + "\n", capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stderr
    assert set(resultado.stdout.splitlines()) == excluidos

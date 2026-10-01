"""Las referencias se publican sin exponer el contexto ni los archivos personales."""

from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_protege_archivos_locales_sin_ocultar_las_referencias(tmp_path):
    # Un repo temporal evita depender del índice o las exclusiones del usuario.
    subprocess.run(["git", "init", "--quiet", "--template=", str(tmp_path)], check=True, capture_output=True, text=True)
    (tmp_path / ".gitignore").write_text((ROOT / ".gitignore").read_text(encoding="utf-8"), encoding="utf-8")
    excluidos = {
        "burocracia/documentos-contratacion/documento-personal.pdf",
        "burocracia/notas.md",
        "referencia/libro.pdf",
        "backups/sesion-anterior.md",
        "samples/grabacion.cu8",
        "gnuradio-flowgraphs/generado.py",
        "AGENTS.md",
        ".planning/HANDOFF.json",
        ".planning/fase-nueva/PLAN.md",
        ".git-context-local/config",
        ".git-context-local/objects/archivo",
    }
    publicables = {
        "sdr-reference-courses/SDR4Engineers.pdf",
        "sdr-reference-courses/Network_GPRS_Prototype_based_on_SDR_and_OpenBTS_as_an_IoT-lab_Testbed.pdf",
        "sdr-reference-courses/sdr-course/README.pdf",
        "sdr-reference-courses/sdr-course/Lesson_1/referencia.pdf",
        "sdr-reference-courses/sdr-course/Lesson_1/ejercicio.grc",
        "sdr-reference-courses/sdr-course/Project/in.txt",
        "gnuradio-flowgraphs/test2.grc",
        "docs/sessions/01-introduccion-sdr/index.md",
    }
    publicables.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "sdr-reference-courses").rglob("*.pdf"))
    resultado = subprocess.run(["git", "-C", str(tmp_path), "-c", "core.excludesFile=/dev/null", "check-ignore", "--no-index", "--stdin"], input="\n".join(sorted(excluidos | publicables)) + "\n", capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stderr
    assert set(resultado.stdout.splitlines()) == excluidos


def test_el_contexto_interno_no_esta_en_el_indice_del_repositorio_publico():
    if not (ROOT / ".git").exists():
        pytest.skip("La copia no tiene el índice Git del repositorio público")
    resultado = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", "AGENTS.md", ".planning", ".git-context-local"], capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stderr
    assert not resultado.stdout, f"Archivos internos incluidos en el índice público:\n{resultado.stdout}"

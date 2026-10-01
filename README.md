# Radio Definida por Software

Curso de pregrado de acceso abierto sobre radio definida por software (SDR) — de las señales IQ y GNU Radio a la recepción y transmisión de sistemas reales.

**Sitio web**: [ollerenac-uni.github.io/sdr](https://ollerenac-uni.github.io/sdr/)
**Licencia**: [![CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## Estructura del repositorio

```
docs/
├── index.md              # Portada: presentación y temas del curso
├── sessions/
│   ├── index.md          # Índice de sesiones
│   └── NN-tema/          # Una carpeta por sesión
│       ├── index.md      # Apuntes de teoría + ejercicios
│       ├── lab.ipynb     # Laboratorio (Colab / GNU Radio)
│       └── figures/      # Figuras PNG
└── exams/
    └── index.md          # Evaluaciones
```

Cada sesión nueva se añade al `nav` de `mkdocs.yml` bajo `Sesiones`.

Los flowgraphs del curso están en `gnuradio-flowgraphs/`. Los laboratorios de
referencia se organizan en `sdr-reference-courses/sdr-course/`; sus `.grc` y los
archivos de texto auxiliares se versionan, pero sus PDFs permanecen locales.

[`test2.grc`](gnuradio-flowgraphs/test2.grc) conserva la solución del laboratorio
sin hardware. [`visualizador_usrp.grc`](gnuradio-flowgraphs/visualizador_usrp.grc)
es la variante independiente para un USRP; no sustituye esa solución.

`backups/`, `burocracia/` y las grabaciones I/Q son archivos locales excluidos de
Git. En particular, `burocracia/` contiene documentos personales de contratación
que no deben publicarse. El sitio web se genera desde `docs/`, no desde estas carpetas.

`AGENTS.md` y `.planning/` son archivos internos de trabajo. Conservan un historial
Git separado, solo en la computadora de trabajo, y no se incluyen en los nuevos
commits del repositorio público.

---

## Uso local

```bash
git clone https://github.com/ollerenac-uni/sdr.git
cd sdr
pip install -r requirements.txt
mkdocs serve    # vista previa en http://127.0.0.1:8000
```

El sitio se publica automáticamente en GitHub Pages con cada push a `main` (ver `.github/workflows/deploy.yml`).

---

## Licencia y atribución

Todo el contenido se publica bajo [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

> *Radio Definida por Software* por ollerenac-uni
> https://github.com/ollerenac-uni/sdr
> Licencia CC BY 4.0

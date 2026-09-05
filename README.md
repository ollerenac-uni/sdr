# Radio Definida por Software

Curso de pregrado de acceso abierto sobre radio definida por software (SDR) — de las señales IQ y GNU Radio a la recepción y transmisión de sistemas reales.

**Sitio web**: [ollerenac.github.io/sdr](https://ollerenac.github.io/sdr/)
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

---

## Uso local

```bash
git clone https://github.com/ollerenac/sdr.git
cd sdr
pip install -r requirements.txt
mkdocs serve    # vista previa en http://127.0.0.1:8000
```

El sitio se publica automáticamente en GitHub Pages con cada push a `main` (ver `.github/workflows/deploy.yml`).

---

## Licencia y atribución

Todo el contenido se publica bajo [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

> *Radio Definida por Software* por ollerenac
> https://github.com/ollerenac/sdr
> Licencia CC BY 4.0

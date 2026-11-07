# Respaldo anterior a la promoción de fm.grc

Se conservaron copias exactas de ambos archivos el 7 de noviembre de 2026.
`manifest.json` contiene sus hashes SHA-256.

| Archivo de respaldo | Contenido |
|---|---|
| `fm.grc.bak` | Receptor con `Python Snippet` e indicador de estado. |
| `fm_sin_snippet.grc.bak` | Variante probada sin `Python Snippet`, antes de cambiar su ID y nombre. |

La variante sin snippet pasó a `gnuradio/flowgraphs/fm.grc`, con `Options.ID = fm`.
La extensión `.bak` evita que los respaldos se confundan con los flowgraphs activos.
Para recuperar una versión, se copia el respaldo a un archivo `.grc`.
Si se conservan varios grafos activos, cada uno debe tener un `Options.ID` distinto.

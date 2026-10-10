#!/usr/bin/env python3
"""Imprime la fuente reproducible del Mermaid de síntesis, sin generar un PNG."""


def generar():
    return '''flowchart TD
    A["Archivo CU8: pares I/Q"] --> B["Decodificar muestras complejas"]
    B --> C["Bloques de N muestras"]
    C --> D["Ventana y FFT"]
    D --> E["Magnitud al cuadrado"]
    E --> F["Promedio de potencia lineal y dB"]
    F --> G["Espectro o waterfall"]
    H["Metadatos: sampling rate y frecuencia central"] -.-> C
    H -.-> G
    B --> I["Seleccionar canal: filtrar y reducir tasa"]
    I --> J["Medir giro entre muestras"]
    J --> K["Filtrar audio, decimar y aplicar de-emphasis"]
    K --> L["Audio mono"]
    M["S04: centrar primero si el canal no está en cero"] -.-> I'''


if __name__ == "__main__":
    print(generar())

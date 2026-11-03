# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
from gnuradio import gr


class rotador_frecuencia(gr.sync_block):
    """Traslada el espectro con un oscilador complejo continuo."""

    def __init__(self, frecuencia_mezcla=0.0, samp_rate=2.4e6):
        gr.sync_block.__init__(
            self,
            name='Rotador I/Q propio',
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )

        self.frecuencia_mezcla = float(frecuencia_mezcla)
        self.samp_rate = float(samp_rate)
        if not np.isfinite(self.frecuencia_mezcla):
            raise ValueError('frecuencia_mezcla debe ser finita')
        if not np.isfinite(self.samp_rate) or self.samp_rate <= 0:
            raise ValueError('samp_rate debe ser positiva y finita')

        # Fase del oscilador para la próxima muestra que procesaremos.
        self.fase = 0.0

    def set_frecuencia_mezcla(self, frecuencia_mezcla):
        valor = float(frecuencia_mezcla)
        if not np.isfinite(valor):
            raise ValueError('frecuencia_mezcla debe ser finita')
        self.frecuencia_mezcla = valor

    def work(self, input_items, output_items):
        # 1. Un complejo de salida por cada complejo de entrada.
        n = len(output_items[0])

        # 2. Avance angular del oscilador por muestra.
        incremento = 2 * np.pi * self.frecuencia_mezcla / self.samp_rate

        # 3. Ángulos de este lote, empezando en la fase conservada.
        indices = np.arange(n, dtype=np.float64)
        fases = self.fase + incremento * indices

        # 4. Multiplicar cada muestra por su oscilador correspondiente.
        oscilador = np.exp(1j * fases)
        output_items[0][:n] = input_items[0][:n] * oscilador

        # 5. Guardar la fase de la siguiente muestra, sin vueltas enteras.
        self.fase = (self.fase + incremento * n) % (2 * np.pi)

        return n

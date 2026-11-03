# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
from gnuradio import gr


class cu8_a_c64(gr.decim_block):
    """Convierte bytes I/Q intercalados a complejos normalizados."""

    def __init__(self, escala=127.5):
        gr.decim_block.__init__(
            self,
            name='Conversor de .cu8 a .c64',
            in_sig=[np.uint8],
            out_sig=[np.complex64],
            decim=2
        )
        self.escala = float(escala)
        if not np.isfinite(self.escala) or self.escala <= 0:
            raise ValueError('escala debe ser un número positivo y finito')

    def work(self, input_items, output_items):
        n = len(output_items[0])
        datos = input_items[0][:2*n]

        i = datos[0::2].astype(np.float32)
        q = datos[1::2].astype(np.float32)

        i = (i - self.escala) / self.escala
        q = (q - self.escala) / self.escala

        output_items[0][:n] = i + 1j*q
        return n

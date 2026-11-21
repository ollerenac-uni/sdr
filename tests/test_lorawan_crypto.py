"""Vectores independientes y rechazo de tramas no autenticadas de LoRaWAN."""

import unittest

try:
    import cryptography  # noqa: F401
except ImportError:
    raise unittest.SkipTest("La verificación criptográfica requiere cryptography")

from scripts.sesion08_lora import verificar_lorawan_brno as modulo


class TestLoRaWANCrypto(unittest.TestCase):
    def test_aes_cmac_rfc4493(self):
        clave = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        self.assertEqual(modulo.cmac128(clave, b"").hex(), "bb1d6929e95937287fa37d129b756746")
        datos = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
        self.assertEqual(modulo.cmac128(clave, datos).hex(), "070a16b46b4d4144f79bdd9dd04a287c")

    def test_vector_lorawan_publicado(self):
        # Ejemplo publicado en nunomcruz/lora-packet-python, README y demo.py.
        frame = bytes.fromhex("40f17dbe4900020001954378762b11ff0d")
        nwk = bytes.fromhex("44024241ed4ce9a68c6a8bc055233fd3")
        app = bytes.fromhex("ec925802ae430ca77fd3dd73cb2cc588")
        resultado = modulo.descifrar_datos(frame, nwk, app)
        self.assertTrue(resultado["mic_valido"])
        self.assertEqual(resultado["frmpayload_claro_ascii"], "test")
        self.assertEqual(resultado["devaddr"], "49be7df1")
        self.assertEqual(resultado["fcnt32"], 2)

    def test_clave_incorrecta_y_alteracion_no_entregan_texto_claro(self):
        frame = bytes.fromhex("40f17dbe4900020001954378762b11ff0d")
        nwk = bytes.fromhex("44024241ed4ce9a68c6a8bc055233fd3")
        app = bytes.fromhex("ec925802ae430ca77fd3dd73cb2cc588")
        alterado = bytearray(frame)
        alterado[9] ^= 1
        for trama, clave in ((frame, bytes(16)), (bytes(alterado), nwk)):
            with self.subTest(trama=trama.hex(), clave=clave.hex()):
                resultado = modulo.descifrar_datos(trama, clave, app)
                self.assertFalse(resultado["mic_valido"])
                self.assertNotIn("frmpayload_claro_hex", resultado)

    def test_trama_truncada_rechazada(self):
        for frame in (b"", b"\x40", b"\x40" * 11):
            with self.subTest(longitud=len(frame)), self.assertRaises(ValueError):
                modulo.descifrar_datos(frame, bytes(16), bytes(16))

    def test_pcap_real_conserva_resultados_y_otaa(self):
        archivo = modulo.CARPETA / "03_Brno_join.pcap"
        if not archivo.is_file():
            self.skipTest("El PCAP de Brno se descarga por separado")
        resultado = modulo.verificar(archivo, modulo.CARPETA)
        self.assertEqual(resultado["conteos"], {
            "paquetes_pcap": 31605, "recepciones_del_devaddr": 857,
            "mic_valido": 809, "estructura_no_admitida": 15,
            "recepciones_aplicacion_descifradas": 386, "mic_invalido": 33,
        })
        self.assertEqual(resultado["tramas_mic_valido_unicas"], 471)
        self.assertEqual(resultado["tramas_aplicacion_unicas"], 246)
        self.assertEqual({p["frmpayload_claro_ascii"]: p["recepciones"]
                          for p in resultado["payloads_aplicacion"]},
                         {"timeout": 288, "test message": 98})
        self.assertTrue(all(resultado["controles"].values()))
        self.assertTrue(any(i["coinciden_con_claves_publicadas"]
                            for i in resultado["incorporaciones_otaa_verificadas"]))

"""Comprueba tramas de datos LoRaWAN 1.0.x y descifra su FRMPayload.

Recibe PHYPayload en hexadecimal, sin cabecera ni CRC de LoRa PHY. No demodula
I/Q, no implementa OTAA y no valida LoRaWAN 1.1 ni protección contra replay.
Si no se proporciona FCnt de 32 bits, supone cero en sus 16 bits superiores.
El MIC autentica con NwkSKey; no comprueba que AppSKey sea la clave correcta.

Referencia: TS001-1.0.4, secciones 4.3 y 4.4:
https://resources.lora-alliance.org/technical-specifications/ts001-1-0-4-lorawan-l2-1-0-4-specification
"""

import argparse
import hmac
import json
from pathlib import Path

from cryptography.hazmat.primitives.cmac import CMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def analizar_trama(trama, nwk_s_key, app_s_key, fcnt=None):
    """Devuelve campos y MIC; solo descifra cuando el MIC es correcto."""
    if len(nwk_s_key) != 16 or len(app_s_key) != 16:
        raise ValueError("Cada clave debe contener 16 bytes")
    if not 12 <= len(trama) <= 255:
        raise ValueError("Longitud incompatible con una trama de datos LoRaWAN")
    if trama[0] not in (0x40, 0x60, 0x80, 0xA0):
        raise ValueError("Solo se admiten tramas de datos LoRaWAN 1.0.x")
    # MHDR[1], DevAddr[4], FCtrl[1], FCnt[2], FOpts[0..15], ... , MIC[4].
    direccion = (trama[0] >> 5) & 1
    fin_fhdr = 8 + (trama[5] & 0x0F)
    mensaje, mic_recibido = trama[:-4], trama[-4:]
    if fin_fhdr > len(mensaje):
        raise ValueError("FHDR truncado: faltan bytes de FOpts")
    fcnt_16 = int.from_bytes(trama[6:8], "little")
    contador = fcnt_16 if fcnt is None else fcnt
    if not 0 <= contador < 2**32 or contador & 0xFFFF != fcnt_16:
        raise ValueError("FCnt de 32 bits no coincide con el campo recibido")
    fport = mensaje[fin_fhdr] if fin_fhdr < len(mensaje) else None
    cifrado = mensaje[fin_fhdr + 1:] if fport is not None else b""
    if fport is not None and not cifrado:
        raise ValueError("FPort presente sin FRMPayload")
    if fport == 0 and fin_fhdr > 8:
        raise ValueError("FOpts y FRMPayload con FPort=0 no pueden coexistir")

    # Los bloques B0 y Ai usan DevAddr y FCnt en little endian.
    contexto = bytes([direccion]) + trama[1:5] + contador.to_bytes(4, "little")
    b0 = b"\x49" + bytes(4) + contexto + b"\x00" + bytes([len(mensaje)])
    cmac = CMAC(algorithms.AES(nwk_s_key))
    cmac.update(b0 + mensaje)
    mic_calculado = cmac.finalize()[:4]
    mic_valido = hmac.compare_digest(mic_recibido, mic_calculado)
    resultado = {
        "version_asumida": "LoRaWAN 1.0.x",
        "phy_payload_hex": trama.hex(),
        "mtype": trama[0] >> 5,
        "direccion": "downlink" if direccion else "uplink",
        "dev_addr": trama[1:5][::-1].hex(),
        "fcnt_16": fcnt_16,
        "fcnt_32": contador,
        "bits_altos_fcnt_asumidos_cero": fcnt is None,
        "fopts_hex": trama[8:fin_fhdr].hex(),
        "fport": fport,
        "frm_payload_cifrado_hex": cifrado.hex(),
        "mic_recibido": mic_recibido.hex(),
        "mic_calculado": mic_calculado.hex(),
        "mic_valido": mic_valido,
        "payload_descifrado_hex": None,
        "payload_descifrado_utf8": None,
        "tipo_payload": "MAC commands" if fport == 0 else "application" if fport is not None else None,
    }
    if mic_valido and fport is not None:
        clave = nwk_s_key if fport == 0 else app_s_key
        aes = Cipher(algorithms.AES(clave), modes.ECB()).encryptor()
        flujo = b"".join(
            aes.update(b"\x01" + bytes(4) + contexto + b"\x00" + bytes([i]))
            for i in range(1, (len(cifrado) + 15) // 16 + 1)
        ) + aes.finalize()
        texto = bytes(a ^ b for a, b in zip(cifrado, flujo))
        resultado["payload_descifrado_hex"] = texto.hex()
        try:
            resultado["payload_descifrado_utf8"] = texto.decode("utf-8")
        except UnicodeDecodeError:
            pass  # Un FRMPayload binario válido no tiene que ser texto UTF-8.
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trama_hex", help="PHYPayload LoRaWAN, sin cabecera ni CRC de LoRa PHY")
    parser.add_argument("--nwk-s-key", required=True, help="NwkSKey en hexadecimal")
    parser.add_argument("--app-s-key", required=True, help="AppSKey en hexadecimal")
    parser.add_argument("--fcnt", type=lambda x: int(x, 0), help="Contador completo de 32 bits")
    parser.add_argument("--salida", type=Path, help="Guardar el informe JSON")
    args = parser.parse_args()
    try:
        resultado = analizar_trama(
            bytes.fromhex(args.trama_hex), bytes.fromhex(args.nwk_s_key),
            bytes.fromhex(args.app_s_key), args.fcnt,
        )
    except ValueError as error:
        parser.error(str(error))
    texto = json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto, encoding="utf-8")
    print(texto, end="")
    return 0 if resultado["mic_valido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

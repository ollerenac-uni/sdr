"""CRC físico de LoRa, compartido por el inspector I/Q y la simulación de replay."""


def pasos_crc(payload):
    """Estados del CRC-16 por byte, antes del XOR final de la convención LoRa."""
    if len(payload) < 2:
        raise ValueError("Este cálculo de CRC LoRa requiere al menos dos bytes")
    crc, pasos = 0, []
    for numero, byte in enumerate(payload[:-2], 1):
        antes = crc
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1) & 0xffff
        pasos.append({"numero": numero, "byte": byte, "antes": antes, "despues": crc})
    return pasos


def crc_lora(payload):
    """Devuelve CRC sobre N-2 bytes y resultado tras XOR con los dos últimos."""
    pasos = pasos_crc(payload)
    crc = pasos[-1]["despues"] if pasos else 0
    return crc, crc ^ (payload[-2] << 8) ^ payload[-1]

"""Compara dos políticas de Network Server ante un replay de datos LoRaWAN 1.0.4.

Simulación local sobre bytes: genera dos lecturas didácticas y repite la primera
sin modificarla. Usa las claves públicas del nodo experimental de Brno, pero
estas dos lecturas no proceden de su captura. No necesita I/Q ni transmite RF.

La clase Receptor agrupa el CRC del gateway, la verificación de MIC y FCnt del
Network Server y el descifrado/estado del Application Server. La diferencia
vulnerable/con FCnt está en el Network Server, no en el gateway ni el cifrado.
Solo estudia una sesión, uplinks con FPort=1 y FCnt entre 0 y 65535 (parte alta
cero). No implementa OTAA, reconstrucción del contador tras rollover, ACK,
NbTrans ni persistencia. Rechazar aquí significa no entregar a la aplicación;
las retransmisiones legítimas pueden requerir otras acciones en una red real.
"""

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path

if __package__:
    from .crc_lora import crc_lora
    from .lora_presentacion import tabla
    from .verificar_lorawan import aes128, analizar_trama, cmac128
else:
    from crc_lora import crc_lora
    from lora_presentacion import tabla
    from verificar_lorawan import aes128, analizar_trama, cmac128


# Material público de prueba; no se obtiene ninguna clave de la señal capturada.
NWK = bytes.fromhex("e2898779a03de59e2317b149abf00238")
APP = bytes.fromhex("59ca1ac91922887093bc7b236bd1b07f")
DEVADDR = bytes.fromhex("dc5de601")  # Orden de transmisión, little endian.


def crear_uplink(datos, contador):
    """Emisor legítimo didáctico: cifra con AppSKey y calcula MIC con NwkSKey."""
    if not 0 <= contador <= 65535:
        raise ValueError("El modelo limita FCnt a 0..65535; sus 16 bits altos son cero")
    if not 1 <= len(datos) <= 242:
        raise ValueError("Se requiere un contenido de 1..242 bytes")
    contexto = b"\x00" + DEVADDR + contador.to_bytes(4, "little")
    bloques = b"".join(
        b"\x01" + bytes(4) + contexto + b"\x00" + bytes([i])
        for i in range(1, (len(datos) + 15) // 16 + 1)
    )
    flujo = aes128(APP, bloques)
    cifrado = bytes(a ^ b for a, b in zip(datos, flujo))
    # MHDR=80, FCtrl=90, sin FOpts, FPort=1; mismo formato que la Figura 6.
    mensaje = b"\x80" + DEVADDR + b"\x90" + contador.to_bytes(2, "little") + b"\x01" + cifrado
    b0 = b"\x49" + bytes(4) + contexto + b"\x00" + bytes([len(mensaje)])
    return mensaje + cmac128(NWK, b0 + mensaje)[:4]


@dataclass(frozen=True)
class Paquete:
    phypayload: bytes
    crc_recibido: int


def empaquetar(trama):
    """Emula el CRC que añadiría el transmisor LoRa; no modula la señal."""
    return Paquete(bytes(trama), crc_lora(trama)[1])


def reproducir(paquete):
    """Acción del atacante: copia los bytes y el CRC; no recibe ninguna clave."""
    return Paquete(paquete.phypayload, paquete.crc_recibido)


@dataclass
class Receptor:
    verificar_fcnt: bool
    ultimos: dict = field(default_factory=dict)
    ultimo_dato: str | None = None
    entregas: list = field(default_factory=list)

    def recibir(self, paquete):
        trama = paquete.phypayload
        resultado = {
            "fcnt": None, "crc_valido": False, "mic_valido": None,
            "ultimo_fcnt_antes": None, "ultimo_fcnt_despues": None,
            "entregado": False, "motivo": "CRC_INVALIDO",
            "dato_entregado": None, "estado_aplicacion": self.ultimo_dato,
        }
        if len(trama) < 12:
            resultado["motivo"] = "TRAMA_TRUNCADA"
            return resultado
        resultado["crc_valido"] = crc_lora(trama)[1] == paquete.crc_recibido
        if not resultado["crc_valido"]:
            return resultado
        if trama[0] != 0x80 or trama[5] != 0x90 or trama[8] != 1:
            raise ValueError("El receptor didáctico admite MHDR=80, FCtrl=90 y FPort=1")
        contador = int.from_bytes(trama[6:8], "little")
        # Cada instancia representa una sesión; el estado se separa por dispositivo/sentido.
        clave_estado = (trama[1:5], "uplink")
        anterior = self.ultimos.get(clave_estado)
        resultado.update(fcnt=contador, ultimo_fcnt_antes=anterior,
                         ultimo_fcnt_despues=anterior)
        mac = analizar_trama(trama, NWK, APP, contador)
        resultado["mic_valido"] = mac["mic_valido"]
        if not mac["mic_valido"]:
            resultado["motivo"] = "MIC_INVALIDO"
            return resultado
        if self.verificar_fcnt and anterior is not None and contador <= anterior:
            resultado["motivo"] = "FCNT_ANTIGUO_O_REPETIDO"
            return resultado
        # Un paquete rechazado nunca modifica el contador ni el estado de la aplicación.
        if self.verificar_fcnt:
            self.ultimos[clave_estado] = contador
            resultado["ultimo_fcnt_despues"] = contador
        self.ultimo_dato = mac["payload_descifrado_utf8"]
        self.entregas.append({"fcnt": contador, "dato": self.ultimo_dato})
        resultado.update(entregado=True, motivo="ENTREGADO", dato_entregado=self.ultimo_dato,
                         estado_aplicacion=self.ultimo_dato)
        return resultado


def ejecutar_experimento():
    normal = empaquetar(crear_uplink(b"temp=25", 4))
    alarma = empaquetar(crear_uplink(b"temp=80", 5))
    replay = reproducir(normal)
    paquetes = [("A_normal", normal), ("B_alarma", alarma), ("A_replay", replay)]
    receptores = {"vulnerable": Receptor(False), "con_fcnt": Receptor(True)}
    eventos = []
    for nombre, paquete in paquetes:
        eventos.append({"entrada": nombre, **{
            tipo: receptor.recibir(paquete) for tipo, receptor in receptores.items()
        }})

    # Ambos controles recalculan solo el CRC y conservan el MIC original.
    alterada = bytearray(normal.phypayload)
    alterada[9] ^= 1
    contador_falso = bytearray(normal.phypayload)
    contador_falso[6:8] = (6).to_bytes(2, "little")
    controles = []
    for nombre, trama in (("Contenido alterado", alterada), ("FCnt cambiado de 4 a 6", contador_falso)):
        paquete = empaquetar(trama)
        controles.append({"entrada": nombre, "phypayload_hex": paquete.phypayload.hex(), **{
            tipo: receptor.recibir(paquete) for tipo, receptor in receptores.items()
        }})

    tramas = []
    for nombre, paquete in paquetes:
        mac = analizar_trama(paquete.phypayload, NWK, APP)
        tramas.append({"nombre": nombre, "phypayload_hex": paquete.phypayload.hex(),
                       "longitud_bytes": len(paquete.phypayload), "fcnt": mac["fcnt_32"],
                       "dato": mac["payload_descifrado_utf8"], "mic_hex": mac["mic_recibido"],
                       "crc_hex_le": paquete.crc_recibido.to_bytes(2, "little").hex()})
    resumen = {tipo: {"entregas": receptor.entregas, "ultimo_dato": receptor.ultimo_dato}
               for tipo, receptor in receptores.items()}
    comprobaciones = {
        "replay_es_copia_exacta": normal == replay,
        "crc_y_mic_validos_en_las_tres_entradas": all(
            e[t]["crc_valido"] and e[t]["mic_valido"] for e in eventos for t in receptores),
        "vulnerable_entrega_el_replay": eventos[-1]["vulnerable"]["entregado"],
        "con_fcnt_no_entrega_el_replay": not eventos[-1]["con_fcnt"]["entregado"],
        "alarma_se_conserva_con_fcnt": resumen["con_fcnt"]["ultimo_dato"] == "temp=80",
        "ambos_rechazan_las_alteraciones_por_mic": all(
            e[t]["crc_valido"] and e[t]["motivo"] == "MIC_INVALIDO"
            for e in controles for t in receptores),
    }
    return {"tipo": "simulacion_local_sobre_bytes", "sesion": "didactica_brno",
            "limites": "Una sesión; FCnt 0..65535, parte alta cero; sin RF, OTAA ni ACK/NbTrans.",
            "tramas": tramas, "eventos": eventos, "controles": controles,
            "resumen": resumen, "comprobaciones": comprobaciones,
            "comprobaciones_aprobadas": all(comprobaciones.values())}


def presentar(r, etapa):
    def validacion(valor):
        return "sin verificar" if valor is None else "OK" if valor else "INVALIDO"

    def contador(valor):
        return "vacío" if valor is None else str(valor)

    partes = ["REPLAY LoRaWAN | Simulación local; lecturas didácticas, sin transmisión RF.",
              "Gateway: CRC y reenvío. Network Server: MIC y control de FCnt. "
              "Application Server: descifrado con AppSKey y estado de la lectura."]
    if etapa in ("tramas", "todo"):
        partes += ["[5.2 | EMISOR Y COPIA DEL ATACANTE]", tabla(
            ["Trama", "FCnt", "Dato de aplicación", "MIC (4 bytes)", "CRC (2 bytes, LE)"],
            [(t["nombre"], t["fcnt"], t["dato"], t["mic_hex"], t["crc_hex_le"])
             for t in r["tramas"]])]
        for t in r["tramas"]:
            partes += [t["nombre"] + " | PHYPayload de 20 bytes (CRC fuera de estos bytes)", tabla(
                [f"{i:02d}" for i in range(1, 21)],
                [[f"{b:02x}" for b in bytes.fromhex(t["phypayload_hex"])]])]
        partes.append("A_replay es idéntica a A_normal: conserva contador, contenido cifrado, MIC y CRC.")
    if etapa in ("replay", "todo"):
        partes.append("[5.3 | MISMAS ENTRADAS, DOS POLÍTICAS DE NETWORK SERVER]")
        for tipo, nombre in (("vulnerable", "NETWORK SERVER VULNERABLE: verifica MIC, omite control de FCnt"),
                             ("con_fcnt", "NETWORK SERVER CON FCnt: verifica MIC y contador por sesión/dispositivo")):
            partes += [nombre, tabla(
                ["Entrada", "FCnt", "CRC GW", "MIC NS", "Último FCnt antes -> después", "Decisión NS", "Estado AS"],
                [(e["entrada"], e[tipo]["fcnt"], validacion(e[tipo]["crc_valido"]), validacion(e[tipo]["mic_valido"]),
                  f"{contador(e[tipo]['ultimo_fcnt_antes'])} -> {contador(e[tipo]['ultimo_fcnt_despues'])}" if tipo == "con_fcnt" else "sin control",
                  "ENTREGA" if e[tipo]["entregado"] else "DESCARTA", e[tipo]["estado_aplicacion"])
                 for e in r["eventos"]])]
        partes += [f"RESULTADO: vulnerable = {r['resumen']['vulnerable']['ultimo_dato']} (dato antiguo); "
                   f"con FCnt = {r['resumen']['con_fcnt']['ultimo_dato']} (última lectura nueva).",
                   "GW = gateway; NS = Network Server; AS = Application Server. "
                   "ENTREGA significa que el NS reenvía a la aplicación.",
                   "El MIC prueba autenticidad/integridad; no demuestra por sí solo que la trama sea nueva."]
    if etapa in ("controles", "todo"):
        partes += ["[5.4 | ¿POR QUÉ NO CAMBIAR EL CONTADOR PARA EVITAR EL CONTROL?]", tabla(
            ["Modificación; CRC recalculado", "CRC", "MIC", "Vulnerable", "Con FCnt"],
            [(e["entrada"], "OK" if e["con_fcnt"]["crc_valido"] else "INVALIDO",
              "OK" if e["con_fcnt"]["mic_valido"] else "INVALIDO",
              e["vulnerable"]["motivo"], e["con_fcnt"]["motivo"]) for e in r["controles"]]),
                   "Ambos rechazan los cambios. No se actualizan el contador ni el estado de la aplicación."]
    partes.append("Comprobaciones: " + ("APROBADAS" if r["comprobaciones_aprobadas"] else "FALLIDAS"))
    return "\n\n".join(partes) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etapa", choices=("tramas", "replay", "controles", "todo"), default="todo")
    parser.add_argument("--salida", type=Path, default=Path("output/lorawan-replay"))
    args = parser.parse_args()
    resultado = ejecutar_experimento()
    texto = presentar(resultado, args.etapa)
    args.salida.mkdir(parents=True, exist_ok=True)
    for t in resultado["tramas"]:
        (args.salida / (t["nombre"] + ".bin")).write_bytes(bytes.fromhex(t["phypayload_hex"]))
    (args.salida / "replay.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.salida / (args.etapa + ".txt")).write_text(texto, encoding="utf-8")
    print(texto, end="")
    print("Archivos:", args.salida)
    return 0 if resultado["comprobaciones_aprobadas"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

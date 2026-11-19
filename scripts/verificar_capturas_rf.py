"""Verifica capturas RF reales con GNU Radio 3.10, sin GUI ni hardware.

La demodulación usa bloques GNU Radio; el análisis de PDU y los CRC de
LaCrosse/BLE/ADS-B se comprueban además en Python. No genera señales RF.
Consultar gnuradio/samples/ingenieria-reversa/README.md para descargar entradas.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import logging
from pathlib import Path
import sys

import numpy as np
import pmt
from gnuradio import analog, blocks, digital, filter, gr
from gnuradio.filter import firdes


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "gnuradio/samples/ingenieria-reversa"
VENDOR = ROOT / "tmp/rf-capturas/vendor/adsb"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Cu8ToComplex(gr.decim_block):
    """Dos bytes I/Q unsigned por cada muestra complex64 normalizada."""

    def __init__(self):
        gr.decim_block.__init__(self, "cu8 a complex64", [np.uint8],
                               [np.complex64], 2)

    def work(self, input_items, output_items):
        n = len(output_items[0])
        data = input_items[0][:2*n].astype(np.float32)
        output_items[0][:] = ((data[::2] - 127.5)
                             + 1j * (data[1::2] - 127.5)) / 128
        return n


def discriminator(path, rate, offset, cutoff, decimation=1, cu8=False):
    tb = gr.top_block("Captura RF: filtro y discriminador")
    source = blocks.file_source(1 if cu8 else gr.sizeof_gr_complex,
                                str(path), False)
    chain = [source]
    if cu8:
        chain.append(Cu8ToComplex())
    chain += [filter.freq_xlating_fir_filter_ccf(
        decimation, firdes.low_pass(1, rate, cutoff, cutoff/2), offset, rate),
        analog.quadrature_demod_cf(1)]
    sink = blocks.vector_sink_f()
    tb.connect(*chain, sink)
    tb.run()
    return np.array(sink.data(), dtype=np.float32)


def crc8(data):
    state = 0
    for byte in data:
        state ^= int(byte)
        for _ in range(8):
            state = (((state << 1) ^ 0x31) if state & 128 else state << 1) & 255
    return state


def lacrosse():
    data = discriminator(SAMPLES / "lacrosse-tx35.cu8", 250000, 25500,
                         45000, cu8=True)
    # Nominal duration 105 us; test sampling phase within one symbol.
    sps = 26.25
    pattern = np.unpackbits(np.frombuffer(bytes.fromhex("a2dd49"), np.uint8))
    found = {}
    for phase in np.arange(0, sps, 0.25):
        indices = np.arange(phase, len(data)-1, sps).astype(int)
        bits = (data[indices] > 0).astype(np.uint8)
        corr = np.correlate(bits.astype(int)*2-1,
                            pattern.astype(int)*2-1, "valid")
        for start in np.flatnonzero(corr == 24):
            packet = np.packbits(bits[start+20:start+60]).tobytes()
            if len(packet) != 5 or crc8(packet[:4]) != packet[4]:
                continue
            a, b, c, d, check = packet
            found[packet.hex()] = {
                "hex": packet.hex(), "id": ((a & 15) << 2) | (b >> 6),
                "temperature_C": round(10*(b & 15) + (c >> 4) + .1*(c & 15) - 40, 1),
                "humidity": d & 127, "crc8": f"{check:02x}",
                "crc_valido": True,
            }
    packets = list(found.values())
    expected = any(p["id"] == 26 and p["temperature_C"] == 24.1
                   and p["humidity"] == 34 for p in packets)
    return {"aprobado": expected, "paquetes_crc_validos_unicos": len(packets),
            "referencia": "rtl_433_tests: id=26, temperatura=24.1 C, humedad=34%",
            "parametros": {"fs": 250000, "offset_hz": 25500,
                           "cutoff_hz": 45000, "symbol_duration_us": 105},
            "paquetes": packets}


def dewhiten(bits, channel):
    state = channel | 0x40
    result = []
    for bit in bits:
        feedback = state & 1
        result.append(int(bit) ^ feedback)
        if feedback:
            state ^= 0x88
        state >>= 1
    return np.array(result, dtype=np.uint8)


def crc_ble(pdu):
    # Reflected register: bitreverse24(0x555555), polynomial bitreverse24(0x65b).
    state = 0xAAAAAA
    for byte in pdu:
        for shift in range(8):
            feedback = (state ^ (byte >> shift)) & 1
            state >>= 1
            if feedback:
                state ^= 0xDA6000
    return state.to_bytes(3, "little")


def advertising_data(pdu):
    fields = []
    payload = pdu[8:]  # Header (2), AdvA (6), advertising structures.
    pos = 0
    while pos < len(payload):
        size = payload[pos]
        if not size or pos+1+size > len(payload):
            if size:
                fields.append({"estructura_incompleta": True, "offset": pos,
                               "hex_restante": payload[pos:].hex()})
            break
        kind = payload[pos+1]
        content = payload[pos+2:pos+1+size]
        item = {"type": kind, "hex": content.hex()}
        if kind in (8, 9):
            item["nombre"] = content.decode("utf-8", errors="replace")
        fields.append(item)
        pos += 1+size
    return fields


def ble():
    access = np.unpackbits(np.frombuffer(bytes.fromhex("d6be898e"), np.uint8),
                            bitorder="little").astype(int)
    packets = []
    # Actual RF channels alias into this special 20-Msps recording (anti-alias
    # filter disabled by its author). This is not a generic receiver setup.
    for channel, offset in [(37, 1000000), (38, 5000000), (39, -1000000)]:
        data = discriminator(SAMPLES / "ble-fcsc2020.sigmf-data", 20000000,
                             offset, 700000, 5)
        # Four samples/bit after decimation; one fixed phase already resolves
        # all six packets. Do not count other phases as new transmissions.
        bits = (data[1::4] > 0).astype(np.uint8)
        corr = np.correlate(bits.astype(int)*2-1, access*2-1, "valid")
        for start in np.flatnonzero(corr == 32):
            whitened = bits[start+32:start+32+8*44]
            decoded = np.packbits(dewhiten(whitened, channel), bitorder="little")
            if len(decoded) < 5:
                continue
            length = int(decoded[1]) & 63
            if not 6 <= length <= 37 or len(decoded) < length+5:
                continue
            pdu = bytes(decoded[:length+2])
            crc = bytes(decoded[length+2:length+5])
            if crc_ble(pdu) != crc:
                continue
            corrupted = bytearray(pdu)
            corrupted[2] ^= 1
            wrong = np.packbits(dewhiten(whitened, (channel+1) % 40), bitorder="little")
            wrong_pdu, wrong_crc = bytes(wrong[:length+2]), bytes(wrong[length+2:length+5])
            packets.append({"canal": channel, "hex": pdu.hex(),
                            "crc24": crc.hex(), "crc_valido": True,
                            "direccion": pdu[2:8][::-1].hex(":"),
                            "campos": advertising_data(pdu),
                            "control_bit_alterado_rechazado": crc_ble(corrupted) != crc,
                            "control_whitening_incorrecto_rechazado": crc_ble(wrong_pdu) != wrong_crc})
    controls = all(p["control_bit_alterado_rechazado"] and
                   p["control_whitening_incorrecto_rechazado"] for p in packets)
    return {"aprobado": len(packets) == 6 and controls,
            "paquetes_crc_validos": len(packets), "paquetes": packets,
            "parametros": {"fs": 20000000, "decimacion": 5,
                           "bitrate": 1000000, "crc_init": "555555"},
            "limite": "Captura especial con aliasing intencional; no contiene conexiones BLE."}


def pdu_bytes(debug):
    return [bytes(pmt.u8vector_elements(pmt.cdr(debug.get_message(i))))
            for i in range(debug.num_messages())]


def unsigned(bits, start, size):
    return int("".join(str(int(b)) for b in bits[start:start+size]), 2)


def signed(bits, start, size):
    value = unsigned(bits, start, size)
    return value - (1 << size) if value & (1 << (size-1)) else value


def ais_fields(packet):
    # HDLC has already restored the original octets from LSB-first transport.
    # AIS fields are interpreted MSB-first within those restored octets,
    # matching gr-ais's pdu_to_nmea block.
    bits = np.unpackbits(np.frombuffer(packet, np.uint8), bitorder="big")
    kind = unsigned(bits, 0, 6)
    result = {"hex_hdlc": packet.hex(), "tipo": kind,
              "mmsi": unsigned(bits, 8, 30)}
    if kind in (1, 2, 3) and len(bits) >= 168:
        result.update({"velocidad_kn": unsigned(bits, 50, 10)/10,
                       "longitud": signed(bits, 61, 28)/600000,
                       "latitud": signed(bits, 89, 27)/600000,
                       "rumbo_deg": unsigned(bits, 116, 12)/10})
    elif kind == 18 and len(bits) >= 168:
        result.update({"velocidad_kn": unsigned(bits, 46, 10)/10,
                       "longitud": signed(bits, 57, 28)/600000,
                       "latitud": signed(bits, 85, 27)/600000,
                       "rumbo_deg": unsigned(bits, 112, 12)/10})
    # Sentinel values (181/91 degrees) mean position unavailable.
    if "latitud" in result and not (-90 <= result["latitud"] <= 90
                                    and -180 <= result["longitud"] <= 180):
        result["posicion_no_disponible"] = True
    return result


def ais():
    packets = []
    counts = {}
    for channel, offset in [("A", -25000), ("B", 25000)]:
        tb = gr.top_block("AIS GMSK y HDLC")
        source = blocks.file_source(gr.sizeof_gr_complex, str(SAMPLES / "ais-sdrangel.sigmf-data"), False)
        fir = filter.freq_xlating_fir_filter_ccf(
            5, firdes.low_pass(1, 250000, 11000, 2000), offset, 250000)
        demod = digital.gmsk_demod(samples_per_symbol=50000/9600,
                                   gain_mu=.175, mu=.5, omega_relative_limit=.01)
        diff = digital.diff_decoder_bb(2)
        invert = digital.map_bb([1, 0])
        hdlc = digital.hdlc_deframer_bp(11, 64)
        debug = blocks.message_debug()
        tb.connect(source, fir, demod, diff, invert, hdlc)
        tb.msg_connect((hdlc, "out"), (debug, "store"))
        tb.run()
        decoded = pdu_bytes(debug)
        counts[channel] = len(decoded)
        packets.extend({"canal": channel, "crc_hdlc_valido": True,
                        **ais_fields(p)} for p in decoded)
    positions = [p for p in packets if "latitud" in p and not p.get("posicion_no_disponible")]
    return {"aprobado": all(counts.values()) and bool(positions),
            "paquetes_crc_validos": len(packets), "por_canal": counts,
            "tipos": dict(Counter(p["tipo"] for p in packets)),
            "reportes_posicion": len(positions), "paquetes": packets,
            "parametros": {"fs": 250000, "fc": 162000000,
                           "decimacion": 5, "bitrate": 9600},
            "limite": "Verificado con demodulación diferencial; no mide la tasa total de pérdidas."}


def ax25_fields(packet):
    addresses = []
    pos = 0
    while pos+7 <= len(packet):
        part = packet[pos:pos+7]
        call = "".join(chr(b >> 1) for b in part[:6]).strip()
        ssid = (part[6] >> 1) & 15
        addresses.append(call + (f"-{ssid}" if ssid else ""))
        pos += 7
        if part[6] & 1:
            break
    return {"hex": packet.hex(), "direcciones": addresses,
            "control": packet[pos] if pos < len(packet) else None,
            "pid": packet[pos+1] if pos+1 < len(packet) else None,
            "informacion": packet[pos+2:].decode("ascii", errors="replace"),
            "crc_hdlc_valido": True}


def aprs():
    tb = gr.top_block("NO-84: FM, AFSK, NRZI, HDLC")
    source = blocks.file_source(gr.sizeof_gr_complex, str(SAMPLES / "aprs-no84.sigmf-data"), False)
    rf = filter.freq_xlating_fir_filter_ccf(
        1, firdes.low_pass(1, 24000, 6500, 1000), 1000, 24000)
    fm = analog.quadrature_demod_cf(1)
    complex_audio = blocks.float_to_complex()
    subtract = blocks.sub_ff()
    branches = []
    for j, tone in enumerate([1200, 2200]):
        band = filter.freq_xlating_fir_filter_ccf(
            1, firdes.low_pass(1, 24000, 600, 400), tone, 24000)
        power = blocks.complex_to_mag_squared()
        tb.connect(complex_audio, band, power, (subtract, j))
        branches += [band, power]
    clock = digital.clock_recovery_mm_ff(20, .25*.175**2, .5, .175, .005)
    slicer = digital.binary_slicer_fb()
    diff = digital.diff_decoder_bb(2)
    invert = digital.map_bb([1, 0])
    hdlc = digital.hdlc_deframer_bp(16, 512)
    debug = blocks.message_debug()
    tb.connect(source, rf, fm, (complex_audio, 0))
    tb.connect(subtract, clock, slicer, diff, invert, hdlc)
    tb.msg_connect((hdlc, "out"), (debug, "store"))
    tb.run()
    packets = [ax25_fields(p) for p in pdu_bytes(debug)]
    return {"aprobado": bool(packets), "paquetes_crc_validos": len(packets),
            "paquetes": packets,
            "parametros": {"fs": 24000, "fc": 145825000, "offset_hz": 1000,
                           "bitrate": 1200, "tonos_hz": [1200, 2200]},
            "limite": "Captura satelital con Doppler; esta cadena no garantiza recuperar todas sus ráfagas."}


def load_adsb_block(name):
    path = VENDOR / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Falta {path}; ejecutar descargar_capturas_rf.py")
    catalog = json.loads((SAMPLES / "catalogo.json").read_text())
    reference = next(b for b in catalog["gr_adsb"]["archivos"]
                     if b["archivo"] == f"{name}.py")
    if sha256(path) != reference["sha256"]:
        raise ValueError(f"El bloque ADS-B difiere de la versión comprobada: {path}")
    spec = importlib.util.spec_from_file_location(f"cbs33m_adsb_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, name)


def mode_s_residue(bits):
    state = 0
    for bit in bits:
        high = state & 0x800000
        state = ((state << 1) | int(bit)) & 0xFFFFFF
        if high:
            state ^= 0xFFF409
    return state


def adsb():
    framer, demod, decoder = [load_adsb_block(n) for n in ("framer", "demod", "decoder")]
    tb = gr.top_block("ADS-B: captura SDRangel y gr-adsb")
    source = blocks.file_source(gr.sizeof_gr_complex, str(SAMPLES / "adsb-sdrangel.sigmf-data"), False)
    resampler = filter.rational_resampler_ccc(interpolation=10, decimation=3)
    power = blocks.complex_to_mag_squared()
    average = blocks.moving_average_ff(4, .25)
    frame = framer(8000000, .3)
    dem = demod(8000000)
    dec = decoder("Extended Squitter Only", "None", "None")
    logging.getLogger().setLevel(logging.CRITICAL)
    null = blocks.null_sink(gr.sizeof_float)
    debug = blocks.message_debug()
    raw_debug = blocks.message_debug()
    tb.connect(source, resampler, power, average, frame, dem, null)
    tb.msg_connect((dem, "demodulated"), (dec, "demodulated"))
    tb.msg_connect((dem, "demodulated"), (raw_debug, "store"))
    tb.msg_connect((dec, "decoded"), (debug, "store"))
    tb.run()
    packets = []
    for i in range(debug.num_messages()):
        meta, bits = pmt.to_python(debug.get_message(i))
        if meta["df"] not in (17, 18):
            continue
        bits = np.array(bits, dtype=np.uint8)[:112]
        if mode_s_residue(bits) != 0:
            raise AssertionError("gr-adsb aceptó una trama que falla la verificación independiente")
        bad = bits.copy()
        bad[40] ^= 1
        # Arrival times produced by upstream refer to this replay, not the
        # original recording. Keep only actual decoded aircraft fields.
        fields = {k: meta[k] for k in ("icao", "df", "callsign", "altitude",
                  "speed", "heading", "latitude", "longitude") if k in meta}
        fields = {k: (v.item() if isinstance(v, np.generic) else v) for k, v in fields.items()}
        fields = {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in fields.items()}
        packets.append({**fields, "hex": np.packbits(bits).tobytes().hex(),
                        "crc24_valido": True,
                        "control_bit_alterado_rechazado": mode_s_residue(bad) != 0})
    return {"aprobado": bool(packets), "rafagas_demoduladas": raw_debug.num_messages(),
            "paquetes_crc_validos": len(packets),
            "icao_distintos": sorted({p["icao"] for p in packets}),
            "paquetes": packets,
            "gr_adsb_commit": "b1b5b139c8849d0090319ba12140bdc88fce236f",
            "parametros": {"fs_entrada": 2400000, "fc": 1090000000,
                           "interpolacion": 10, "decimacion": 3,
                           "fs_receptor": 8000000, "umbral_potencia": .3,
                           "promedio_potencia_muestras": 4,
                           "correccion_errores": "None"},
            "limite": "Sólo se cuentan DF17/18 con CRC sin corrección; no se exige obtener una posición CPR completa."}


CHECKS = {"lacrosse": lacrosse, "aprs": aprs, "ais": ais, "ble": ble, "adsb": adsb}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tecnologias", choices=[*CHECKS, "todas"], nargs="+",
                        help="Usar todas para verificar las cinco capturas")
    parser.add_argument("--salida", type=Path, default=SAMPLES / "verificacion.json")
    args = parser.parse_args()
    selected = list(CHECKS) if "todas" in args.tecnologias else list(dict.fromkeys(args.tecnologias))
    catalog = json.loads((SAMPLES / "catalogo.json").read_text())
    inputs = []
    # Check only inputs needed by the selected tests.
    for entry in catalog["capturas"]:
        if entry["id"] not in selected:
            continue
        path = SAMPLES / entry["archivo"]
        digest = sha256(path)
        if digest != entry["sha256"]:
            raise ValueError(f"Hash de captura incorrecto: {path}")
        inputs.append({"id": entry["id"], "archivo": entry["archivo"], "sha256": digest})
    report = {"fecha_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version.split()[0], "gnuradio": gr.version(),
              "numpy": np.__version__,
              "entradas": inputs, "resultados": {}}
    for name in selected:
        print(f"Verificando {name}...", flush=True)
        result = CHECKS[name]()
        report["resultados"][name] = result
        print(f"  {name}: {'OK' if result['aprobado'] else 'FALLO'}; "
              f"{result.get('paquetes_crc_validos', result.get('paquetes_crc_validos_unicos', 0))} tramas CRC válidas", flush=True)
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    return 0 if all(r["aprobado"] for r in report["resultados"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

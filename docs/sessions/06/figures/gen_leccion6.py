"""Genera las figuras de la lección 6 desde modelos y señales identificados.

Desde la raíz, después de descargar OSU y generar output/lorawan-iq:
    python docs/sessions/06/figures/gen_leccion6.py
Los I/Q no se versionan. Los informes y las figuras sí.
"""

from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
REAL = ROOT / 'gnuradio/samples/lora-915-osu/IQ_1.sigmf-data'
IQ = ROOT / 'output/lorawan-iq/correcto.sigmf-data'
REPORT = ROOT / 'gnuradio/samples/lorawan-didactico/verificacion.json'
BLUE, GREEN, PURPLE, ORANGE = '#2563a6', '#137d68', '#7951a4', '#bc6225'
INK, PALE, GRAY = '#18334e', '#eef4fa', '#687c8f'
ROLES = [('End device', BLUE), ('Gateway', BLUE), ('Network Server', GREEN),
         ('Join Server', ORANGE), ('Application Server', PURPLE)]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.labelcolor': INK, 'text.color': INK,
                     'axes.titlesize': 12, 'figure.facecolor': 'white'})


def canvas(title, height=4.6):
    f, a = plt.subplots(figsize=(11, height), layout='constrained')
    a.set(xlim=(0, 11), ylim=(0, 5)); a.axis('off')
    f.suptitle(title, fontsize=15, fontweight='bold', color=INK)
    return f, a


def box(a, x, y, w, h, text, color=BLUE, size=11):
    a.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle='round,pad=0.05,rounding_size=0.08', facecolor=PALE,
        edgecolor=color, linewidth=1.6))
    a.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=size,
           color=color, linespacing=1.5)


def arrow(a, x, y, xx, yy, color=GRAY):
    a.annotate('', xy=(xx, yy), xytext=(x, y),
               arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.6})


def save(f, name):
    f.savefig(OUT / name, dpi=160, metadata={'Software': 'SDR UNI: gen_leccion6.py'})
    plt.close(f)


def dibujar_arquitectura(arquitectura):
    arquitectura.set(xlim=(0, 11), ylim=(0, 5))
    arquitectura.axis('off')
    for x, indice, descripcion in [(0.2, 0, 'Sensor o actuador'), (3, 1, 'Recepción y reenvío'),
                                    (5.8, 2, 'Gestión de red'), (8.6, 4, 'Datos de aplicación')]:
        nombre, color = ROLES[indice]
        box(arquitectura, x, 2.3, 2.15, 1.5, f'{nombre}\n{descripcion}', color, 10)
    for x in (2.4, 5.2, 8):
        arrow(arquitectura, x, 3.05, x+0.55, 3.05)
    arquitectura.text(2.675, 4.2, 'Radio LoRa', ha='center', fontsize=10)
    arquitectura.text(7.1, 4.2, 'Reenvío y procesamiento', ha='center', fontsize=10)
    box(arquitectura, 5.8, 0.15, 2.15, 1.1, 'Join Server\nActivación y claves', ORANGE, 10)
    arquitectura.annotate('', xy=(6.875, 1.33), xytext=(6.875, 2.22),
                            arrowprops={'arrowstyle': '<->', 'color': ORANGE, 'lw': 1.6})


def figura_arquitectura():
    f, a = plt.subplots(figsize=(11, 7.3), layout='constrained')
    f.suptitle('Arquitectura y pila de protocolos de LoRaWAN',
               fontsize=15, fontweight='bold', color=INK)
    a.set(xlim=(0, 14), ylim=(0, 13.6))
    a.axis('off')

    centros = [3.5, 5.78, 8.06, 10.34, 12.62]
    ancho_bloque = 1.90
    for centro, (nombre, color) in zip(centros, ROLES):
        box(a, centro - ancho_bloque / 2, 11.75, ancho_bloque, 0.82, nombre, color, 10)

    dispositivo, gateway, red, activacion, aplicacion = centros
    borde = ancho_bloque / 2 + 0.055
    arrow(a, dispositivo + borde, 12.16, gateway - borde, 12.16, BLUE)
    arrow(a, gateway + borde, 12.16, red - borde, 12.16)
    a.annotate('', xy=(activacion - borde, 12.16), xytext=(red + borde, 12.16),
               arrowprops={'arrowstyle': '<->', 'color': ORANGE, 'lw': 1.6,
                           'mutation_scale': 8, 'shrinkA': 0, 'shrinkB': 0})
    a.plot([red, red, aplicacion], [12.64, 13.04, 13.04], color=GRAY, linewidth=1.6)
    arrow(a, aplicacion, 13.04, aplicacion, 12.64)
    a.text((red + aplicacion) / 2, 13.14, 'Datos de aplicación', ha='center', fontsize=10)
    a.text((dispositivo + gateway) / 2, 12.76, 'Radio LoRa', ha='center', fontsize=10)
    a.text((gateway + red) / 2, 12.76, 'Por IP', ha='center', fontsize=10)

    grupos = [
        (11.28, 'LoRaWAN y enlace de radio', [
            ('Aplicación', ['Datos del sensor', '', '', '', 'Descifrado y\nprocesamiento']),
            ('Activación OTAA', ['Solicita activación', '', 'Coordina la\nactivación', 'Valida y deriva\nlas claves', '']),
            ('MAC LoRaWAN', ['Control del enlace', '', 'Control del enlace', '', '']),
            ('PHY LoRa', ['Modula y\ndemodula', 'Modula y\ndemodula', '', '', '']),
        ]),
        (7.02, 'Enlaces por IP · ejemplo con Basics Station y The Things Stack', [
            ('Interfaz sobre IP', ['', 'LNS de Basics Station\nsobre WebSocket', 'gRPC sobre HTTP/2', 'gRPC sobre HTTP/2', 'gRPC sobre HTTP/2']),
            ('Seguridad', ['', 'TLS', 'TLS', 'TLS', 'TLS']),
            ('Transporte', ['', 'TCP', 'TCP', 'TCP', 'TCP']),
            ('Red', ['', 'IP', 'IP', 'IP', 'IP']),
            ('Enlace local y medio', ['', 'Ethernet', 'Ethernet', 'Ethernet', 'Ethernet']),
        ]),
    ]
    ancho_celda = 2.20
    for y_titulo, titulo, filas in grupos:
        a.text(0.14, y_titulo, titulo, fontsize=11, fontweight='bold')
        for indice, (capa, celdas) in enumerate(filas):
            y = y_titulo - 0.96 * (indice + 1)
            a.text(0.14, y + 0.40, capa, va='center', fontsize=10)
            for centro, contenido in zip(centros, celdas):
                a.add_patch(Rectangle((centro - ancho_celda / 2, y), ancho_celda, 0.8,
                                      facecolor=PALE if contenido else 'white',
                                      edgecolor='#c5d2df', linewidth=0.8))
                a.text(centro, y + 0.40, contenido, ha='center', va='center', fontsize=9.5)

    a.text(0.14, 1.64, 'Basics Station se conecta por IP al Gateway Server, que entrega las tramas al Network Server.',
           fontsize=9.5)
    a.add_patch(Rectangle((0.14, 0.85), 0.35, 0.35, facecolor=PALE, edgecolor='#c5d2df'))
    a.text(0.62, 1.025, 'El sombreado indica las capas, protocolos o funciones que usa cada bloque.',
           va='center', fontsize=9.5)
    save(f, '01-arquitectura.png')


def figura_arquitectura_otaa():
    f, (arquitectura, secuencia) = plt.subplots(
        2, 1, figsize=(11, 8.7), height_ratios=[2, 6], layout='constrained')
    f.suptitle('1 · Arquitectura y activación LoRaWAN 1.0.4',
               fontsize=15, fontweight='bold', color=INK)
    arquitectura.set_title('A · Funciones de la red')
    dibujar_arquitectura(arquitectura)

    secuencia.set(xlim=(0, 11), ylim=(0, 16), title='B · Activación por aire (OTAA) y primer envío de datos')
    secuencia.axis('off')
    centros = [1.1, 3.3, 5.5, 7.7, 9.9]
    for x, (nombre, color) in zip(centros, ROLES):
        box(secuencia, x-0.98, 14.65, 1.96, 1.04, nombre, color, 10)
        secuencia.vlines(x, 0.35, 14.55, color='#c5d2df', linestyle='dashed', linewidth=1.2)

    mensajes = [
        (13.0, 0, 1, '1 · Join-Request con MIC (radio)', BLUE),
        (11.9, 1, 2, 'Reenvío por IP', GRAY),
        (10.8, 2, 3, '2 · JoinReq', ORANGE),
        (8.2, 3, 2, '3 · JoinAns con claves de sesión', ORANGE),
        (7.1, 2, 1, '4 · Reenvío de Join-Accept', GRAY),
        (6.0, 1, 0, 'Join-Accept cifrado (radio)', BLUE),
        (3.6, 0, 1, '5 · Datos cifrados (radio)', BLUE),
        (2.5, 1, 2, 'Reenvío de la trama', GRAY),
        (1.4, 2, 4, '6 · Datos y AppSKey protegida', PURPLE),
    ]
    for y, origen, destino, mensaje, color in mensajes:
        x, xx = centros[origen], centros[destino]
        arrow(secuencia, x, y, xx, y, color)
        secuencia.text((x+xx)/2, y+0.16, mensaje, ha='center', va='bottom',
                       fontsize=9, color=color)

    operaciones = [
        (0, 14.1, 'AppKey provisionada', BLUE),
        (3, 14.1, 'AppKey provisionada', ORANGE),
        (3, 9.55, 'Verifica el MIC y DevNonce\nDeriva las claves de sesión', ORANGE),
        (0, 4.8, 'Valida la respuesta\nDeriva las mismas claves', BLUE),
        (4, 0.55, 'Descifra los datos', PURPLE),
    ]
    for actor, y, descripcion, color in operaciones:
        secuencia.text(centros[actor], y, descripcion, ha='center', va='center',
                       fontsize=9, color=color, bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 2})
    save(f, '01-capas.png')


def main():
    if not REAL.is_file() or not IQ.is_file():
        raise SystemExit('Faltan I/Q: descargar OSU y ejecutar scripts/verificar_lorawan_iq.py primero.')
    digest = hashlib.sha256(REAL.read_bytes()).hexdigest()
    if digest != '3a6ef845f8af169419d71753bdd9936cf3eaf75a0f5b6e098e6a5e11228dbd95':
        raise SystemExit('La captura OSU no coincide con la fuente verificada.')
    real = np.memmap(REAL, dtype='<c8', mode='r')
    iq = np.fromfile(IQ, dtype='<c8')
    report = json.loads(REPORT.read_text())
    active = np.flatnonzero(np.abs(iq) > 0.1)
    start, end = int(active[0]), int(active[-1])+1
    ns, fs = 1024, 1000000

    figura_arquitectura()
    figura_arquitectura_otaa()

    f, axs = plt.subplots(2, 1, figsize=(11, 6), layout='constrained')
    f.suptitle('2 · Chirps y duración del símbolo', fontsize=15, fontweight='bold')
    chirps = iq[start:start+3*ns]
    freq = np.angle(chirps[1:] * chirps[:-1].conj()) * fs/(2*np.pi*1000)
    axs[0].plot(np.arange(1, len(chirps))/fs*1000, freq, color=BLUE, lw=1)
    axs[0].set(xlabel='Tiempo desde el inicio del preámbulo (ms)',
               ylabel='Frecuencia relativa (kHz)', title='A · Tres upchirps del I/Q generado, SF7 y BW 125 kHz')
    for sf, col in ((7, BLUE), (8, PURPLE)):
        ts = 2**sf/125000
        t = np.linspace(0, ts, 600)
        axs[1].plot(t*1000, -62.5+125*t/ts, label=f'SF{sf}: {ts*1000:.3f} ms', color=col)
    axs[1].set(xlabel='Tiempo (ms)', ylabel='Frecuencia relativa (kHz)',
               title='B · Modelo de un chirp: misma banda y distinta duración')
    axs[1].legend(); [a.grid(alpha=.2) for a in axs]
    save(f, '02-chirps.png')

    f, a = canvas('3 · El paquete físico y su contenido')
    names = ['Preámbulo', 'Sync word\ny SFD', 'Cabecera\nexplícita', 'Payload\n20 bytes', 'CRC LoRa\n2 bytes']
    for i, name in enumerate(names):
        box(a, .3+i*2.15, 3.1, 1.95, 1, name, PURPLE if i==3 else BLUE)
        if i < 4: arrow(a, 2.3+i*2.15, 3.6, 2.43+i*2.15, 3.6)
    arrow(a, 7.72, 3, 7.72, 2.25, PURPLE)
    box(a, 3.5, .8, 6.9, 1.3, 'En este ejemplo: PHYPayload LoRaWAN\nMHDR | FHDR | FPort | FRMPayload | MIC', PURPLE)
    a.text(.5, 1.4, 'Esquema lógico.\nLos anchos no\nrepresentan tiempo.', fontsize=10)
    save(f, '03-paquete-phy.png')

    # Ventanas cortas de una captura real, sin generar una señal sustitutiva.
    powers = np.array([np.mean(np.abs(real[i:i+10000])**2) for i in range(0, len(real), 10000)])
    peak = int(np.argmax(powers)) * 10000
    begin = max(0, peak-5000)
    clip = np.asarray(real[begin:begin+16000])
    f, axs = plt.subplots(2, 1, figsize=(11, 6), layout='constrained')
    f.suptitle('4 · Muestras originales OSU: recepción real a 915 MHz', fontsize=15, fontweight='bold')
    axs[0].plot(np.arange(len(powers))*.01, 10*np.log10(powers+1e-20), color=BLUE)
    axs[0].set(xlabel='Tiempo desde el inicio del archivo (s)', ylabel='Potencia media relativa (dB)',
               title='A · Potencia media por ventanas de 10 ms; sin calibración en dBm')
    axs[0].grid(alpha=.2)
    _, _, _, im = axs[1].specgram(clip, NFFT=256, Fs=fs, noverlap=224,
                                 cmap='viridis', scale='dB')
    axs[1].set(ylim=(-100000, 100000), xlabel='Tiempo dentro del recorte (s)',
               ylabel='Frecuencia relativa (Hz)', title=f'B · Espectrograma de 16 ms desde t={begin/fs:.6f} s')
    f.colorbar(im, ax=axs[1], label='Densidad espectral relativa (dB/Hz)')
    save(f, '04-captura-real.png')

    f, a = canvas('5 · Tipos y salidas de LoRa Rx')
    box(a, .2, 2, 2.25, 1.3, 'File Source\nID: captura_lora\nComplex · 1 Msps')
    box(a, 3.45, 2, 2.25, 1.3, 'LoRa Rx\nID: receptor_lora\nSF7 · BW 125 kHz')
    box(a, 7.15, 3.15, 3.5, 1.2, 'Message Debug\nID: mensajes_lora\nPuerto print', PURPLE)
    box(a, 7.15, .55, 3.5, 1.2, 'Tag Debug\nID: etiquetas_lora\nByte · frame_info', GREEN)
    arrow(a, 2.5, 2.65, 3.4, 2.65)
    arrow(a, 5.75, 2.8, 7.1, 3.7, PURPLE)
    arrow(a, 5.75, 2.4, 7.1, 1.15, GREEN)
    a.text(5.95, 3.8, 'Mensaje', fontsize=10, color=PURPLE)
    a.text(5.9, .7, 'Stream de bytes\ncon etiquetas', fontsize=10, color=GREEN)
    a.text(.3, .4, 'El programa de verificación usa Vector Sink para consultar también crc_valid.', fontsize=10)
    save(f, '05-receptor.png')

    r = json.loads((ROOT/'gnuradio/samples/lora-915-osu/verificacion.json').read_text())
    f, axs = plt.subplots(1, 2, figsize=(11, 4.4), layout='constrained')
    f.suptitle('6 · Qué acredita la verificación de la captura real', fontsize=15, fontweight='bold')
    vals = [r['tramas_recuperadas'], r['paquetes_crc_validos'], r['tramas_con_crc_invalido']]
    axs[0].bar(['Recuperadas', 'CRC válido', 'CRC inválido'], vals, color=[BLUE, GREEN, ORANGE])
    axs[0].set(ylabel='Tramas contadas', ylim=(0, 58))
    for i, v in enumerate(vals): axs[0].text(i, v+1, str(v), ha='center')
    axs[1].axis('off')
    axs[1].text(.08, .8, '48 × 255 bytes = 12 240 bytes', fontsize=15, color=BLUE)
    axs[1].text(.08, .52, 'Un único payload distinto\nrepetido 48 veces.', fontsize=12)
    axs[1].text(.08, .16, 'Total transmitido: desconocido.\nEstos conteos no determinan una PER.', fontsize=12, color=ORANGE)
    save(f, '06-resultados.png')

    f, a = canvas('7 · Los 20 bytes del PHYPayload LoRaWAN', 4.8)
    fields = [('MHDR', 1, '80'), ('DevAddr', 4, 'dc 5d e6 01'), ('FCtrl', 1, '90'),
              ('FCnt', 2, '04 00'), ('FPort', 1, '01'),
              ('FRMPayload', 7, 'db f5 a4 e3 12 39 d0'), ('MIC', 4, '53 21 68 7b')]
    x = .3
    for i, (name, n, value) in enumerate(fields):
        w = .5*n
        box(a, x, 2.8, w, 1.05, f'{name}\n{n} B', PURPLE if i in (5,6) else BLUE, 9)
        a.text(x+w/2, 2.37-(i%2)*.4, value, ha='center', fontsize=9)
        x += w+.06
    a.text(.45, 4.5, '1 + 4 + 1 + 2 + 1 + 7 + 4 = 20 bytes', fontsize=13)
    box(a, 1, .35, 9, .9, 'DevAddr mostrado: 01e65ddc   ·   FCnt: 4   ·   FPort: 1\nFOptsLen = 0: esta trama no incluye FOpts.', GREEN, 11)
    save(f, '07-campos.png')

    f, a = canvas('8 · Dos claves, dos comprobaciones distintas')
    for y, key, proc, result, col in [(3.1, 'NwkSKey', 'AES-CMAC\nCabecera + datos cifrados', 'MIC\n4 bytes', GREEN),
                                     (.65, 'AppSKey', 'Flujo AES + XOR\nFPort de aplicación', 'Dato de aplicación\ntimeout', PURPLE)]:
        box(a, .3, y, 2, 1.1, key, col); box(a, 3.6, y, 3.2, 1.1, proc, col)
        box(a, 8, y, 2.7, 1.1, result, col)
        arrow(a, 2.4, y+.55, 3.5, y+.55, col); arrow(a, 6.9, y+.55, 7.9, y+.55, col)
    a.text(5.5, 2.35, 'Caso LoRaWAN 1.0.x, FPort = 1', ha='center', fontsize=12)
    save(f, '08-claves.png')

    f, a = plt.subplots(figsize=(11, 4.6), layout='constrained')
    f.suptitle('9 · I/Q generado: paquete y ceros de guarda', fontsize=15, fontweight='bold')
    t = np.arange(len(iq))/fs*1000
    a.plot(t[::32], np.abs(iq[::32]), color=BLUE, lw=1)
    a.axvspan(0, start/fs*1000, color=PALE)
    a.axvspan(end/fs*1000, len(iq)/fs*1000, color=PALE)
    a.set(xlabel='Tiempo desde el comienzo del archivo (ms)', ylabel='Magnitud |I+jQ|',
           ylim=(-.1, 1.7), title='Señal generada por GNU Radio; sin transmisión por aire')
    a.text((start+end)/2/fs*1000, 1.3, f'Paquete: {(end-start)/fs*1000:.3f} ms', ha='center')
    a.text(3, .45, 'Ceros', rotation=90)
    a.text(88, .5, 'Ceros de cierre\ny padding del modulador', ha='center')
    a.text(2, 1.55, f'Archivo completo: {len(iq)} muestras = {len(iq)/fs*1000:.2f} ms', fontsize=11)
    save(f, '09-iq-generado.png')

    f, a = canvas('10 · Descifrado del dato de aplicación')
    ct = bytes.fromhex(report['casos'][0]['lorawan']['frm_payload_cifrado_hex'])
    pt = b'timeout'; stream = bytes(x^y for x,y in zip(ct, pt))
    for y, label, vals, col in [(3.7, 'FRMPayload cifrado', ct, PURPLE),
                                (2.3, 'Flujo AES (7 bytes)', stream, GRAY),
                                (.9, 'Resultado del XOR', pt, GREEN)]:
        a.text(.2, y+.35, label, fontsize=11)
        for i, v in enumerate(vals): box(a, 3.3+i*1.02, y, .85, .7, f'{v:02x}', col)
    a.text(7, 3.15, 'XOR', ha='center', fontsize=12)
    a.text(7, .2, 't       i       m       e       o       u       t', ha='center', fontsize=13)
    save(f, '10-descifrado.png')

    f, a = plt.subplots(figsize=(11, 4.4), layout='constrained'); a.axis('off')
    f.suptitle('11 · Resultados medidos al cambiar una condición', fontsize=15, fontweight='bold')
    rows = [['Correcto','Sí','Correcto','Correcto','timeout'],
            ['Contenido alterado','Sí','Correcto','Incorrecto','No se descifra'],
            ['NwkSKey incorrecta','Sí','Correcto','Incorrecto','No se descifra'],
            ['AppSKey incorrecta','Sí','Correcto','Correcto','Distinto'],
            ['Sync word 0x12','No','—','—','—']]
    tab = a.table(cellText=rows, colLabels=['Condición','Trama RX','CRC LoRa','MIC','Dato'],
                  loc='center', cellLoc='center', colWidths=[.3,.13,.17,.17,.23])
    tab.auto_set_font_size(False); tab.set_fontsize(11); tab.scale(1, 2.8)
    for (row, col), cell in tab.get_celld().items():
        cell.set_edgecolor('#d3dfeb')
        cell.set_facecolor(PALE if row else BLUE)
        if row == 0: cell.set_text_props(color='white', weight='bold')
    save(f, '11-controles.png')

    f, a = canvas('12 · Recorrido de las representaciones')
    for x, label, col in [(0.2,'I/Q\n113 920 complejos',BLUE),
                           (3,'Payload LoRa\n20 bytes',BLUE),
                           (5.8,'FRMPayload\n7 bytes cifrados',PURPLE),
                           (8.6,'Dato\ntimeout · 7 bytes',GREEN)]:
        box(a,x,2.2,2.2,1.3,label,col,10)
    for x in (2.45,5.25,8.05): arrow(a,x,2.85,x+.5,2.85)
    a.text(2.6,1.4,'LoRa Rx\n+ CRC',ha='center',fontsize=11)
    a.text(5.4,1.4,'Campos\n+ MIC',ha='center',fontsize=11)
    a.text(8.2,1.4,'AppSKey\n+ descifrado',ha='center',fontsize=11)
    a.text(5.5,4.3,'Una muestra compleja no es un byte ni un símbolo LoRa.',ha='center',fontsize=12)
    save(f,'12-sintesis.png')

    f, axs = plt.subplots(1,2,figsize=(11,4.6),layout='constrained')
    f.suptitle('13 · Magnitudes para resolver los ejercicios',fontsize=15,fontweight='bold')
    sf = np.arange(7,10); ts = 2.**sf/125000*1000
    axs[0].bar([f'SF{x}' for x in sf],ts,color=[BLUE,PURPLE,GREEN])
    axs[0].set(ylabel='Duración de símbolo (ms)',title='A · BW fija: 125 kHz',ylim=(0,5))
    for i,v in enumerate(ts): axs[0].text(i,v+.12,f'{v:.3f}',ha='center')
    axs[1].axis('off')
    axs[1].text(.05,.78,'Archivo real:\n160 000 000 bytes / 8 =\n20 000 000 muestras',fontsize=14,color=BLUE)
    axs[1].text(.05,.22,'Archivo generado:\n113 920 muestras / 1 Msps =\n113,92 ms',fontsize=14,color=GREEN)
    save(f,'13-ejercicios.png')

    f,a=canvas('14 · Protocolo del laboratorio comparativo')
    box(a,.3,3.35,4.6,.9,'A · Captura real OSU\nReferencia: 48 paquetes con CRC',BLUE)
    box(a,6.1,3.35,4.6,.9,'B · Ejemplo LoRaWAN generado\nReferencia: CRC + MIC + timeout',PURPLE)
    for x in (2.6,8.4): arrow(a,x,3.25,x,2.6)
    box(a,.3,1.4,10.4,1.05,'Cambiar una condición → repetir → guardar el informe\nMantener constantes archivo, tasa, BW y SF al probar las claves.',GREEN)
    arrow(a,5.5,1.3,5.5,.8)
    a.text(5.5,.4,'Entrega: parámetros + conteos + evidencia + explicación del resultado.',ha='center',fontsize=11)
    save(f,'14-laboratorio.png')

    f,a=canvas('15 · Cada fuente responde una pregunta')
    sources=[(.4,3.15,'OSU\n¿De dónde viene el I/Q?',BLUE),
             (6,3.15,'gr-lora_sdr\n¿Cómo trabajan los bloques?',BLUE),
             (.4,.6,'LoRa Alliance · TS001\n¿Cómo se interpreta la trama?',PURPLE),
             (6,.6,'Brno + informes de prueba\n¿Qué dato y resultado se esperan?',GREEN)]
    for x,y,label,col in sources: box(a,x,y,4.6,1.25,label,col,12)
    save(f,'15-fuentes.png')
    print('Figuras PNG generadas. Fuentes I/Q verificadas.')


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""Extrae invitados previos de un canal de podcast en YouTube.

Cuota: ~3 unidades por show (videos:1 + channels:1 + playlistItems:1 por pagina).
Compara con search, que cuesta 100. Por eso NUNCA se usa search aqui.
"""
import json, urllib.request, io, os, re, sys

def _key():
    # Primero el entorno: quien instala el plugin la exporta, no tiene .env.local.
    k = os.environ.get('YOUTUBE_API_KEY')
    if k:
        return k
    for p in ('.env.local', '.env'):
        if os.path.exists(p):
            for line in io.open(p, encoding='utf-8', errors='ignore'):
                if line.strip().startswith('YOUTUBE_API_KEY'):
                    return line.split('=', 1)[1].strip().strip('"').strip("'").replace('\\n', '')
    # SystemExit con mensaje, no traceback: esto lo lee una persona, no un dev.
    raise SystemExit("""Falta YOUTUBE_API_KEY.

Es gratis, 3 minutos:
  1. console.cloud.google.com/apis/library/youtube.googleapis.com
  2. Habilitar -> Credenciales -> Crear credenciales -> Clave de API
  3. echo \"YOUTUBE_API_KEY=tu-clave\" >> .env.local

Cuota: 10,000 unidades/dia gratis (una busqueda cuesta 100).

Sin clave YA funcionan: pg-escuchar (transcribe), pg-pitch, pg-setup, pg-store.""")

KEY = _key()

def api(path):
    url = 'https://www.googleapis.com/youtube/v3/' + path + '&key=' + KEY
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

# Titulos que no son episodios de entrevista.
# Los tutoriales ("Automatizar X con Y") producen falsos positivos: el patron
# "con Y" captura el nombre de una herramienta como si fuera una persona.
RUIDO = re.compile(
    r'#shorts|^untitled$|^\s*$|\bshort\b'
    r'|\b(tutorial|c[oó]mo automatizar|automatiza(r)?\s|reto\s*\d|d[ií]a\s*\d'
    r'|webinar|masterclass|curso|clase\s*\d|review del|paso a paso)\b', re.I)

# Marcas y productos que el patron "con X" captura como si fueran personas.
HERRAMIENTAS = re.compile(
    r'\b(google|sheets|drive|docs|data studio|zoho|hubspot|salesforce|whatsapp|'
    r'telegram|slack|notion|airtable|make|integromat|zapier|n8n|shopify|'
    r'woocommerce|wordpress|stripe|paypal|meta|facebook|instagram|linkedin|'
    r'tiktok|youtube|chatgpt|openai|claude|gemini|api|crm|erp|excel|gmail|'
    r'calendly|typeform|webinar|everwebinar|mailchimp|activecampaign)\b', re.I)

# Patrones de invitado, del mas fiable al menos
PATRONES = [
    r'\bcon\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+){1,3})',
    r'\bwith\s+([A-Z][\w.\'-]+(?:\s+[A-Z][\w.\'-]+){1,3})',
    r'\bft\.?\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+){1,3})',
    r'\|\s*([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+){1,3})\s*(?:,|\||$)',
]

# Palabras que delatan que el match no es una persona
NO_PERSONA = re.compile(
    r'\b(IA|AI|ChatGPT|Claude|Marketing|Ventas|Negocio|Empresa|Podcast|Episodio|'
    r'Parte|Como|Cómo|Que|Qué|Por|Para|Los|Las|El|La|Un|Una|Tu|Mi|Su)\b', re.I)

def extraer_nombre(titulo):
    for pat in PATRONES:
        m = re.search(pat, titulo)
        if not m:
            continue
        nombre = re.sub(r'\s+', ' ', m.group(1)).strip(' .,|-—–')
        palabras = nombre.split()
        if not (2 <= len(palabras) <= 4):
            continue
        # Si TODAS las palabras son ruido conceptual, no es un nombre
        if NO_PERSONA.match(palabras[0]):
            continue
        # "Google Sheets", "Zoho CRM", "WhatsApp Cloud API" no son invitados
        if HERRAMIENTAS.search(nombre):
            continue
        return nombre
    return None

def canal_de_video(video_id):
    r = api('videos?part=snippet&id=' + video_id)
    if not r.get('items'):
        return None
    s = r['items'][0]['snippet']
    return {'channelId': s['channelId'], 'channelTitle': s['channelTitle']}

def invitados_de_canal(channel_id, max_paginas=40):
    c = api('channels?part=contentDetails,statistics,snippet&id=' + channel_id)
    if not c.get('items'):
        return None
    item = c['items'][0]
    uploads = item['contentDetails']['relatedPlaylists']['uploads']
    stats = item['statistics']

    vistos, invitados, total, token = set(), [], 0, ''
    for _ in range(max_paginas):
        path = 'playlistItems?part=snippet&maxResults=50&playlistId=' + uploads
        if token:
            path += '&pageToken=' + token
        pl = api(path)
        for it in pl.get('items', []):
            t = it['snippet']['title']
            if RUIDO.search(t):
                continue
            total += 1
            n = extraer_nombre(t)
            if n and n.lower() not in vistos:
                vistos.add(n.lower())
                invitados.append({
                    'nombre': n,
                    'episodio': t[:110],
                    'url': 'https://youtu.be/' + it['snippet']['resourceId']['videoId'],
                    'fecha': it['snippet']['publishedAt'][:10],
                })
        token = pl.get('nextPageToken', '')
        if not token:
            break

    return {
        'canal': item['snippet']['title'],
        'suscriptores': stats.get('subscriberCount'),
        'videos_totales': stats.get('videoCount'),
        'episodios_revisados': total,
        'invitados': invitados,
    }

def _norm(s):
    return re.sub(r'\s+', ' ', s or '').strip().lower()

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    como_json = '--json' in sys.argv
    # Nunca listarse a uno mismo como "invitado a contactar". El nombre sale de
    # --yo=, de PG_NOMBRE o del perfil del wiki: este script se distribuye, asi
    # que no puede traer el nombre de nadie hardcodeado.
    def _yo_default():
        env = os.environ.get('PG_NOMBRE')
        if env:
            return env
        for ruta in ('wiki-podcast/perfil.md', '.podcast-guesting/config.yaml'):
            if os.path.exists(ruta):
                for line in io.open(ruta, encoding='utf-8', errors='ignore'):
                    m = re.match(r'\s*(?:nombre|name)\s*[:=]\s*(.+)', line, re.I)
                    if m:
                        return m.group(1).strip().strip('"').strip("'")
        return ''

    yo = _norm(next((a.split('=', 1)[1] for a in sys.argv[1:]
                     if a.startswith('--yo=')), _yo_default()))

    salida = []
    for vid in args:
        ch = canal_de_video(vid)
        if not ch:
            print('no encontrado:', vid, file=sys.stderr)
            continue
        r = invitados_de_canal(ch['channelId'])
        if not r:
            continue
        if yo:
            r['invitados'] = [g for g in r['invitados'] if _norm(g['nombre']) != yo]
        salida.append(r)

        if como_json:
            continue
        print('=' * 72)
        print('SHOW:', r['canal'], '| subs:', r['suscriptores'], '| videos:', r['videos_totales'])
        print('episodios revisados:', r['episodios_revisados'],
              '| invitados detectados:', len(r['invitados']))
        print('-' * 72)
        for g in r['invitados'][:15]:
            print('  %-26s %s  %s' % (g['nombre'], g['fecha'], g['episodio'][:52]))

    if como_json:
        io.open('invitados.json', 'w', encoding='utf-8').write(
            json.dumps(salida, ensure_ascii=False, indent=2))
        print('escrito invitados.json —',
              sum(len(s['invitados']) for s in salida), 'invitados')

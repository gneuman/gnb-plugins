# -*- coding: utf-8 -*-
"""Busca podcasts candidatos en YouTube y los califica.

Presupuesto de cuota (10,000 unidades/dia):
    search        100  <- solo UNA vez por corrida
    channels        1
    playlistItems   1  por pagina de 50
    videos          1  por lote de 50 ids

Una corrida tipica gasta ~130 unidades. Encadenar busquedas es lo unico que
quema la cuota, y por eso este script busca una sola vez y luego navega por
playlist de uploads.

Uso:
    python buscar-youtube.py "automatizacion pymes" --region MX --idioma es
    python buscar-youtube.py "b2b sales" --region US --idioma en --json
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = 'https://www.googleapis.com/youtube/v3/'

PAT_INVITADO = [
    r'\bcon\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+){1,3})',
    r'\bwith\s+([A-Z][\w.\'-]+(?:\s+[A-Z][\w.\'-]+){1,3})',
    r'\bft\.?\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+)',
    r'\|\s*([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+)',
]
# Un episodio de entrevista dura mas de 10 minutos. Debajo de eso es short,
# trailer o clip promocional.
MIN_SEG_EPISODIO = 600

RUIDO = re.compile(r'#shorts|^untitled$|\btutorial\b|\bcurso\b|\bwebinar\b', re.I)
HERRAMIENTAS = re.compile(
    r'\b(google|sheets|zoho|hubspot|whatsapp|telegram|notion|airtable|make|'
    r'zapier|n8n|shopify|stripe|chatgpt|openai|claude|api|crm|excel)\b', re.I)


def key():
    k = os.environ.get('YOUTUBE_API_KEY')
    if k:
        return k
    for p in ('.env.local', '.env'):
        if os.path.exists(p):
            for line in io.open(p, encoding='utf-8', errors='ignore'):
                if line.strip().startswith('YOUTUBE_API_KEY'):
                    return line.split('=', 1)[1].strip().strip('"').strip("'").replace('\\n', '')
    sys.exit("""Falta YOUTUBE_API_KEY.

Es gratis, 3 minutos:
  1. console.cloud.google.com/apis/library/youtube.googleapis.com
  2. Habilitar -> Credenciales -> Crear credenciales -> Clave de API
  3. echo \"YOUTUBE_API_KEY=tu-clave\" >> .env.local

Cuota: 10,000 unidades/dia gratis (una busqueda cuesta 100).

Sin clave YA funcionan: pg-escuchar (transcribe), pg-pitch, pg-setup, pg-store.""")


KEY = key()


def api(path, **params):
    params['key'] = KEY
    url = API + path + '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def dura_mas_de(video, segundos):
    """contentDetails.duration viene en ISO-8601: PT1H2M3S."""
    d = video.get('contentDetails', {}).get('duration', '')
    m = re.match(r'P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', d)
    if not m:
        return False
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se >= segundos


def mediana(xs):
    if not xs:
        return 0
    s = sorted(xs)
    n = len(s)
    # Mediana, no promedio: un solo viral distorsiona el promedio de un show chico.
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) // 2


def es_invitado(titulo):
    if RUIDO.search(titulo):
        return False
    for p in PAT_INVITADO:
        m = re.search(p, titulo)
        if m and not HERRAMIENTAS.search(m.group(1)):
            return True
    return False


def evaluar(channel_id, min_vistas, max_vistas, dias_activo, min_subs=1000):
    """channels(1) + playlistItems(1) + videos(1) = 3 unidades por canal."""
    c = api('channels', part='snippet,statistics,contentDetails', id=channel_id)
    if not c.get('items'):
        return None
    it = c['items'][0]
    uploads = it['contentDetails']['relatedPlaylists']['uploads']
    st = it['statistics']

    pl = api('playlistItems', part='snippet', maxResults=50, playlistId=uploads)
    items = [x for x in pl.get('items', []) if not RUIDO.search(x['snippet']['title'])]
    if not items:
        return None

    ids = [x['snippet']['resourceId']['videoId'] for x in items[:50]]
    vids = api('videos', part='statistics,snippet,contentDetails', id=','.join(ids))

    # Los shorts se detectan por DURACION, no por el titulo: muchos no llevan
    # #shorts y envenenan tanto la mediana de vistas como el ratio de
    # invitados. Sin este filtro, un show de 1,400 episodios con invitado en
    # cada uno sale descartado por 'mediana 22 vistas'.
    largos = [v for v in vids.get('items', []) if dura_mas_de(v, MIN_SEG_EPISODIO)]
    if not largos:
        return {'canal': it['snippet']['title'], 'channelId': channel_id,
                'url': 'https://www.youtube.com/channel/' + channel_id,
                'suscriptores': None, 'videos': int(st.get('videoCount', 0)),
                'vistasMedianas': 0, 'ratioInvitados': 0, 'diasSinPublicar': 9999,
                'califica': False,
                'motivos': ['sin episodios largos en los ultimos %d videos' % len(ids)]}

    # Dedup por titulo: los lives recurrentes suben el MISMO titulo decenas de
    # veces ("Confesiones de SoloEmprendedores #113" x7 en una muestra de 14) e
    # inflan el denominador del ratio hasta descartar un show que si entrevista.
    unicos, vistos_t = [], set()
    for v in largos:
        t = v['snippet']['title'].strip().lower()
        if t not in vistos_t:
            vistos_t.add(t)
            unicos.append(v)
    largos = unicos

    vistas = [int(v['statistics'].get('viewCount', 0)) for v in largos]
    titulos = [v['snippet']['title'] for v in largos]
    con_invitado = sum(1 for t in titulos if es_invitado(t))
    ratio = con_invitado / len(titulos) if titulos else 0

    ultimo = max((v['snippet']['publishedAt'] for v in largos), default='')
    dias = 9999
    if ultimo:
        d = datetime.fromisoformat(ultimo.replace('Z', '+00:00'))
        dias = (datetime.now(timezone.utc) - d).days

    med = mediana(vistas)
    subs = int(st.get('subscriberCount', 0)) if not st.get('hiddenSubscriberCount') else None

    # Tamaño: pasa por vistas O por suscriptores.
    #
    # En español, muchos podcasts publican en Spotify/Apple primero y usan
    # YouTube como canal secundario. Medir solo por vistas los descarta a todos:
    # un show real de 1,400 episodios y 9,000 subs tiene episodios de 53 min con
    # 20 vistas en YouTube — y sigue siendo un show al que vale la pena entrar.
    motivos = []
    pasa_vistas = min_vistas <= med <= max_vistas
    pasa_subs = subs is not None and min_subs <= subs
    if not pasa_vistas and not pasa_subs:
        motivos.append('chico: %d vistas medianas y %s subs' % (med, subs if subs is not None else '?'))
    if med > max_vistas:
        motivos.append('vistas medianas %d > %d (demasiado grande)' % (med, max_vistas))

    # Umbral en 40%: un show de entrevistas intercala episodios en solo, y la
    # deteccion por titulo se pierde los que solo nombran al invitado en la
    # descripcion. Exigir 50% descarta shows que si entrevistan.
    if ratio < 0.4:
        motivos.append('solo %d%% de episodios con invitado' % round(ratio * 100))
    if dias > dias_activo:
        motivos.append('ultimo episodio hace %d dias' % dias)

    return {
        'canal': it['snippet']['title'],
        'channelId': channel_id,
        'url': 'https://www.youtube.com/channel/' + channel_id,
        'suscriptores': subs,
        'videos': int(st.get('videoCount', 0)),
        'vistasMedianas': med,
        'ratioInvitados': round(ratio, 2),
        'diasSinPublicar': dias,
        'califica': not motivos,
        'motivos': motivos,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tema')
    ap.add_argument('--region', default='MX')
    ap.add_argument('--idioma', default='es')
    ap.add_argument('--min-vistas', type=int, default=500)
    ap.add_argument('--max-vistas', type=int, default=50000)
    ap.add_argument('--dias-activo', type=int, default=45)
    ap.add_argument('--min-subs', type=int, default=1000,
                    help='via alterna: shows que publican sobre todo fuera de YouTube')
    ap.add_argument('--max', type=int, default=15, help='canales a evaluar')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    # UNA sola busqueda: 100 unidades. Todo lo demas cuesta 1.
    r = api('search', part='snippet', q=a.tema + ' podcast', type='video',
            maxResults=50, regionCode=a.region, relevanceLanguage=a.idioma,
            order='relevance')

    canales, vistos = [], set()
    for it in r.get('items', []):
        cid = it['snippet']['channelId']
        if cid not in vistos:
            vistos.add(cid)
            canales.append(cid)

    print('candidatos: %d canales unicos (cuota usada: ~%d)' %
          (len(canales), 100 + min(len(canales), a.max) * 3), file=sys.stderr)

    res = []
    for cid in canales[:a.max]:
        try:
            e = evaluar(cid, a.min_vistas, a.max_vistas, a.dias_activo, a.min_subs)
            if e:
                res.append(e)
        except Exception as ex:
            print('  fallo %s: %s' % (cid, ex), file=sys.stderr)

    califican = [x for x in res if x['califica']]
    descartados = [x for x in res if not x['califica']]

    if a.json:
        io.open('shows-candidatos.json', 'w', encoding='utf-8').write(
            json.dumps({'califican': califican, 'descartados': descartados},
                       ensure_ascii=False, indent=2))
        print('escrito shows-candidatos.json — %d califican de %d' % (len(califican), len(res)))
        return

    print('\n=== CALIFICAN (%d de %d) ===' % (len(califican), len(res)))
    for x in califican:
        print('  %-34s %6s subs  vistas~%-6d invitados %d%%  hace %dd' %
              (x['canal'][:34], x['suscriptores'] if x['suscriptores'] is not None else '?',
               x['vistasMedianas'], round(x['ratioInvitados'] * 100), x['diasSinPublicar']))
        print('     %s' % x['url'])

    # Los descartes se imprimen SIEMPRE: "encontre 3" sin decir que revisaste 40
    # oculta que el nicho puede estar agotado.
    print('\n=== DESCARTADOS (%d) ===' % len(descartados))
    for x in descartados:
        print('  %-38s %s' % (x['canal'][:38], '; '.join(x['motivos'])))


if __name__ == '__main__':
    main()

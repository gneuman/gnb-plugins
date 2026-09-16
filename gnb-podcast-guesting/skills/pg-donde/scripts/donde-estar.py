# -*- coding: utf-8 -*-
"""Encuentra shows donde podrias estar, por cinco caminos distintos.

Cada camino responde una pregunta diferente, y por eso se corren juntos: uno
solo deja huecos que los otros ven.

  competidores  ¿Donde han estado los que hacen lo mismo que yo?
                Si invitaron a alguien de tu perfil, invitan a alguien de tu
                perfil. Es la señal mas fuerte que existe.

  coinvitados   ¿En que OTROS shows ha estado la gente que coincidio conmigo?
                Cada uno es una puerta con anclaje: "los dos pasamos por X".

  icp           ¿Que escucha quien me compra?
                No busca shows sobre tu tema — busca shows sobre el PROBLEMA de
                tu cliente. Un consultor de automatizacion no quiere estar en un
                podcast de automatizacion (ahi estan sus competidores): quiere
                estar donde escuchan los duenos de PyME.

  tema          Busqueda abierta por keyword. Cubre lo que no toca tu red.

  directorio    Listen Notes por categoria e idioma. Trae RSS y correo del host,
                y alcanza shows que no publican en YouTube.

Cuota de YouTube (10,000/dia): search 100, todo lo demas 1. Los caminos
`competidores` y `coinvitados` navegan por playlist, asi que cuestan ~3 por
canal. `icp` y `tema` gastan 100 cada uno porque si necesitan buscar.

Uso:
    python donde-estar.py competidores "Nombre Competidor" "Otro Mas"
    python donde-estar.py coinvitados invitados.json
    python donde-estar.py icp "duenos de pyme que quieren escalar" --region MX
    python donde-estar.py tema "automatizacion ventas" --region MX
    python donde-estar.py todo --config wiki-podcast/perfil.md
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

API = 'https://www.googleapis.com/youtube/v3/'
MIN_SEG_EPISODIO = 600

RUIDO = re.compile(
    r'#shorts|^untitled$|\btutorial\b|\bcurso\b|\bwebinar\b|\bclase\s*\d', re.I)
HERRAMIENTAS = re.compile(
    r'\b(google|sheets|zoho|hubspot|whatsapp|telegram|notion|airtable|make|'
    r'zapier|n8n|shopify|stripe|chatgpt|openai|claude|api|crm|excel)\b', re.I)
PAT_INVITADO = [
    r'\bcon\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+){1,3})',
    r'\bwith\s+([A-Z][\w.\'-]+(?:\s+[A-Z][\w.\'-]+){1,3})',
    r'\bft\.?\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.\'-]+)',
]


def key():
    k = os.environ.get('YOUTUBE_API_KEY')
    if k:
        return k
    for p in ('.env.local', '.env'):
        if os.path.exists(p):
            for line in io.open(p, encoding='utf-8', errors='ignore'):
                if line.strip().startswith('YOUTUBE_API_KEY'):
                    return line.split('=', 1)[1].strip().strip('"').strip("'").replace('\\n', '')
    raise SystemExit("""Falta YOUTUBE_API_KEY.

Es gratis, 3 minutos:
  1. console.cloud.google.com/apis/library/youtube.googleapis.com
  2. Habilitar -> Credenciales -> Crear credenciales -> Clave de API
  3. echo \"YOUTUBE_API_KEY=tu-clave\" >> .env.local

Cuota: 10,000 unidades/dia gratis (una busqueda cuesta 100).

Sin clave YA funcionan: pg-escuchar (transcribe), pg-pitch, pg-setup, pg-store.""")


KEY = key()
_gasto = [0]


def api(path, costo=1, **params):
    params['key'] = KEY
    _gasto[0] += costo
    url = API + path + '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def _log(m):
    print(m, file=sys.stderr)


def dura_mas_de(v, seg):
    m = re.match(r'P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',
                 v.get('contentDetails', {}).get('duration', '') or '')
    if not m:
        return False
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se >= seg


def mediana(xs):
    if not xs:
        return 0
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) // 2


def es_invitado(t):
    if RUIDO.search(t):
        return False
    for p in PAT_INVITADO:
        m = re.search(p, t)
        if m and not HERRAMIENTAS.search(m.group(1)):
            return True
    return False


# Niveles de alcanzabilidad. El techo importa tanto como el piso: un show de un
# millon de suscriptores recibe cientos de pitches al mes y no contesta a alguien
# sin historial. Empezar por ahi es perder el tiempo.
#
#   alcanzable  el que SI contesta cuando estas empezando
#   estirado    posible con dos o tres apariciones de respaldo
#   sonado      solo con un caso fuerte o un contacto en comun
NIVELES = [
    ('alcanzable', 300, 15000, 1000, 60000),
    ('estirado', 15000, 60000, 60000, 250000),
    ('sonado', 60000, 10 ** 9, 250000, 10 ** 9),
]


def nivel_de(med, subs):
    for nombre, vmin, vmax, smin, smax in NIVELES:
        if vmin <= med < vmax or (subs and smin <= subs < smax):
            return nombre
    return 'alcanzable'


def evaluar_canal(cid, min_subs=1000, min_vistas=300, max_vistas=60000, dias=90,
                  nivel='alcanzable'):
    """Califica un canal como show al que valdria la pena entrar. ~3 unidades.

    `max_vistas` por defecto deja fuera lo que no contesta cuando arrancas. Para
    ver los grandes: --nivel estirado o --nivel sonado.
    """
    c = api('channels', part='snippet,statistics,contentDetails', id=cid)
    if not c.get('items'):
        return None
    it = c['items'][0]
    st = it['statistics']
    uploads = it['contentDetails']['relatedPlaylists']['uploads']

    pl = api('playlistItems', part='snippet', maxResults=50, playlistId=uploads)
    items = [x for x in pl.get('items', []) if not RUIDO.search(x['snippet']['title'])]
    if not items:
        return None
    ids = [x['snippet']['resourceId']['videoId'] for x in items[:50]]
    vids = api('videos', part='statistics,snippet,contentDetails', id=','.join(ids))

    largos = [v for v in vids.get('items', []) if dura_mas_de(v, MIN_SEG_EPISODIO)]
    if not largos:
        return None
    # Dedup por titulo: los lives recurrentes repiten el mismo titulo e inflan
    # el denominador del ratio de invitados.
    vistos, unicos = set(), []
    for v in largos:
        t = v['snippet']['title'].strip().lower()
        if t not in vistos:
            vistos.add(t)
            unicos.append(v)

    vistas = [int(v['statistics'].get('viewCount', 0)) for v in unicos]
    titulos = [v['snippet']['title'] for v in unicos]
    ratio = sum(1 for t in titulos if es_invitado(t)) / len(titulos)
    med = mediana(vistas)
    subs = int(st.get('subscriberCount', 0)) if not st.get('hiddenSubscriberCount') else None

    from datetime import datetime, timezone
    ultimo = max((v['snippet']['publishedAt'] for v in unicos), default='')
    sin_pub = (datetime.now(timezone.utc) -
               datetime.fromisoformat(ultimo.replace('Z', '+00:00'))).days if ultimo else 9999

    # El techo aplica a AMBAS medidas. Con techo solo en vistas, un canal de
    # 1.09M subs con vistas medianas bajas entraba por la puerta de suscriptores
    # — y ese show recibe cientos de pitches al mes y no contesta a quien empieza.
    max_subs = {'alcanzable': 60000, 'estirado': 250000,
                'sonado': 10 ** 9, 'todos': 10 ** 9}[nivel]
    max_vistas = {'alcanzable': 15000, 'estirado': 60000,
                  'sonado': 10 ** 9, 'todos': 10 ** 9}[nivel]

    motivos = []
    # Piso: pasa por vistas O por subs. Muchos podcasts en español publican
    # primero en Spotify y usan YouTube de canal secundario, asi que medir solo
    # por vistas los descarta a todos.
    if med < min_vistas and not (subs and subs >= min_subs):
        motivos.append('chico: %d vistas / %s subs' % (med, subs))
    # Techo: cualquiera de las dos lo excede.
    if med > max_vistas:
        motivos.append('para despues: %d vistas medianas' % med)
    elif subs and subs > max_subs:
        motivos.append('para despues: %s subs, no contesta a quien empieza' % f'{subs:,}')
    if ratio < 0.4:
        motivos.append('solo %d%% con invitado' % round(ratio * 100))
    if sin_pub > dias:
        motivos.append('inactivo hace %dd' % sin_pub)

    return {
        'canal': it['snippet']['title'], 'channelId': cid,
        'nivel': nivel_de(med, subs),
        'url': 'https://www.youtube.com/channel/' + cid,
        'suscriptores': subs, 'vistasMedianas': med,
        'ratioInvitados': round(ratio, 2), 'diasSinPublicar': sin_pub,
        'califica': not motivos, 'motivos': motivos,
    }


def canales_donde_aparece(nombre, maximo=12):
    """Shows que han tenido a esta persona de invitada. Cuesta 100 (una search)."""
    r = api('search', costo=100, part='snippet', q='"%s" podcast entrevista' % nombre,
            type='video', maxResults=50, order='relevance')
    canales = {}
    for it in r.get('items', []):
        t = it['snippet']['title']
        # El nombre tiene que estar en el titulo: si no, es un video que solo lo
        # menciona, no una entrevista.
        if nombre.lower() not in t.lower():
            continue
        cid = it['snippet']['channelId']
        canales.setdefault(cid, {'canal': it['snippet']['channelTitle'], 'episodios': []})
        canales[cid]['episodios'].append({'titulo': t[:100],
                                          'url': 'https://youtu.be/' + it['id']['videoId']})
    return dict(list(canales.items())[:maximo])


def buscar_por_query(q, region, idioma, maximo=12):
    r = api('search', costo=100, part='snippet', q=q, type='video',
            maxResults=50, regionCode=region, relevanceLanguage=idioma, order='relevance')
    canales, orden = {}, []
    for it in r.get('items', []):
        cid = it['snippet']['channelId']
        if cid not in canales:
            canales[cid] = it['snippet']['channelTitle']
            orden.append(cid)
    return [(c, canales[c]) for c in orden[:maximo]]


# ── Comandos ─────────────────────────────────────────────────────────────────

def cmd_competidores(a):
    """La señal mas fuerte: si invitaron a alguien de tu perfil, te invitan a ti."""
    salida = []
    for nombre in a.nombres:
        _log('buscando donde ha estado %s...' % nombre)
        for cid, info in canales_donde_aparece(nombre).items():
            e = evaluar_canal(cid, nivel=a.nivel)
            if not e:
                continue
            e['porque'] = 'tuvo a %s de invitado' % nombre
            e['evidencia'] = info['episodios'][0]['url'] if info['episodios'] else None
            salida.append(e)
    return salida


def cmd_coinvitados(a):
    """Los shows de tu propia red. Anclaje: coincidieron contigo en otro show."""
    data = json.load(io.open(a.archivo, encoding='utf-8'))
    personas = []
    for s in (data if isinstance(data, list) else [data]):
        for g in s.get('invitados', []):
            personas.append((g['nombre'], s.get('canal', '?')))
    personas = personas[:a.max_personas]
    _log('rastreando %d coinvitados (cuota ~%d)...' % (len(personas), len(personas) * 100))

    salida, vistos = [], set()
    for nombre, origen in personas:
        for cid, info in canales_donde_aparece(nombre, maximo=5).items():
            if cid in vistos:
                continue
            vistos.add(cid)
            e = evaluar_canal(cid, nivel=a.nivel)
            if not e:
                continue
            e['porque'] = '%s estuvo ahi; coincidimos en %s' % (nombre, origen)
            e['evidencia'] = info['episodios'][0]['url'] if info['episodios'] else None
            salida.append(e)
    return salida


def cmd_icp(a):
    """Donde escucha quien te compra — NO donde estan tus competidores.

    Un consultor de automatizacion no quiere entrar a un podcast de
    automatizacion: ahi la audiencia ya sabe. Quiere entrar donde escuchan los
    duenos de PyME que tienen el problema y no saben que existe la solucion.
    """
    salida = []
    for q in a.queries:
        # Sin "podcast entrevista invitado" la busqueda devuelve canales de
        # creadores que hablan EN SOLO al ICP, no shows que reciben invitados.
        # Probado: la query cruda dio 0 de 10, todos canales de una persona.
        _log('buscando shows para: %s' % q)
        for cid, nombre in buscar_por_query(q + ' podcast entrevista invitado',
                                            a.region, a.idioma):
            e = evaluar_canal(cid, nivel=a.nivel)
            if not e:
                continue
            e['porque'] = 'su audiencia es el ICP: %s' % q
            salida.append(e)
    return salida


def cmd_tema(a):
    salida = []
    for q in a.queries:
        _log('buscando por tema: %s' % q)
        for cid, nombre in buscar_por_query(q + ' podcast', a.region, a.idioma):
            e = evaluar_canal(cid, nivel=a.nivel)
            if not e:
                continue
            e['porque'] = 'tema afin: %s' % q
            salida.append(e)
    return salida


def reportar(res, a):
    # Dedup por canal, quedandose con la razon mas fuerte (el primero que llego).
    vistos, unicos = set(), []
    for e in res:
        if e['channelId'] in vistos:
            continue
        vistos.add(e['channelId'])
        unicos.append(e)

    califican = [x for x in unicos if x['califica']]
    descartados = [x for x in unicos if not x['califica']]
    califican.sort(key=lambda x: -(x['suscriptores'] or 0))

    if a.json:
        io.open('donde-estar.json', 'w', encoding='utf-8').write(
            json.dumps({'califican': califican, 'descartados': descartados},
                       ensure_ascii=False, indent=2))
        print('escrito donde-estar.json — %d califican de %d' % (len(califican), len(unicos)))
        return

    print('\n=== CALIFICAN (%d de %d) ===' % (len(califican), len(unicos)))
    for x in califican:
        print('  [%-10s] %-28s %7s subs  invitados %d%%' % (
            x.get('nivel', '?'), x['canal'][:28],
            x['suscriptores'] if x['suscriptores'] is not None else '?',
            round(x['ratioInvitados'] * 100)))
        print('     %s' % x['porque'])
        print('     %s' % x['url'])
    # Los descartes se imprimen siempre: "encontre 3" sin decir que revisaste 40
    # oculta que el camino esta agotado.
    print('\n=== DESCARTADOS (%d) ===' % len(descartados))
    for x in descartados:
        print('  %-32s %s' % (x['canal'][:32], '; '.join(x['motivos'])))
    print('\ncuota usada: ~%d unidades de 10,000' % _gasto[0], file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    def comunes(p):
        p.add_argument('--region', default='MX')
        p.add_argument('--idioma', default='es')
        p.add_argument('--nivel', default='alcanzable',
                       choices=['alcanzable', 'estirado', 'sonado', 'todos'],
                       help='alcanzable = el que si contesta cuando empiezas')
        p.add_argument('--json', action='store_true')

    p = sub.add_parser('competidores', help='shows que invitaron a tus competidores')
    p.add_argument('nombres', nargs='+'); comunes(p); p.set_defaults(fn=cmd_competidores)

    p = sub.add_parser('coinvitados', help='otros shows de quienes coincidieron contigo')
    p.add_argument('archivo'); p.add_argument('--max-personas', type=int, default=8)
    comunes(p); p.set_defaults(fn=cmd_coinvitados)

    p = sub.add_parser('icp', help='shows que escucha tu cliente ideal')
    p.add_argument('queries', nargs='+'); comunes(p); p.set_defaults(fn=cmd_icp)

    p = sub.add_parser('tema', help='busqueda abierta por keyword')
    p.add_argument('queries', nargs='+'); comunes(p); p.set_defaults(fn=cmd_tema)

    a = ap.parse_args()
    reportar(a.fn(a), a)


if __name__ == '__main__':
    main()

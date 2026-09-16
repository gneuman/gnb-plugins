# -*- coding: utf-8 -*-
"""Almacenamiento del sistema de podcast guesting.

Local por defecto, CRM si hay credenciales. Nunca al revés: un agente que corre
solo no puede detenerse a preguntar si hay base de datos.

Uso:
    python store.py init
    python store.py show     "Nombre del Show" --youtube-channel UCxxx --subs 9030
    python store.py persona  "Nombre Apellido" --show "Nombre del Show" --bucket plataforma \
                             --porque "tiene newsletter propia, cross-promo natural"
    python store.py envio    nombre-apellido --canal linkedin
    python store.py respuesta nombre-apellido
    python store.py etapa    nombre-del-show --a pitcheado
    python store.py kpi
    python store.py importar invitados.json --show "Nombre del Show"
"""
import argparse
import json
import io
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

DIR = '.podcast-guesting'
ARCHIVOS = {
    'shows': 'shows.json',
    'personas': 'personas.json',
    'mensajes': 'mensajes.json',
    'eventos': 'eventos.json',
}

ETAPAS_SHOW = ['prospecto', 'pitcheado', 'vio_onesheet', 'respondio', 'agendado',
               'grabado', 'publicado', 'distribuido', 'rechazado', 'descartado']
ETAPAS_PERSONA = ['identificado', 'investigado', 'contactado', 'respondio',
                  'llamada', 'alianza', 'sin_respuesta', 'descartado']
BUCKETS = ['plataforma', 'referido', 'cliente', 'dfy', 'competencia', 'sin_definir']

# Etapas que ya pasaron por "pitch enviado": el denominador del KPI.
PITCHEADAS = ['pitcheado', 'vio_onesheet', 'respondio', 'agendado',
              'grabado', 'publicado', 'distribuido']
# vio_onesheet NO esta aqui: es senal de intencion, no respuesta humana.
CON_RESPUESTA = ['respondio', 'agendado', 'grabado', 'publicado', 'distribuido']
GANADAS = ['grabado', 'publicado', 'distribuido']
P_CONTACTADAS = ['contactado', 'respondio', 'llamada', 'alianza', 'sin_respuesta']
P_RESPONDIERON = ['respondio', 'llamada', 'alianza']


def ahora():
    return datetime.now(timezone.utc).isoformat()


def slug(s):
    s = unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'-+$', '', re.sub(r'^-+', '', re.sub(r'[^a-z0-9]+', '-', s.lower())))[:60]


def ruta(k):
    return os.path.join(DIR, ARCHIVOS[k])


def leer(k):
    p = ruta(k)
    if not os.path.exists(p):
        return []
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def escribir(k, data):
    os.makedirs(DIR, exist_ok=True)
    with io.open(ruta(k), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_error(msg):
    os.makedirs(DIR, exist_ok=True)
    with io.open(os.path.join(DIR, 'errores.log'), 'a', encoding='utf-8') as f:
        f.write('%s  %s\n' % (ahora(), msg))


# ── Sync opcional al CRM ──────────────────────────────────────────────────────

def crm_config():
    url, token = os.environ.get('GNB_CRM_URL'), os.environ.get('GNB_CRM_TOKEN')
    return (url.rstrip('/'), token) if url and token else (None, None)


def es_worker(url):
    """El Worker de Cloudflare y el CRM de GNB exponen rutas distintas.

    Se distingue por la URL en vez de pedir otra variable de entorno: una
    variable mas es una cosa mas que el cliente puede configurar mal.
    """
    return 'workers.dev' in url or os.environ.get('PG_BACKEND') == 'worker'


def ruta_api(kind, slug=None):
    url, _ = crm_config()
    if not url:
        return None
    if es_worker(url):
        return {'alta_show': '/api/shows', 'alta_persona': '/api/personas',
                'mensaje': '/api/mensajes', 'respuesta': '/api/mensajes',
                'etapa': '/api/etapa'}[kind]
    return {'alta_show': '/api/v1/podcasts', 'alta_persona': '/api/v1/podcasts',
            'mensaje': '/api/v1/podcasts/%s/mensajes' % slug,
            'respuesta': '/api/v1/podcasts/%s/respuesta' % slug,
            'etapa': '/api/v1/podcasts/%s/etapa' % slug}[kind]


def crm_post(path, payload):
    """Best-effort. Un backend caido nunca detiene el outreach.

    Excepcion: un 401 se reporta a stderr — token malo significa que el pipeline
    se vaciaria en silencio, y eso si hay que verlo.
    """
    if not path:
        return None
    url, token = crm_config()
    if not url:
        return None
    import urllib.request, urllib.error
    req = urllib.request.Request(
        url + path,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print('  [!] CRM rechazo el token (401). Revisa GNB_CRM_TOKEN.', file=sys.stderr)
        log_error('POST %s -> HTTP %s' % (path, e.code))
    except Exception as e:
        log_error('POST %s -> %s' % (path, e))
    return None


# ── Comandos ──────────────────────────────────────────────────────────────────

def cmd_init(a):
    os.makedirs(DIR, exist_ok=True)
    for k in ARCHIVOS:
        if not os.path.exists(ruta(k)):
            escribir(k, [])
    gi = os.path.join(DIR, '.gitignore')
    if not os.path.exists(gi):
        # Nombres y correos de terceros: nunca a git.
        io.open(gi, 'w', encoding='utf-8').write('*\n')
    url, _ = crm_config()
    print('listo en %s/' % DIR)
    print('destino: CRM + local' if url else 'destino: local (sin GNB_CRM_URL/TOKEN)')


def _upsert(k, doc, clave='slug'):
    """Idempotente: correr dos veces la misma alta no duplica."""
    data = leer(k)
    for i, x in enumerate(data):
        if x.get(clave) == doc[clave]:
            x.update({kk: vv for kk, vv in doc.items() if vv is not None})
            x['updatedAt'] = ahora()
            data[i] = x
            escribir(k, data)
            return x, False
    data.append(doc)
    escribir(k, data)
    return doc, True


def cmd_show(a):
    s = slug(a.nombre)
    doc = {'slug': s, 'nombre': a.nombre, 'tipo': 'show', 'stage': 'prospecto',
           'youtubeChannelId': a.youtube_channel, 'suscriptores': a.subs,
           'episodiosTotales': a.episodios, 'hostNombre': a.host,
           'notas': a.notas or '', 'mensajes': [],
           'createdAt': ahora(), 'updatedAt': ahora()}
    doc, nuevo = _upsert('shows', doc)
    crm_post(ruta_api('alta_show'), doc)
    print('%s  %s (%s)' % ('creado' if nuevo else 'actualizado', a.nombre, s))


def cmd_persona(a):
    if a.bucket not in BUCKETS:
        sys.exit('bucket invalido: %s (validos: %s)' % (a.bucket, ', '.join(BUCKETS)))
    s = slug(a.nombre)
    doc = {'slug': s, 'nombre': a.nombre, 'tipo': 'persona', 'stage': 'identificado',
           'bucket': a.bucket, 'bucketPorque': a.porque, 'showOrigen': a.show,
           'episodioSuyo': {'url': a.episodio} if a.episodio else None,
           'linkedin': a.linkedin, 'notas': a.notas or '', 'mensajes': [],
           'personaRef': s, 'createdAt': ahora(), 'updatedAt': ahora()}
    doc, nuevo = _upsert('personas', doc)
    crm_post(ruta_api('alta_persona'), doc)
    print('%s  %s [%s]' % ('creada' if nuevo else 'actualizada', a.nombre, a.bucket))


def _buscar(s):
    for k in ('shows', 'personas'):
        for x in leer(k):
            if x['slug'] == s:
                return k, x
    return None, None


def cmd_envio(a):
    k, doc = _buscar(a.slug)
    if not doc:
        sys.exit('no encontrado: %s' % a.slug)

    data = leer(k)
    for x in data:
        if x['slug'] != a.slug:
            continue
        x.setdefault('mensajes', []).append({
            'fecha': ahora(), 'canal': a.canal, 'asunto': a.asunto,
            'followUp': len(x.get('mensajes', [])), 'respondido': False})
        # El envio adelanta la etapa inicial: sin esto no hay denominador.
        if x['tipo'] == 'show' and x['stage'] == 'prospecto':
            x['stage'] = 'pitcheado'
        elif x['tipo'] == 'persona' and x['stage'] in ('identificado', 'investigado'):
            x['stage'] = 'contactado'
        x['updatedAt'] = ahora()
        n = len(x['mensajes'])
        break
    escribir(k, data)

    ms = leer('mensajes')
    ms.append({'slug': a.slug, 'canal': a.canal, 'fecha': ahora(), 'followUp': n - 1})
    escribir('mensajes', ms)
    crm_post(ruta_api('mensaje', a.slug), {'targetId': a.slug, 'canal': a.canal, 'asunto': a.asunto})
    print('envio #%d registrado a %s por %s' % (n, doc['nombre'], a.canal))


def cmd_respuesta(a):
    k, doc = _buscar(a.slug)
    if not doc:
        sys.exit('no encontrado: %s' % a.slug)
    data = leer(k)
    for x in data:
        if x['slug'] != a.slug:
            continue
        for m in reversed(x.get('mensajes', [])):
            if not m.get('respondido'):
                m['respondido'] = True
                m['respondidoEn'] = ahora()
                break
        x['stage'] = 'respondio'
        x['updatedAt'] = ahora()
        break
    escribir(k, data)
    crm_post(ruta_api('respuesta', a.slug), {'targetId': a.slug, 'respondido': True})
    print('%s respondio' % doc['nombre'])


def cmd_etapa(a):
    k, doc = _buscar(a.slug)
    if not doc:
        sys.exit('no encontrado: %s' % a.slug)
    validas = ETAPAS_SHOW if doc['tipo'] == 'show' else ETAPAS_PERSONA
    if a.a not in validas:
        sys.exit('etapa invalida para %s: %s\nvalidas: %s' % (doc['tipo'], a.a, ', '.join(validas)))
    data = leer(k)
    for x in data:
        if x['slug'] == a.slug:
            x['stage'] = a.a
            x['updatedAt'] = ahora()
            # Marca permanente: el KPI cuenta cuantos ABRIERON el one-sheet
            # alguna vez, no cuantos estan parados ahi hoy. Sin esto, un show
            # que abre y luego agenda deja de contarse y la tasa da 0%.
            if a.a == 'vio_onesheet' or a.a in CON_RESPUESTA:
                x['vioOnesheet'] = True
    escribir(k, data)
    crm_post(ruta_api('etapa', a.slug), {'targetId': a.slug, 'tipo': doc['tipo'], 'stage': a.a, 'etapa': a.a})
    print('%s -> %s' % (doc['nombre'], a.a))


def cmd_importar(a):
    """Importa la salida de pg-invitados. Entran como sin_definir a proposito:
    clasificar sin investigar es adivinar."""
    with io.open(a.archivo, encoding='utf-8') as f:
        data = json.load(f)
    shows = data if isinstance(data, list) else [data]
    n_nuevos = n_dup = 0
    for sh in shows:
        origen = sh.get('canal', a.show or '?')
        for g in sh.get('invitados', []):
            s = slug(g['nombre'])
            doc = {'slug': s, 'nombre': g['nombre'], 'tipo': 'persona',
                   'stage': 'identificado', 'bucket': 'sin_definir',
                   'showOrigen': origen,
                   'episodioSuyo': {'titulo': g.get('episodio'), 'url': g.get('url'),
                                    'fecha': g.get('fecha')},
                   'notas': '', 'mensajes': [], 'personaRef': s,
                   'createdAt': ahora(), 'updatedAt': ahora()}
            _, nuevo = _upsert('personas', doc)
            n_nuevos += nuevo
            n_dup += (not nuevo)
    print('importados: %d nuevos, %d ya existian' % (n_nuevos, n_dup))


def _pct(n, d):
    # None, no 0: "sin datos" no es "0%" y no debe pintar rojo en el tablero.
    return None if d <= 0 else round(n / d * 1000) / 10


def cmd_kpi(a):
    shows = [x for x in leer('shows') if not x.get('archived')]
    personas = [x for x in leer('personas') if not x.get('archived')]

    pitch = len([x for x in shows if x['stage'] in PITCHEADAS])
    resp = len([x for x in shows if x['stage'] in CON_RESPUESTA])
    vieron = len([x for x in shows if x.get('vioOnesheet')])
    agend = len([x for x in shows if x['stage'] in ['agendado'] + GANADAS])
    grab = len([x for x in shows if x['stage'] in GANADAS])

    p_cont = len([x for x in personas if x['stage'] in P_CONTACTADAS])
    p_resp = len([x for x in personas if x['stage'] in P_RESPONDIERON])

    envs = sum(len(x.get('mensajes', [])) for x in shows + personas)
    rsps = sum(len([m for m in x.get('mensajes', []) if m.get('respondido')])
               for x in shows + personas)

    def f(v):
        return '—' if v is None else '%.1f%%' % v

    print('SHOWS')
    print('  prospecto ........ %d' % len([x for x in shows if x['stage'] == 'prospecto']))
    print('  pitcheados ....... %d' % pitch)
    print('  vieron one-sheet . %d   %s' % (vieron, f(_pct(vieron, pitch))))
    print('  respondieron ..... %d   %s' % (resp, f(_pct(resp, pitch))))
    print('  agendados ........ %d   %s' % (agend, f(_pct(agend, pitch))))
    print('  GRABADOS ......... %d' % grab)
    print()
    print('PERSONAS (%d)' % len(personas))
    for b in BUCKETS:
        n = len([x for x in personas if x.get('bucket') == b])
        if n:
            print('  %-12s %d' % (b, n))
    print('  contactadas ...... %d' % p_cont)
    print('  respondieron ..... %d   %s' % (p_resp, f(_pct(p_resp, p_cont))))
    print()
    print('MENSAJES  enviados: %d  respondidos: %d  %s' % (envs, rsps, f(_pct(rsps, envs))))
    url, _ = crm_config()
    print('\ndestino: %s' % ('CRM + local' if url else 'local'))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    sub.add_parser('init').set_defaults(fn=cmd_init)

    p = sub.add_parser('show'); p.set_defaults(fn=cmd_show)
    p.add_argument('nombre')
    p.add_argument('--youtube-channel'); p.add_argument('--subs', type=int)
    p.add_argument('--episodios', type=int); p.add_argument('--host'); p.add_argument('--notas')

    p = sub.add_parser('persona'); p.set_defaults(fn=cmd_persona)
    p.add_argument('nombre'); p.add_argument('--show', required=True)
    p.add_argument('--bucket', default='sin_definir'); p.add_argument('--porque')
    p.add_argument('--episodio'); p.add_argument('--linkedin'); p.add_argument('--notas')

    p = sub.add_parser('envio'); p.set_defaults(fn=cmd_envio)
    p.add_argument('slug'); p.add_argument('--canal', default='linkedin')
    p.add_argument('--asunto')

    p = sub.add_parser('respuesta'); p.set_defaults(fn=cmd_respuesta); p.add_argument('slug')

    p = sub.add_parser('etapa'); p.set_defaults(fn=cmd_etapa)
    p.add_argument('slug'); p.add_argument('--a', required=True)

    p = sub.add_parser('importar'); p.set_defaults(fn=cmd_importar)
    p.add_argument('archivo'); p.add_argument('--show')

    sub.add_parser('kpi').set_defaults(fn=cmd_kpi)

    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()

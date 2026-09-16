# -*- coding: utf-8 -*-
"""Transcribe un episodio de podcast desde YouTube.

Estrategia en tres niveles, del mas barato al mas caro. La mayoria de los
episodios se resuelven en el nivel 1, en segundos y sin costo:

  1. Subtitulos del autor      yt-dlp --write-subs        ~5s, gratis, exactos
  2. Subtitulos automaticos    yt-dlp --write-auto-subs   ~10s, gratis, buenos
  3. Whisper local             ffmpeg + whisper           minutos, gratis, CPU

El nivel 3 solo se intenta si esta instalado y si los dos primeros fallaron.
Un podcast sin subtitulos en YouTube es raro; pagar por transcribir lo que ya
esta escrito es tirar dinero.

Uso:
    python transcribir.py https://youtu.be/VIDEO_ID
    python transcribir.py VIDEO_ID --idioma es --salida transcripcion.txt
    python transcribir.py VIDEO_ID --json     # con timestamps
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request


def _log(msg):
    print(msg, file=sys.stderr)


def video_id(url_o_id):
    """Acepta URL completa, youtu.be, /live/ o el id pelado."""
    if re.fullmatch(r'[\w-]{11}', url_o_id):
        return url_o_id
    m = re.search(r'(?:v=|youtu\.be/|/live/|/embed/|/shorts/)([\w-]{11})', url_o_id)
    if m:
        return m.group(1)
    sys.exit('No pude sacar el ID del video de: %s' % url_o_id)


def _yt_dlp(*args):
    if not shutil.which('yt-dlp'):
        sys.exit('Falta yt-dlp. Instala con: pip install yt-dlp')
    return subprocess.run(['yt-dlp', *args], capture_output=True, text=True, timeout=300)


def json3_a_texto(ruta):
    """json3 trae los segmentos partidos por palabra; se reconstruyen con su tiempo."""
    d = json.load(io.open(ruta, encoding='utf-8'))
    lineas = []
    for e in d.get('events', []):
        segs = e.get('segs') or []
        texto = ''.join(s.get('utf8', '') for s in segs).strip()
        if texto:
            lineas.append({'ms': e.get('tStartMs', 0), 'texto': texto})
    return lineas


def bajar_subs(vid, idioma, tmp, automaticos):
    flag = '--write-auto-subs' if automaticos else '--write-subs'
    base = os.path.join(tmp, 'sub')
    r = _yt_dlp(flag, '--sub-langs', idioma, '--sub-format', 'json3',
                '--skip-download', '-o', base + '.%(ext)s',
                'https://www.youtube.com/watch?v=' + vid)
    if r.returncode != 0:
        return None
    for f in os.listdir(tmp):
        if f.endswith('.json3'):
            return json3_a_texto(os.path.join(tmp, f))
    return None


def por_whisper(vid, idioma, tmp):
    """Ultimo recurso: baja el audio y lo pasa por Whisper local."""
    if not shutil.which('whisper'):
        _log('  whisper no esta instalado (pip install openai-whisper) — sin nivel 3')
        return None
    if not shutil.which('ffmpeg'):
        _log('  ffmpeg no esta instalado — sin nivel 3')
        return None

    _log('  bajando audio (esto tarda)...')
    audio = os.path.join(tmp, 'audio.m4a')
    r = _yt_dlp('-f', 'bestaudio[ext=m4a]/bestaudio', '-o', audio,
                'https://www.youtube.com/watch?v=' + vid)
    if r.returncode != 0 or not os.path.exists(audio):
        _log('  no pude bajar el audio')
        return None

    _log('  transcribiendo con whisper (varios minutos)...')
    subprocess.run(['whisper', audio, '--language', idioma, '--model', 'base',
                    '--output_format', 'json', '--output_dir', tmp],
                   capture_output=True, text=True, timeout=3600)
    for f in os.listdir(tmp):
        if f.endswith('.json') and 'audio' in f:
            d = json.load(io.open(os.path.join(tmp, f), encoding='utf-8'))
            return [{'ms': int(s['start'] * 1000), 'texto': s['text'].strip()}
                    for s in d.get('segments', [])]
    return None


def _api_key():
    k = os.environ.get('YOUTUBE_API_KEY')
    if k:
        return k
    for p in ('.env.local', '.env'):
        if os.path.exists(p):
            for line in io.open(p, encoding='utf-8', errors='ignore'):
                if line.strip().startswith('YOUTUBE_API_KEY'):
                    return line.split('=', 1)[1].strip().strip('"').strip("'").replace('\n', '')
    return None


def _iso_a_seg(d):
    m = re.match(r'P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', d or '')
    if not m:
        return None
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se


def metadata(vid):
    """Datos del video: primero la Data API, si no yt-dlp.

    La API cuesta 1 unidad y da algo que yt-dlp no trae: los `tags` del video,
    que dicen de que va el show sin tener que leer la descripcion. Si no hay
    key, yt-dlp cubre todo lo demas sin cuota.
    """
    key = _api_key()
    if key:
        try:
            url = ('https://www.googleapis.com/youtube/v3/videos'
                   '?part=snippet,statistics,contentDetails&id=' + vid + '&key=' + key)
            with urllib.request.urlopen(url, timeout=25) as r:
                d = json.load(r)
            if d.get('items'):
                it = d['items'][0]
                sn, st = it['snippet'], it.get('statistics', {})
                return {
                    'titulo': sn.get('title'),
                    'canal': sn.get('channelTitle'),
                    'canalId': sn.get('channelId'),
                    'fecha': (sn.get('publishedAt') or '')[:10],
                    'duracionSeg': _iso_a_seg(it.get('contentDetails', {}).get('duration')),
                    'vistas': int(st['viewCount']) if st.get('viewCount') else None,
                    'tags': sn.get('tags', []),
                    'descripcion': (sn.get('description') or '')[:2000],
                    'url': 'https://youtu.be/' + vid,
                    'fuenteMeta': 'youtube-data-api',
                }
        except Exception as e:
            _log('  la Data API fallo (%s); uso yt-dlp' % e)

    r = _yt_dlp('--dump-json', '--skip-download',
                'https://www.youtube.com/watch?v=' + vid)
    if r.returncode != 0:
        return {}
    d = json.loads(r.stdout)
    fecha = d.get('upload_date') or ''
    return {
        'titulo': d.get('title'),
        'canal': d.get('uploader'),
        'canalId': d.get('channel_id'),
        # yt-dlp devuelve YYYYMMDD; se normaliza a ISO para que no cambie el
        # formato de la salida segun de donde vinieron los datos.
        'fecha': '%s-%s-%s' % (fecha[:4], fecha[4:6], fecha[6:8]) if len(fecha) == 8 else fecha,
        'duracionSeg': d.get('duration'),
        'vistas': d.get('view_count'),
        'tags': d.get('tags') or [],
        'descripcion': (d.get('description') or '')[:2000],
        'url': 'https://youtu.be/' + vid,
        'fuenteMeta': 'yt-dlp',
    }


def hhmmss(ms):
    s = ms // 1000
    return '%02d:%02d:%02d' % (s // 3600, (s % 3600) // 60, s % 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--idioma', default='es')
    ap.add_argument('--salida', help='archivo destino (default: stdout)')
    ap.add_argument('--json', action='store_true', help='incluye timestamps y metadata')
    ap.add_argument('--sin-whisper', action='store_true', help='no intentar el nivel 3')
    a = ap.parse_args()

    vid = video_id(a.video)
    tmp = tempfile.mkdtemp(prefix='pg-transcribir-')
    try:
        lineas, fuente = None, None

        _log('1/3 subtitulos del autor...')
        lineas = bajar_subs(vid, a.idioma, tmp, automaticos=False)
        if lineas:
            fuente = 'subtitulos-autor'

        if not lineas:
            _log('2/3 subtitulos automaticos...')
            lineas = bajar_subs(vid, a.idioma, tmp, automaticos=True)
            if lineas:
                fuente = 'subtitulos-automaticos'

        if not lineas and not a.sin_whisper:
            _log('3/3 whisper local...')
            lineas = por_whisper(vid, a.idioma, tmp)
            if lineas:
                fuente = 'whisper'

        if not lineas:
            sys.exit('No pude transcribir el video %s en idioma "%s".\n'
                     'Prueba con otro --idioma, o instala whisper para el nivel 3.' % (vid, a.idioma))

        meta = metadata(vid)
        texto = ' '.join(x['texto'] for x in lineas)
        _log('listo: %s — %d palabras (fuente: %s)' % (vid, len(texto.split()), fuente))

        if a.json:
            salida = json.dumps({'video': vid, 'fuente': fuente, 'meta': meta,
                                 'texto': texto, 'lineas': lineas},
                                ensure_ascii=False, indent=2)
        else:
            cab = ['# %s' % (meta.get('titulo') or vid),
                   '', '- Canal: %s' % meta.get('canal'),
                   '- Fecha: %s' % meta.get('fecha'),
                   '- URL: %s' % meta.get('url'),
                   '- Fuente de la transcripcion: %s' % fuente, '', '---', '']
            # Bloques de ~2 min con timestamp: sirven para citar un momento exacto
            # en el pitch, que es lo unico que prueba que si lo escuchaste.
            cuerpo, buf, marca = [], [], None
            for x in lineas:
                if marca is None or x['ms'] - marca >= 120000:
                    if buf:
                        cuerpo.append('[%s] %s' % (hhmmss(marca), ' '.join(buf)))
                    marca, buf = x['ms'], []
                buf.append(x['texto'])
            if buf:
                cuerpo.append('[%s] %s' % (hhmmss(marca), ' '.join(buf)))
            salida = '\n'.join(cab) + '\n\n'.join(cuerpo) + '\n'

        if a.salida:
            io.open(a.salida, 'w', encoding='utf-8').write(salida)
            print('escrito %s' % a.salida)
        else:
            sys.stdout.write(salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()

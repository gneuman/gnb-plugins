---
name: pg-escuchar
description: >
  Transcribe un episodio de podcast de YouTube para poder citarlo con
  precisión en el pitch. Baja subtítulos si existen (segundos, gratis) y solo
  usa Whisper si no hay. Úsalo cuando el usuario diga "transcribe este
  episodio", "de qué habla este podcast", "escucha este video", "saca la
  transcripción", "/pg-escuchar", o antes de escribir un pitch cuando no
  conoces el contenido del show.
---

# pg-escuchar — la materia prima del pitch

Un pitch que dice "me encantó tu episodio" sin decir **qué** se archiva. Uno que
cita un momento exacto se contesta. Este skill produce ese momento.

Es la diferencia entre haber visto el título y haber escuchado el episodio — y
un host la nota en dos segundos.

## Tres niveles, del más barato al más caro

| Nivel | Método | Tiempo | Costo |
|---|---|---|---|
| 1 | Subtítulos del autor | ~5s | $0 |
| 2 | Subtítulos automáticos de YouTube | ~10s | $0 |
| 3 | Whisper local (ffmpeg + whisper) | minutos | $0, CPU |

**La mayoría se resuelve en el nivel 2.** Casi todos los podcasts en YouTube
tienen subtítulos automáticos, y en español son buenos. Transcribir con Whisper
lo que ya está escrito es tirar tiempo y electricidad — por eso el nivel 3 solo
corre si los dos primeros fallan.

```bash
python scripts/transcribir.py https://youtu.be/VIDEO_ID --salida ep.md
python scripts/transcribir.py VIDEO_ID --json          # timestamps + metadata
python scripts/transcribir.py VIDEO_ID --sin-whisper   # nunca nivel 3
```

Acepta URL completa, `youtu.be`, `/live/` o el ID pelado.

### Por qué no se usa la YouTube Data API

Pregunta razonable: si ya usamos la API para todo lo demás, ¿por qué aquí no?

Porque **`captions.download` no acepta API key**. Verificado contra un episodio
real de un canal ajeno:

```
GET /youtube/v3/captions?part=snippet&videoId=... &key=...   → 200 OK
    (lista las pistas: lang=es, kind=asr)

GET /youtube/v3/captions/{id}?tfmt=srt &key=...              → 401
    "API keys are not supported by this API. Expected OAuth2 access token..."
```

Y aun con OAuth2, YouTube solo permite descargar los subtítulos de **videos
propios** — el dueño del canal tiene que autorizar. Para el podcast de otra
persona, que es todo el caso de uso, no hay camino por la API.

`captions.list` sí funciona con key y sirve de **sonda**: dice en qué idiomas
hay pista y si es `asr` (automática) o `standard` (del autor), antes de bajar
nada. Cuesta **50 unidades** de cuota, contra 0 de yt-dlp, así que solo vale la
pena si necesitas decidir el idioma sin intentar la descarga.

### Requisitos

- **`yt-dlp`** — obligatorio (`pip install yt-dlp`). Sin esto no hay nada.
- **`ffmpeg` + `whisper`** — opcionales, solo para el nivel 3.

## Qué produce

Markdown con cabecera (título, canal, fecha, URL, **de qué fuente salió la
transcripción**) y el cuerpo en bloques de ~2 minutos con timestamp.

Los timestamps son el punto: permiten citar *"cuando dijiste en el minuto 12
que…"*, que es la frase que separa un pitch leído de uno inventado.

Declarar la fuente importa: los subtítulos automáticos traen errores de nombres
propios. Si vas a citar textual, **verifica esa frase en el video**.

## Qué buscar en la transcripción

Para un pitch:

1. **La tesis del host** — qué defiende, qué le molesta del mercado.
2. **Un momento concreto** — una cifra, una objeción, una frase con filo.
3. **Cómo llama a su audiencia** — el host de un show dice "David" o "founder"
   o "los Goliat". Usar su palabra prueba que escuchaste.
4. **Qué le preguntan siempre** — para no repetir lo que ya cubrió.

Para tu propio episodio, además: **la presentación que hizo de ti.** Ahí suelen
estar tus cifras dichas por un tercero, que es la forma más creíble de tenerlas.

## Límites

- **Solo YouTube.** Un show que solo publica en Spotify o Apple no se cubre por
  aquí. Para esos, baja el audio del RSS y usa el nivel 3.
- **Los subtítulos automáticos erran en nombres propios** y a veces en cifras.
  Verifica antes de citar textual.
- **No resume.** Devuelve la transcripción completa. Resumir es trabajo del
  agente que la lee, con el criterio de para qué la necesita.

## Encadenado

```
/pg-research    → encuentra el show
/pg-escuchar    → transcribe un episodio reciente   ← aquí
/pg-pitch       → escribe el pitch citando ese momento
/pg-invitados   → cosecha a los coinvitados
```

## MAA

- **Medir:** tasa de respuesta de pitches con cita textual vs. sin ella.
- **Analizar:** si no hay diferencia, la cita es decorativa — probablemente
  genérica. Una cita real menciona algo que solo aparece en ese episodio.
- **Actuar:** guardar en `pitch-ganadores.md` qué tipo de cita funcionó.

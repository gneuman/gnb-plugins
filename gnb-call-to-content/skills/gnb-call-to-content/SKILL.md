---
name: gnb-call-to-content
description: >
  Convierte una llamada grabada (Zoom, Loom, podcast, webinar, masterclass) en un plan de
  contenido distribuible: 5 posts LinkedIn, hilo + 10 tweets, carrusel de 10 slides, 10
  imágenes con prompts, 5 correos. Output JSON estructurado listo para importar en sistema
  de publicación o pegar manualmente.
  Use when: "convierte esta llamada en contenido", "repurpose del Zoom", "saca contenido del
  Loom", "transcripción a posts", "/call-to-content", "gnb-call-to-content".
related: [gnb-call-to-voc]
---

# GNB Call to Content

Transforma cualquier llamada grabada en contenido distribuible. Input flexible (transcripción, notas, URL del video, descripción), output JSON estructurado con 5 LinkedIn + 15 tweets + 10 slides + 10 imágenes + 5 correos.

> **Antes de correr este skill:** lee el bloque `[CUSTOMIZE]` al final. Define `$AUTHOR_VOICE`, `$INTERNAL_LINKS` y `$OUTPUT_PATH` para tu autor/agencia.

## Tipos de llamada soportados

| Tipo | Input típico | Énfasis del contenido |
|---|---|---|
| **Podcast** | transcripción + título + URL Spotify/YT | invitado, insights, citas textuales |
| **Webinar / masterclass** | recording + slides + Q&A | enseñanza estructurada, framework |
| **Discovery / sales call** | transcripción | NO usar — privacy. Para insights internos usar `gnb-call-to-voc` |
| **Loom interno** | transcripción + contexto | decisión tomada, behind-the-scenes |
| **Live LinkedIn / Twitter Space** | transcripción + chat | mejores momentos, hot takes |

**Regla dura:** si la llamada es discovery/sales con cliente, NO generar contenido público. Usar `gnb-call-to-voc` para insights internos.

## Antes de empezar

Necesitas al menos uno:
- **Título** + **descripción o notas**
- **Transcripción o fragmentos clave**
- **URL** del video/audio en plataforma pública

Si falta info, preguntar:
1. ¿Qué tipo de llamada es? (podcast / webinar / loom interno / live)
2. ¿Quién es el host/invitado?
3. ¿Cuál es el insight más valioso o momento clave?
4. ¿Cuál es el CTA principal? (curso, consultoría, newsletter, lead magnet)
5. ¿Hay timestamp del momento más valioso?
6. ¿Datos, resultados o anécdotas concretas que se mencionan?

NO inventar contenido que no esté en la fuente. Si la transcripción no tiene el insight, decirlo, no rellenar.

## Voz

Aplicar voz del autor definida en `$AUTHOR_VOICE` (del `[CUSTOMIZE]`). Si la voz tiene skill propio (ej. `voz-gnb`), invocar VOICE GATE antes de cerrar el output.

Reglas universales (sobre cualquier voz):
- Preferir citas textuales del audio sobre paráfrasis genéricas
- Hook ≤ 10 palabras en posts y slides
- URL al final del último tweet del hilo, NO al principio
- Sin hashtags (a menos que `$USE_HASHTAGS: true`)
- Incluir timestamp si se proporcionó (formato "Min 23:" en LinkedIn)

## Schema raíz del plan.json

```json
{
  "meta": {
    "slug": "[call-slug]",
    "title": "[Título]",
    "type": "podcast|webinar|loom|live",
    "guest": "[Nombre o null]",
    "sourceUrl": "[URL de la llamada]",
    "authorUrl": "[URL del autor — del CUSTOMIZE]",
    "generatedAt": "[YYYY-MM-DD]",
    "totalItems": 0
  },
  "items": []
}
```

Guarda en: `$OUTPUT_PATH/[call-slug]/plan.json`.

## Items a generar

### 5 Posts de LinkedIn

```json
{
  "id": "linkedin-post-[n]",
  "day": 0,
  "platform": "linkedin",
  "type": "post",
  "role": "[ver tabla]",
  "body": "[texto completo listo para publicar]",
  "cta": {
    "text": "[texto del enlace]",
    "url": "[URL]"
  },
  "status": "draft"
}
```

| id | day | role |
|---|---|---|
| linkedin-post-1 | 0 | lanzamiento — hook + de qué trata + CTA a escuchar |
| linkedin-post-2 | 3 | insight-valioso — extrae y desarrolla la idea más poderosa |
| linkedin-post-3 | 5 | cita-comentario — frase textual + perspectiva del autor |
| linkedin-post-4 | 7 | contrarian — desafía una creencia común basado en la llamada |
| linkedin-post-5 | 10 | detras-de-escena — qué aprendió el autor grabando |

Reglas: hook ≤ 10 palabras, párrafos de 1–2 líneas, URL directa, sin hashtags por default.

### 15 Tweets

**Hilo de lanzamiento (día 0):**

```json
{
  "id": "twitter-thread-1",
  "day": 0,
  "platform": "twitter",
  "type": "thread",
  "role": "lanzamiento",
  "tweets": [
    { "order": 1, "body": "[hook ≤280 chars]" },
    { "order": 2, "body": "[insight 1]" },
    { "order": 3, "body": "[insight 2]" },
    { "order": 4, "body": "[insight 3]" },
    { "order": 5, "body": "[CTA con URL al final]" }
  ],
  "status": "draft"
}
```

**Tweets independientes:**

| id | day | role |
|---|---|---|
| twitter-post-6 a 10 | 1–5 | insights — un insight por tweet |
| twitter-post-11 a 15 | 6–10 | conversión — CTA al CTA principal |

Reglas: ≤ 280 chars, sin hashtags, URL solo al final del hilo o de los CTA.

### 10 Slides (carrusel LinkedIn)

```json
{
  "id": "carousel-1",
  "day": 6,
  "platform": "linkedin-carousel",
  "type": "carousel",
  "role": "carrusel-llamada",
  "slides": [
    {
      "order": 1,
      "role": "portada",
      "title": "[título de la llamada]",
      "subtitle": "[invitado / tagline]",
      "background": "[color de portada]",
      "imagePrompt": "[descripción visual detallada]"
    }
  ],
  "status": "draft"
}
```

Roles de las 10 slides: `portada · problema · insight×5 · cita-textual · aplicacion-practica · cta`.

Cada slide: `title` (≤10 palabras), `body` opcional (≤30 palabras), `background`, `imagePrompt`.

### 10 Imágenes

**6 imágenes 1080×1080:**

```json
{
  "id": "image-sq-[n]",
  "day": 0,
  "platform": "instagram",
  "type": "image",
  "size": "1080x1080",
  "role": "[ver tabla]",
  "imagePrompt": "[fondo, color, tipografía, texto principal, subtexto, pie, paleta del CUSTOMIZE]",
  "caption": "[caption para Instagram]",
  "status": "draft"
}
```

| id | day | role |
|---|---|---|
| image-sq-1 | 0 | anuncio-llamada |
| image-sq-2 | 1 | insight-textual (cita) |
| image-sq-3 | 3 | dato-clave |
| image-sq-4 | 5 | error-comun (❌) |
| image-sq-5 | 7 | solucion (✅) |
| image-sq-6 | 10 | cta |

**4 imágenes 1920×1080:**

| id | day | role |
|---|---|---|
| image-h-1 | 0 | banner (thumbnail YT/LinkedIn) |
| image-h-2 | 2 | cita-destacada (frase textual en tipografía grande) |
| image-h-3 | 5 | comparativa antes/después |
| image-h-4 | 10 | cta-horizontal |

### 5 Correos

```json
{
  "id": "email-[n]",
  "day": [1-10],
  "platform": "email",
  "type": "email",
  "role": "[ver tabla]",
  "subject": "[subject line]",
  "preheader": "[preheader ≤90 chars]",
  "body": "[cuerpo en markdown]",
  "cta": {
    "text": "[texto del botón]",
    "url": "[URL]"
  },
  "status": "draft"
}
```

| id | day | role |
|---|---|---|
| email-1 | 1 | lanzamiento-acceso (entrega la llamada) |
| email-2 | 4 | insight-valioso |
| email-3 | 6 | prueba-viva (caso del invitado o aplicación real) |
| email-4 | 8 | contrarian |
| email-5 | 10 | cta-principal |

## Criterios de calidad (output contract)

Antes de cerrar:
- [ ] `plan.json` creado en `$OUTPUT_PATH/[call-slug]/`
- [ ] `meta.totalItems` = número real de items
- [ ] 5 posts LinkedIn con `body` completo, hook ≤10 palabras
- [ ] 1 thread (5 tweets) + 10 tweets independientes = 15 total, todos ≤280 chars
- [ ] 10 slides con `title`, `body` (donde aplique) e `imagePrompt`
- [ ] 6 imágenes 1080×1080 con `imagePrompt` detallado (paleta del CUSTOMIZE)
- [ ] 4 imágenes 1920×1080 con `imagePrompt` detallado
- [ ] 5 correos con `subject`, `preheader`, `body`, `cta`
- [ ] Todos los items con `day` asignado
- [ ] Si `VOICE_SKILL` definido, VOICE GATE pasado

## Anti-patrones

- ❌ Inventar citas que no están en la transcripción. Si no hay cita, parafrasear y marcar `"role": "paraphrase"` en el campo.
- ❌ Generar contenido público de una discovery/sales call (privacy del cliente). Usar `gnb-call-to-voc` para uso interno.
- ❌ Usar hashtags por default. Solo si `USE_HASHTAGS: true` en `[CUSTOMIZE]`.
- ❌ URL al principio del hilo de Twitter (mata el alcance del primer tweet).
- ❌ Slides de carrusel con paredes de texto. Title ≤10 palabras, body ≤30.
- ❌ Asumir el CTA si no se pidió. Preguntar.

## Reportar al cerrar

Máximo 6 líneas:
- Archivo generado: `$OUTPUT_PATH/[call-slug]/plan.json`
- Total items: N
- Distribución por plataforma (LinkedIn / Twitter / IG / Email)
- Días de calendario cubiertos
- Próximo paso: "Revisar plan.json, ajustar copys, importar a [tu herramienta]"
- Link de la llamada original (si se proporcionó)

---

## [CUSTOMIZE] — Configuración por autor/agencia

### Identidad del autor
```yaml
AUTHOR_NAME: "Gabriel Neuman"
AUTHOR_URL: "https://gabrielneuman.com"
AUTHOR_HANDLE_LINKEDIN: "gabrielneuman"
AUTHOR_HANDLE_TWITTER: "neumang"
```

### Voz del autor
```yaml
AUTHOR_VOICE: "Directo, sin fluff, LATAM-first, contrarian con evidencia. Sin emojis en exceso."
VOICE_SKILL: "voz-gnb"            # si tienes skill de voz, apunta aquí
LANGUAGE: "es-MX"
```

### Paleta de marca (para imagePrompts)
```yaml
BRAND_PALETTE:
  primary: "#2f4ac8"               # brand-600
  background: "white"
  accent_dark: "gray-900"
```

### CTAs y links internos
```yaml
PRIMARY_CTA: "consultoria-nocode"  # slug del CTA principal por default
INTERNAL_LINKS:
  - { slug: "claudia", url: "https://gabrielneuman.com/claudia", when: "tema de IA operativa" }
  - { slug: "mi-primer-empleado-ai", url: "https://gabrielneuman.com/mi-primer-empleado-ai", when: "tema de IA + delegación" }
  - { slug: "consultoria-nocode", url: "https://gabrielneuman.com/consultoria-nocode", when: "tema de automatización" }
  - { slug: "mejores-practicas-claude-code", url: "https://gabrielneuman.com/mejores-practicas-claude-code", when: "tema de Claude Code" }
```

### Output
```yaml
OUTPUT_PATH: "content/repurpose"   # ruta donde se crean los plan.json
GENERATE_EMAILS_VIA: "correos-lanzamiento"  # skill secundario para los 5 correos, o "self" si este skill los hace
```

### Formato de plataformas
```yaml
USE_HASHTAGS: false                # default: sin hashtags
INCLUDE_TIMESTAMPS: true           # "Min 23:" en LinkedIn cuando se proporciona
URL_POSITION_TWITTER: "end"        # end | start del hilo
```

### Tipos de llamada bloqueados (no generar contenido público)
```yaml
BLOCKED_TYPES:
  - "discovery"
  - "sales-call"
  - "client-internal"
# Si el tipo cae aquí, abortar y sugerir gnb-call-to-voc
```

---

## Para forkar este skill

1. Copiar a `~/.claude/skills/<nuevo-nombre>/SKILL.md` o a tu plugin propio.
2. Editar `[CUSTOMIZE]` con tu autor, voz, paleta y CTAs.
3. Si tienes skill de correos propio, apunta `GENERATE_EMAILS_VIA` a él.
4. Probar con una llamada real corta (≤ 30 min) antes de aplicarlo a contenido largo.

## Atribución

Base original: skill `repurpose-podcast` de GNB Labs (2026). Patrón `[CUSTOMIZE]` de Anthropic.

/**
 * GNB Podcast Guesting — Worker de Cloudflare.
 *
 * Sirve dos cosas desde el mismo origen:
 *   /api/*    API para el plugin (auth por token Bearer)
 *   /         tablero de KPI (protegido por Cloudflare Access)
 *
 * Regla central: el catalogo de shows y personas es GLOBAL — informacion
 * publica que mejora con cada cliente. El pipeline es PRIVADO — toda consulta
 * filtra por cliente_id, siempre, sin excepcion. Dos competidores del mismo
 * nicho no pueden verse el pipeline.
 */

const JSON_H = { 'content-type': 'application/json; charset=utf-8' }

const ok = (data, status = 200) =>
  new Response(JSON.stringify({ data }), { status, headers: JSON_H })

const fail = (code, message, status = 400) =>
  new Response(JSON.stringify({ error: { code, message } }), { status, headers: JSON_H })

const ahora = () => new Date().toISOString()

/** El token nunca se guarda; se compara su hash. */
async function hashToken(token) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token))
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

async function autenticar(req, env) {
  const h = req.headers.get('authorization') || ''
  const m = h.match(/^Bearer\s+(.+)$/i)
  if (!m) return null
  const row = await env.DB.prepare(
    'SELECT id, nombre, plan FROM clientes WHERE token_hash = ? AND activo = 1',
  ).bind(await hashToken(m[1])).first()
  return row || null
}

function slug(s) {
  return (s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60)
}

// ── Catalogo global ──────────────────────────────────────────────────────────

/**
 * Alta o refresco de un show en el catalogo compartido.
 *
 * Idempotente por id. En un conflicto gana el dato mas reciente, porque las
 * metricas envejecen: un show activo hace seis meses puede estar muerto hoy.
 */
async function guardarShow(env, cliente, s) {
  const id = s.id || slug(s.nombre)
  if (!id) return null
  await env.DB.prepare(
    `INSERT INTO shows (id, nombre, youtube_channel, rss_url, sitio_web, idioma, pais,
       suscriptores, vistas_medianas, episodios_totales, ratio_invitados,
       dias_sin_publicar, califica, motivos_descarte, host_nombre, host_linkedin,
       aportado_por, verificado_en, creado_en)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
     ON CONFLICT(id) DO UPDATE SET
       nombre = excluded.nombre,
       youtube_channel = COALESCE(excluded.youtube_channel, shows.youtube_channel),
       suscriptores = COALESCE(excluded.suscriptores, shows.suscriptores),
       vistas_medianas = COALESCE(excluded.vistas_medianas, shows.vistas_medianas),
       episodios_totales = COALESCE(excluded.episodios_totales, shows.episodios_totales),
       ratio_invitados = COALESCE(excluded.ratio_invitados, shows.ratio_invitados),
       dias_sin_publicar = COALESCE(excluded.dias_sin_publicar, shows.dias_sin_publicar),
       califica = excluded.califica,
       motivos_descarte = excluded.motivos_descarte,
       host_nombre = COALESCE(excluded.host_nombre, shows.host_nombre),
       verificado_en = excluded.verificado_en`,
  ).bind(
    id, s.nombre, s.youtubeChannelId ?? null, s.rssUrl ?? null, s.sitioWeb ?? null,
    s.idioma ?? null, s.pais ?? null, s.suscriptores ?? null, s.vistasMedianas ?? null,
    s.episodiosTotales ?? null, s.ratioInvitados ?? null, s.diasSinPublicar ?? null,
    s.califica ? 1 : 0, JSON.stringify(s.motivos ?? []), s.hostNombre ?? null,
    s.hostLinkedin ?? null, cliente.id, ahora(), ahora(),
  ).run()
  return id
}

async function guardarPersona(env, cliente, p, showId) {
  const id = p.id || slug(p.nombre)
  if (!id || !showId) return null

  // `personas.show_id` tiene FK a `shows`. Un coinvitado puede llegar antes que
  // su show — el nombre del canal en YouTube no siempre coincide con el que se
  // dio de alta ("Automatiza con Make" vs "Automatiza con Make (antes
  // Integromat)"). Sin este alta minima, el lote entero revienta con
  // FOREIGN KEY constraint failed y se pierden las personas buenas por una mala.
  const existe = await env.DB.prepare('SELECT 1 FROM shows WHERE id = ?').bind(showId).first()
  if (!existe) {
    await env.DB.prepare(
      `INSERT INTO shows (id, nombre, califica, aportado_por, verificado_en, creado_en)
       VALUES (?,?,0,?,?,?) ON CONFLICT(id) DO NOTHING`,
    ).bind(showId, p.showOrigen || showId, cliente.id, ahora(), ahora()).run()
  }
  await env.DB.prepare(
    `INSERT INTO personas (id, nombre, show_id, episodio_url, episodio_tit,
       episodio_fecha, linkedin, sitio_web, aportado_por, creado_en)
     VALUES (?,?,?,?,?,?,?,?,?,?)
     ON CONFLICT(id) DO UPDATE SET
       linkedin = COALESCE(excluded.linkedin, personas.linkedin),
       sitio_web = COALESCE(excluded.sitio_web, personas.sitio_web)`,
  ).bind(
    id, p.nombre, showId, p.episodioUrl ?? null, p.episodioTitulo ?? null,
    p.episodioFecha ?? null, p.linkedin ?? null, p.sitioWeb ?? null, cliente.id, ahora(),
  ).run()
  return id
}

// ── Pipeline privado ─────────────────────────────────────────────────────────

async function upsertPipeline(env, clienteId, targetId, tipo, campos = {}) {
  const prev = await env.DB.prepare(
    'SELECT etapa FROM pipeline WHERE cliente_id = ? AND target_id = ?',
  ).bind(clienteId, targetId).first()

  if (!prev) {
    await env.DB.prepare(
      `INSERT INTO pipeline (cliente_id, target_id, tipo, etapa, bucket, bucket_porque,
         notas, creado_en, actualizado_en) VALUES (?,?,?,?,?,?,?,?,?)`,
    ).bind(
      clienteId, targetId, tipo,
      campos.etapa ?? (tipo === 'show' ? 'prospecto' : 'identificado'),
      campos.bucket ?? null, campos.bucketPorque ?? null, campos.notas ?? null,
      ahora(), ahora(),
    ).run()
    return { creado: true }
  }

  const sets = [], vals = []
  for (const [col, v] of [
    ['etapa', campos.etapa], ['bucket', campos.bucket],
    ['bucket_porque', campos.bucketPorque], ['notas', campos.notas],
    ['contacto_privado', campos.contactoPrivado],
  ]) {
    if (v !== undefined && v !== null) { sets.push(`${col} = ?`); vals.push(v) }
  }
  if (sets.length) {
    sets.push('actualizado_en = ?'); vals.push(ahora(), clienteId, targetId)
    await env.DB.prepare(
      `UPDATE pipeline SET ${sets.join(', ')} WHERE cliente_id = ? AND target_id = ?`,
    ).bind(...vals).run()
  }
  return { creado: false }
}

// ── KPI ──────────────────────────────────────────────────────────────────────

const PITCHEADAS = ['pitcheado', 'vio_onesheet', 'respondio', 'agendado', 'grabado', 'publicado', 'distribuido']
const CON_RESPUESTA = ['respondio', 'agendado', 'grabado', 'publicado', 'distribuido']
const GANADAS = ['grabado', 'publicado', 'distribuido']
const P_CONTACTADAS = ['contactado', 'respondio', 'llamada', 'alianza', 'sin_respuesta']
const P_RESPONDIERON = ['respondio', 'llamada', 'alianza']

/** null, no 0, cuando no hay denominador: "sin datos" no es "0%". */
const pct = (n, d) => (d > 0 ? Math.round((n / d) * 1000) / 10 : null)

async function calcularKpi(env, clienteId) {
  const filas = await env.DB.prepare(
    'SELECT tipo, etapa, bucket, vio_onesheet FROM pipeline WHERE cliente_id = ?',
  ).bind(clienteId).all()
  const rows = filas.results || []

  const shows = rows.filter((r) => r.tipo === 'show')
  const personas = rows.filter((r) => r.tipo === 'persona')
  const cnt = (xs, etapas) => xs.filter((r) => etapas.includes(r.etapa)).length

  const pitcheados = cnt(shows, PITCHEADAS)
  const respondieron = cnt(shows, CON_RESPUESTA)
  const vieron = shows.filter((r) => r.vio_onesheet).length
  const agendados = cnt(shows, ['agendado', ...GANADAS])
  const contactadas = cnt(personas, P_CONTACTADAS)
  const respPersonas = cnt(personas, P_RESPONDIERON)

  const msg = await env.DB.prepare(
    'SELECT COUNT(*) AS envios, SUM(respondido) AS resp FROM mensajes WHERE cliente_id = ?',
  ).bind(clienteId).first()

  const porBucket = {}
  for (const p of personas) porBucket[p.bucket || 'sin_definir'] = (porBucket[p.bucket || 'sin_definir'] || 0) + 1

  return {
    showsProspecto: cnt(shows, ['prospecto']),
    showsPitcheados: pitcheados,
    showsVieronOnesheet: vieron,
    showsRespondieron: respondieron,
    showsAgendados: agendados,
    showsGrabados: cnt(shows, GANADAS),
    personasIdentificadas: personas.length,
    personasContactadas: contactadas,
    personasRespondieron: respPersonas,
    personasAlianza: cnt(personas, ['alianza']),
    porBucket,
    tasaVistaOnesheet: pct(vieron, pitcheados),
    tasaRespuestaShows: pct(respondieron, pitcheados),
    tasaAgendado: pct(agendados, pitcheados),
    tasaRespuestaPersonas: pct(respPersonas, contactadas),
    mensajesEnviados: msg?.envios ?? 0,
    mensajesRespondidos: msg?.resp ?? 0,
    actualizadoEn: ahora(),
  }
}

// ── Router ───────────────────────────────────────────────────────────────────

export default {
  async fetch(req, env) {
    const url = new URL(req.url)
    const p = url.pathname

    if (req.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: {
          'access-control-allow-origin': '*',
          'access-control-allow-methods': 'GET, POST, OPTIONS',
          'access-control-allow-headers': 'authorization, content-type',
        },
      })
    }

    // Tablero. Cloudflare Access lo protege ANTES de llegar aqui: el Worker no
    // implementa login propio, lo delega a la plataforma.
    if (p === '/' || p === '/tablero') {
      const email = req.headers.get('cf-access-authenticated-user-email')
      if (!email && env.REQUIERE_ACCESS === '1') {
        return new Response('No autorizado. Este tablero exige Cloudflare Access.', { status: 403 })
      }
      const cliente = email
        ? await env.DB.prepare('SELECT id, nombre FROM clientes WHERE email = ?').bind(email).first()
        : null
      if (!cliente) return new Response('Sin cliente asociado a ' + (email || 'este acceso'), { status: 403 })
      return new Response(tableroHtml(await calcularKpi(env, cliente.id), cliente), {
        headers: { 'content-type': 'text/html; charset=utf-8' },
      })
    }

    // ── /api/* ──
    if (!p.startsWith('/api/')) return fail('not_found', 'Ruta desconocida', 404)

    // El tracking del one-sheet es publico: lo llama el navegador de un host,
    // que no tiene token. Fail-open — un bot nunca rompe la pagina.
    if (p === '/api/eventos' && req.method === 'POST') {
      try {
        const b = await req.json()
        await env.DB.prepare(
          `INSERT INTO eventos (cliente_id, target_id, tipo, seccion, segundos, sesion, creado_en)
           VALUES (?,?,?,?,?,?,?)`,
        ).bind(
          b.clienteId ?? null, b.targetId ?? null, b.tipo || 'onesheet_opened',
          b.seccion ?? null, b.segundos ?? null, b.sesion ?? null, ahora(),
        ).run()
        if (b.tipo === 'onesheet_opened' && b.clienteId && b.targetId) {
          await env.DB.prepare(
            `UPDATE pipeline SET vio_onesheet = 1,
               vio_onesheet_en = COALESCE(vio_onesheet_en, ?),
               etapa = CASE WHEN etapa = 'pitcheado' THEN 'vio_onesheet' ELSE etapa END,
               actualizado_en = ?
             WHERE cliente_id = ? AND target_id = ?`,
          ).bind(ahora(), ahora(), b.clienteId, b.targetId).run()
        }
      } catch { /* silencio deliberado */ }
      return new Response(null, { status: 204, headers: { 'access-control-allow-origin': '*' } })
    }

    const cliente = await autenticar(req, env)
    if (!cliente) return fail('unauthorized', 'Token invalido o ausente', 401)

    // Catalogo global: lo ven todos. Es el valor compartido del producto.
    if (p === '/api/catalogo' && req.method === 'GET') {
      const idioma = url.searchParams.get('idioma')
      const q = idioma
        ? env.DB.prepare('SELECT * FROM shows WHERE califica = 1 AND idioma = ? ORDER BY verificado_en DESC LIMIT 500').bind(idioma)
        : env.DB.prepare('SELECT * FROM shows WHERE califica = 1 ORDER BY verificado_en DESC LIMIT 500')
      const r = await q.all()
      return ok({ shows: r.results || [], total: (r.results || []).length })
    }

    if (p === '/api/shows' && req.method === 'POST') {
      const b = await req.json()
      const lista = Array.isArray(b) ? b : [b]
      const ids = []
      for (const s of lista) {
        const id = await guardarShow(env, cliente, s)
        if (id) { await upsertPipeline(env, cliente.id, id, 'show', { etapa: s.etapa }); ids.push(id) }
      }
      return ok({ guardados: ids.length, ids }, 201)
    }

    if (p === '/api/personas' && req.method === 'POST') {
      const b = await req.json()
      const lista = Array.isArray(b) ? b : [b]
      let n = 0
      for (const x of lista) {
        const showId = x.showId || slug(x.showOrigen)
        const id = await guardarPersona(env, cliente, x, showId)
        if (id) {
          await upsertPipeline(env, cliente.id, id, 'persona', {
            etapa: x.etapa, bucket: x.bucket, bucketPorque: x.bucketPorque,
          })
          n++
        }
      }
      return ok({ guardados: n }, 201)
    }

    if (p === '/api/pipeline' && req.method === 'GET') {
      const r = await env.DB.prepare(
        `SELECT pl.*, COALESCE(s.nombre, pe.nombre) AS nombre,
                COALESCE(s.host_nombre, pe.show_id) AS contexto
         FROM pipeline pl
         LEFT JOIN shows s ON s.id = pl.target_id AND pl.tipo = 'show'
         LEFT JOIN personas pe ON pe.id = pl.target_id AND pl.tipo = 'persona'
         WHERE pl.cliente_id = ? ORDER BY pl.actualizado_en DESC LIMIT 1000`,
      ).bind(cliente.id).all()
      return ok({ pipeline: r.results || [] })
    }

    if (p === '/api/mensajes' && req.method === 'POST') {
      const b = await req.json()
      const prev = await env.DB.prepare(
        'SELECT COUNT(*) AS n FROM mensajes WHERE cliente_id = ? AND target_id = ?',
      ).bind(cliente.id, b.targetId).first()
      await env.DB.prepare(
        'INSERT INTO mensajes (cliente_id, target_id, canal, asunto, follow_up, enviado_en) VALUES (?,?,?,?,?,?)',
      ).bind(cliente.id, b.targetId, b.canal || 'email', b.asunto ?? null, prev?.n ?? 0, ahora()).run()
      // Un target con mensaje enviado ya no es prospecto.
      await env.DB.prepare(
        `UPDATE pipeline SET
           etapa = CASE WHEN etapa = 'prospecto' THEN 'pitcheado'
                        WHEN etapa IN ('identificado','investigado') THEN 'contactado'
                        ELSE etapa END,
           actualizado_en = ?
         WHERE cliente_id = ? AND target_id = ?`,
      ).bind(ahora(), cliente.id, b.targetId).run()
      return ok({ followUp: prev?.n ?? 0 }, 201)
    }

    if (p === '/api/etapa' && req.method === 'POST') {
      const b = await req.json()
      await upsertPipeline(env, cliente.id, b.targetId, b.tipo || 'show', {
        etapa: b.etapa, bucket: b.bucket, bucketPorque: b.bucketPorque,
      })
      return ok({ targetId: b.targetId, etapa: b.etapa })
    }

    if (p === '/api/kpi' && req.method === 'GET') {
      return ok({ kpi: await calcularKpi(env, cliente.id), cliente: cliente.nombre })
    }

    return fail('not_found', 'Ruta desconocida', 404)
  },
}

// ── Tablero ──────────────────────────────────────────────────────────────────

function tableroHtml(k, cliente) {
  // "—" y no "0%" cuando no hay denominador: en un tablero, "todavia no
  // mandamos nada" y "mandamos y nadie contesto" piden decisiones opuestas.
  const t = (v) => (v === null || v === undefined ? '—' : v + '%')
  const card = (label, valor, sub = '') => `
    <div class="card">
      <div class="label">${label}</div>
      <div class="valor">${valor}</div>
      ${sub ? `<div class="sub">${sub}</div>` : ''}
    </div>`

  const buckets = Object.entries(k.porBucket || {})
    .sort((a, b) => b[1] - a[1])
    .map(([b, n]) => `<tr><td>${b}</td><td class="num">${n}</td></tr>`)
    .join('')

  const sinDatos = k.showsPitcheados === 0 && k.personasContactadas === 0

  return `<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Podcast Guesting — ${cliente.nombre}</title>
<style>
  :root {
    --bg:#fafafa; --fg:#18181b; --muted:#71717a; --linea:#e4e4e7;
    --card:#fff; --acento:#ea580c;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#0a0a0a; --fg:#fafafa; --muted:#a1a1aa; --linea:#27272a; --card:#18181b; }
  }
  * { box-sizing:border-box; }
  body { margin:0; padding:2rem 1rem; background:var(--bg); color:var(--fg);
    font:15px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif; }
  .wrap { max-width:1000px; margin:0 auto; }
  h1 { font-size:1.6rem; margin:0 0 .25rem; letter-spacing:-.02em; }
  .meta { color:var(--muted); font-size:.85rem; margin-bottom:2rem; }
  h2 { font-size:.8rem; text-transform:uppercase; letter-spacing:.08em;
    color:var(--muted); margin:2.5rem 0 .75rem; font-weight:600; }
  .grid { display:grid; gap:.75rem; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); }
  .card { background:var(--card); border:1px solid var(--linea); border-radius:10px; padding:1rem; }
  .label { font-size:.75rem; color:var(--muted); }
  .valor { font-size:1.9rem; font-weight:700; letter-spacing:-.03em; margin-top:.2rem; }
  .sub { font-size:.75rem; color:var(--acento); font-weight:600; }
  table { width:100%; border-collapse:collapse; background:var(--card);
    border:1px solid var(--linea); border-radius:10px; overflow:hidden; }
  td { padding:.6rem .9rem; border-bottom:1px solid var(--linea); }
  tr:last-child td { border-bottom:0; }
  .num { text-align:right; font-variant-numeric:tabular-nums; font-weight:600; }
  .aviso { background:var(--card); border:1px solid var(--linea); border-left:3px solid var(--acento);
    border-radius:8px; padding:.9rem 1rem; color:var(--muted); font-size:.9rem; margin-bottom:1.5rem; }
  footer { margin-top:3rem; color:var(--muted); font-size:.78rem; }
</style></head><body><div class="wrap">

<h1>Podcast Guesting</h1>
<div class="meta">${cliente.nombre} · actualizado ${new Date(k.actualizadoEn).toLocaleString('es-MX')}</div>

${sinDatos ? '<div class="aviso">Aún no se envía ningún pitch. Por eso las tasas están en “—”: no hay denominador todavía, que no es lo mismo que 0%.</div>' : ''}

<h2>Shows</h2>
<div class="grid">
  ${card('Prospectos', k.showsProspecto)}
  ${card('Pitches enviados', k.showsPitcheados)}
  ${card('Vieron el one-sheet', k.showsVieronOnesheet, t(k.tasaVistaOnesheet))}
  ${card('Respondieron', k.showsRespondieron, t(k.tasaRespuestaShows))}
  ${card('Agendados', k.showsAgendados, t(k.tasaAgendado))}
  ${card('Grabados', k.showsGrabados)}
</div>

<h2>Coinvitados</h2>
<div class="grid">
  ${card('Identificados', k.personasIdentificadas)}
  ${card('Contactados', k.personasContactadas)}
  ${card('Respondieron', k.personasRespondieron, t(k.tasaRespuestaPersonas))}
  ${card('Alianzas', k.personasAlianza)}
</div>

<h2>Por bucket</h2>
<table>${buckets || '<tr><td colspan="2">Sin coinvitados todavía.</td></tr>'}</table>

<h2>Mensajes</h2>
<div class="grid">
  ${card('Enviados', k.mensajesEnviados)}
  ${card('Respondidos', k.mensajesRespondidos, t(pct(k.mensajesRespondidos, k.mensajesEnviados)))}
</div>

<footer>
  “Vio el one-sheet” no cuenta como respuesta: es señal de intención de alguien
  que abrió y leyó pero no contestó. Mezclarlas inflaría la tasa de respuesta.
</footer>
</div></body></html>`
}

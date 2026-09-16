-- GNB Podcast Guesting — esquema D1 (Cloudflare)
--
-- Dos mundos en la misma base, y la separacion es la decision central del
-- producto:
--
--   GLOBAL   catalogo de shows y personas. Informacion publica que cualquiera
--            puede ver en YouTube. Se comparte entre todos los clientes: el
--            cliente #50 llega a un catalogo ya calificado por los 49 previos.
--
--   PRIVADO  el pipeline de cada quien. A quien pitcheo, quien contesto, que
--            escribio. NUNCA se comparte: dos competidores del mismo nicho
--            verian a quien le esta escribiendo el otro, y eso hunde el
--            producto el dia que se sepa.
--
-- Todas las tablas privadas llevan `cliente_id` y toda consulta lo filtra.

-- ── GLOBAL: catalogo de shows ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS shows (
  id                TEXT PRIMARY KEY,          -- slug del nombre
  nombre            TEXT NOT NULL,
  youtube_channel   TEXT UNIQUE,               -- llave natural cuando existe
  rss_url           TEXT,
  sitio_web         TEXT,
  idioma            TEXT,
  pais              TEXT,

  -- Metricas de calificacion. Se refrescan; `verificado_en` dice que tan
  -- viejas son, porque un show activo hace seis meses puede estar muerto hoy.
  suscriptores      INTEGER,
  vistas_medianas   INTEGER,
  episodios_totales INTEGER,
  ratio_invitados   REAL,                      -- 0..1
  dias_sin_publicar INTEGER,
  califica          INTEGER DEFAULT 0,         -- 0/1
  motivos_descarte  TEXT,                      -- JSON array

  host_nombre       TEXT,
  host_linkedin     TEXT,
  -- El correo del host NO va aqui: es PII y el catalogo es compartido.
  -- Vive en pipeline.contacto_privado, del cliente que lo consiguio.

  aportado_por      TEXT,                      -- cliente_id de quien lo descubrio
  verificado_en     TEXT NOT NULL,
  creado_en         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shows_califica ON shows (califica, idioma);
CREATE INDEX IF NOT EXISTS idx_shows_verificado ON shows (verificado_en DESC);

-- ── GLOBAL: personas que ya fueron invitadas ─────────────────────────────────
-- Nombre y episodio son publicos (estan en el titulo del video de YouTube).
-- El bucket NO es global: depende del ICP de cada cliente — la misma persona
-- es "cliente" para uno y "competencia" para otro.

CREATE TABLE IF NOT EXISTS personas (
  id            TEXT PRIMARY KEY,
  nombre        TEXT NOT NULL,
  show_id       TEXT NOT NULL REFERENCES shows(id),
  episodio_url  TEXT,
  episodio_tit  TEXT,
  episodio_fecha TEXT,
  linkedin      TEXT,
  sitio_web     TEXT,
  aportado_por  TEXT,
  creado_en     TEXT NOT NULL,
  UNIQUE (id, show_id)
);

CREATE INDEX IF NOT EXISTS idx_personas_show ON personas (show_id);

-- ── PRIVADO: clientes ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS clientes (
  id          TEXT PRIMARY KEY,
  nombre      TEXT NOT NULL,
  email       TEXT,
  -- Hash SHA-256 del token, nunca el token. Si la base se filtra, no sirve
  -- para autenticarse contra la API.
  token_hash  TEXT NOT NULL UNIQUE,
  plan        TEXT DEFAULT 'basico',
  activo      INTEGER DEFAULT 1,
  creado_en   TEXT NOT NULL
);

-- ── PRIVADO: el pipeline de cada cliente ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS pipeline (
  cliente_id    TEXT NOT NULL REFERENCES clientes(id),
  target_id     TEXT NOT NULL,                 -- shows.id o personas.id
  tipo          TEXT NOT NULL CHECK (tipo IN ('show','persona')),
  etapa         TEXT NOT NULL,
  bucket        TEXT,                          -- solo personas; depende del ICP
  bucket_porque TEXT,
  notas         TEXT,
  -- Correo/telefono que el cliente consiguio por su cuenta. Privado por
  -- definicion: no se promueve al catalogo global.
  contacto_privado TEXT,
  vio_onesheet  INTEGER DEFAULT 0,
  vio_onesheet_en TEXT,
  creado_en     TEXT NOT NULL,
  actualizado_en TEXT NOT NULL,
  PRIMARY KEY (cliente_id, target_id)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_cliente ON pipeline (cliente_id, etapa);
CREATE INDEX IF NOT EXISTS idx_pipeline_bucket ON pipeline (cliente_id, bucket);

-- ── PRIVADO: mensajes ────────────────────────────────────────────────────────
-- Es el denominador del KPI: sin registro de envio no hay tasa de respuesta.

CREATE TABLE IF NOT EXISTS mensajes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  cliente_id  TEXT NOT NULL REFERENCES clientes(id),
  target_id   TEXT NOT NULL,
  canal       TEXT NOT NULL,
  asunto      TEXT,
  follow_up   INTEGER DEFAULT 0,
  respondido  INTEGER DEFAULT 0,
  respondido_en TEXT,
  enviado_en  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mensajes_cliente ON mensajes (cliente_id, enviado_en DESC);

-- ── PRIVADO: eventos del one-sheet ───────────────────────────────────────────
-- `sesion` permite agregar el tiempo con MAX por sesion en vez de SUM sobre
-- todos los eventos: sin eso, los heartbeats acumulativos inflan el total.

CREATE TABLE IF NOT EXISTS eventos (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  cliente_id  TEXT,
  target_id   TEXT,
  tipo        TEXT NOT NULL,
  seccion     TEXT,
  segundos    INTEGER,
  sesion      TEXT,
  creado_en   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eventos_target ON eventos (cliente_id, target_id, creado_en DESC);

# Cloud — API y tablero en Cloudflare

Worker + D1 que sirve la API del plugin y el tablero de KPI desde el mismo
origen. Corre en el plan gratuito de Cloudflare.

## Qué es global y qué es privado

Esta es la decisión central del producto, y está en el esquema, no en una
política escrita:

| Global (se comparte) | Privado (por cliente) |
|---|---|
| Qué shows existen y sus métricas | A quién pitcheó y cuándo |
| Si hace entrevistas, idioma, actividad | Quién le contestó |
| Nombre público del show y del host | Los correos que escribió, sus notas |
| Coinvitados (nombre y episodio) | Su pipeline, sus buckets, sus KPI |

Lo global es **información pública** — está en YouTube, cualquiera la ve.
Compartirla es lo que hace valioso el producto: el cliente #50 llega a un
catálogo ya calificado por los 49 anteriores.

Lo privado **nunca se comparte**. Dos competidores del mismo nicho no pueden
verse el pipeline, y toda consulta filtra por `cliente_id`.

Dos consecuencias concretas del diseño:

- **El correo del host no vive en el catálogo global.** Es PII de un tercero.
  Vive en `pipeline.contacto_privado`, del cliente que lo consiguió.
- **El bucket tampoco es global.** Depende del ICP de cada quien: la misma
  persona es "cliente" para uno y "competencia" para otro.

## Desplegar

```bash
cd cloud
npm i -g wrangler && wrangler login

wrangler d1 create podcast-guesting          # copia el database_id al wrangler.toml
wrangler d1 execute podcast-guesting --remote --file=schema.sql
wrangler deploy
```

### Proteger el tablero — obligatorio

`REQUIERE_ACCESS = "1"` hace que el Worker rechace a quien no venga por
Cloudflare Access. Falta configurar Access del lado de Cloudflare:

1. Zero Trust → Access → Applications → Add an application → Self-hosted
2. Dominio: el de tu Worker
3. Policy: `Emails` → los correos que pueden entrar

Sin esto, `REQUIERE_ACCESS = "1"` bloquea a todos (falla cerrada, que es lo
correcto). Con `"0"` cualquiera con la URL vería el pipeline — úsalo solo en
local.

### Dar de alta un cliente

El token se guarda **hasheado**: si la base se filtra, no sirve para
autenticarse.

```bash
TOKEN=$(openssl rand -hex 24)
HASH=$(printf '%s' "$TOKEN" | openssl dgst -sha256 | awk '{print $2}')

wrangler d1 execute podcast-guesting --remote --command \
  "INSERT INTO clientes (id,nombre,email,token_hash,creado_en)
   VALUES ('acme','ACME','quien@acme.com','$HASH','$(date -u +%FT%TZ)')"

echo "Token para el cliente (se muestra UNA vez): $TOKEN"
```

El `email` debe ser el mismo con el que entra por Cloudflare Access: así el
tablero sabe qué cliente mostrar.

Luego el cliente exporta:

```bash
export GNB_CRM_URL=https://podcast-guesting.TU-SUBDOMINIO.workers.dev
export GNB_CRM_TOKEN=<su token>
```

## API

| Método | Ruta | Auth | Qué hace |
|---|---|---|---|
| GET | `/api/catalogo` | token | Catálogo global de shows que califican |
| POST | `/api/shows` | token | Alta o refresco de shows |
| POST | `/api/personas` | token | Alta de coinvitados |
| GET | `/api/pipeline` | token | El pipeline del cliente |
| POST | `/api/mensajes` | token | Registra un envío |
| POST | `/api/etapa` | token | Mueve de etapa o reclasifica bucket |
| GET | `/api/kpi` | token | KPI del cliente |
| POST | `/api/eventos` | **público** | Tracking del one-sheet |
| GET | `/` | Access | Tablero |

`/api/eventos` es público a propósito: lo llama el navegador de un host que
abrió el one-sheet, y ese visitante no tiene token. Fail-open — devuelve 204
pase lo que pase, porque un bot o un link viejo no pueden romper una página
pública ni delatar que el link es rastreado.

## Actualizar

Una mejora tuya llega a las tres capas con dos comandos:

```bash
git pull                          # skills + worker + esquema
./instalar.sh                     # actualiza los skills locales
cd cloud && wrangler deploy       # actualiza API y tablero
```

Si el `schema.sql` cambió, aplica la migración antes del deploy:

```bash
wrangler d1 execute podcast-guesting --remote --file=schema.sql
```

Es idempotente (`CREATE TABLE IF NOT EXISTS`), así que re-aplicarlo no rompe
datos. **Pero `IF NOT EXISTS` no agrega columnas nuevas a una tabla que ya
existe**: para eso hace falta un `ALTER TABLE` explícito. Cuando agregues una
columna, escribe la migración; no confíes en que el schema la propague.

Los datos del cliente nunca se tocan: viven en D1 y en `.podcast-guesting/`,
fuera del código.

## Costo

Plan gratuito de Cloudflare: 100,000 requests/día en Workers y 5 GB en D1. Un
cliente activo hace decenas de requests por día. No vas a acercarte al límite.

## Estado

Probado en local con `wrangler dev` y D1 local: alta de shows y personas,
registro de envío, evento de one-sheet, transición de etapa y render del
tablero. Falta correrlo en producción con Access configurado.

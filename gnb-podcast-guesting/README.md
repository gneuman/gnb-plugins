# GNB Podcast Guesting

Sistema para conseguir apariciones en podcasts y convertirlas en clientes.

Un episodio en un show de 200 oyentes que son exactamente tu cliente ideal vale
más que uno de 50,000 que no te compra. Este plugin encuentra esos shows,
escribe el pitch, y hace lo que casi nadie hace: cosechar a los **coinvitados**
del show, que suelen ser mejor oportunidad que el host.

## Instalación

Dos formas. Cualquiera deja lo mismo.

**Clonando el repo** — una sola línea:

```bash
git clone https://github.com/gneuman/gnb-plugins
cd gnb-plugins/gnb-podcast-guesting && ./instalar.sh
```

El instalador copia los skills a `~/.claude/skills/`, revisa qué dependencias
faltan y te dice exactamente qué instalar. Correrlo dos veces no rompe nada.

**Desde el marketplace**, si ya lo tienes agregado:

```
/plugin install gnb-podcast-guesting@gnb-labs
```

Luego, en cualquier repo:

```
/pg-setup
```

Ocho preguntas que escriben tu perfil, tu ICP y tus criterios. Sin eso el
sistema escribe correos genéricos.

**Si ya estuviste en algún podcast**, ten los links a la mano: `/pg-setup` los
transcribe y saca de ahí tu voz, tus cifras y tu ICP dichos por ti mismo. Es
mejor material que cualquier respuesta de entrevista.

## Los seis skills

| Skill | Qué hace |
|---|---|
| `/pg-setup` | Entrevista guiada → tu perfil, ICP, temas y criterios |
| `/pg-research` | Busca shows que califican y los mete al pipeline |
| `/pg-pitch` | Escribe el pitch, personalizado a un episodio concreto |
| `/pg-invitados` | Extrae los coinvitados de un show → 4 buckets de alianza |
| `/pg-escuchar` | Transcribe un episodio para poder citarlo con precisión |
| `/pg-store` | Guarda el estado y calcula el KPI |

## Funciona sin nada configurado

El estado vive en `.podcast-guesting/` dentro de tu repo. **No necesitas base de
datos, ni cuenta, ni servidor.**

Si además tienes un CRM, exporta `GNB_CRM_URL` y `GNB_CRM_TOKEN` y sincroniza —
escribiendo en ambos lados. Si el CRM se cae, el error se registra y el trabajo
sigue: un pipeline caído no puede bloquear el outreach.

### Variables opcionales

| Variable | Para qué | Sin ella |
|---|---|---|
| `YOUTUBE_API_KEY` | Buscar shows, extraer coinvitados, metadata | `/pg-research` y `/pg-invitados` no corren; `/pg-escuchar` sí (usa yt-dlp) |
| `LISTEN_NOTES_API_KEY` | Traer el RSS y el correo del host | Se busca el contacto a mano |
| `GNB_CRM_URL` + `GNB_CRM_TOKEN` | Sincronizar al CRM | Todo funciona en local |

La API de YouTube da 10,000 unidades diarias gratis. Una corrida de búsqueda
gasta ~135 y un barrido de coinvitados ~3 por show: no vas a topar el límite.

## Los cuatro buckets

Cada coinvitado cae en uno, y eso define qué se le propone:

| Bucket | Señal | Propuesta |
|---|---|---|
| **Plataforma** | Tiene podcast, newsletter o canal | Intercambio de audiencia |
| **Referido** | Vende complementario al mismo ICP | Pase de clientes mutuo |
| **Cliente** | Es tu ICP | Conversación comercial |
| **DFY** | Tiene alcance pero opera a mano | Prospecto de implementación |

Un coinvitado que hace lo mismo que tú no es un bucket: es competencia. Se
vigila, y la alianza se decide caso por caso.

El anclaje del primer mensaje es que coincidieron en el mismo micrófono. Eso
convierte un correo frío en uno tibio.

## De guiado a automático

No hay un interruptor. El sistema se vuelve autónomo porque acumula:

| Corridas | Comportamiento |
|---|---|
| 1–3 | Para antes de enviar, pregunta qué cambiarías, guarda tu edición |
| 4–10 | Ya tiene referencias propias. Redacta y pide una confirmación |
| 10+ | Sabe qué convirtió. Corre solo y reporta |

Las ediciones se guardan en `wiki-podcast/pitch-ganadores.md`. Ese archivo es el
que hace la diferencia entre un generador de plantillas y un agente que aprende
tu voz.

## El KPI

```bash
python skills/pg-store/scripts/store.py kpi
```

Pitches enviados · vieron el one-sheet · respondieron · agendados · grabados.

Las tasas se muestran como **"—"** cuando todavía no hay denominador, no como
0%. "No hemos mandado nada" y "mandamos y nadie contestó" piden decisiones
opuestas.

## Privacidad

`.podcast-guesting/` escribe su propio `.gitignore` con `*`. Son nombres y
correos de terceros: **nunca van a git.**

## Créditos

La metodología de pitch viene de Dustin Riechmann, vía la masterclass de Corey
Ganim. La idea de cosechar coinvitados es de esa misma sesión — Corey la nombra
como su mayor arrepentimiento por no haberla hecho antes.

Lo que este plugin agrega: los buckets definidos, la instrumentación del
one-sheet para ver quién te consideró aunque no conteste, y que todo corra sin
depender de una base de datos.

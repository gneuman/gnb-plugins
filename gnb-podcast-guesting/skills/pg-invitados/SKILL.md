---
name: pg-invitados
description: >
  Extrae los invitados previos de un podcast y los clasifica en cuatro buckets
  de oportunidad (plataforma, referido, cliente, DFY) para outreach tibio.
  Úsalo después de aparecer en un show, o antes de pitchearlo, cuando el
  usuario diga "quiénes han estado en ese podcast", "saca los invitados de",
  "a quién más entrevistaron", "busca aliados del podcast", "outreach a los
  invitados", "/pg-invitados". También cuando pegue un link de YouTube de un
  podcast y pregunte con quién hacer alianza.
---

# pg-invitados — los otros invitados del show

El host es un contacto. Los veinte invitados que ya pasaron por su micrófono
son veinte contactos, cada uno con plataforma propia, y el anclaje para
escribirles ya existe: **coincidieron en el mismo show**.

Es la mitad del valor de un podcast que casi nadie cosecha. La tasa de
respuesta con ese anclaje ronda el 50%, contra el 2-5% de un correo frío.

## Cuándo se usa

- **Después** de grabar en un show → los coinvitados son outreach tibio inmediato.
- **Antes** de pitchear un show → ver a quién invitan dice si tu perfil encaja.

## Paso 1 — Extraer

```bash
python skills/pg-invitados/scripts/extraer-invitados.py <VIDEO_ID> [VIDEO_ID...]
python skills/pg-invitados/scripts/extraer-invitados.py <VIDEO_ID> --json   # → invitados.json
```

Recibe el ID de **cualquier** video del show (de un link
`youtu.be/XXXX` o `youtube.com/watch?v=XXXX`), resuelve el canal y recorre sus
uploads.

**Cuota: ~3 unidades por show** de las 10,000 diarias. El script usa
`playlistItems`, que cuesta 1, y **nunca `search`**, que cuesta 100. Un barrido
de 20 shows gasta 60 unidades — menos de lo que gasta una sola búsqueda.

Filtra `#shorts`, títulos vacíos y "Untitled"; deduplica por nombre; y se
excluye a sí mismo (override: `--yo="Otro Nombre"`).

**El script propone, tú confirmas.** Detecta nombres por patrón de título
(`con X`, `with X`, `ft. X`, `| X`), así que un título sin invitado en el
nombre se le escapa, y un nombre de sección puede colarse. Revisa la lista
antes de escribirle a nadie.

## Paso 2 — Clasificar en cuatro buckets

Cada invitado cae en **uno**. Investiga lo mínimo para decidir: su LinkedIn y
si tiene show, newsletter o canal propio.

| Bucket | Señal | Qué le propones |
|---|---|---|
| **Plataforma** | tiene podcast, newsletter o canal propio | Intercambio: entras a su audiencia, entra a la tuya |
| **Referido** | vende algo complementario al mismo ICP | Pase de clientes en ambas direcciones |
| **Cliente** | **es** el ICP del perfil | Conversación comercial, sin pitch en el primer mensaje |
| **DFY** | tiene alcance pero opera todo a mano | Prospecto del servicio de implementación |

Un invitado sin señal clara **no se fuerza a un bucket**. Se descarta y se
anota por qué en `decisiones.md` — eso evita volver a evaluarlo cada corrida.

Si el perfil del cliente vive en `wiki-podcast/perfil.md`, léelo antes de
clasificar: el ICP de ahí es el que define los buckets "cliente" y "DFY".

## Paso 3 — Escribir el primer mensaje

Una regla: **el anclaje va en la primera línea**. Es lo único que separa esto
de un correo frío.

> Hola [Nombre], te escribo porque los dos pasamos por [Show] — tú en
> [su episodio], yo en [el mío]. [Una línea concreta sobre algo que dijo].
>
> [La razón de escribir, según el bucket, en una sola frase.]
>
> ¿Te late una llamada de 15 minutos?

Reglas duras:

- **Menciona su episodio por lo que dijo, no por el título.** "Vi que estuviste
  en X" no prueba que lo escuchaste.
- **Un solo ask.** Nunca "y de paso, ¿me compras?".
- **Nada de halago genérico.** "Me encantó tu episodio" sin decir qué, resta.
- Español de México. Sin voseo. La regla completa vive en `voz-gnb`.

## Paso 4 — Registrar

Cada invitado contactado se registra con su bucket, el show que los une y la
fecha. Sin registro, a la tercera corrida no sabrás a quién ya escribiste.

- Si hay CRM configurado → `podcast_targets` vía `/api/v1/podcasts`.
- Si no → `invitados.json` y una línea en `wiki-podcast/logs/`.

Al cerrar, reporta: **cuántos se extrajeron, cuántos por bucket, cuántos se
descartaron y por qué.** Un descarte silencioso se lee como cobertura completa
sin serlo.

## Límites conocidos

- **Solo YouTube.** Un show que solo publica en Spotify o Apple no se cubre por
  aquí; para esos, `podcast-scout` (Listen Notes) trae el RSS.
- **Solo los últimos ~100 episodios** (2 páginas). Un show con 1,400 videos
  tiene invitados más viejos que este barrido no ve.
- **La detección es por título.** Los shows que ponen al invitado solo en la
  descripción quedan fuera.

## MAA

- **Medir:** respuestas / mensajes enviados, y llamadas agendadas.
- **Analizar:** contra outreach frío del mismo periodo. Si el anclaje sirve, la
  brecha debe ser grande. Si no la hay, el problema es el mensaje, no la lista.
- **Actuar:** el bucket con mejor tasa manda la siguiente corrida.

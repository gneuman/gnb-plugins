---
name: pg-donde
description: >
  Encuentra shows donde podrías estar, por cinco caminos: dónde han estado tus
  competidores, en qué otros shows están tus coinvitados, qué escucha tu ICP,
  búsqueda abierta por tema y directorios. Úsalo cuando el usuario diga "dónde
  podría estar", "a qué podcasts puedo entrar", "busca shows para mí", "dónde
  han estado mis competidores", "qué escucha mi cliente", "/pg-donde".
---

# pg-donde — dónde podrías estar

`/pg-research` busca por tema. Este busca por **relación**: quién ya invitó a
alguien como tú, y dónde está tu cliente escuchando.

```bash
python scripts/donde-estar.py competidores "Nombre" "Otro Nombre"
python scripts/donde-estar.py coinvitados invitados.json
python scripts/donde-estar.py icp "dueños de pyme" --region MX
python scripts/donde-estar.py tema "automatización ventas" --region MX
```

Todos aceptan `--json` para guardar el resultado.

## Los cinco caminos

Se corren juntos porque cada uno deja huecos que los otros ven.

### 1. Competidores — la señal más fuerte

Toma a quien hace lo que tú y busca dónde ha estado de invitado.

**La lógica:** si un host invitó a alguien de tu perfil, invita a alguien de tu
perfil. Ya validó que el tema le interesa y que su audiencia lo aguanta. No
estás pidiendo que abra una categoría nueva.

Verificado: buscando "Gabriel Neuman" encontró el show de Javier Yranzo (9,030
subs, 71% con invitado) y descartó SalesRobot por inactivo 247 días.

### 2. Coinvitados — tu propia red

Los que ya coincidieron contigo, ¿en qué **otros** shows han estado?

Cada uno es una puerta con anclaje real: *"vi que tuviste a X; los dos pasamos
por Y"*. Es outreach tibio sin haber hablado nunca con el host.

### 3. ICP — el mejor de todos

**No busca shows sobre tu tema. Busca shows sobre el problema de tu cliente.**

Un consultor de automatización no quiere estar en un podcast de automatización:
ahí la audiencia ya sabe, y están sus competidores. Quiere estar donde escuchan
los dueños de PyME que tienen el problema y no saben que existe la solución.

La query lleva `podcast entrevista invitado` pegado. Sin eso la búsqueda
devuelve canales de creadores que hablan en solo — probado: 0 de 10, todos
canales de una persona. Con el ajuste apareció Oso Trava (1.09M subs, 50% con
invitados).

### 4. Tema — búsqueda abierta

Lo que ya hace `/pg-research`. Cubre lo que no toca tu red.

### 5. Directorio — Listen Notes

Alcanza shows que no publican en YouTube y trae el RSS, de donde sale el correo
del host. Requiere `LISTEN_NOTES_API_KEY`.

## Niveles: a quién puedes llegar HOY

El techo importa tanto como el piso. Un show de un millón de suscriptores recibe
cientos de pitches al mes y **no contesta a alguien sin historial** — encontrarlo
no sirve de nada si empezar por ahí es perder el tiempo.

| Nivel | Rango | Cuándo |
|---|---|---|
| `alcanzable` *(default)* | hasta 15K vistas / 60K subs | El que sí contesta cuando arrancas |
| `estirado` | hasta 60K / 250K | Con dos o tres apariciones de respaldo |
| `sonado` | sin techo | Con un caso fuerte o un contacto en común |

```bash
python scripts/donde-estar.py icp "dueños de pyme" --nivel sonado
```

**El techo aplica a vistas Y a suscriptores.** Con techo solo en vistas, un canal
de 1.09M subs con vistas medianas bajas se colaba por la puerta de suscriptores
— pasó en la prueba con Oso Trava.

Los descartados por tamaño se marcan "para después", no como error: son buenos
shows, guardados para cuando tengas historial.

## Cómo califica

Mismo criterio que `/pg-research`, y por las mismas razones aprendidas:

- **Tamaño:** pasa por vistas **o** por suscriptores. Muchos podcasts en español
  publican primero en Spotify y usan YouTube de canal secundario; medir solo por
  vistas los descarta a todos.
- **Formato:** ≥40% de episodios con invitado, midiendo solo videos de +10 min y
  deduplicando por título — los lives recurrentes repiten el mismo título e
  inflan el denominador.
- **Actividad:** episodio en los últimos 90 días.
- **Techo:** un show demasiado grande tampoco califica. No te va a contestar.

## Cuota

10,000 unidades diarias. `search` cuesta **100**; el resto, 1.

| Camino | Costo | Notas |
|---|---|---|
| competidores | ~100 + 3 por canal | Una búsqueda por persona |
| coinvitados | ~100 por persona | **El más caro** — limita con `--max-personas` |
| icp / tema | ~136 por query | Una búsqueda + evaluación |

`coinvitados` con 8 personas gasta ~800. Es el que hay que dosificar.

## Qué reporta

Los que califican, con **por qué** cada uno (la razón es lo que después va en el
pitch), y **los descartados con su motivo**. Eso último importa: "encontré 3" sin
decir que revisaste 40 oculta que el camino está agotado.

## Después

Los que califican entran al pipeline con `/pg-store`, y de ahí a `/pg-escuchar`
+ `/pg-pitch`.

## MAA

- **Medir:** tasa de respuesta por camino de origen.
- **Analizar:** la hipótesis es que `competidores` y `coinvitados` convierten
  mejor que `tema`, porque llevan anclaje. Si no se cumple, el anclaje no se
  está usando en el pitch.
- **Actuar:** concentrar el gasto de cuota en el camino que convierte.

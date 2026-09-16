---
name: pg-pitch
description: >
  Escribe el pitch a un host de podcast, personalizado a partir de un episodio
  concreto de su show. Úsalo cuando el usuario diga "escribe el pitch para",
  "pitchea este podcast", "mándale a este host", "quiero entrar a este show",
  "/pg-pitch", o cuando pegue el link de un podcast y pida el correo. Requiere
  `wiki-podcast/perfil.md` — si no existe, corre `/pg-setup` primero.
---

# pg-pitch — el correo que un host contesta

Un host recibe pitches genéricos todas las semanas. Lo único que separa el tuyo
es la prueba de que escuchaste su show.

## Antes de escribir

1. **Lee `wiki-podcast/perfil.md`** — de ahí sale la voz, el ICP y la marca propia.
2. **Lee `wiki-podcast/pitch-ganadores.md`** — si tiene entradas, son tu
   referencia. Un pitch que ya convirtió vale más que cualquier plantilla.
3. **Investiga un episodio concreto.** Sin esto no hay pitch, solo spam.

## El episodio es el trabajo

Escoge uno **reciente** y **relacionado con tus temas**. Extrae:

- Número, título, fecha
- La tesis del invitado o del host
- Un momento específico: una frase, un dato, una objeción

**El filtro:** si lo que escribiste sobre el episodio podría aplicar a
cualquier otro episodio de cualquier otro podcast, no lo escuchaste lo
suficiente. Vuelve.

Ese es el punto entero. Un host distingue en dos segundos entre "me encantó tu
episodio sobre marketing" y "cuando dijiste que el 80% de los leads se pierden
entre marketing y ventas, me quedé pensando en…".

## Estructura

```
Asunto: Episodio #[N]

Hola [Host],

[Aprecio al show + una línea sobre su posicionamiento. Sin adulación.]

Me llamó la atención el episodio #[N]. [1-2 frases conectando algo CONCRETO
que se dijo ahí con tu trabajo.]

[Tu bio de una línea, de perfil.md.]

Me encantaría ir como invitado a compartir:

• [Punto 1 — para SU audiencia, no para la tuya]
• [Punto 2]
• [Punto 3]
• [Punto 4 — con tu marca propia en *itálicas*, atada a su audiencia]

¿Te late tenerme en el show?

Un saludo,
[Firma de perfil.md]
```

### Por qué el asunto es solo "Episodio #N"

Es curiosidad pura. El host no sabe si es feedback, un patrocinio o un link
roto — y lo abre. Un asunto que dice "Propuesta de invitado" se archiva sin
abrir.

**Si el show no numera episodios**, usa algo igual de específico y sin vender:
una frase textual del episodio funciona.

### El último bullet

Ahí va tu método o categoría propia, en itálicas, atado a *su* audiencia. Si
`perfil.md` no tiene marca propia, ese bullet lleva un caso concreto con
resultado. **Nunca inventes un framework para llenar el hueco.**

## Reglas duras

- **Cuatro bullets.** Cinco ya es un folleto.
- **Un solo ask.** Nada de "y si no, ¿me recomiendas a alguien?".
- **Sin adjetivos sobre ti mismo.** "Experto reconocido" resta. El caso concreto suma.
- **Sin links en el primer correo** salvo el one-sheet. Los correos con muchos
  links caen en promociones.
- Español de México, sin voseo, salvo que el show sea de otro país — ahí se
  neutraliza el léxico.

## El link rastreable

Si el sistema tiene tracking configurado, el one-sheet va con parámetros:

```
https://[dominio]/me-invitas?c=[campaña]&p=[slug-del-host]
```

Eso permite ver quién abrió y cuánto se quedó, **aunque nunca conteste**. Un
host que pasó tres minutos en la sección de temas está considerándote: ese es
el mejor momento para el seguimiento, y sin el link es invisible.

## Antes de enviar

**Registra el envío primero, envía después** (`/pg-store`). Al revés se pierden
envíos, y sin registro no hay denominador: la tasa de respuesta deja de existir.

## El ciclo de aprendizaje

| Corridas | Comportamiento |
|---|---|
| 1–3 | **Para.** Muestra el borrador, pregunta qué cambiarías, guarda la versión editada |
| 4–10 | Ya hay referencias. Redacta y pide una confirmación |
| 10+ | Corre solo y reporta |

Cuando un pitch consigue respuesta, **guárdalo en `pitch-ganadores.md`** con lo
que lo hizo funcionar. Eso es lo que vuelve autónomo al sistema.

## Seguimiento

Uno solo, a los 5-7 días, en otro canal si se puede (correo → LinkedIn). Aporta
algo nuevo — nunca "siguiendo mi correo anterior".

Dos seguimientos sin respuesta = no. Se marca y se sigue. Insistir quema el
contacto para siempre.

## MAA

- **Medir:** tasa de apertura del one-sheet, tasa de respuesta, agendados.
- **Analizar:** el asunto se juzga por la vista; el cuerpo, por la respuesta.
- **Actuar:** vista alta y respuesta baja → el cuerpo falla. Vista baja → el
  asunto falla. Registrar la vuelta en `logs/`.

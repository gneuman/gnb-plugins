---
name: pg-setup
description: >
  Configura el sistema de podcast guesting para una persona o marca: entrevista
  guiada que produce el perfil (voz, ICP, temas, categoría propia), los criterios
  de calificación y el one-sheet. Es el primer skill que se corre al instalar el
  plugin. Úsalo cuando el usuario diga "configura el sistema", "arranca podcast
  guesting", "setup de podcasts", "instalar el agente de podcasts", "/pg-setup",
  o cuando cualquier otro skill del sistema no encuentre `wiki-podcast/perfil.md`.
---

# pg-setup — la entrevista que hace propio el sistema

Sin esto, el sistema escribe pitches genéricos. El perfil es lo que separa
"otro correo de IA" de un mensaje que un host contesta.

Produce un **wiki**, no un archivo de configuración: se lee al empezar cada
sesión, crece con cada corrida, y es a la vez configuración y memoria.

## Antes de preguntar nada

Revisa si ya existe `wiki-podcast/`. Si existe, **no reinicies el setup** —
muestra lo que hay y pregunta qué actualizar. Rehacer la entrevista completa
borra el aprendizaje acumulado.

## Atajo: si ya estuvo en podcasts, escúchalo primero

**Antes de preguntar nada**, si la persona tiene apariciones previas, pídele los
links y transcríbelos:

```bash
python ~/.claude/skills/pg-escuchar/scripts/transcribir.py <URL> --salida ep1.md
```

Un episodio de 57 minutos tarda 14 segundos y sale gratis. De ahí salen su voz
real, sus cifras y su ICP dicho con sus palabras — mejor material que cualquier
respuesta de entrevista, porque en una entrevista la gente se describe como
quisiera ser.

Con eso llegas a las ocho preguntas con un borrador lleno, y la persona solo
corrige. Es mucho más fácil contestar "¿esto es correcto?" que una hoja en
blanco.

Cómo extraer cada cosa: [`references/derivar-de-episodios.md`](references/derivar-de-episodios.md).

**Regla dura:** nada que no esté en la transcripción. Si una cifra no se dijo,
se pregunta — no se infiere.

## La entrevista

Ocho preguntas, en este orden. **Una a la vez**, con `AskUserQuestion` cuando
haya opciones acotadas. No las hagas todas de golpe: cada respuesta afina la
siguiente.

Si una respuesta es vaga, **repregunta una vez**. "Ayudo a empresas con IA" no
sirve para calificar shows; "ayudo a agencias de 2 a 10 personas a automatizar
su operación" sí.

### 1. Quién eres

Nombre, rol y una línea de posicionamiento. La que usarías si alguien pregunta
"¿a qué te dedicas?" en una fiesta.

### 2. Tu ICP

A quién le vendes: tamaño, sector, cargo. **Es el filtro de todo lo demás** —
define qué show vale la pena y qué coinvitado es cliente potencial.

Si no lo tiene claro: que mire sus últimos 5 clientes buenos. Los que pagaron a
tiempo, obtuvieron resultado y fueron agradables de tratar. Ese es el perfil.

### 3. Los temas que puedes sostener 40 minutos

Tres a cinco. Para cada uno: el título, la tesis en una línea, y tres cosas
concretas que exploras.

**El filtro es honesto:** si no aguantas 40 minutos de preguntas sobre ese tema
sin repetirte, no es tu tema. Un host lo detecta en el minuto diez.

### 4. Tu marca propia

¿Tienes un método, framework o categoría con nombre? Va en el último bullet del
pitch, en itálicas — es lo que da señal de que sabes de qué hablas.

**No inventes un acrónimo si no existe.** Una categoría propia
("Chief Automation Officer externo") funciona mejor que unas siglas que nadie ha
oído. Si no hay nada, este campo queda vacío y el pitch usa un caso concreto en
su lugar. Vacío es mejor que inventado.

### 5. Tus apariciones previas

Podcasts donde ya estuviste: nombre, link, fecha. Si son más de tres, **quédate
con las tres más recientes y on-topic**.

Una aparición de hace ocho años sobre un tema que ya no vendes resta: le dice al
host que llevas ocho años sin que te inviten. Las demás se archivan, no se
borran.

Si no hay ninguna, el one-sheet lo dice de otra forma — no lo finge.

### 6. Prueba social

Testimonios, logos de medios, números verificables.

**Regla dura: nada inventado.** Un número sin fuente es peor que no tener
número. Si no hay testimonios de hosts, se usan de clientes y se etiquetan como
tales.

### 7. Dónde te agendan

El link de calendario. Si no hay, el sistema degrada el CTA a correo — funciona,
pero convierte peor.

### 8. Criterios de calificación

Qué show vale tu tiempo. Los defaults, ajustables:

| Criterio | Default | Por qué |
|---|---|---|
| Tamaño | 30–1,000 ratings Apple, o 500–50,000 vistas medianas | Chico para que conteste, grande para que valga |
| Formato | Hace entrevistas | Ser su primera entrevista es improbable |
| Actividad | Episodio en los últimos 30 días | Un show muerto no publica el tuyo |
| Idioma | El del ICP | — |

En español, **YouTube manda sobre Apple**: los shows en español publican ahí
antes, y las vistas por episodio son dato más honesto que los ratings.

## Lo que se escribe

```
wiki-podcast/
├── index.md            ← mapa; se lee al empezar cada sesión
├── perfil.md           ← respuestas 1-4. La fuente de la voz
├── one-sheet.md        ← respuestas 5-7. Lo que ve el host
├── criterios.md        ← respuesta 8. Lo que filtra shows
├── pitch-ganadores.md  ← vacío al inicio; se llena solo
├── decisiones.md       ← por qué se descartó tal show
├── agents.md           ← protocolo de sesión
└── logs/               ← una entrada por corrida
```

`pitch-ganadores.md` arranca vacío **a propósito**. Se llena con los pitches que
el usuario editó y que consiguieron respuesta. Es el mecanismo que vuelve
autónomo al sistema: las primeras corridas preguntan, las siguientes ya tienen
de dónde copiar.

## El ciclo guiado → automático

No hay flag. El comportamiento cambia porque el wiki acumula:

| Corridas | Qué hace `/pg-pitch` |
|---|---|
| 1–3 | Para antes de enviar, muestra el borrador, pregunta qué cambiarías. Guarda tu edición |
| 4–10 | Ya hay referencias. Redacta solo, pide una confirmación |
| 10+ | `logs/` muestra qué convirtió. Corre solo y reporta |

Escribe esa tabla en `agents.md` para que la siguiente sesión sepa en qué punto
va.

## Al terminar

Reporta qué quedó configurado y **qué quedó vacío**. Un campo vacío no es un
fallo — es información: dice qué falta conseguir antes de empezar a pitchear.

Luego di el siguiente paso concreto: correr `/pg-research` para el primer lote
de shows.

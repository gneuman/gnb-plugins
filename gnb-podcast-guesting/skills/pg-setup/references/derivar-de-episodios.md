# Derivar el perfil de episodios previos

Si la persona ya estuvo en podcasts, **no le preguntes cómo habla — escúchala**.
Una transcripción de 40 minutos contiene su voz real, sus cifras y su ICP dicho
con sus palabras. Todo eso es mejor que lo que conteste en una entrevista, donde
la gente se describe como quisiera ser, no como es.

Esto no reemplaza las ocho preguntas de `/pg-setup`: **las precarga**. Llegas
con un borrador y preguntas "¿esto es correcto?", que es mucho más fácil de
contestar que una hoja en blanco.

## Cuándo aplica

Con **una** aparición previa ya sirve. Con tres, el perfil sale sólido.
Sin ninguna, se hacen las ocho preguntas normales.

## Paso 1 — Transcribir

```bash
python ~/.claude/skills/pg-escuchar/scripts/transcribir.py <URL> --salida ep1.md
```

Un episodio de 57 minutos tarda ~14 segundos y sale gratis.

## Paso 2 — Qué extraer

Lee la transcripción buscando **seis cosas concretas**. No resumas el episodio:
busca evidencia.

### 1. La presentación que hizo el host

Lo primero del episodio. Ahí está la bio en boca de un tercero — con las cifras
que esa persona reporta de sí misma, pero validadas por alguien que las
investigó.

> "implementó más de 121,000 automatizaciones… más de 500 empresas… recuperó
> 225,000 horas"

**Es la mejor fuente de stats que existe**: son públicas, verificables y no
suenan a autobombo porque las dijo otro.

### 2. Cómo se describe cuando le preguntan

Casi siempre corrige o matiza la presentación del host. Esa corrección **es** su
posicionamiento real.

> "Yo creo que la ley demasiado, para mí es mucho, pero sí es lo que hago
> normalmente todos los días: simplificar, optimizar y trabajar más
> eficientemente."

### 3. Muletillas y estructura de frase

Para la voz. Fíjate en:

- Cómo abre una explicación ("Mira…", "Va, si nosotros hablamos de…")
- Si tutea o habla de usted
- Si usa analogías, y de qué tipo
- Palabras que repite

**Cópialas al perfil textualmente.** Una voz se imita con ejemplos, no con
adjetivos: "directo y sin fluff" no le dice nada a nadie.

### 4. El ICP, dicho con sus palabras

Casi nunca dice "mi ICP es". Lo dice contando casos:

> "yo soy una persona trabajando acá, no creas que somos más" → solopreneur
> "para el David que quiere trabajar" → usa el nombre que el host le dio a la audiencia

Busca a quién le habla cuando da un consejo.

### 5. Historias con números

Las anécdotas que ya contó y funcionaron. Sirven dos veces: como prueba en el
one-sheet, y para **no repetirlas** en el mismo show.

> "empecé con automatización en 2005… creamos un coche autónomo con una
> computadora 486"

### 6. Los temas que sostiene sin esfuerzo

Aquellos donde la respuesta se extiende sola y con ejemplos propios. Si al
hablar de algo se pone genérico o corto, **no es su tema** — aunque crea que sí.

## Paso 3 — Presentar el borrador

Muestra lo derivado y pregunta qué corregir. **Cita la fuente de cada dato**:

```
De tu episodio en [Show] ([fecha]) saqué:

  Cifras      121,000 automatizaciones · 500+ empresas · 225,000 horas
              (las dijo el host al presentarte, minuto 00:00)
  Desde       2005
  Temas       automatización de procesos · IA aplicada a PyMEs · NoCode
  Voz         tuteo, analogías cotidianas, arranca con "Mira…"
  ICP         solopreneurs y PyMEs de servicios en LATAM

¿Qué está mal o falta?
```

## Reglas duras

- **Nada que no esté en la transcripción.** Si una cifra no se dijo, no se
  inventa: se pregunta.
- **Los subtítulos automáticos erran en nombres propios y a veces en números.**
  Antes de poner una cifra en el one-sheet, verifícala en el video.
- **Anota la fuente de cada dato** — episodio y minuto. Después nadie recuerda
  de dónde salió un número, y un número sin fuente termina borrado por dudoso.
- **Si contradice lo que la persona dijo en la entrevista, gana la persona** —
  pero menciónalo. Puede ser un dato viejo, o puede ser que se esté subestimando.

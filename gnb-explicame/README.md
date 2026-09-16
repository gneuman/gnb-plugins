# GNB Explícame

Un skill de Claude Code que convierte una duda en la **pieza visual más chica que la
resuelve**. En español de México.

Sin workspace, sin misión, sin archivos de seguimiento. Se dispara, contesta y se va.

## El problema

Pides una explicación y recibes tres párrafos donde cabía un árbol de cinco líneas. O al
revés: preguntas qué cambió y recibes un diagrama de arquitectura completo del que tienes
que adivinar cuál caja es nueva.

El problema no es que falten diagramas. Es que **nadie elige la forma a propósito**.

## El método

`explicame` primero clasifica la duda. La forma sale de ahí:

```
duda de ORDEN      → call tree           ("¿qué llama a qué?")
duda de CAMBIO     → diff                ("¿qué se movió?")
duda de FORMA      → árbol de archivos   ("¿dónde vive esto?")
duda de DECISIÓN   → tabla comparativa   ("¿cuál escojo?")
duda de FLUJO      → mermaid             ("¿cómo viaja el dato?")
duda de LÓGICA     → pseudocódigo        ("¿qué decide qué?")
demasiado densa    → HTML de una pieza   (último recurso, no primero)
```

Y dos reglas que sostienen todo lo demás:

1. **Una pieza por respuesta.** Si necesitas dos, la duda son dos dudas. Tres piezas juntas
   no explican tres veces mejor.
2. **HTML es el último recurso.** Un call tree en bloque de código se lee sin salir del
   terminal. Un HTML obliga a cambiar de ventana, así que tiene que ganárselo.

## Quick start

```bash
# 1. Agrega el marketplace
claude plugin marketplace add gneuman/websitegnb

# 2. Instala el plugin
claude plugin install gnb-explicame@gnb-labs

# 3. Úsalo
/explicame                       # sobre lo que estén hablando
/explicame el flujo de auth      # sobre algo específico
```

También se dispara solo cuando dices "no entiendo cómo funciona X", "muéstrame el flujo",
"en qué orden corre esto" o "¿qué cambió?".

## Customizar

Todo lo específico de marca vive en un bloque `[CUSTOMIZE]` al final de
[`skills/explicame/SKILL.md`](skills/explicame/SKILL.md): nombre, URL, tipografía, colores,
idioma y el comando para abrir archivos (PowerShell por default; hay línea para macOS y
Linux).

Los valores que trae son los de GNB Labs y **funcionan tal cual**. Forkear es sobreescribir,
no rellenar vacíos. El método de arriba no se toca.

Dos variables son opcionales y no son requisito para que el skill corra:

- `VOICE_SKILL` — si tienes un skill de voz propio, apúntalo ahí. Con `none` se salta el
  VOICE GATE y basta con `LANGUAGE`.
- `STUDY_SKILL` — a dónde mandar los temas que no caben en una pieza. Con `none` el skill
  solo te dice que el tema es grande y no lo intenta.

## Qué NO es

No es un curso. Resuelve **una** duda de ahora.

Si el tema vale tres o más sesiones, `explicame` te lo dice y te manda a un skill de estudio
dirigido. Un explicador que también pretende ser currículum termina siendo mal explicador y
mal currículum.

## Crédito

El catálogo de formas visuales viene de
[humanlayer/skills/show-me](https://github.com/humanlayer/skills/tree/main/plugins/show-me)
(MIT), robado como artista.

Lo que agrega esta versión: el método explícito duda→forma (el original lo deja al juicio del
modelo), la regla de una pieza por respuesta, HTML como último recurso, la frontera con el
skill de estudio dirigido, español de México y el bloque `[CUSTOMIZE]`.

## Licencia

MIT. Ver [LICENSE](LICENSE).

---

Hecho por [Gabriel Neuman](https://gabrielneuman.com) / GNB Labs.

¿Quieres montar esto adentro de tu operación —tus procesos, tu equipo, tus skills? Eso se
trabaja en el [Club de IA para PyMEs](https://gabrielneuman.com/club-ia/): taller quincenal
en vivo, cupo de 10 empresas.

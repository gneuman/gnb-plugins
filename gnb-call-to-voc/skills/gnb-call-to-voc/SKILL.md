---
name: gnb-call-to-voc
description: >
  Convierte una llamada de discovery, sales o customer interview en un Voice-of-Customer doc
  estructurado: objeciones con frase literal, lenguaje exacto del cliente, jobs-to-be-done,
  pain points cuantificados, frases listas para usar en landing pages y outreach. USO INTERNO
  — no genera contenido público. Para contenido público usar gnb-call-to-content.
  Use when: "voice of customer", "VoC doc", "qué dijo el cliente", "saca insights del
  discovery", "objeciones del cliente", "/call-to-voc", "gnb-call-to-voc".
related: [gnb-call-to-content, customize-block]
---

# GNB Call to VoC

Transforma una transcripción de discovery/sales en un **Voice-of-Customer doc**: el lenguaje exacto que tu mercado usa, las objeciones reales, los pain points cuantificados, los jobs-to-be-done. Material para landings, outreach, posicionamiento y mejora de oferta.

> **Importante:** este skill es **uso interno**. NO genera contenido público (privacy del cliente). Si quieres convertir una llamada PÚBLICA en contenido distribuible, usa `gnb-call-to-content`.

> **Antes de correr este skill:** lee el bloque `[CUSTOMIZE]` al final. Define `$OUTPUT_PATH`, `$STAKEHOLDERS_TO_SHARE` y tu framework JTBD si tienes uno.

## Por qué un VoC doc importa

La diferencia entre una landing que convierte y una que no es **usar el lenguaje exacto del cliente**, no el de la agencia. Una llamada de 30 min con un cliente real contiene 20+ frases que valen oro:

- La forma en que describe su problema (no como el marketing lo describe)
- Las objeciones que tiene contra soluciones existentes
- El criterio con el que evaluaría tu propuesta
- Los workarounds que ya está usando (= competencia real)
- El costo del problema en su lenguaje (no en el tuyo)

Sin un VoC doc, ese material se pierde después de la llamada. Con uno, alimenta landings, ads, outreach y mejora del producto.

## Antes de empezar

Necesitas:
- **Transcripción** de la llamada (mínimo viable — sin transcripción este skill no opera bien)
- **Tipo de llamada:** discovery, sales (closing), customer interview (cliente activo), churn interview (cliente que se fue)
- **Contexto:** quién es el cliente (industria, tamaño, rol), qué ofrecías/estabas explorando

Si no hay transcripción, preguntar primero:
1. ¿Tienes la grabación? (recomendar transcribir con Whisper / Otter / Fireflies primero)
2. Si solo hay notas: ¿podemos trabajar con notas? (output será más débil, marcarlo en el doc)

## Privacy y consentimiento

Antes de procesar:
- Confirmar que la llamada se grabó con consentimiento del cliente.
- El doc generado es **uso interno**. NO publicar frases del cliente sin permiso explícito.
- Si vas a usar una frase específica en landing/marketing, anonimizar (rol + industria, sin nombre).
- Si el cliente pidió "off the record" en algún momento, marcar esos pasajes y excluirlos del VoC.

Si no hay consentimiento explícito de grabación, abortar.

## Estructura del VoC doc (output)

Generar `$OUTPUT_PATH/[call-slug]/voc.md` con esta estructura:

```markdown
# Voice of Customer — [Slug de la llamada]

## Meta
- **Fecha de la llamada:** YYYY-MM-DD
- **Tipo:** discovery | sales | customer-interview | churn-interview
- **Cliente:** [rol] en [tipo de empresa] de [industria] (sin nombre si va a circular fuera del núcleo)
- **Duración:** N min
- **Resultado:** [interés / quote enviada / cerró / no cerró / churned]
- **Fuente:** [path o URL de la transcripción]
- **Procesado por:** Claude Code + gnb-call-to-voc v0.1.0

---

## 1. Lenguaje del cliente (literal)

Frases textuales que el cliente usó para describir su mundo. Sin parafrasear. Cada frase tagueada por tema.

### Sobre el problema
> "[frase literal]" — *contexto: hablaba de [X]*
> "[frase literal]" — *contexto: hablaba de [Y]*

### Sobre soluciones existentes
> "[frase literal]" — *referencia a [competidor/workaround]*

### Sobre lo que buscan
> "[frase literal]"

### Sobre criterios de decisión
> "[frase literal]"

---

## 2. Pain points (con costo cuantificado si se mencionó)

Por cada pain point identificado:

### Pain: [nombre corto]
- **Frase del cliente:** "[literal]"
- **Frecuencia:** "[cada cuánto pasa según el cliente]"
- **Costo:** "[en dinero, tiempo, oportunidad — lo que se haya dicho]"
- **Workaround actual:** "[qué hace hoy para mitigarlo]"
- **Urgencia:** alta / media / baja (según tono del cliente, no inferencia)

---

## 3. Jobs to be Done (framework Christensen)

Por cada job detectado:

### Job: [verbo + objeto + contexto]
> "Cuando [situación], quiero [acción], para que [resultado deseado]."

- **Funcional:** [qué tarea concreta]
- **Emocional:** [qué siente o quiere sentir]
- **Social:** [cómo quiere ser percibido]
- **Evidencia en la llamada:** "[frase literal que lo prueba]"

---

## 4. Objeciones detectadas

Cada objeción con la respuesta que tú/tu equipo dio (si la dieron) y evaluación de si funcionó:

### Objeción: [resumen corto]
- **Frase del cliente:** "[literal]"
- **Tipo:** precio | timing | confianza | feature | autoridad-decisión | competencia
- **Respuesta que se dio:** "[lo que se respondió, o 'no se respondió']"
- **Cómo reaccionó el cliente:** [tono, siguiente pregunta, cambio de tema]
- **Score de respuesta:** funcionó / funcionó parcialmente / no funcionó / no se respondió
- **Mejor respuesta para próxima vez:** [propuesta del skill, basada en el contexto]

---

## 5. Competencia mencionada

Toda referencia a otra empresa, herramienta o solución alternativa:

| Mención | Contexto en la llamada | Sentimiento (positivo/negativo/neutral) |
|---|---|---|
| [nombre] | "[frase literal]" | [+/-/0] |

---

## 6. Criterios de decisión del cliente

Lista exhaustiva de criterios que mencionó (explícita o implícitamente) para evaluar una propuesta:

1. [Criterio 1 — frase literal]
2. [Criterio 2 — frase literal]
3. ...

Subrayar cuáles son **deal-breakers** (sin esto, no compra) vs **nice-to-have**.

---

## 7. Personas y autoridad

- **Quién estaba en la llamada:** roles
- **Quién decide en realidad:** [rol o nombre — qué dijo o no dijo lo revela]
- **Quién paga:** [si es distinto al que decide]
- **Otros stakeholders mencionados:** [con qué influencia]

---

## 8. Señales de fit / no-fit

### Señales de buen fit
- [Frase o comportamiento que sugiere que esta cuenta SÍ es ideal]
- [Frase o comportamiento que sugiere lo mismo]

### Señales de mal fit (red flags)
- [Frase o comportamiento que sugiere que no — ej. presupuesto, autoridad, urgencia, timing]
- [Otra señal]

### Verdict
[Recomendación: avanzar | calificar más | descartar | nutrir 6 meses]

---

## 9. Material listo para usar

### Para landing pages
- Headlines candidatos (extraídos del lenguaje del cliente):
  - "[propuesta 1 — usando palabras del cliente]"
  - "[propuesta 2]"
- Bullets de feature → benefit:
  - **Feature:** [...] → **Benefit en lenguaje cliente:** "[literal del cliente]"

### Para outreach
- Asunto de email basado en pain literal: "[propuesta]"
- Apertura usando frase del cliente: "[propuesta]"

### Para FAQ / objection handling
- [Objeción literal] → respuesta corta

### Para roadmap de producto
- [Feature que el cliente pidió o implicó que faltaba]
- [Bug o fricción que mencionó]

---

## 10. Acciones para el equipo

- [ ] [Acción 1 con dueño + deadline]
- [ ] [Acción 2 con dueño + deadline]
- [ ] [Acción 3]

---

## 11. Citas para revisar con humano

Frases que pueden ser oro pero requieren validación con quien estuvo en la llamada (matiz, tono, ironía):

> "[frase]" — *no quedó claro si era queja o broma*
> "[frase]" — *contradice lo que dijo antes*

---

## Cómo se procesó este doc

- Modelo: claude-opus / claude-sonnet
- Skill: gnb-call-to-voc v0.1.0
- Transcripción: [fuente]
- Tiempo de procesado: N min
- Confianza global: alta / media / baja (alta = transcripción completa y clara; baja = solo notas o audio parcial)
```

## Reglas

1. **Citas LITERALES, no parafraseadas.** Si la transcripción es ambigua, marcar la cita como "(aproximada)" y pedir validación humana.
2. **NO inventar pains que el cliente no mencionó.** Inferir está OK, pero marcarlo: "(inferencia — no dicho explícitamente)".
3. **NO publicar nada de este doc sin permiso del cliente.** El skill genera para uso interno.
4. **Marcar nivel de confianza honestamente.** Notas vagas → confianza baja. Transcripción completa con timestamps → alta.
5. **Anonimizar antes de circular fuera del núcleo.** Reemplazar nombre de empresa por "[empresa B2B fintech mediana]" si el doc va a marketing/diseño.
6. **Si la llamada tuvo "off the record":** excluir esos pasajes del VoC. Mencionarlo en Meta del doc.

## Cuándo usar este skill

✅ Después de cada discovery call (incluso si no cierra)
✅ Después de cada sales call larga (>30 min)
✅ Customer interview programada para research
✅ Churn interview con cliente que canceló
✅ Cuando vas a refactorizar una landing y necesitas lenguaje real
✅ Cuando vas a escribir outreach a una vertical específica y tienes calls previas

## Anti-patrones

- ❌ Procesar una llamada sin consentimiento de grabación.
- ❌ Publicar frases literales del cliente sin anonimizar y sin permiso.
- ❌ Usar este skill para generar contenido público de podcast/webinar (usar `gnb-call-to-content`).
- ❌ Marcar todo como "confianza alta" cuando la transcripción es mediocre.
- ❌ Crear "objeciones inferidas" sin frase literal que las respalde.
- ❌ Parafrasear el lenguaje del cliente al lenguaje de marketing (mata el propósito del VoC).

## Reportar al cerrar

Máximo 7 líneas:
- Archivo generado: `$OUTPUT_PATH/[call-slug]/voc.md`
- Pains identificados: N
- Objeciones detectadas: N (cuántas se respondieron bien / mal / no se respondieron)
- Jobs to be done: N
- Headlines candidatos para landing: N
- Verdict de fit: [avanzar / calificar / descartar / nutrir]
- Próximo paso recomendado: [1 línea]

---

## [CUSTOMIZE] — Configuración por agencia/equipo

### Identidad
```yaml
AGENCY_NAME: "GNB Labs"
AGENCY_CONTACT: "soy@gabrielneuman.com"
```

### Output
```yaml
OUTPUT_PATH: "cerebro/voc"          # ruta donde se generan voc.md por call
SHARE_WITH:                         # dónde notificar cuando se genera un VoC nuevo
  - "marketing"
  - "product"
  - "ventas"
ANONYMIZE_BY_DEFAULT: true          # reemplaza nombres antes de circular
```

### Framework JTBD
```yaml
JTBD_FORMAT: "christensen"          # christensen | ulwick | switch-interview
USE_JOBS_HIERARCHY: true            # funcional + emocional + social
```

### Objeciones — tipos esperados
```yaml
OBJECTION_TYPES:
  - "precio"
  - "timing"
  - "confianza"
  - "feature-falta"
  - "autoridad-decision"
  - "competencia"
  - "implementacion"
  - "soporte"
# Agregar tipos según el mercado del cliente
```

### Calificación de fit (umbrales para verdict)
```yaml
FIT_CRITERIA_HIGH:                  # señales de buen fit
  - "tiene presupuesto mencionado"
  - "tiene autoridad o acceso directo a quien decide"
  - "tiene urgencia (deadline o evento gatillo)"
  - "el problema le cuesta dinero medible"
FIT_CRITERIA_RED_FLAG:              # señales de mal fit
  - "pide mucho free / proof of concept gratis"
  - "no puede nombrar el costo del problema"
  - "decide por comité de >5"
  - "ya intentó con 3+ vendors y no avanzó"
```

### Tipos de llamada bloqueados
```yaml
BLOCKED_TYPES: []
# Vacío por default — este skill procesa todo lo interno. Si una llamada es PÚBLICA (podcast,
# webinar), redirigir a gnb-call-to-content.
```

### Voz
```yaml
VOICE_SKILL: "voz-gnb"              # para los headlines candidatos
LANGUAGE: "es-MX"
```

### Privacy
```yaml
REQUIRE_CONSENT_CHECK: true         # preguntar antes de procesar si hubo consentimiento
EXCLUDE_OFF_THE_RECORD: true        # respetar pasajes "off the record"
RETENTION_DAYS: 365                 # cuánto vive el voc.md antes de archivar
```

---

## Para forkar este skill

1. Copiar a `~/.claude/skills/<nuevo-nombre>/SKILL.md` o a tu plugin propio.
2. Editar `[CUSTOMIZE]` con tu agencia, output path y criterios de fit.
3. Si tu mercado tiene objeciones específicas (regulación, idioma, vertical), ajusta `OBJECTION_TYPES`.
4. Procesa una llamada real antes de usarlo regularmente — calibra el output al tono que necesitas.

## Atribución

Framework JTBD: Clayton Christensen + Bob Moesta (*Competing Against Luck*). Patrón `[CUSTOMIZE]` de Anthropic.

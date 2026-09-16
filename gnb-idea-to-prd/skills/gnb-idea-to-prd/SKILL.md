---
name: gnb-idea-to-prd
description: >
  Convierte una idea suelta (brain dump, voicenote del cliente, descripción informal) en un
  PRD estructurado listo para construir. Entrevista guiada en 10 fases que produce PRD +
  CLAUDE.md + AGENTS.md + llms.txt + prompts de milestone. Aplica para proyectos nuevos Y
  features dentro de proyectos existentes.
  Use when: "PRD", "convertir idea en spec", "necesito un PRD", "quiero construir",
  "nueva funcionalidad", "/idea-to-prd", "gnb-idea-to-prd".
related: [gnb-prd-to-issues]
---

# GNB Idea to PRD

De la idea cruda al PRD listo para construir. Output: archivos en `_build_plan/` que cualquier agente puede leer para empezar a trabajar.

> **Antes de correr este skill:** lee el bloque `[CUSTOMIZE]` al final. Define `$DEFAULT_STACK` y `$AGENCY_NAME` para tu agencia. Si este skill se reusa en otra agencia/cliente, ese bloque es lo único que cambia.

## Principios

1. **No existe milestone sin PRD aprobado.** Antes de escribir código, existe un PRD. Siempre.
2. **Proponer un default con razón, luego confirmar.** Nunca preguntar "¿qué quieres?" en abierto cuando se puede proponer algo concreto.
3. **AskUserQuestion para decisiones con opciones claras.** Texto libre solo para brain dump inicial y nombres cortos.
4. **Una decisión a la vez, en secuencia.** Cerrar cada fase antes de avanzar.
5. **El PRD describe el QUÉ, no el CÓMO.** Comportamiento del usuario, flujos, scope. Sin librerías ni nombres de métodos — eso lo decide el agente en plan mode.
6. **Docs duales.** Todo proyecto genera documentación para humanos (PRD, README) Y para agentes (AGENTS.md, llms.txt).

## Detección de contexto

Antes de empezar, determinar sin preguntar:
- ¿Es un **proyecto nuevo** o un **feature dentro de un proyecto existente**?
  - Proyecto nuevo: generar set completo (PRD + CLAUDE.md + AGENTS.md + llms.txt + milestones)
  - Feature existente: solo `_build_plan/features/{slug}/prd.md` + milestone prompt, y actualizar AGENTS.md
- ¿Hay codebase? Leer CLAUDE.md, package.json, Gemfile, estructura. Reportar lo encontrado antes de proponer stack.

## Fases

### Fase 0 — Brain dump
Si el primer mensaje ya es sustancial, esa es la entrada. Si no, pedir en texto libre: "Descríbeme la idea: qué quieres construir, para quién, y qué problema resuelve."

### Fase 1 — Core purpose
Sintetizar en 1–3 oraciones. Proponer de vuelta. `AskUserQuestion`: Sí / Casi (edito en chat) / No (explico de nuevo).

### Fase 2 — Features en scope
Proponer 4–8 features core con una línea cada uno. Usuario confirma, recorta o agrega.

### Fase 3 — Out of scope
Proponer lista de cosas que podrían estar pero NO van en v1, con una línea de por qué cada una. Común: mobile nativa, roles complejos, analytics avanzados, importaciones masivas, API pública.

### Fase 4 — Stack
Detectar stack existente. Si no hay: proponer `$DEFAULT_STACK` del `[CUSTOMIZE]`. `AskUserQuestion`: Usar default / Ya tengo (especifico en chat) / No sé (explícame opciones).

### Fase 5 — Integraciones y credenciales
Por cada feature que necesite servicio externo:
1. Qué hace el servicio en lenguaje llano
2. Proponer proveedor con razón (más simple / más barato / más estándar)
3. Listar credenciales que el usuario necesita obtener antes del milestone que las usa

No prescribir cómo se almacenan — eso lo decide el agente.

### Fase 6 — Data model
"Aquí están las cosas que el sistema necesita recordar y cómo se relacionan." Por entidad: nombre, campos en lenguaje llano, relaciones. Sin tipos de DB. Confirmar.

### Fase 7 — Scoping por feature
Feature por feature (no en batch):
- **En scope:** qué ve el usuario, qué puede hacer, cómo se ve el output
- **Fuera de scope:** versiones más ambiciosas de este feature que v1 no tiene

Sin implementación técnica. Confirmar cada feature antes del siguiente.

### Fase 8 — Milestones
Proponer 3 opciones de breakout:
- **Default:** 3 milestones — Fundación/Auth → Features Core → Integraciones/Polish
- **Compacta:** 2 milestones — Foundation+Core junto → Polish
- **Granular:** 4–6 milestones — uno por feature principal

Cada milestone entrega algo visible y testeable. Confirmar.

### Fase 9 — Dev Portal (nota)
Linear (o `$TRACKER_DEFAULT`) es el Dev Portal de los proyectos. **Pero se configura cuando el cliente paga onboarding** — no durante el PRD. En el PRD solo va la nota:

```markdown
### Dev Portal — pendiente de onboarding
- Tracker: $TRACKER_DEFAULT
- Cada milestone = un cycle/sprint
- Labels base: feature, bug, feedback, question, cliente
- Acceso del cliente: solo lectura + crear issues
- Regla: todo feedback entra como issue, no por WhatsApp ni email
```

### Fase 10 — Escribir archivos
Sin pedir aprobación adicional. Generar:

**Proyecto nuevo:**
```
_build_plan/
  prd.md
  milestones/
    1-{slug}/prompt.md
    2-{slug}/prompt.md
CLAUDE.md
AGENTS.md
llms.txt
```

**Feature en proyecto existente:**
```
_build_plan/features/{slug}/
  prd.md
  milestones/1-{slug}/prompt.md
```
Y actualizar `AGENTS.md` con el nuevo feature.

Reportar qué está listo y cómo usarlo (≤4 líneas).

## Templates

### `_build_plan/prd.md`

```markdown
# {Nombre} — PRD

## Qué construimos

{1–3 oraciones de core purpose. Párrafo de contexto. "El build está estructurado en N milestones."}

### Qué hace el sistema
{5–10 bullets desde la perspectiva del usuario.}

### Ya provisto por el stack / codebase
{Lo que no hay que construir.}

### Fuera de scope (v1)
{Lista con razón por ítem.}

### Modelo de datos
{Por entidad: campos en lenguaje llano, relaciones. Sin tipos de DB.}

### Dev Portal — {$TRACKER_DEFAULT}
- Pendiente de onboarding (se configura cuando el cliente paga)
- Cada milestone = un cycle/sprint
- Acceso cliente: lectura + crear issues con label `cliente`

---

## Milestone 1 — {Nombre}

{Qué entrega este milestone en 1–2 oraciones.}

### Qué se construye
{Lista de capacidades visibles al terminar — lo que el usuario puede hacer en el browser.}

### Explícitamente fuera de este milestone
{Cosas que alguien podría asumir que van aquí pero no van.}

### Done when
{1–2 oraciones: criterio de verificación en el browser.}

---

{Repetir por milestone}
```

### `AGENTS.md`

```markdown
# {Nombre} — Instrucciones para Agentes

## Regla principal
No construir fuera del scope del milestone activo. Si algo no está en el PRD del milestone, documentarlo y preguntar antes de construir.

## Stack
$DEFAULT_STACK

## Correr localmente
{Comando único según stack}

## Documentos clave
- PRD: `_build_plan/prd.md`
- Milestone activo: `_build_plan/milestones/{N}-{slug}/prompt.md`
- Log anterior: `_build_plan/milestones/{N-1}-{slug}/milestone-log.md`

## Dev Portal
- {$TRACKER_DEFAULT}: pendiente de configurar en onboarding

## Al terminar un milestone
Escribir `milestone-log.md` con: archivos modificados, decisiones tomadas no especificadas en PRD, lo que el siguiente milestone necesita saber, desviaciones del PRD y por qué.
```

### `llms.txt`

```markdown
# {Nombre}

{1 párrafo: qué es, para quién, qué problema resuelve.}

## Stack
$DEFAULT_STACK

## Archivos clave
{rutas según stack}

## Documentación
- PRD: `_build_plan/prd.md`
- Para agentes: `AGENTS.md`

## Dev Portal
- {$TRACKER_DEFAULT}: pendiente

## Estado actual
{Qué está construido, qué milestone está activo.}
```

### `_build_plan/milestones/N-{slug}/prompt.md`

```markdown
# Milestone {N} — {Nombre}

Entrar en plan mode para planear y construir.

## Contexto
- Leer `@_build_plan/prd.md`
- Leer `@AGENTS.md`
- Leer logs de milestones anteriores si existen

## Tarea
1. Planear la implementación de SOLO el milestone {N}
2. Usar AskUserQuestion para confirmar el plan antes de construir
3. Construir solo lo que está en scope
4. Verificar contra el criterio "Done when" del PRD
5. Escribir `milestone-log.md` al terminar

El log debe incluir: archivos creados, decisiones de implementación, lo que el siguiente milestone necesita saber, desviaciones del PRD.
```

## Cuándo usar este skill

✅ Antes de cualquier milestone — sin excepción
✅ Al empezar un proyecto nuevo
✅ Cuando el cliente pide un feature nuevo
✅ Para alinear expectativas antes de cotizar
✅ Cuando el scope está borroso y hay que aterrizarlo

## Anti-patrones

- ❌ Generar el PRD sin pasar por las 10 fases. Es entrevista, no template fill.
- ❌ Decidir librerías o nombres de métodos en el PRD. Eso lo decide el agente.
- ❌ Crear el proyecto en el tracker durante el PRD. Eso es del onboarding (cuando el cliente paga).
- ❌ Aceptar scope vago "queremos que sea como Notion" — pedir features concretas en Fase 2.

---

## [CUSTOMIZE] — Configuración por agencia/cliente

> Edita SOLO este bloque cuando reuses este skill en otro contexto.

### Identidad de la agencia
```yaml
AGENCY_NAME: "GNB Labs"
AGENCY_CONTACT: "soy@gabrielneuman.com"
AGENCY_URL: "https://gabrielneuman.com"
```

### Stack técnico por defecto
```yaml
DEFAULT_STACK:
  framework: "Next.js 15 + TypeScript + Tailwind CSS"
  database: "Supabase (PostgreSQL + Auth + Storage)"
  hosting: "Vercel"
  run_local: "npm install && npm run dev"
```

### Tracker / Dev Portal por defecto
```yaml
TRACKER_DEFAULT: "Linear"           # Linear, Jira, GitHub Projects, Notion, etc.
TRACKER_LABELS_BASE:
  - "feature"
  - "bug"
  - "feedback"
  - "question"
  - "cliente"
CLIENT_ACCESS_LEVEL: "Guest — lectura + crear issues, sin asignar ni cambiar prioridades"
```

### Output paths
```yaml
PRD_PATH: "_build_plan/prd.md"
FEATURE_PRD_PATH: "_build_plan/features/{slug}/prd.md"
MILESTONE_PROMPT_PATH: "_build_plan/milestones/{N}-{slug}/prompt.md"
```

### Voz
```yaml
VOICE_SKILL: "voz-gnb"
LANGUAGE: "es-MX"
```

### Reglas duras (no cambiar entre forks salvo razón fuerte)
```yaml
REQUIRE_PRD_BEFORE_MILESTONE: true
ALLOW_TECH_DETAILS_IN_PRD: false
GENERATE_AGENTS_MD: true
GENERATE_LLMS_TXT: true
```

---

## Para forkar este skill

1. Copiar a `~/.claude/skills/<nuevo-nombre>/SKILL.md` o a tu plugin propio.
2. Editar SOLO `[CUSTOMIZE]` con tu stack default, tracker y voz.
3. Renombrar `name:` del frontmatter.
4. Probar con una idea real antes de usar en cliente.

## Atribución

Patrón de empaquetado inspirado en [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins) (Apache 2.0). Filosofía `[CUSTOMIZE]` de Anthropic.

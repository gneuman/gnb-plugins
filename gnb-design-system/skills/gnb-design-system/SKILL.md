---
name: gnb-design-system
description: >
  Scaffolder de página /admin/design-system para proyectos Next.js + Tailwind + shadcn.
  Genera una ruta única visible al equipo con todos los tokens (colores, tipografía, spacing,
  radios), componentes base y patrones de dominio. Una sola fuente de verdad visual para
  diseñadores, devs y stakeholders.
  Use when: "design system", "style guide", "tokens del proyecto", "página de componentes",
  "/admin/design-system", "gnb-design-system".
---

# GNB Design System

Genera una página `/admin/design-system` (o la ruta que configure el cliente) en proyectos Next.js + Tailwind + shadcn. La página es **una sola fuente de verdad visual** — tokens, primitivos, patrones de dominio — accesible al equipo y al cliente en lugar de Figma desactualizado.

> **Antes de correr este skill:** lee el bloque `[CUSTOMIZE]` al final. Define `$DS_ROUTE`, `$BRAND_PALETTE` y `$DOMAIN_PATTERNS` para tu proyecto. Si el skill se reusa en otra agencia/cliente, ese bloque es lo único que cambia.

## Filosofía

1. **Una ruta, no Figma.** Figma desactualizado miente; código en producción no. La página vive dentro de la app y siempre refleja la verdad.
2. **Tokens antes de componentes.** Antes de generar un botón, definir su color, radio y tipografía. Lo demás se deriva.
3. **Patrones de dominio sí, branding del cliente no.** El skill scaffolea patrones genéricos (KPI cards, badges de estado, tablas de operaciones). El branding del cliente entra vía `[CUSTOMIZE]`.
4. **shadcn como base.** No reinventamos primitivos. Copiamos componentes shadcn y los envolvemos con tokens del proyecto.
5. **Re-runnable.** El skill puede correrse N veces sin sobreescribir customizaciones del usuario (zonas marcadas con `gnb-design-system:start` / `:end`).

## Fases

### Fase 0 — Detectar contexto

Sin preguntar:
- Leer `package.json` → confirmar Next.js (App Router preferred) + Tailwind. Si falta Tailwind o es Vite/Rails/otro, **abortar** con mensaje claro: "Este skill soporta Next.js + Tailwind. Para otros stacks, ver gnb-design-system-vite (roadmap)."
- Leer `tailwind.config.ts` / `tailwind.config.js` → ver tokens existentes (colors, fontFamily, borderRadius).
- Leer `components/ui/` → ver si shadcn ya está instalado y qué componentes existen.
- Leer `app/globals.css` → ver variables CSS de tema (modo claro/oscuro shadcn).

Reportar lo encontrado al usuario en 4 líneas máximo. NO pedir confirmación si todo está bien — proceder.

### Fase 1 — Confirmar ruta

Default: `/admin/design-system`. Si el proyecto ya tiene `/admin/*` → ok. Si no → preguntar con `AskUserQuestion` si el cliente quiere `/admin/design-system`, `/design-system`, `/styleguide`, u otra.

### Fase 2 — Cargar branding del `[CUSTOMIZE]`

Leer el bloque `[CUSTOMIZE]` del propio skill. Tomar:
- `BRAND_PALETTE` (paleta del cliente: primary, accent, ink, surface, ...)
- `BRAND_FONTS` (font-family principal y secundaria)
- `BRAND_RADIUS_SCALE` (escala de border-radius)
- `DOMAIN_PATTERNS` (qué patrones generar: kpi-cards, status-badges, data-table, etc.)

Si el bloque no está customizado (vars en blanco), preguntar al usuario los 3 datos mínimos:
1. Color primario (hex)
2. Color de acento (hex)
3. Font principal (Google Font o "system-ui")

NO preguntar más. El resto se deriva.

### Fase 3 — Modo (instalación nueva vs re-run)

Detectar si ya existe `app/admin/design-system/page.tsx` (o equivalente). Si existe:
- `AskUserQuestion`: "(a) Actualizar tokens manteniendo customizaciones, (b) Reemplazar todo, (c) Cancelar."
- Si (a): leer el archivo, parsear las zonas marcadas, actualizar SOLO el contenido entre marcadores.
- Si (b): backup del archivo a `*.bak` y reemplazar.
- Si (c): salir limpio.

### Fase 4 — Escribir archivos

Generar (con substitución de tokens del `[CUSTOMIZE]`):

```
app/[$DS_ROUTE]/
  page.tsx                          ← página principal con todas las secciones
  _components/
    Section.tsx                     ← wrapper de sección con título + descripción
    SubSection.tsx                  ← wrapper de subsección
    TokenSwatch.tsx                 ← muestra de color con hex
    TypeScale.tsx                   ← muestra de tipografía
components/ui/
  button.tsx, badge.tsx, card.tsx, ... ← copiar shadcn si faltan
  (todos opcionales si ya existen)
```

Estructura de `page.tsx` (secciones):

1. **Branding** — paleta del cliente, fonts, tagline si aplica
2. **Tokens base** — colores semánticos (background, foreground, primary, accent, destructive, muted, border), escala de spacing, escala de radius
3. **Tipografía** — h1 a xs con tamaño y line-height
4. **Componentes base** — Button (6 variantes), Badge (4 variantes), Card, Tabs, Input, Progress, Separator
5. **Patrones de dominio** — sección parametrizada por `$DOMAIN_PATTERNS`:
   - `kpi-cards`: 4 KPIs en grid con valor + delta + sparkline opcional
   - `status-badges`: badges de estado con color por estado (`active`, `pending`, `error`, `success`, `archived`)
   - `data-table`: tabla con header sticky + paginación + filtros
   - `empty-states`: estados vacíos con ilustración + CTA
   - `forms`: formularios con validación visible

Zonas marcadas:
```tsx
{/* gnb-design-system:start branding */}
... contenido auto-generado ...
{/* gnb-design-system:end branding */}
```

Lo que está afuera de los marcadores es customización del usuario y NO se toca en re-run.

### Fase 5 — Actualizar AGENTS.md / CLAUDE.md

Agregar al `CLAUDE.md` raíz (o `AGENTS.md` si existe) un bloque marcado:

```markdown
<!-- gnb-design-system:start -->
## Design System

Ruta: `/[$DS_ROUTE]`. Una sola fuente de verdad visual.

- **Antes de inventar un componente nuevo:** chécalo en la página, probablemente ya existe.
- **Antes de hardcodear un color:** úsalo como token (`text-primary`, `bg-accent`). Si falta, agrégalo a `tailwind.config.ts` Y a la página.
- **Antes de cambiar un primitivo:** edita el componente en `components/ui/` y verifica que la página sigue legible.
<!-- gnb-design-system:end -->
```

Re-run actualiza solo entre marcadores.

### Fase 6 — Resumen

Reportar al usuario en máximo 6 líneas:
- Ruta generada
- N archivos creados / actualizados
- Tokens detectados desde `tailwind.config.ts`: N
- Patrones de dominio incluidos: lista
- Link para abrir: `http://localhost:3000/[$DS_ROUTE]`
- Próximo paso sugerido (1 línea, accionable)

## Reglas

1. **NO usar marcas del cliente en el output sin `[CUSTOMIZE]`.** Si el cliente es "Acme", NO escribir "Acme" en el código — usar `$AGENCY_NAME` o "Tu Marca" como placeholder.
2. **NO instalar shadcn si ya está.** Detectar y reusar. Solo agregar primitivos faltantes.
3. **NO modificar `tailwind.config.ts` sin permiso explícito.** Reportar qué falta, pedir confirmación, luego editar.
4. **NO crear nuevos componentes si shadcn los tiene.** Reusar siempre.
5. **Patrones de dominio van comentados como "ejemplo".** El cliente decide si los conserva o borra después. Skill no asume industria.
6. **Voz GNB en todo texto visible del scaffold.** Aplica VOICE GATE de `voz-gnb` antes de escribir copys placeholder.

## Output contract

Cuando el usuario invoca `/gnb-design-system`:

1. Detectar stack y reportar (Fase 0).
2. Confirmar ruta (Fase 1).
3. Cargar branding del `[CUSTOMIZE]` o preguntar 3 datos mínimos (Fase 2).
4. Decidir modo new/re-run (Fase 3).
5. Escribir archivos con substitución (Fase 4).
6. Actualizar AGENTS.md/CLAUDE.md (Fase 5).
7. Reportar (Fase 6).

NO escribir nada más en el sistema. NO modificar tailwind.config.ts sin confirmar. NO instalar paquetes.

## Anti-patrones

- ❌ Hardcodear hex del cliente en el código del skill.
- ❌ Generar componentes que ya existen en shadcn (Button propio, Card propio).
- ❌ Mezclar patrones de dominio de industrias (fintech + e-commerce + saas en la misma página). El usuario elige los suyos.
- ❌ Modificar archivos del usuario fuera de marcadores `gnb-design-system:start/end`.
- ❌ Asumir App Router cuando el proyecto usa Pages Router (detectar, no asumir).

---

## [CUSTOMIZE] — Configuración por agencia/cliente

> Edita SOLO este bloque cuando reuses este skill en otro contexto. Lo de arriba es la lógica
> del scaffolder y NO se toca.

### Ruta de instalación
```yaml
DS_ROUTE: "admin/design-system"  # ruta relativa a /app, sin slash inicial
```

### Identidad de la agencia
```yaml
AGENCY_NAME: "GNB Labs"
AGENCY_CONTACT: "soy@gabrielneuman.com"
AGENCY_URL: "https://gabrielneuman.com"
```

### Paleta de marca por defecto
```yaml
BRAND_PALETTE:
  primary: "#0891b2"       # cyan-600 — CTAs principales
  accent: "#f59e0b"        # amber-500 — destacados
  ink: "#0f172a"           # slate-900 — texto principal
  surface: "#ffffff"       # background base
  muted: "#64748b"         # slate-500 — texto secundario
  border: "#e2e8f0"        # slate-200 — divisores
  destructive: "#dc2626"   # red-600 — errores
  success: "#16a34a"       # green-600 — confirmación
```

### Fonts por defecto
```yaml
BRAND_FONTS:
  sans: "Inter"            # body — Google Font
  display: "DM Sans"       # headings — Google Font
  mono: "ui-monospace"     # código — system stack
```

### Escala de radius
```yaml
BRAND_RADIUS_SCALE:
  sm: "0.25rem"
  md: "0.5rem"
  lg: "0.75rem"
  xl: "1rem"
  "2xl": "1.5rem"
  "3xl": "2rem"
```

### Patrones de dominio a generar
```yaml
DOMAIN_PATTERNS:
  - kpi-cards              # 4 KPIs con delta y trend
  - status-badges          # badges de estado parametrizables
  - data-table             # tabla con header sticky y filtros
  - empty-states           # estados vacíos con CTA
  - forms                  # formularios con validación visible
  # comentar/descomentar según el proyecto
```

### Voz
```yaml
VOICE_SKILL: "voz-gnb"
LANGUAGE: "es-MX"
```

### Atribución en footer del DS
```yaml
DS_FOOTER: "Design System generado con GNB Design System v0.1.0 — gabrielneuman.com/sistemas/skills/design-system"
SHOW_FOOTER: true
```

---

## Para forkar este skill a otro contexto

1. Copiar este SKILL.md a `~/.claude/skills/<nuevo-nombre>/SKILL.md` o a tu plugin propio.
2. Editar SOLO el bloque `[CUSTOMIZE]` con la paleta, fonts y patrones de tu cliente.
3. Renombrar `name:` del frontmatter.
4. Apuntar `VOICE_SKILL` a tu skill de voz si tienes uno propio.
5. Probar con un repo Next.js + Tailwind real antes de usar en cliente.

## Atribución

Patrón de empaquetado inspirado en [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins) (Apache 2.0) y [`buildermethods/bm-skills`](https://github.com/buildermethods/bm-skills). Filosofía `[CUSTOMIZE]` de Anthropic.

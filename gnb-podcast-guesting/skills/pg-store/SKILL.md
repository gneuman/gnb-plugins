---
name: pg-store
description: >
  Capa de almacenamiento del sistema de podcast guesting. Decide sola dónde
  guardar shows, personas y mensajes: al CRM si hay credenciales, a archivos
  locales si no. Ningún otro skill del sistema habla con Mongo ni con la API
  directamente — todos pasan por aquí. Úsalo cuando el usuario diga "guarda
  esto en el CRM", "registra el envío", "cómo va el pipeline", "dame el KPI de
  podcasts", "/pg-store".
---

# pg-store — dónde vive el estado

Un agente que corre solo no puede detenerse a preguntar si hay base de datos.
Este skill resuelve eso: **detecta el destino y sigue**.

## Regla de degradación

Se evalúa en orden y se usa el primero disponible. Nunca al revés.

| Orden | Destino | Condición | Qué implica |
|---|---|---|---|
| 1 | **CRM** | `GNB_CRM_URL` y `GNB_CRM_TOKEN` presentes | KPI en el Radar, historial completo |
| 2 | **Local** | siempre | `.podcast-guesting/` en el repo. Funciona sin nada configurado |

**El local no es un modo degradado, es el default.** El CRM es el extra que
tiene Gabriel. Un cliente que instala el plugin funciona completo desde el
minuto uno sin configurar nada.

**Escritura dual:** cuando hay CRM, se escribe en los dos. El archivo local es
la fuente de verdad para el agente; el CRM es para el tablero humano. Si el CRM
falla, el agente **no se detiene**: registra el fallo en `errores.log` y sigue
con el local. Un pipeline caído no puede bloquear el outreach.

## Estructura local

```
.podcast-guesting/
├── config.yaml       ← perfil, ICP, criterios. Lo escribe /pg-setup
├── shows.json        ← podcasts objetivo + su etapa
├── personas.json     ← coinvitados + bucket
├── mensajes.json     ← cada envío, con fecha y canal
├── eventos.json      ← visitas al one-sheet (si hay tracking)
├── errores.log       ← fallos de sync, para no perderlos en silencio
└── logs/             ← una entrada por corrida
```

Todo va en `.gitignore`: **son nombres y correos de terceros.** Esa es regla
dura del proyecto, no preferencia.

## Operaciones

Cada una es idempotente por `slug` (nombre normalizado). Correr dos veces el
mismo alta no duplica.

| Operación | Qué hace |
|---|---|
| `guardar_show` | Alta o actualización de un podcast objetivo |
| `guardar_persona` | Alta de un coinvitado con su bucket |
| `mover_etapa` | Transición con historial. No retrocede etapas |
| `registrar_envio` | Un mensaje enviado. **Es el denominador del KPI** |
| `registrar_respuesta` | Marca respondido y adelanta etapa |
| `kpi` | Los números del tablero |

### El registro de envío no es opcional

Sin él no hay denominador, y sin denominador no hay tasa de respuesta — solo un
conteo de respuestas que no dice nada. **Si el agente manda un mensaje y no lo
registra, el KPI miente.**

Por eso la regla: *primero se registra, luego se envía*. Si el envío falla, se
marca el registro como fallido. Al revés se pierden envíos.

## Contrato con el CRM

Cuando hay credenciales, el skill llama a la API. **Nunca importa código de
gnb-crm** — un plugin instalado en otra máquina no tiene ese repo.

```
POST   {GNB_CRM_URL}/api/v1/podcasts          → alta
PATCH  {GNB_CRM_URL}/api/v1/podcasts/{id}     → etapa, bucket, mensajes
GET    {GNB_CRM_URL}/api/v1/podcasts/kpi      → KPI
```

Auth: `Authorization: Bearer {GNB_CRM_TOKEN}`.

Timeout de 10s. Si expira o devuelve 5xx, se anota en `errores.log` y se
continúa con el local. **Un 401 sí se reporta al usuario** — significa token
malo, y callarlo haría que el pipeline se vacíe en silencio.

## KPI

Se calcula igual con o sin CRM:

| Métrica | Fórmula | Para qué |
|---|---|---|
| Pitches enviados | mensajes con `followUp: 0` | Volumen real de actividad |
| Tasa de respuesta | respondieron / pitcheados | Si el mensaje sirve |
| Tasa de vista | vieron one-sheet / pitcheados | Si el asunto abre |
| Tasa de agendado | agendados / pitcheados | El que paga |
| Apariciones | etapa `grabado` o más | El KPI final |

**Las tasas son `null`, no `0`, cuando no hay denominador.** "Todavía no hay
datos" y "0%" son cosas distintas: la primera no debe pintar rojo en el
tablero ni disparar una alerta.

**`vio_onesheet` no cuenta como respuesta.** Es señal de intención — alguien
que abrió y leyó, pero no contestó. Mezclarlas inflaría la tasa de respuesta y
haría creer que el mensaje funciona cuando lo que funcionó fue el asunto.

## Al cerrar una corrida

Reportar siempre: **cuántos se guardaron, cuántos se saltaron por duplicado, y
cuántos fallaron al sincronizar.** Un fallo silencioso se lee como éxito.

## MAA

- **Medir:** pitches enviados, tasa de respuesta, apariciones/mes.
- **Analizar:** base = cero medido. Hoy no existe instrumentación.
- **Actuar:** si la vista es alta y la respuesta baja, el problema es el
  one-sheet. Si la vista es baja, el problema es el asunto del pitch.

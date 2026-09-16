---
name: pg-research
description: >
  Busca podcasts que califican para pitchear como invitado y los da de alta en el
  pipeline. Filtra por tamaño, formato de entrevista, actividad e idioma. Úsalo
  cuando el usuario diga "busca podcasts de", "encuentra shows para pitchear",
  "podcasts sobre [tema]", "a qué podcasts puedo entrar", "/pg-research".
  Requiere `wiki-podcast/criterios.md` — si no existe, corre `/pg-setup`.
---

# pg-research — encontrar shows que valgan el tiempo

Buscar a mano toma horas y trae listicles desactualizados con shows muertos
hace años. Esto lo hace en minutos contra datos vivos.

## Criterios

Se leen de `wiki-podcast/criterios.md`. Los defaults:

| Criterio | Regla | Por qué |
|---|---|---|
| Tamaño | 30–1,000 ratings Apple **o** 500–50,000 vistas medianas | Chico para que conteste, grande para que valga |
| Formato | Hace entrevistas (≥50% de episodios recientes con invitado) | Ser su primera entrevista es improbable |
| Actividad | Episodio en los últimos 30 días | Un show muerto no publica el tuyo |
| Idioma / región | Los del ICP | Un show en inglés no sirve si vendes en México |

**No busques al más grande.** Un show de 200 oyentes que son exactamente tu ICP
vale más que uno de 50,000 que no te compra. El caso que cuenta Corey Ganim: un
episodio con menos de 3,000 vistas generó la mitad de los miembros de su
comunidad de pago.

## Fuentes, en orden

### 1. YouTube — primera opción en español

Los shows en español publican en YouTube antes que en Apple, y las vistas por
episodio son dato más honesto que los ratings.

```bash
python scripts/buscar-youtube.py "[tema]" --region MX --idioma es
```

**Cuota:** la YouTube Data API da 10,000 unidades diarias. `search` cuesta
**100**, `playlistItems` y `videos` cuestan **1**. Por eso el script busca una
vez y luego navega por playlist — nunca encadena búsquedas. Un barrido de 20
shows gasta menos que una sola búsqueda mal hecha.

Necesita `YOUTUBE_API_KEY` en el entorno.

### 2. Listen Notes — cuando hace falta el RSS

Trae el feed, y del feed sale el correo del host. Plan gratis: 300
requests/mes. Necesita `LISTEN_NOTES_API_KEY`.

### 3. Apple Podcasts — última opción

Sin API pública usable. Requiere navegador y es lento. Úsalo solo para
verificar ratings de un show específico, nunca para descubrir.

## Verificación

Para cada candidato:

1. **Tamaño** — ratings o vistas medianas de los últimos episodios (la mediana,
   no el promedio: un viral distorsiona).
2. **Formato** — revisa los últimos 10 títulos. Patrones de invitado: `con X`,
   `with X`, `ft. X`, `| X`, `#N — X`.
3. **Actividad** — fecha del último episodio.
4. **Encaje** — ¿su audiencia es tu ICP? Un show de marketing con audiencia de
   agencias sirve si le vendes a agencias.

**El script propone, tú confirmas.** La detección por título falla con shows que
solo nombran al invitado en la descripción.

## Alta en el pipeline

Cada show que califica entra vía `/pg-store` como `tipo: show`, etapa
`prospecto`, con sus métricas del momento — se congelan porque explican por qué
entró.

Los que **no** califican van a `wiki-podcast/decisiones.md` con el motivo. Sin
eso, la siguiente corrida vuelve a evaluar los mismos y a descartarlos otra vez.

## Al cerrar

Reporta: **cuántos candidatos, cuántos calificaron, y por qué se cayeron los
demás** — agrupado por motivo. "Encontré 3" sin decir que revisaste 40 y 12
estaban muertos oculta que el nicho puede estar agotado.

## Después

- `/pg-pitch` para escribirle al host.
- **`/pg-invitados` sobre cada show que califica** — los coinvitados suelen ser
  mejor oportunidad que el host, y ya viste que el show es relevante.

## MAA

- **Medir:** shows calificados por corrida y tasa de calificación.
- **Analizar:** si la tasa cae bajo 10%, el nicho se está agotando: cambia el
  tema o el idioma.
- **Actuar:** ajusta `criterios.md` y registra la vuelta en `logs/`.

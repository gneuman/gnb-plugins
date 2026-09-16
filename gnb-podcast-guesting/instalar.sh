#!/usr/bin/env bash
# Instalador de GNB Podcast Guesting.
#
#   git clone https://github.com/gneuman/gnb-plugins
#   cd gnb-plugins/gnb-podcast-guesting && ./instalar.sh
#
# Copia los skills a ~/.claude/skills/, verifica dependencias y deja el sistema
# listo. No pide permisos de administrador ni toca nada fuera de ~/.claude.
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESTINO="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

echo "GNB Podcast Guesting"
echo "===================="
echo

# ── 1. Skills ────────────────────────────────────────────────────────────────
mkdir -p "$DESTINO"
n=0
for skill in "$AQUI"/skills/*/; do
  nombre="$(basename "$skill")"
  # -T evita que una segunda corrida anide el skill dentro del anterior.
  cp -rT "$skill" "$DESTINO/$nombre"
  echo "  instalado  $nombre"
  n=$((n + 1))
done
echo
echo "$n skills en $DESTINO"
echo

# ── 2. Dependencias ──────────────────────────────────────────────────────────
echo "Dependencias"
echo "------------"
faltan=0

check() { # nombre, comando, obligatorio, como_instalar
  if command -v "$2" >/dev/null 2>&1; then
    printf '  ok       %-10s\n' "$1"
  elif [ "$3" = "req" ]; then
    printf '  FALTA    %-10s  %s\n' "$1" "$4"
    faltan=$((faltan + 1))
  else
    printf '  opcional %-10s  %s\n' "$1" "$4"
  fi
}

check python3 python3 req "instala Python 3.8+"
check yt-dlp  yt-dlp  req "pip install yt-dlp"
check ffmpeg  ffmpeg  opt "solo para transcribir shows sin subtitulos"
check whisper whisper opt "pip install openai-whisper — idem"

echo

# ── 3. Credenciales ──────────────────────────────────────────────────────────
echo "Credenciales"
echo "------------"
if [ -n "${YOUTUBE_API_KEY:-}" ]; then
  echo "  ok       YOUTUBE_API_KEY"
else
  echo "  FALTA    YOUTUBE_API_KEY   sin esto no corren pg-research ni pg-invitados"
  echo "           Sacala gratis en console.cloud.google.com (YouTube Data API v3)"
  echo "           export YOUTUBE_API_KEY=..."
  faltan=$((faltan + 1))
fi

if [ -n "${GNB_CRM_URL:-}" ] && [ -n "${GNB_CRM_TOKEN:-}" ]; then
  echo "  ok       CRM            sincroniza ademas del archivo local"
else
  echo "  opcional CRM            sin esto todo funciona en local"
fi

echo
if [ "$faltan" -gt 0 ]; then
  echo "Resuelve lo que dice FALTA y vuelve a correr esto."
  echo
fi

# ── 4. Siguiente paso ────────────────────────────────────────────────────────
cat <<'FIN'
Siguiente paso
--------------
Abre Claude Code en el repo donde quieras trabajar y corre:

    /pg-setup

Son ocho preguntas. De ahi sale tu perfil, tu ICP, tus temas y los criterios
para calificar shows. Sin eso el sistema escribe correos genericos.

Si ya estuviste en algun podcast, ten los links a la mano: se pueden
transcribir con /pg-escuchar y de ahi salen tu voz y tus cifras reales.
FIN

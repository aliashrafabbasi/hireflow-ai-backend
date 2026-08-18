#!/usr/bin/env bash
# HireFlow — one command to start (or rebuild) the backend in Docker.
#
#   ./start.sh           # start
#   ./start.sh --build   # rebuild after code changes
#   ./start.sh --rpa     # start + grant X11 for visible browser RPA
#   ./start.sh --n8n     # start API + n8n automation
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

BUILD=0
RPA=0
N8N=0
EXTRA=()

for arg in "$@"; do
  case "$arg" in
    --build|-b) BUILD=1 ;;
    --rpa) RPA=1 ;;
    --n8n) N8N=1 ;;
    *) EXTRA+=("$arg") ;;
  esac
done

if [[ -f .env ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    export "$key=$val"
  done < .env
fi

if [[ "$RPA" == 1 || ( "${RPA_ENABLED:-false}" == "true" && "${RPA_HEADLESS:-false}" != "true" ) ]]; then
  if command -v xhost >/dev/null 2>&1; then
    xhost +local: >/dev/null
    echo "X11 ready for visible RPA (revoke later: xhost -local:)"
  fi
fi

COMPOSE=(docker compose)
if [[ "$N8N" == 1 ]]; then
  COMPOSE+=(--profile automation)
fi

if [[ "$BUILD" == 1 ]]; then
  "${COMPOSE[@]}" up --build -d "${EXTRA[@]}"
else
  "${COMPOSE[@]}" up -d "${EXTRA[@]}"
fi

echo ""
echo "HireFlow API:  http://localhost:8000/docs"
echo "Health check:  curl http://localhost:8000/api/v1/health"
if [[ "$N8N" == 1 ]]; then
  echo "n8n:           http://localhost:5678"
fi
echo "Frontend:      http://localhost:3000  (run separately: npm run dev)"
echo "pgAdmin DB:    localhost:5432 / hireflow_db"

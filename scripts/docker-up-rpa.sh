#!/usr/bin/env bash
# Start HireFlow Compose with headed RPA (visible browser on your Linux desktop).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

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

headless="${RPA_HEADLESS:-false}"
enabled="${RPA_ENABLED:-false}"

if [[ "${enabled,,}" == "true" && "${headless,,}" != "true" ]]; then
  if ! command -v xhost >/dev/null 2>&1; then
    echo "WARNING: xhost not found — headed RPA may fail inside Docker." >&2
  else
    xhost +local: >/dev/null
    echo "Granted local X11 access for headed RPA (revoke later with: xhost -local:)"
  fi
fi

exec docker compose "$@"

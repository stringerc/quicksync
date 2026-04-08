#!/usr/bin/env bash
# Start Lawbot (FastAPI + static UI) after optional preflight.
# Usage:
#   bash scripts/launch.sh              # preflight then uvicorn
#   SKIP_PREFLIGHT=1 bash scripts/launch.sh   # dev iteration (server only)
#
# Optional env:
#   LAWBOT_HOST   (default 127.0.0.1 — use 0.0.0.0 for LAN)
#   LAWBOT_PORT   (default 8765)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  . .venv/bin/activate
fi

if [[ "${SKIP_PREFLIGHT:-}" != "1" ]]; then
  bash scripts/preflight_launch.sh
fi

HOST="${LAWBOT_HOST:-127.0.0.1}"
PORT="${LAWBOT_PORT:-8765}"
echo ""
echo "Starting Lawbot at http://${HOST}:${PORT}/  (Ctrl+C to stop)"
exec uvicorn lawbot.api.app:app --host "$HOST" --port "$PORT" --reload

#!/usr/bin/env bash
# Local Lawbot UI + API (default http://127.0.0.1:8765/)
# For full preflight + server, use: bash scripts/launch.sh
# Env: LAWBOT_HOST (default 127.0.0.1), LAWBOT_PORT (default 8765)
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${LAWBOT_HOST:-127.0.0.1}"
PORT="${LAWBOT_PORT:-8765}"
exec uvicorn lawbot.api.app:app --host "$HOST" --port "$PORT" --reload

#!/usr/bin/env bash
# OpenClaw-friendly wrapper: full Lawbot verification (HTTP + Hermes + mock LLM tests).
# Install: symlink or copy to a PATH location, or call with absolute path from an OpenClaw HTTP tool.
#
# Usage:
#   ./scripts/openclaw_lawbot_verify.sh
#   BASE_URL=https://your-host ./scripts/openclaw_lawbot_verify.sh
#
# Requires: running Lawbot (uvicorn), same as verify_user_flow.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec "${ROOT}/scripts/verify_user_flow.sh"

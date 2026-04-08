#!/usr/bin/env bash
# Run all automated gates before serving Lawbot (tests + golden + optional live API probes).
# Usage: bash scripts/preflight_launch.sh
# No keys needed for unittest + ci_quality. Live probes run only if NVIDIA_API_KEY (or OPENAI_COMPATIBLE_API_KEY) is set in .env.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  . .venv/bin/activate
fi

echo "== Lawbot preflight (repo: $ROOT) =="

echo "== 1/3 Draft quality + golden fixtures =="
bash scripts/ci_quality.sh

echo "== 2/3 Full unit test suite =="
python -m unittest discover -s tests -p 'test_*.py' -q

echo "== 3/3 Live API probes =="
if python -c "from lawbot.config import settings; import sys; sys.exit(0 if settings.openai_compatible_key() else 1)"; then
  python scripts/verify_apis.py
else
  echo "SKIP: No OPENAI-compatible API key in environment — run 'python scripts/verify_apis.py' after setting NVIDIA_API_KEY in .env"
fi

echo ""
echo "PREFLIGHT OK — safe to launch: bash scripts/launch.sh"

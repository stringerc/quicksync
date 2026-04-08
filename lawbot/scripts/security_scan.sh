#!/usr/bin/env bash
# Ruff + Bandit on lawbot/ (medium+ severity). Safe to run locally and in CI.
# Tool versions: `requirements-dev.txt` (keep aligned with .pre-commit-config.yaml).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "== ruff =="
ruff check lawbot tests scripts
echo "== bandit (lawbot/, severity medium+) =="
bandit -r lawbot -ll -q -f txt
echo "== OK =="

#!/usr/bin/env bash
# Strict gate: lint/security + unit tests with ResourceWarning as error + bytes warnings.
# Run before releases or when validating resilience changes.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== 1. security_scan (ruff + bandit) =="
bash scripts/security_scan.sh

echo "== 2. unittest (strict warnings: ResourceWarning → error, -bb bytes checks) =="
export PYTHONWARNINGS=error::ResourceWarning
export PYTHONDEVMODE=${PYTHONDEVMODE:-1}
python -bb -W error::ResourceWarning -m unittest discover -s tests -p 'test_*.py' -q

echo "== 3. Hermes golden fixtures (offline) =="
python -m lawbot.eval.run_goldens

echo "== 4. Golden matrix coverage report =="
python -m lawbot.eval.matrix_report --write eval/runs/matrix_report.json

echo "== OK (strict_test) =="

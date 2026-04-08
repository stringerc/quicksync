#!/usr/bin/env bash
# Deterministic quality gates + golden fixtures (no LLM). Run in CI or locally.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== lawbot: draft_quality_gate + golden fixtures =="
python -m unittest tests.test_draft_quality_gate tests.test_golden_drafts -v
echo "== golden metrics (CI log / artifact) =="
python scripts/draft_quality_golden_metrics.py --jsonl-out draft-quality-golden.jsonl
echo "== OK =="

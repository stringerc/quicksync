#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-baseline} # baseline|resonance
DURATION=${DURATION:-300}
RATE=${RATE:-1000}

if [[ "$MODE" == "resonance" ]]; then
  export RESONANCE_MODE=active
  echo "Running k6 with Resonance in active mode..."
else
  export RESONANCE_MODE=observe
  echo "Running k6 in baseline mode..."
fi

# Run k6 load test
k6 run \
  --vus 100 \
  --duration ${DURATION}s \
  --out json=out_${MODE}.json \
  bench/k6_script.js

echo "Results saved to out_${MODE}.json"


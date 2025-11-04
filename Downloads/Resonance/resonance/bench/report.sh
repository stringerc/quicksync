#!/usr/bin/env bash

BASELINE=${1:-baseline}
RESONANCE=${2:-resonance}

echo "Generating report comparing $BASELINE vs $RESONANCE..."

# Parse JSON outputs and compute deltas
node -e "
const fs = require('fs');

const baseline = JSON.parse(fs.readFileSync('out_${BASELINE}.json', 'utf8'));
const resonance = JSON.parse(fs.readFileSync('out_${RESONANCE}.json', 'utf8'));

const metrics = ['p(95)', 'p(99)', 'p(99.9)', 'p(99.99)'];

console.log('\n=== Benchmark Results ===\n');

metrics.forEach(metric => {
  const base = baseline.metrics[\`http_req_duration{\\\${metric}}\`]?.value || 0;
  const res = resonance.metrics[\`http_req_duration{\\\${metric}}\`]?.value || 0;
  const delta = base > 0 ? ((base - res) / base * 100).toFixed(1) : 0;
  
  console.log(\`\${metric}: \${delta}% improvement\`);
});

console.log('\n');
"


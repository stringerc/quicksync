#!/usr/bin/env node

const DEFAULT_URL = process.env.RESONANCE_AGENT_INTAKE || 'https://syncscript-backend-1.onrender.com/intake/phase';
const TOTAL_SAMPLES = parseInt(process.env.PHASE_SAMPLES || '120', 10);
const INTERVAL_MS = parseInt(process.env.PHASE_INTERVAL_MS || '1000', 10);

if (!globalThis.fetch) {
  console.error('This script requires Node.js 18+ (fetch API available)');
  process.exit(1);
}

function generatePhases(count) {
  const now = Date.now();
  const phases = [];
  for (let i = 0; i < count; i += 1) {
    const phase = (Math.sin((now / 1000) + i) + 1) * Math.PI; // in [0, 2π]
    phases.push(phase);
  }
  return phases;
}

async function sendSample(sampleIndex) {
  const phases = generatePhases(16);
  const spectralEntropy = 0.4 + 0.1 * Math.sin(sampleIndex / 5);
  const payload = {
    phases,
    spectralEntropy,
    p99Risk: 0.1,
  };

  const response = await fetch(DEFAULT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status} - ${text}`);
  }

  const body = await response.json();
  console.log(`[#${sampleIndex + 1}] R=${body.R?.toFixed?.(3) ?? body.R}, entropy=${body.spectralEntropy?.toFixed?.(3) ?? body.spectralEntropy}`);
}

async function main() {
  console.log(`Streaming ${TOTAL_SAMPLES} phase samples to ${DEFAULT_URL} (interval ${INTERVAL_MS} ms)`);
  for (let i = 0; i < TOTAL_SAMPLES; i += 1) {
    try {
      await sendSample(i);
    } catch (err) {
      console.error(`Error sending sample #${i + 1}:`, err.message);
      process.exit(1);
    }
    if (i < TOTAL_SAMPLES - 1) {
      await new Promise((resolve) => setTimeout(resolve, INTERVAL_MS));
    }
  }
  console.log('Completed phase streaming.');
}

main();

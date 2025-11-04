/**
 * Simple Resonance Example
 * Demonstrates basic usage
 */

import { ResonanceCore } from '../resonance-core';
import { ResonanceClient } from '../sdk/node';
import { ResonanceCalculus } from '../resonance-core/calculus';
import { TokenBucket } from '../sdk/node/client';

async function main() {
  console.log('=== Resonance Example ===\n');

  // Initialize core
  const core = new ResonanceCore({
    R_band: [0.35, 0.65],
    K_min: 0.05,
    K_max: 1.0,
    maxMicroDelayMs: 7,
    defaultBatchLatencyMs: 25,
  });

  // Initialize calculus and token bucket
  const calculus = new ResonanceCalculus();
  const tokenBucket = new TokenBucket({ refillRate: 10, capacity: 100 });

  // Create client
  const client = new ResonanceClient(core, calculus, tokenBucket);

  // Example 1: Basic submit
  console.log('1. Basic Submit:');
  const result1 = await client.submit(
    async () => {
      await new Promise((r) => setTimeout(r, 10));
      return { value: 42 };
    },
    {
      id: 'task-1',
      importance: 'normal',
      canBatch: false,
    }
  );
  console.log(`   Result: ${JSON.stringify(result1)}`);

  // Example 2: Submit with activation
  console.log('\n2. Submit with Resonance Active:');
  core.setMode('active');
  const result2 = await client.submit(
    async () => {
      await new Promise((r) => setTimeout(r, 10));
      return { value: 100 };
    },
    {
      id: 'task-2',
      importance: 'normal',
      canBatch: false,
    }
  );
  console.log(`   Result: ${JSON.stringify(result2)}`);
  console.log(`   State: R=${core.getState().R.toFixed(3)}`);

  // Example 3: Explainability
  console.log('\n3. Explain Decision:');
  const explanation = client.explain('task-2');
  console.log(`   Decision: ${explanation.decision}`);
  console.log(`   Reason: ${explanation.reason}`);
  console.log(`   Features:`, explanation.features);

  // Example 4: Retry with jitter
  console.log('\n4. Retry with Jitter:');
  let attempts = 0;
  const result4 = await client.retry(
    async () => {
      attempts++;
      if (attempts < 3) {
        throw new Error(`Attempt ${attempts} failed`);
      }
      return { success: true, attempts };
    },
    {
      strategy: 'full_jitter',
      baseDelayMs: 20,
      maxDelayMs: 20000,
      maxAttempts: 5,
    }
  );
  console.log(`   Result: ${JSON.stringify(result4)}`);

  // Example 5: State monitoring
  console.log('\n5. State Monitoring:');
  const state = client.getState();
  console.log(`   R: ${state?.R.toFixed(3)}`);
  console.log(`   K: ${state?.K.toFixed(3)}`);
  console.log(`   Mode: ${state?.mode}`);
  console.log(`   Spectral Entropy: ${state?.spectralEntropy.toFixed(3)}`);

  console.log('\n=== Example Complete ===');
}

if (require.main === module) {
  main().catch(console.error);
}


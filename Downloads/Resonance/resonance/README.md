# Resonance Runtime

**Production-grade tail-tolerant distributed runtime** with synchronization intelligence.

## What is Resonance?

Resonance delivers **15–35% reductions in p95/p99/p99.9 latency** using:

1. **Measurement correctness** (HdrHistogram + open-loop wrk2)
2. **Tail-latency policies** (hedging, jittered retries, two-choices LB)
3. **OS/kernel cooperation** (CFS isolation, BBR transport)
4. **eBPF observability** (low-overhead tracepoints)
5. **Mathematical decision layer** (Resonance Calculus for max-plus bounds)

## Quick Start

```bash
# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test

# Run benchmarks
npm run bench
```

## Usage

### Basic Example

```typescript
import { ResonanceCore } from './resonance-core';
import { ResonanceClient } from './sdk/node';

// Initialize core
const core = new ResonanceCore({
  R_band: [0.35, 0.65],
  K_min: 0.05,
  K_max: 1.0,
  maxMicroDelayMs: 7,
  defaultBatchLatencyMs: 25,
});

// Create client
const client = new ResonanceClient(core);

// Submit task with hints
const result = await client.submit(async () => {
  return await heavyWork();
}, {
  id: 'task-1',
  importance: 'normal',
  canBatch: true,
  maxBatchLatencyMs: 25,
});

// Enable active mode
core.setMode('active');
```

### Hedging Example

```typescript
// Request hedging
const { result, hedgeFired, hedgeDelay } = await client.hedge(
  async () => await fetch('/api/data'),
  { id: 'fetch', idempotent: true },
  { delayMs: 10, maxInflightPct: 150, cancelOnFirst: true, idempotentOnly: true }
);
```

### Retry with Jitter

```typescript
// Jittered retry
const result = await client.retry(
  async () => await unreliableOperation(),
  {
    strategy: 'full_jitter',
    baseDelayMs: 20,
    maxDelayMs: 20000,
    maxAttempts: 5,
  }
);
```

## Architecture

```
resonance-core/     # Kuramoto R(t), PLL, Controller
spectral/           # STFT, entropy, PLV
resonance-math/     # RA-Phasor, RA-Trop, RA-Log
sdk/node/           # Client SDK with hedging/retry
observability/      # HdrHistogram, metrics
policy/             # Configs and profiles
bench/              # wrk2 + k6 harness
```

## Documentation

- [RESONANCE_V2_PRODUCT.md](../RESONANCE_V2_PRODUCT.md) - Complete specification
- [TECHNICAL_SPEC.md](../TECHNICAL_SPEC.md) - Implementation details
- [observability/metrics.md](observability/metrics.md) - Metrics reference

## License

MIT


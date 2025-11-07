# Resonance Bench Harness

## Overview

Bench harness for **open-loop constant-rate load generation** to avoid coordinated omission artifacts.

## Requirements

- **wrk2**: Open-loop load generator
- **k6**: Alternative load generator
- **HdrHistogram**: For accurate percentile collection

## Installation

```bash
# Install wrk2
brew install wrk2  # macOS
# Or compile from: https://github.com/giltene/wrk2

# Install k6
brew install k6

# Node dependencies
npm install
```

## Usage

### Baseline Run

```bash
./run.sh baseline
```

### Resonance Active Run

```bash
RESONANCE_MODE=active ./run.sh resonance
```

### Generate Report

```bash
./report.sh baseline resonance
```

### Feed Phase Samples to the Agent

Use the helper script to stream synthetic phase samples into the agent's intake endpoint (default is the Render-hosted service):

```bash
# Optional: override the intake URL and sample count
export RESONANCE_AGENT_INTAKE="https://syncscript-backend-1.onrender.com/intake/phase"
export PHASE_SAMPLES=240          # total samples to send
export PHASE_INTERVAL_MS=1000     # delay between samples

node bench/feed_phases.js
```

After a few minutes of streaming, the Resonance Calculus metrics will populate and the band-compliance percentage will begin trending upward.

## Benchmark Configs

### wrk2-config.yaml

```yaml
rate: 1000              # Constant 1000 RPS (open-loop)
connections: 100        # Connection pool
duration: 300s          # 5-minute sustained load
threads: 4              # Parallel workers
latency: true           # Collect latency histogram
hdr_histogram: true     # HdrHistogram output
```

## Success Criteria

- p95 improvement: ≥15%
- p99 improvement: ≥20%
- p99.9 improvement: ≥30%
- Overhead: <2%


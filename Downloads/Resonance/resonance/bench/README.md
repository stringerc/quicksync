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


/**
 * Resonance Agent
 * Production agent entry point for DaemonSet/Sidecar deployment
 */

import * as fs from 'fs';
import * as path from 'path';
import * as http from 'http';
import { ResonanceCore } from '../resonance-core';

// Load configuration
const configPath = process.env.RESONANCE_CONFIG_FILE || path.join(__dirname, '../../policy/defaults.json');
const defaults = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

// Initialize core
const mode = (process.env.RESONANCE_MODE as any) || defaults.mode || 'shadow';
const core = new ResonanceCore({
  R_band: defaults.R_band || [0.35, 0.65],
  K_min: defaults.K_min || 0.05,
  K_max: defaults.K_max || 1.0,
  maxMicroDelayMs: defaults.maxMicroDelayMs || 7,
  defaultBatchLatencyMs: defaults.defaultBatchLatencyMs || 25,
});
core.setMode(mode);

// Metrics server (Prometheus format)
const metricsPort = parseInt(process.env.RESONANCE_METRICS_PORT || '9090');
const metricsServer = http.createServer((req, res) => {
  if (req.url === '/metrics') {
    const state = core.getState();
    const modeValue = state.mode === 'observe' ? 0 : state.mode === 'shadow' ? 1 : state.mode === 'adaptive' ? 2 : 3;
    
    // Get Resonance Calculus metrics if available
    const calculus = (globalThis as any).__resonance_calculus;
    
    let metrics = `# HELP resonance_R Kuramoto order parameter R(t) [0-1]
# TYPE resonance_R gauge
resonance_R ${state.R}

# HELP resonance_K Adaptive coupling strength
# TYPE resonance_K gauge
resonance_K ${state.K}

# HELP resonance_spectral_entropy Spectral entropy H_s [0-1]
# TYPE resonance_spectral_entropy gauge
resonance_spectral_entropy ${state.spectralEntropy}

# HELP resonance_mode Controller mode (0=observe, 1=shadow, 2=adaptive, 3=active)
# TYPE resonance_mode gauge
resonance_mode{value="${state.mode}"} ${modeValue}

# HELP resonance_up Agent is running
# TYPE resonance_up gauge
resonance_up 1

`;

    // Add Resonance Calculus metrics if available
    if (calculus) {
      metrics += `# HELP resonance_coherence_score Coherence-weighted service curve score [0-1]
# TYPE resonance_coherence_score gauge
resonance_coherence_score ${calculus.coherenceScore ?? 0.5}

# HELP resonance_tail_health_score Tail health score from EVT/GPD [0-1]
# TYPE resonance_tail_health_score gauge
resonance_tail_health_score ${calculus.tailHealthScore ?? 0.5}

# HELP resonance_timing_score Timing score from max-plus algebra [0-1]
# TYPE resonance_timing_score gauge
resonance_timing_score ${calculus.timingScore ?? 0.5}

# HELP resonance_lambda_res Max-plus eigenvalue (cycle time)
# TYPE resonance_lambda_res gauge
resonance_lambda_res ${calculus.lambdaRes ?? 0}

`;

      // Add GPD parameters if available
      if (calculus.gpd) {
        metrics += `# HELP resonance_gpd_xi GPD shape parameter (xi)
# TYPE resonance_gpd_xi gauge
resonance_gpd_xi ${calculus.gpd.xi}

# HELP resonance_gpd_sigma GPD scale parameter (sigma)
# TYPE resonance_gpd_sigma gauge
resonance_gpd_sigma ${calculus.gpd.sigma}

# HELP resonance_gpd_threshold GPD threshold (u)
# TYPE resonance_gpd_threshold gauge
resonance_gpd_threshold ${calculus.gpd.threshold}

`;
      }

      // Add tail quantiles if available
      if (calculus.tailQuantiles) {
        metrics += `# HELP resonance_tail_q99 Tail quantile Q99
# TYPE resonance_tail_q99 gauge
resonance_tail_q99 ${calculus.tailQuantiles.q99}

# HELP resonance_tail_q99_9 Tail quantile Q99.9
# TYPE resonance_tail_q99_9 gauge
resonance_tail_q99_9 ${calculus.tailQuantiles.q99_9}

`;
      }
    }
    
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end(metrics);
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

// Health check server
const healthPort = parseInt(process.env.RESONANCE_HEALTH_PORT || '8080');
const healthServer = http.createServer((req, res) => {
  if (req.url === '/health' || req.url === '/healthz') {
    const state = core.getState();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      resonance: {
        mode: state.mode,
        R: state.R.toFixed(3),
        K: state.K.toFixed(3),
        entropy: state.spectralEntropy.toFixed(3),
      },
      timestamp: new Date().toISOString(),
    }));
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

metricsServer.listen(metricsPort, () => {
  console.log(`Metrics server started on port ${metricsPort}`);
});

healthServer.listen(healthPort, () => {
  console.log(`Resonance Agent started`);
  console.log(`Mode: ${mode}`);
  console.log(`Health: http://localhost:${healthPort}/health`);
  console.log(`Metrics: http://localhost:${metricsPort}/metrics`);
});

// Update metrics periodically
setInterval(() => {
  // Update state to generate metrics
  const phases = [Math.random() * Math.PI * 2, Math.random() * Math.PI * 2, Math.random() * Math.PI * 2];
  core.update(phases, 0.5, 0.1);
}, 5000);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully');
  metricsServer.close();
  healthServer.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, shutting down gracefully');
  metricsServer.close();
  healthServer.close();
  process.exit(0);
});

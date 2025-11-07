/**
 * Resonance Agent - Secure Production Entry (Render-compatible)
 *
 * - Binds to Render's provided PORT
 * - Serves /health (public), /metrics (API key protected), /intake/phase (optional key)
 * - Exposes Resonance Calculus metrics when available
 * - Applies security headers, simple rate limiting, and optional CORS
 */

import * as fs from 'fs';
import * as path from 'path';
import * as http from 'http';
import { URL } from 'url';

import { ResonanceCore } from '../resonance-core';
import type { Mode } from '../resonance-core/types';
import {
  SecurityConfig,
  checkRateLimit,
  getClientIP,
  setSecurityHeaders,
  validateApiKey,
} from './security';

// -----------------------------------------------------------------------------
// Configuration
// -----------------------------------------------------------------------------

const configPath =
  process.env.RESONANCE_CONFIG_FILE ||
  path.join(__dirname, '../../policy/defaults.json');
const defaults = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

const baseSecurityConfig: SecurityConfig = {
  apiKey: process.env.RESONANCE_API_KEY,
  rateLimitWindowMs: parseInt(
    process.env.RESONANCE_RATE_LIMIT_WINDOW_MS || '60000',
    10,
  ),
  rateLimitMaxRequests: parseInt(
    process.env.RESONANCE_RATE_LIMIT_MAX || '100',
    10,
  ),
  allowedOrigins: (process.env.RESONANCE_ALLOWED_ORIGINS || '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean),
  enableCORS: process.env.RESONANCE_ENABLE_CORS === 'true',
};

const intakeSecurityConfig: SecurityConfig = {
  ...baseSecurityConfig,
  apiKey: process.env.RESONANCE_INTAKE_API_KEY || baseSecurityConfig.apiKey,
  rateLimitWindowMs: parseInt(
    process.env.RESONANCE_INTAKE_RATE_LIMIT_WINDOW_MS || '60000',
    10,
  ),
  rateLimitMaxRequests: parseInt(
    process.env.RESONANCE_INTAKE_RATE_LIMIT_MAX || '600',
    10,
  ),
};

const port = parseInt(
  process.env.PORT ||
    process.env.RESONANCE_HEALTH_PORT ||
    process.env.RESONANCE_PORT ||
    '8080',
  10,
);

// -----------------------------------------------------------------------------
// Core initialisation
// -----------------------------------------------------------------------------

const mode = (process.env.RESONANCE_MODE as Mode | undefined) || defaults.mode || 'shadow';

const core = new ResonanceCore({
  R_band: defaults.R_band || [0.35, 0.65],
  K_min: defaults.K_min || 0.05,
  K_max: defaults.K_max || 1.0,
  maxMicroDelayMs: defaults.maxMicroDelayMs || 7,
  defaultBatchLatencyMs: defaults.defaultBatchLatencyMs || 25,
});

core.setMode(mode);

let lastIntakeAt = 0;

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

type HttpHandler = (req: http.IncomingMessage, res: http.ServerResponse) => void;

function withSecurity(handler: HttpHandler, config: SecurityConfig): HttpHandler {
  return (req, res) => {
    setSecurityHeaders(res, config);

    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    if (!validateApiKey(req, config)) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Unauthorized: Invalid or missing API key' }));
      return;
    }

    const clientIP = getClientIP(req);
    if (!checkRateLimit(clientIP, config)) {
      res.writeHead(429, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Rate limit exceeded' }));
      return;
    }

    handler(req, res);
  };
}

function writeNotFound(res: http.ServerResponse) {
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
}

function getResonanceMetricsText(): string {
  const state = core.getState();
  const modeValue =
    state.mode === 'observe' ? 0 : state.mode === 'shadow' ? 1 : state.mode === 'adaptive' ? 2 : 3;
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

  return metrics;
}

// -----------------------------------------------------------------------------
// Route Handlers
// -----------------------------------------------------------------------------

const handleMetrics: HttpHandler = (_req, res) => {
  const metrics = getResonanceMetricsText();
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end(metrics);
};

const handlePhaseIntake: HttpHandler = (req, res) => {
  let body = '';

  req.on('data', (chunk) => {
    body += chunk;
    if (body.length > 1e6) {
      req.socket.destroy();
    }
  });

  req.on('end', () => {
    try {
      const payload = body ? JSON.parse(body) : {};
      const phases = Array.isArray(payload.phases) ? payload.phases : [];

      if (!phases.length) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            error: 'Payload must include a non-empty `phases` array (radians).',
          }),
        );
        return;
      }

      const state = core.getState();
      const spectralEntropy =
        typeof payload.spectralEntropy === 'number'
          ? payload.spectralEntropy
          : state.spectralEntropy;
      const p99Risk =
        typeof payload.p99Risk === 'number' ? payload.p99Risk : payload.tailRisk ?? 0.1;

      const features = core.update(phases, spectralEntropy, p99Risk);
      lastIntakeAt = Date.now();

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          message: 'Phase sample ingested',
          R: features.R,
          spectralEntropy: features.spectralEntropy,
          p99Risk: features.p99Risk,
        }),
      );
    } catch (error: any) {
      console.error('Failed to ingest phase sample:', error);
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: error?.message ?? 'Invalid payload' }));
    }
  });
};

const secureMetricsHandler = withSecurity(handleMetrics, baseSecurityConfig);
const secureIntakeHandler =
  intakeSecurityConfig.apiKey && intakeSecurityConfig.apiKey.length > 0
    ? withSecurity(handlePhaseIntake, intakeSecurityConfig)
    : handlePhaseIntake;

// -----------------------------------------------------------------------------
// HTTP Server
// -----------------------------------------------------------------------------

const server = http.createServer((req, res) => {
  try {
    const url = new URL(req.url ?? '/', `http://localhost:${port}`);

    // Always set baseline headers (will be overwritten if secure handler runs)
    setSecurityHeaders(res, baseSecurityConfig);

    // Handle CORS preflight globally when CORS is enabled
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    if (url.pathname === '/' || url.pathname === '') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          service: 'resonance-agent',
          status: 'running',
          mode,
          endpoints: {
            health: '/health',
            intake: '/intake/phase',
            metrics: '/metrics',
          },
          intakeProtected: Boolean(intakeSecurityConfig.apiKey),
        }),
      );
      return;
    }

    if (url.pathname === '/health' || url.pathname === '/healthz') {
      const state = core.getState();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          status: 'healthy',
          resonance: {
            mode: state.mode,
            R: state.R.toFixed(3),
            K: state.K.toFixed(3),
            entropy: state.spectralEntropy.toFixed(3),
          },
          lastIntakeAt: lastIntakeAt ? new Date(lastIntakeAt).toISOString() : null,
          timestamp: new Date().toISOString(),
        }),
      );
      return;
    }

    if (url.pathname === '/metrics') {
      secureMetricsHandler(req, res);
      return;
    }

    if (url.pathname === '/intake/phase' && req.method === 'POST') {
      secureIntakeHandler(req, res);
      return;
    }

    writeNotFound(res);
  } catch (error) {
    console.error('Unhandled error in agent server:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Internal server error' }));
  }
});

server.listen(port, '0.0.0.0', () => {
  console.log('Resonance Agent started');
  console.log(`Mode: ${mode}`);
  console.log(`Port: ${port}`);
  console.log(`Health: http://0.0.0.0:${port}/health`);
  console.log(`Phase intake: http://0.0.0.0:${port}/intake/phase`);
  console.log(`Metrics: http://0.0.0.0:${port}/metrics`);
  if (baseSecurityConfig.apiKey) {
    console.log('Security: API key authentication enabled for /metrics');
  } else {
    console.warn('Security: API key not set - /metrics is currently unprotected');
  }
  if (intakeSecurityConfig.apiKey) {
    console.log('Intake: API key required for /intake/phase');
  } else {
    console.warn('Intake: No API key configured - /intake/phase accepts unauthenticated traffic');
  }
});

// -----------------------------------------------------------------------------
// Background updates & shutdown handling
// -----------------------------------------------------------------------------

setInterval(() => {
  // Skip synthetic samples if we have seen real traffic recently (30s window)
  if (Date.now() - lastIntakeAt < 30000) {
    return;
  }

  const phases = [
    Math.random() * Math.PI * 2,
    Math.random() * Math.PI * 2,
    Math.random() * Math.PI * 2,
  ];

  core.update(phases, 0.5, 0.1);
}, 5000);

process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});



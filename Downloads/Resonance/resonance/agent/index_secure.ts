/**
 * Resonance Agent - Secure Production Version
 * Includes authentication, rate limiting, and security headers
 */

import * as fs from 'fs';
import * as path from 'path';
import * as http from 'http';
import { ResonanceCore } from '../resonance-core';
import {
  validateApiKey,
  checkRateLimit,
  getClientIP,
  setSecurityHeaders,
  type SecurityConfig,
} from './security';

// Load configuration
const configPath = process.env.RESONANCE_CONFIG_FILE || path.join(__dirname, '../../policy/defaults.json');
const defaults = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

// Security configuration
const securityConfig: SecurityConfig = {
  apiKey: process.env.RESONANCE_API_KEY, // Set via environment variable
  rateLimitWindowMs: parseInt(process.env.RESONANCE_RATE_LIMIT_WINDOW_MS || '60000'),
  rateLimitMaxRequests: parseInt(process.env.RESONANCE_RATE_LIMIT_MAX || '100'),
  allowedOrigins: (process.env.RESONANCE_ALLOWED_ORIGINS || '').split(',').filter(Boolean),
  enableCORS: process.env.RESONANCE_ENABLE_CORS === 'true',
};

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

/**
 * Security middleware wrapper
 */
function secureHandler(handler: (req: http.IncomingMessage, res: http.ServerResponse) => void) {
  return (req: http.IncomingMessage, res: http.ServerResponse) => {
    // Set security headers
    setSecurityHeaders(res, securityConfig);

    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    // Validate API key (if configured)
    if (!validateApiKey(req, securityConfig)) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Unauthorized: Invalid or missing API key' }));
      return;
    }

    // Rate limiting
    const ip = getClientIP(req);
    if (!checkRateLimit(ip, securityConfig)) {
      res.writeHead(429, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Rate limit exceeded' }));
      return;
    }

    // Call actual handler
    handler(req, res);
  };
}

// Metrics server (Prometheus format)
const metricsPort = parseInt(process.env.RESONANCE_METRICS_PORT || '9090');
const metricsServer = http.createServer(
  secureHandler((req, res) => {
    if (req.url === '/metrics') {
      const state = core.getState();
      const modeValue = state.mode === 'observe' ? 0 : state.mode === 'shadow' ? 1 : state.mode === 'adaptive' ? 2 : 3;
      
      const metrics = `# HELP resonance_R Kuramoto order parameter R(t) [0-1]
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
      
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end(metrics);
    } else {
      res.writeHead(404);
      res.end('Not found');
    }
  })
);

// Health check server (public, no auth required)
const healthPort = parseInt(process.env.RESONANCE_HEALTH_PORT || '8080');
const healthServer = http.createServer((req, res) => {
  // Set security headers even for health endpoint
  setSecurityHeaders(res, securityConfig);

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
  if (securityConfig.apiKey) {
    console.log(`Security: API key authentication enabled`);
  } else {
    console.warn(`Security: API key not set - metrics endpoint is unprotected`);
  }
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
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  metricsServer.close();
  healthServer.close();
  process.exit(0);
});


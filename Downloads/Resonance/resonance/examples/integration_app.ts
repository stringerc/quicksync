/**
 * Production Integration Example
 * Shows how to integrate Resonance into a real Express.js application
 */

import * as express from 'express';
import { ResonanceCore } from '../resonance-core';
import { ResonanceClient } from '../sdk/node';
import { ResonanceCalculus } from '../resonance-core/calculus';
import { TokenBucket } from '../sdk/node/client';
import { OtelExporter } from '../observability/otel_exporter';

const app = express();
app.use(express.json());

// Initialize Resonance
const core = new ResonanceCore({
  mode: process.env.RESONANCE_MODE || 'shadow',
  R_band: [0.35, 0.65],
  K_min: 0.05,
  K_max: 1.0,
  maxMicroDelayMs: 7,
  defaultBatchLatencyMs: 25,
});

const calculus = new ResonanceCalculus();
const tokenBucket = new TokenBucket({ refillRate: 10, capacity: 100 });

const client = new ResonanceClient(core, calculus, tokenBucket);

// Initialize observability
const otelExporter = new OtelExporter({
  port: 9090,
  enableConsole: process.env.NODE_ENV === 'development',
});

// Example 1: Search API with Resonance submit
app.get('/api/search', async (req, res) => {
  try {
    const query = req.query.q as string;

    const result = await client.submit(
      async () => {
        // Simulate database search
        await new Promise((resolve) => setTimeout(resolve, 50 + Math.random() * 50));
        return {
          query,
          results: Array.from({ length: 10 }, (_, i) => ({
            id: i + 1,
            title: `Result ${i + 1} for ${query}`,
          })),
        };
      },
      {
        id: `search-${query}`,
        importance: 'normal',
        canBatch: false,
        maxDeferralMs: 50,
      }
    );

    // Update metrics
    otelExporter.updateMetrics(client.getState());

    res.json(result);
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

// Example 2: Payment API with hedging
app.post('/api/payment', async (req, res) => {
  try {
    const { amount, card } = req.body;

    const { result, hedgeFired, hedgeDelay } = await client.hedge(
      async () => {
        // Simulate payment processing
        await new Promise((resolve) => setTimeout(resolve, 100 + Math.random() * 100));
        return {
          transactionId: `txn-${Date.now()}`,
          amount,
          status: 'completed',
        };
      },
      {
        id: 'payment',
        importance: 'critical',
        idempotent: true,
      },
      {
        delayMs: 20,
        idempotentOnly: true,
      }
    );

    // Log hedge events
    if (hedgeFired) {
      console.log(`Payment hedge fired after ${hedgeDelay}ms`);
    }

    otelExporter.updateMetrics(client.getState());

    res.json(result);
  } catch (error) {
    console.error('Payment error:', error);
    res.status(500).json({ error: 'Payment failed' });
  }
});

// Example 3: Batch API with retry
app.post('/api/batch', async (req, res) => {
  try {
    const { items } = req.body;

    const result = await client.retry(
      async () => {
        // Simulate unreliable batch processing
        if (Math.random() < 0.3) {
          throw new Error('Batch processing failed');
        }
        return {
          processed: items.length,
          status: 'success',
        };
      },
      {
        strategy: 'full_jitter',
        baseDelayMs: 20,
        maxDelayMs: 20000,
        maxAttempts: 5,
      }
    );

    otelExporter.updateMetrics(client.getState());

    res.json(result);
  } catch (error) {
    console.error('Batch error:', error);
    res.status(500).json({ error: 'Batch processing failed' });
  }
});

// Health check
app.get('/health', (req, res) => {
  const state = client.getState();
  res.json({
    status: 'healthy',
    resonance: {
      mode: state.mode,
      R: state.R,
      K: state.K,
    },
  });
});

// Metrics endpoint (for Prometheus)
app.get('/metrics', async (req, res) => {
  try {
    const metrics = await otelExporter.getMetrics();
    res.set('Content-Type', 'text/plain');
    res.send(metrics);
  } catch (error) {
    res.status(500).send('Failed to retrieve metrics');
  }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Resonance mode: ${core.getMode()}`);
  console.log(`Metrics: http://localhost:${PORT}/metrics`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully');
  await otelExporter.shutdown();
  process.exit(0);
});


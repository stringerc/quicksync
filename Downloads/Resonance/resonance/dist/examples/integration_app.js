"use strict";
/**
 * Production Integration Example
 * Shows how to integrate Resonance into a real Express.js application
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const express = __importStar(require("express"));
const resonance_core_1 = require("../resonance-core");
const node_1 = require("../sdk/node");
const calculus_1 = require("../resonance-core/calculus");
const client_1 = require("../sdk/node/client");
const otel_exporter_1 = require("../observability/otel_exporter");
const app = express();
app.use(express.json());
// Initialize Resonance
const core = new resonance_core_1.ResonanceCore({
    mode: process.env.RESONANCE_MODE || 'shadow',
    R_band: [0.35, 0.65],
    K_min: 0.05,
    K_max: 1.0,
    maxMicroDelayMs: 7,
    defaultBatchLatencyMs: 25,
});
const calculus = new calculus_1.ResonanceCalculus();
const tokenBucket = new client_1.TokenBucket({ refillRate: 10, capacity: 100 });
const client = new node_1.ResonanceClient(core, calculus, tokenBucket);
// Initialize observability
const otelExporter = new otel_exporter_1.OtelExporter({
    port: 9090,
    enableConsole: process.env.NODE_ENV === 'development',
});
// Example 1: Search API with Resonance submit
app.get('/api/search', async (req, res) => {
    try {
        const query = req.query.q;
        const result = await client.submit(async () => {
            // Simulate database search
            await new Promise((resolve) => setTimeout(resolve, 50 + Math.random() * 50));
            return {
                query,
                results: Array.from({ length: 10 }, (_, i) => ({
                    id: i + 1,
                    title: `Result ${i + 1} for ${query}`,
                })),
            };
        }, {
            id: `search-${query}`,
            importance: 'normal',
            canBatch: false,
            maxDeferralMs: 50,
        });
        // Update metrics
        otelExporter.updateMetrics(client.getState());
        res.json(result);
    }
    catch (error) {
        console.error('Search error:', error);
        res.status(500).json({ error: 'Search failed' });
    }
});
// Example 2: Payment API with hedging
app.post('/api/payment', async (req, res) => {
    try {
        const { amount, card } = req.body;
        const { result, hedgeFired, hedgeDelay } = await client.hedge(async () => {
            // Simulate payment processing
            await new Promise((resolve) => setTimeout(resolve, 100 + Math.random() * 100));
            return {
                transactionId: `txn-${Date.now()}`,
                amount,
                status: 'completed',
            };
        }, {
            id: 'payment',
            importance: 'critical',
            idempotent: true,
        }, {
            delayMs: 20,
            idempotentOnly: true,
        });
        // Log hedge events
        if (hedgeFired) {
            console.log(`Payment hedge fired after ${hedgeDelay}ms`);
        }
        otelExporter.updateMetrics(client.getState());
        res.json(result);
    }
    catch (error) {
        console.error('Payment error:', error);
        res.status(500).json({ error: 'Payment failed' });
    }
});
// Example 3: Batch API with retry
app.post('/api/batch', async (req, res) => {
    try {
        const { items } = req.body;
        const result = await client.retry(async () => {
            // Simulate unreliable batch processing
            if (Math.random() < 0.3) {
                throw new Error('Batch processing failed');
            }
            return {
                processed: items.length,
                status: 'success',
            };
        }, {
            strategy: 'full_jitter',
            baseDelayMs: 20,
            maxDelayMs: 20000,
            maxAttempts: 5,
        });
        otelExporter.updateMetrics(client.getState());
        res.json(result);
    }
    catch (error) {
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
    }
    catch (error) {
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
//# sourceMappingURL=integration_app.js.map
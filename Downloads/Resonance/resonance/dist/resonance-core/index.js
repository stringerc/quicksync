"use strict";
/**
 * Resonance Core
 * Main coordination engine combining all components
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
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ResonanceCore = void 0;
const kuramoto_1 = require("./kuramoto");
const controller_pi_1 = require("./controller_pi");
const adaptive_coupling_1 = require("./adaptive_coupling");
const actuators_1 = require("./actuators");
const resonance_bridge_1 = require("./resonance_bridge");
const histogram_1 = require("../observability/histogram");
class ResonanceCore {
    constructor(cfg) {
        this.state = {
            R: 0,
            spectralEntropy: 0.5,
            K: 0.3,
            mode: 'observe',
        };
        this.phases = [];
        this.lastUpdate = Date.now();
        // Resonance Calculus integration
        this.coherenceHistory = [];
        this.maxHistorySize = 100; // Keep last 100 coherence samples
        this.useResonanceCalculus = true; // Enable/disable calculus integration
        this.controller = new controller_pi_1.BandController(cfg);
        this.latencyHistogram = new histogram_1.LatencyHistogram();
        this.updateGlobalState();
    }
    /**
     * Update global state with current phases
     * Now uses Resonance Calculus to compute R when enabled
     */
    update(phases, spectralEntropy, p99Risk) {
        this.phases = phases;
        const { R: R_phase } = (0, kuramoto_1.orderParameter)(phases);
        const sigmaTheta = (0, kuramoto_1.phaseDispersion)(phases);
        // Record coherence sample for Resonance Calculus
        const now = Date.now() / 1000; // Convert to seconds
        this.coherenceHistory.push({ t: now, c: R_phase });
        // Keep history bounded
        if (this.coherenceHistory.length > this.maxHistorySize) {
            this.coherenceHistory.shift();
        }
        // Compute R using Resonance Calculus if enabled
        let R = R_phase;
        if (this.useResonanceCalculus && this.coherenceHistory.length >= 10) {
            try {
                const resonance = this.computeResonance();
                R = resonance.R;
                // Update state with calculus-derived R
                this.state.R = R;
                // Store additional metrics for telemetry
                if (typeof globalThis !== 'undefined') {
                    globalThis.__resonance_calculus = {
                        R,
                        coherenceScore: resonance.coherenceScore,
                        tailHealthScore: resonance.tailHealthScore,
                        timingScore: resonance.timingScore,
                        lambdaRes: resonance.lambdaRes,
                        gpd: resonance.gpd,
                        tailQuantiles: resonance.tailQuantiles,
                    };
                }
            }
            catch (e) {
                // Fallback to phase-based R if calculus fails
                console.warn('Resonance Calculus computation failed, using phase-based R:', e);
                R = R_phase;
            }
        }
        else {
            // Use phase-based R (fallback or when calculus disabled)
            this.state.R = R_phase;
        }
        this.state.spectralEntropy = spectralEntropy;
        this.state.K = (0, adaptive_coupling_1.adaptK)(this.state.K, sigmaTheta, p99Risk, { min: this.controller.getConfig().K_min, max: this.controller.getConfig().K_max });
        this.updateGlobalState();
        return { R, spectralEntropy, p99Risk, sigmaTheta };
    }
    /**
     * Compute resonance using Resonance Calculus
     */
    computeResonance() {
        // Get tail samples from histogram
        const tailSamples = this.getTailSamples();
        // Build dependency graph from phases (each phase = node)
        const graphSize = Math.max(this.phases.length, 1);
        const edges = this.buildDependencyGraph();
        // Normalize coherence history to recent time window (last 10 seconds)
        const now = Date.now() / 1000;
        const windowStart = now - 10;
        const recentCoherence = this.coherenceHistory
            .filter(s => s.t >= windowStart)
            .map(s => ({ ...s, t: s.t - windowStart })); // Normalize to [0, 10]
        // If no recent samples, use all history
        const coherenceSamples = recentCoherence.length > 0 ? recentCoherence : this.coherenceHistory;
        const inputs = {
            tHorizon: 5.0, // 5 second horizon
            rateLatency: {
                R: 100, // 100 req/s baseline rate
                T: 0.1 // 100ms baseline latency
            },
            coherenceSamples,
            tailSamples,
            tailThresholdQuantile: 0.95,
            graphSize,
            edges,
        };
        return (0, resonance_bridge_1.computeResonanceFromInputs)(inputs);
    }
    /**
     * Get tail samples from latency histogram
     */
    getTailSamples() {
        const samples = [];
        // Get percentiles from histogram
        const percentiles = this.latencyHistogram.getPercentiles();
        const count = this.latencyHistogram.getCount();
        if (count === 0) {
            // Return default samples if histogram is empty
            return Array.from({ length: 50 }, (_, i) => ({
                value: 100 + i * 10, // Synthetic values
                isExtreme: false,
            }));
        }
        // Generate samples from histogram buckets
        // This is a simplified approach - in production, use actual histogram data
        const p95 = percentiles.p95 * 1000; // Convert to microseconds
        const p99 = percentiles.p99 * 1000;
        const p99_9 = percentiles.p99_9 * 1000;
        // Create samples around key percentiles
        for (let i = 0; i < 20; i++) {
            samples.push({
                value: p95 + (i * 5),
                isExtreme: p95 + (i * 5) > p99,
            });
        }
        for (let i = 0; i < 20; i++) {
            samples.push({
                value: p99 + (i * 10),
                isExtreme: true,
            });
        }
        for (let i = 0; i < 10; i++) {
            samples.push({
                value: p99_9 + (i * 50),
                isExtreme: true,
            });
        }
        return samples;
    }
    /**
     * Build dependency graph from phases
     * Each phase represents a node, edges represent coherence-modulated delays
     */
    buildDependencyGraph() {
        const edges = [];
        const n = this.phases.length;
        if (n === 0)
            return edges;
        // Create a ring topology: each node connects to next
        for (let i = 0; i < n; i++) {
            const next = (i + 1) % n;
            // Delay weight based on phase difference and coherence
            const phaseDiff = Math.abs(this.phases[i] - this.phases[next]);
            const coherence = Math.abs(Math.cos(phaseDiff));
            // Higher coherence = lower delay (better synchronization)
            const baseDelay = 10; // Base delay in arbitrary units
            const w = baseDelay * (2 - coherence); // Invert coherence for delay
            edges.push({ u: i, v: next, w });
        }
        // Also add reverse edges for full connectivity
        for (let i = 0; i < n; i++) {
            const prev = (i - 1 + n) % n;
            const phaseDiff = Math.abs(this.phases[i] - this.phases[prev]);
            const coherence = Math.abs(Math.cos(phaseDiff));
            const baseDelay = 10;
            const w = baseDelay * (2 - coherence);
            edges.push({ u: i, v: prev, w });
        }
        return edges;
    }
    /**
     * Record latency for tail analysis
     */
    recordLatency(latencyMs) {
        this.latencyHistogram.recordValueMs(latencyMs);
    }
    /**
     * Decide and run task with resonance logic
     * Now uses Resonance Calculus-derived R for controller decisions
     */
    async decideAndRun(hint, run) {
        if (this.state.mode === 'observe') {
            return run(); // No intervention
        }
        // Critical tasks bypass controller
        if (hint.mustRunNow || hint.importance === 'critical') {
            return run();
        }
        // Use Resonance Calculus-derived R for controller decisions
        const features = {
            R: this.state.R, // This is now computed from Resonance Calculus when enabled
            spectralEntropy: this.state.spectralEntropy,
            p99Risk: 0.1,
            sigmaTheta: 1 - this.state.R,
        };
        const act = this.controller.decide(features);
        // Apply actuation if in active mode
        if (this.state.mode === 'active' || this.state.mode === 'adaptive') {
            return (0, actuators_1.applyActuation)(act, run);
        }
        // Shadow mode: decide but don't act
        return run();
    }
    /**
     * Get current state
     */
    getState() {
        return { ...this.state };
    }
    /**
     * Update mode
     */
    setMode(mode) {
        this.state.mode = mode;
        this.updateGlobalState();
    }
    /**
     * Update controller config
     */
    updateConfig(partial) {
        this.controller.updateConfig(partial);
    }
    /**
     * Reset core state
     */
    reset() {
        this.controller.reset();
        this.phases = [];
        this.lastUpdate = Date.now();
        this.coherenceHistory = [];
        this.latencyHistogram.reset();
    }
    /**
     * Enable/disable Resonance Calculus
     */
    setUseResonanceCalculus(enable) {
        this.useResonanceCalculus = enable;
    }
    /**
     * Get latency histogram for external access
     */
    getLatencyHistogram() {
        return this.latencyHistogram;
    }
    /**
     * Update global state for telemetry
     */
    updateGlobalState() {
        // Store in global for metrics collectors
        if (typeof globalThis !== 'undefined') {
            globalThis.__resonance_state = this.state;
        }
    }
}
exports.ResonanceCore = ResonanceCore;
// Export all components
__exportStar(require("./types"), exports);
__exportStar(require("./phase_estimator"), exports);
__exportStar(require("./kuramoto"), exports);
__exportStar(require("./pll"), exports);
__exportStar(require("./controller_pi"), exports);
__exportStar(require("./adaptive_coupling"), exports);
__exportStar(require("./actuators"), exports);
__exportStar(require("./calculus"), exports);
__exportStar(require("./resonance_bridge"), exports);
//# sourceMappingURL=index.js.map
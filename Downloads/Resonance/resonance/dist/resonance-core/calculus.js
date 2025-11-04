"use strict";
/**
 * Resonance Calculus (RC)
 * Max-Plus/Min-Plus forecaster for backlog and delay bounds
 * See: Le Boudec/Van Bemten "Applied Queueing Theory"
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ResonanceCalculus = void 0;
exports.maxPlusConvolve = maxPlusConvolve;
exports.minPlusDeconvolve = minPlusDeconvolve;
exports.backlogBound = backlogBound;
exports.delayBound = delayBound;
/**
 * Max-Plus convolution operator (⊗)
 * α ⊗ β(t) = max{α(s) + β(t-s) : s ∈ [0,t]}
 */
function maxPlusConvolve(alpha, beta) {
    const result = [];
    for (let t = 0; t < Math.max(alpha.length, beta.length); t++) {
        let max = -Infinity;
        for (let s = 0; s <= t; s++) {
            const alphaVal = alpha[s] || 0;
            const betaVal = beta[t - s] || 0;
            max = Math.max(max, alphaVal + betaVal);
        }
        result.push(max);
    }
    return result;
}
/**
 * Min-Plus deconvolution operator (⊖)
 * (α ⊖ β)(t) = min{α(s) - β(s-t) : s ≥ t}
 */
function minPlusDeconvolve(alpha, beta) {
    const result = [];
    const maxLen = Math.max(alpha.length, beta.length);
    for (let t = 0; t < maxLen; t++) {
        let min = Infinity;
        for (let s = t; s < maxLen; s++) {
            const alphaVal = alpha[s] || 0;
            const betaVal = beta[s - t] || 0;
            min = Math.min(min, alphaVal - betaVal);
        }
        result.push(min);
    }
    return result;
}
/**
 * Compute backlog bound from arrival and service curves
 */
function backlogBound(arrivalWindow, serviceWindow) {
    let max = -Infinity;
    for (let t = 0; t < arrivalWindow.length; t++) {
        const arrival = arrivalWindow[t] || 0;
        const service = serviceWindow[t] || 0;
        const diff = arrival - service;
        max = Math.max(max, diff);
    }
    return Math.max(0, max);
}
/**
 * Estimate delay bound from curves
 */
function delayBound(arrivalWindow, serviceWindow, timeWindowMs) {
    const backlog = backlogBound(arrivalWindow, serviceWindow);
    if (serviceWindow.length === 0 || serviceWindow.reduce((a, b) => a + b, 0) === 0) {
        return 0;
    }
    const avgServiceRate = serviceWindow.reduce((a, b) => a + b, 0) / (serviceWindow.length || 1);
    const estimatedDelay = (backlog / avgServiceRate) * timeWindowMs;
    return Math.max(0, estimatedDelay);
}
/**
 * Resonance Calculus Decision Engine
 */
class ResonanceCalculus {
    constructor() {
        this.arrivals = [];
        this.completions = [];
        this.windowSize = 1000; // 1 second window
        this.maxSamples = 1000;
    }
    /**
     * Record arrival
     */
    recordArrival() {
        this.arrivals.push(Date.now());
        this.trim();
    }
    /**
     * Record completion
     */
    recordCompletion() {
        this.completions.push(Date.now());
        this.trim();
    }
    /**
     * Get sliding window counts
     */
    slidingWindow(windowMs, timestamps) {
        const now = Date.now();
        const cutoff = now - windowMs;
        const inWindow = timestamps.filter((ts) => ts >= cutoff);
        // Bin into time windows
        const bins = [];
        const numBins = 10;
        const binSize = windowMs / numBins;
        for (let i = 0; i < numBins; i++) {
            const binStart = cutoff + i * binSize;
            const binEnd = cutoff + (i + 1) * binSize;
            const count = inWindow.filter((ts) => ts >= binStart && ts < binEnd).length;
            bins.push(count);
        }
        return bins;
    }
    /**
     * Make decision based on backlog bounds
     */
    decide(deferBudgetMs, hedgeThresholdMs = 100) {
        const arrivalWindow = this.slidingWindow(this.windowSize, this.arrivals);
        const serviceWindow = this.slidingWindow(this.windowSize, this.completions);
        const backlog = backlogBound(arrivalWindow, serviceWindow);
        const delayMs = delayBound(arrivalWindow, serviceWindow, this.windowSize);
        if (delayMs > hedgeThresholdMs) {
            return {
                action: 'hedge',
                reason: `High backlog bound ${delayMs.toFixed(1)}ms > ${hedgeThresholdMs}ms`,
                boundMs: delayMs,
                backlog,
            };
        }
        if (delayMs > deferBudgetMs / 2) {
            return {
                action: 'defer',
                reason: `Backlog ${delayMs.toFixed(1)}ms allows safe deferral within ${deferBudgetMs}ms`,
                boundMs: delayMs,
                backlog,
            };
        }
        return {
            action: 'execute',
            reason: 'Normal backlog',
            boundMs: delayMs,
            backlog,
        };
    }
    /**
     * Get current curves for analysis
     */
    getCurves() {
        return {
            arrival: this.slidingWindow(this.windowSize, this.arrivals),
            service: this.slidingWindow(this.windowSize, this.completions),
        };
    }
    /**
     * Trim old samples
     */
    trim() {
        if (this.arrivals.length > this.maxSamples) {
            this.arrivals = this.arrivals.slice(-this.maxSamples);
        }
        if (this.completions.length > this.maxSamples) {
            this.completions = this.completions.slice(-this.maxSamples);
        }
    }
    /**
     * Reset state
     */
    reset() {
        this.arrivals = [];
        this.completions = [];
    }
}
exports.ResonanceCalculus = ResonanceCalculus;
//# sourceMappingURL=calculus.js.map
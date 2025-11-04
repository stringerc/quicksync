"use strict";
/**
 * Phase-Locked Loop (PLL)
 * Tracks soft global tempo while allowing drift correction
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.PLL = void 0;
class PLL {
    constructor(bandwidth = 0.05) {
        this.bandwidth = bandwidth;
        this.phase = 0; // tracked phase
        this.lastUpdate = Date.now();
    }
    /**
     * Update PLL with new measurement
     * @param inputFreq Global tempo (Hz or radians/s)
     * @param phaseMeasure Measured phase
     * @returns Current phase estimate
     */
    tick(inputFreq, phaseMeasure) {
        const now = Date.now();
        const dt = (now - this.lastUpdate) / 1000; // seconds
        this.lastUpdate = now;
        // Simple first-order loop: error between measured and internal phase
        const phaseError = normalizeAngle(phaseMeasure - this.phase);
        // Update: phase follows input with bandwidth correction
        this.phase = normalizeAngle(this.phase + inputFreq * dt + this.bandwidth * phaseError);
        return this.phase;
    }
    /**
     * Get current phase
     */
    getPhase() {
        return this.phase;
    }
    /**
     * Set bandwidth (higher = tighter lock)
     */
    setBandwidth(bandwidth) {
        this.bandwidth = bandwidth;
    }
    /**
     * Reset PLL state
     */
    reset() {
        this.phase = 0;
        this.lastUpdate = Date.now();
    }
}
exports.PLL = PLL;
/**
 * Normalize angle to [-π, π]
 */
function normalizeAngle(a) {
    while (a > Math.PI)
        a -= 2 * Math.PI;
    while (a < -Math.PI)
        a += 2 * Math.PI;
    return a;
}
//# sourceMappingURL=pll.js.map
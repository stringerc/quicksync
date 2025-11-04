"use strict";
/**
 * Adaptive Coupling
 * Dynamically adjusts coupling strength K(t) based on load and risk
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.SmoothCoupling = void 0;
exports.adaptK = adaptK;
exports.estimateP99Risk = estimateP99Risk;
/**
 * Adapt coupling strength K(t) based on phase dispersion and tail latency risk
 *
 * @param K0 Current coupling value
 * @param sigmaTheta Phase dispersion (1-R)
 * @param p99Risk Estimated p99 tail latency risk [0,1]
 * @param bounds Min/max bounds for K
 * @returns New coupling value
 */
function adaptK(K0, sigmaTheta, p99Risk, bounds) {
    // Heuristics: tune in bench
    const a = 0.5; // Dispersion weight
    const b = 0.7; // Risk weight
    // Increase K when dispersion rises (need more coordination)
    // Decrease K when p99 risk increases (need less interference)
    let K = K0 + a * sigmaTheta - b * p99Risk;
    return Math.max(bounds.min, Math.min(bounds.max, K));
}
/**
 * Compute p99 risk estimate from recent latency samples
 */
function estimateP99Risk(recentLatencies, targetP99) {
    if (recentLatencies.length === 0)
        return 0.1;
    // Simple heuristic: compare recent max to target
    const recentMax = Math.max(...recentLatencies);
    const risk = Math.min(1, recentMax / targetP99);
    return risk;
}
/**
 * Smooth coupling changes to avoid oscillations
 */
class SmoothCoupling {
    constructor(initialK) {
        this.smoothing = 0.3; // How fast to converge
        this.targetK = initialK;
        this.currentK = initialK;
    }
    update(newK) {
        this.targetK = newK;
        // Exponential smoothing
        this.currentK = this.currentK * (1 - this.smoothing) + this.targetK * this.smoothing;
        return this.currentK;
    }
    get() {
        return this.currentK;
    }
    setSmoothing(alpha) {
        this.smoothing = Math.max(0, Math.min(1, alpha));
    }
}
exports.SmoothCoupling = SmoothCoupling;
//# sourceMappingURL=adaptive_coupling.js.map
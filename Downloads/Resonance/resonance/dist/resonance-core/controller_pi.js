"use strict";
/**
 * PI Controller
 * Band control on R(t) with anti-herd and anti-freeze guardrails
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.BandController = void 0;
class BandController {
    constructor(cfg, kp = 0.6, ki = 0.2) {
        this.cfg = cfg;
        this.kp = kp;
        this.ki = ki;
        this.integ = 0;
    }
    decide(feat) {
        const [Rlow, Rhigh] = this.cfg.R_band;
        const target = (Rlow + Rhigh) / 2;
        const e = target - feat.R;
        this.integ = clamp(this.integ + e, -1, 1);
        const u = this.kp * e + this.ki * this.integ;
        const actions = {};
        // High coherence regime: potential herding risk
        if (feat.R > Rhigh) {
            actions.microDelayMs = Math.min(this.cfg.maxMicroDelayMs, Math.round(Math.random() * this.cfg.maxMicroDelayMs));
            actions.adjustK = -Math.abs(u); // reduce coupling
            actions.dither = Math.random(); // inject randomness
        }
        // Low coherence regime: try to re-entrain
        else if (feat.R < Rlow) {
            actions.adjustK = Math.abs(u); // increase coupling
            // Optionally encourage batching if spectral entropy suggests noise
            if (feat.spectralEntropy > 0.7) {
                actions.batchSize = 2; // simple heuristic; tune per workload
            }
        }
        else {
            // Within band: small dither only if desired
            actions.dither = 0;
        }
        return actions;
    }
    /**
     * Get configuration
     */
    getConfig() {
        return this.cfg;
    }
    /**
     * Update configuration
     */
    updateConfig(partial) {
        this.cfg = { ...this.cfg, ...partial };
    }
    /**
     * Reset controller state
     */
    reset() {
        this.integ = 0;
    }
}
exports.BandController = BandController;
function clamp(x, lo, hi) {
    return x < lo ? lo : x > hi ? hi : x;
}
//# sourceMappingURL=controller_pi.js.map
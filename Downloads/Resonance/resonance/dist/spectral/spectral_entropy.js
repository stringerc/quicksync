"use strict";
/**
 * Spectral Entropy
 * Normalized entropy measure of spectral distribution
 * Measures rigidity vs. noise in timing patterns
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.spectralEntropy = spectralEntropy;
exports.isEntropyInBand = isEntropyInBand;
exports.getEntropyState = getEntropyState;
/**
 * Compute spectral entropy from magnitude spectrum
 *
 * Interpretation:
 * - Low entropy (<0.2): Rigid, over-locked, harmonic patterns
 * - High entropy (>0.8): Noisy, uncoordinated, broad spectrum
 * - Target: [0.2, 0.8] for healthy balance
 *
 * @param mag Magnitude spectrum
 * @returns Normalized entropy [0,1]
 */
function spectralEntropy(mag) {
    const sum = mag.reduce((a, b) => a + b, 0) || 1;
    // Normalize to probability distribution
    const p = mag.map((m) => (m > 0 ? m : 1e-12) / sum);
    // Compute Shannon entropy
    let H = 0;
    for (const pi of p) {
        if (pi > 0) {
            H -= pi * Math.log(pi);
        }
    }
    // Normalize by maximum entropy (uniform distribution)
    const Hmax = Math.log(p.length);
    return H / Hmax;
}
/**
 * Check if entropy is within target band
 */
function isEntropyInBand(entropy, band = [0.2, 0.8]) {
    return entropy >= band[0] && entropy <= band[1];
}
/**
 * Get entropy state category
 */
function getEntropyState(entropy) {
    if (entropy < 0.2)
        return 'too_rigid';
    if (entropy > 0.8)
        return 'too_noisy';
    return 'healthy';
}
//# sourceMappingURL=spectral_entropy.js.map
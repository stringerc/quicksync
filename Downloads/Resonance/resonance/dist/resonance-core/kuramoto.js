"use strict";
/**
 * Kuramoto Order Parameter
 * Computes global coherence R(t) and phase dispersion
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.orderParameter = orderParameter;
exports.phaseDispersion = phaseDispersion;
exports.circularStdDev = circularStdDev;
/**
 * Compute Kuramoto order parameter R(t)
 * Measures global coherence of oscillators
 */
function orderParameter(phases) {
    const N = phases.length || 1;
    let sumRe = 0;
    let sumIm = 0;
    for (const th of phases) {
        sumRe += Math.cos(th);
        sumIm += Math.sin(th);
    }
    const Re = sumRe / N;
    const Im = sumIm / N;
    const R = Math.min(1, Math.max(0, Math.hypot(Re, Im)));
    const psi = Math.atan2(Im, Re);
    return { R, psi };
}
/**
 * Compute phase dispersion (inverse of coherence)
 * Higher dispersion = less coherent
 */
function phaseDispersion(phases) {
    const { R } = orderParameter(phases);
    return 1 - R; // Simple dispersion proxy
}
/**
 * Compute circular standard deviation of phases
 * Alternative dispersion measure
 */
function circularStdDev(phases) {
    const { R } = orderParameter(phases);
    return Math.sqrt(-2 * Math.log(R));
}
//# sourceMappingURL=kuramoto.js.map
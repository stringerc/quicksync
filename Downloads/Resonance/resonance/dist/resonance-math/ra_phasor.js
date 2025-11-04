"use strict";
/**
 * RA-Phasor: Complex Phasor Algebra
 * Coherent superposition for phase planning
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.add = add;
exports.subtract = subtract;
exports.scalarMult = scalarMult;
exports.conjugate = conjugate;
exports.magnitude = magnitude;
exports.phase = phase;
exports.isAligned = isAligned;
exports.zero = zero;
/**
 * Add two phasors (vector addition in complex plane)
 * Result: coherent superposition
 */
function add(z1, z2) {
    const x1 = z1.a * Math.cos(z1.phi);
    const y1 = z1.a * Math.sin(z1.phi);
    const x2 = z2.a * Math.cos(z2.phi);
    const y2 = z2.a * Math.sin(z2.phi);
    const X = x1 + x2;
    const Y = y1 + y2;
    const a = Math.hypot(X, Y);
    const phi = Math.atan2(Y, X);
    return { a, phi };
}
/**
 * Subtract two phasors
 */
function subtract(z1, z2) {
    const z2Neg = { a: z2.a, phi: z2.phi + Math.PI };
    return add(z1, z2Neg);
}
/**
 * Multiply phasor by scalar
 */
function scalarMult(z, c) {
    return { a: z.a * c, phi: z.phi };
}
/**
 * Conjugate phasor
 */
function conjugate(z) {
    return { a: z.a, phi: -z.phi };
}
/**
 * Magnitude of phasor
 */
function magnitude(z) {
    return z.a;
}
/**
 * Phase of phasor
 */
function phase(z) {
    return z.phi;
}
/**
 * Check if phases are aligned (within threshold)
 */
function isAligned(z1, z2, threshold = 0.1) {
    const phaseDiff = normalizeAngle(z1.phi - z2.phi);
    return Math.abs(phaseDiff) < threshold;
}
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
/**
 * Zero phasor
 */
function zero() {
    return { a: 0, phi: 0 };
}
//# sourceMappingURL=ra_phasor.js.map
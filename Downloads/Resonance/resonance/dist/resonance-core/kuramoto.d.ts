/**
 * Kuramoto Order Parameter
 * Computes global coherence R(t) and phase dispersion
 */
export interface KuramotoResult {
    R: number;
    psi: number;
}
/**
 * Compute Kuramoto order parameter R(t)
 * Measures global coherence of oscillators
 */
export declare function orderParameter(phases: number[]): KuramotoResult;
/**
 * Compute phase dispersion (inverse of coherence)
 * Higher dispersion = less coherent
 */
export declare function phaseDispersion(phases: number[]): number;
/**
 * Compute circular standard deviation of phases
 * Alternative dispersion measure
 */
export declare function circularStdDev(phases: number[]): number;
//# sourceMappingURL=kuramoto.d.ts.map
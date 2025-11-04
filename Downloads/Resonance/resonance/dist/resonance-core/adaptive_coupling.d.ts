/**
 * Adaptive Coupling
 * Dynamically adjusts coupling strength K(t) based on load and risk
 */
export interface CouplingBounds {
    min: number;
    max: number;
}
/**
 * Adapt coupling strength K(t) based on phase dispersion and tail latency risk
 *
 * @param K0 Current coupling value
 * @param sigmaTheta Phase dispersion (1-R)
 * @param p99Risk Estimated p99 tail latency risk [0,1]
 * @param bounds Min/max bounds for K
 * @returns New coupling value
 */
export declare function adaptK(K0: number, sigmaTheta: number, p99Risk: number, bounds: CouplingBounds): number;
/**
 * Compute p99 risk estimate from recent latency samples
 */
export declare function estimateP99Risk(recentLatencies: number[], targetP99: number): number;
/**
 * Smooth coupling changes to avoid oscillations
 */
export declare class SmoothCoupling {
    private targetK;
    private currentK;
    private smoothing;
    constructor(initialK: number);
    update(newK: number): number;
    get(): number;
    setSmoothing(alpha: number): void;
}
//# sourceMappingURL=adaptive_coupling.d.ts.map
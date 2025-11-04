/**
 * Resonance Calculus (RC)
 * Max-Plus/Min-Plus forecaster for backlog and delay bounds
 * See: Le Boudec/Van Bemten "Applied Queueing Theory"
 */
export interface ArrivalServiceCurves {
    arrival: number[];
    service: number[];
}
export interface CalculusDecision {
    action: 'hedge' | 'defer' | 'execute';
    reason: string;
    boundMs: number;
    backlog: number;
}
/**
 * Max-Plus convolution operator (⊗)
 * α ⊗ β(t) = max{α(s) + β(t-s) : s ∈ [0,t]}
 */
export declare function maxPlusConvolve(alpha: number[], beta: number[]): number[];
/**
 * Min-Plus deconvolution operator (⊖)
 * (α ⊖ β)(t) = min{α(s) - β(s-t) : s ≥ t}
 */
export declare function minPlusDeconvolve(alpha: number[], beta: number[]): number[];
/**
 * Compute backlog bound from arrival and service curves
 */
export declare function backlogBound(arrivalWindow: number[], serviceWindow: number[]): number;
/**
 * Estimate delay bound from curves
 */
export declare function delayBound(arrivalWindow: number[], serviceWindow: number[], timeWindowMs: number): number;
/**
 * Resonance Calculus Decision Engine
 */
export declare class ResonanceCalculus {
    private arrivals;
    private completions;
    private windowSize;
    private maxSamples;
    /**
     * Record arrival
     */
    recordArrival(): void;
    /**
     * Record completion
     */
    recordCompletion(): void;
    /**
     * Get sliding window counts
     */
    private slidingWindow;
    /**
     * Make decision based on backlog bounds
     */
    decide(deferBudgetMs: number, hedgeThresholdMs?: number): CalculusDecision;
    /**
     * Get current curves for analysis
     */
    getCurves(): ArrivalServiceCurves;
    /**
     * Trim old samples
     */
    private trim;
    /**
     * Reset state
     */
    reset(): void;
}
//# sourceMappingURL=calculus.d.ts.map
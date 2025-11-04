/**
 * Phase Estimator
 * Derives phase angle from event timestamps using modulo against detected base period
 */
export declare class PhaseEstimator {
    private windowMs;
    constructor(windowMs?: number);
    /**
     * Estimate phase from timestamp series and base period
     * @param tsSeries Array of timestamps (ms)
     * @param basePeriodMs Detected base period (ms)
     * @returns Phase angle in radians [0, 2π)
     */
    estimatePhase(tsSeries: number[], basePeriodMs: number): number;
    /**
     * Detect base period from timestamp series using autocorrelation
     * @param tsSeries Array of timestamps
     * @returns Detected period in ms, or 0 if none detected
     */
    detectPeriod(tsSeries: number[]): number;
}
//# sourceMappingURL=phase_estimator.d.ts.map
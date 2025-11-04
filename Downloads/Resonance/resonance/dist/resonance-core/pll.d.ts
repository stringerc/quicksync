/**
 * Phase-Locked Loop (PLL)
 * Tracks soft global tempo while allowing drift correction
 */
export declare class PLL {
    private bandwidth;
    private phase;
    private lastUpdate;
    constructor(bandwidth?: number);
    /**
     * Update PLL with new measurement
     * @param inputFreq Global tempo (Hz or radians/s)
     * @param phaseMeasure Measured phase
     * @returns Current phase estimate
     */
    tick(inputFreq: number, phaseMeasure: number): number;
    /**
     * Get current phase
     */
    getPhase(): number;
    /**
     * Set bandwidth (higher = tighter lock)
     */
    setBandwidth(bandwidth: number): void;
    /**
     * Reset PLL state
     */
    reset(): void;
}
//# sourceMappingURL=pll.d.ts.map
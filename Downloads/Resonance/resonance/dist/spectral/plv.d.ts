/**
 * Pairwise Phase-Locking Value (PLV)
 * Measures synchronization between two oscillators
 */
/**
 * Compute PLV between two phase series
 *
 * PLV = |mean(e^(j(θᵢ-θⱼ)))| over sliding windows
 *
 * Interpretation:
 * - PLV ≈ 1: Strongly synchronized
 * - PLV ≈ 0: Independent, uncorrelated
 *
 * @param phasesI Phase series for oscillator i
 * @param phasesJ Phase series for oscillator j
 * @returns PLV [0,1]
 */
export declare function plv(phasesI: number[], phasesJ: number[]): number;
/**
 * Compute PLV matrix for multiple oscillators
 * Returns sparse top-N edges for efficiency
 *
 * @param phases Phase series for each oscillator [series][time]
 * @param topN Number of top edges to return
 * @returns Array of [i, j, PLV] tuples
 */
export declare function plvMatrix(phases: number[][], topN?: number): Array<[number, number, number]>;
/**
 * Community detection based on PLV threshold
 * Groups oscillators with high mutual PLV
 */
export declare function detectCommunities(phases: number[][], threshold?: number): number[][];
//# sourceMappingURL=plv.d.ts.map
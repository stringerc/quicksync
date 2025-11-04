/**
 * Spectral Entropy
 * Normalized entropy measure of spectral distribution
 * Measures rigidity vs. noise in timing patterns
 */
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
export declare function spectralEntropy(mag: number[]): number;
/**
 * Check if entropy is within target band
 */
export declare function isEntropyInBand(entropy: number, band?: [number, number]): boolean;
/**
 * Get entropy state category
 */
export declare function getEntropyState(entropy: number): 'too_rigid' | 'too_noisy' | 'healthy';
//# sourceMappingURL=spectral_entropy.d.ts.map
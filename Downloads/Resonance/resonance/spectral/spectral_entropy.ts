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
export function spectralEntropy(mag: number[]): number {
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
export function isEntropyInBand(entropy: number, band: [number, number] = [0.2, 0.8]): boolean {
  return entropy >= band[0] && entropy <= band[1];
}

/**
 * Get entropy state category
 */
export function getEntropyState(entropy: number): 'too_rigid' | 'too_noisy' | 'healthy' {
  if (entropy < 0.2) return 'too_rigid';
  if (entropy > 0.8) return 'too_noisy';
  return 'healthy';
}


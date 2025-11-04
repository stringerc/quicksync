/**
 * Phase Estimator
 * Derives phase angle from event timestamps using modulo against detected base period
 */

export class PhaseEstimator {
  constructor(private windowMs = 10000) {}

  /**
   * Estimate phase from timestamp series and base period
   * @param tsSeries Array of timestamps (ms)
   * @param basePeriodMs Detected base period (ms)
   * @returns Phase angle in radians [0, 2π)
   */
  estimatePhase(tsSeries: number[], basePeriodMs: number): number {
    if (!basePeriodMs || basePeriodMs <= 0) {
      // No valid period, return random phase
      return 2 * Math.PI * Math.random();
    }
    
    const latest = tsSeries[tsSeries.length - 1] ?? Date.now();
    const phi = ((latest % basePeriodMs) / basePeriodMs) * 2 * Math.PI;
    return phi;
  }

  /**
   * Detect base period from timestamp series using autocorrelation
   * @param tsSeries Array of timestamps
   * @returns Detected period in ms, or 0 if none detected
   */
  detectPeriod(tsSeries: number[]): number {
    if (tsSeries.length < 10) return 0;

    const intervals: number[] = [];
    for (let i = 1; i < tsSeries.length; i++) {
      intervals.push(tsSeries[i] - tsSeries[i - 1]);
    }

    // Simple peak detection in histogram
    const histogram = new Map<number, number>();
    const binSize = 100; // 100ms bins

    for (const interval of intervals) {
      const bin = Math.round(interval / binSize) * binSize;
      histogram.set(bin, (histogram.get(bin) || 0) + 1);
    }

    // Find most common interval
    let maxCount = 0;
    let period = 0;
    for (const [bin, count] of histogram.entries()) {
      if (count > maxCount && bin > 0) {
        maxCount = count;
        period = bin;
      }
    }

    return period;
  }
}


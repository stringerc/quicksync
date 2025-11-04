/**
 * Phase-Locked Loop (PLL)
 * Tracks soft global tempo while allowing drift correction
 */

export class PLL {
  private phase = 0; // tracked phase
  private lastUpdate = Date.now();

  constructor(private bandwidth = 0.05) {}

  /**
   * Update PLL with new measurement
   * @param inputFreq Global tempo (Hz or radians/s)
   * @param phaseMeasure Measured phase
   * @returns Current phase estimate
   */
  tick(inputFreq: number, phaseMeasure: number): number {
    const now = Date.now();
    const dt = (now - this.lastUpdate) / 1000; // seconds
    this.lastUpdate = now;

    // Simple first-order loop: error between measured and internal phase
    const phaseError = normalizeAngle(phaseMeasure - this.phase);

    // Update: phase follows input with bandwidth correction
    this.phase = normalizeAngle(
      this.phase + inputFreq * dt + this.bandwidth * phaseError
    );

    return this.phase;
  }

  /**
   * Get current phase
   */
  getPhase(): number {
    return this.phase;
  }

  /**
   * Set bandwidth (higher = tighter lock)
   */
  setBandwidth(bandwidth: number): void {
    this.bandwidth = bandwidth;
  }

  /**
   * Reset PLL state
   */
  reset(): void {
    this.phase = 0;
    this.lastUpdate = Date.now();
  }
}

/**
 * Normalize angle to [-π, π]
 */
function normalizeAngle(a: number): number {
  while (a > Math.PI) a -= 2 * Math.PI;
  while (a < -Math.PI) a += 2 * Math.PI;
  return a;
}


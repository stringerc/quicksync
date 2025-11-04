/**
 * PI Controller
 * Band control on R(t) with anti-herd and anti-freeze guardrails
 */

import { ControllerConfig, Features, Actuators } from './types';

export class BandController {
  private integ = 0;

  constructor(
    private cfg: ControllerConfig,
    private kp = 0.6,
    private ki = 0.2
  ) {}

  decide(feat: Features): Actuators {
    const [Rlow, Rhigh] = this.cfg.R_band;
    const target = (Rlow + Rhigh) / 2;
    const e = target - feat.R;

    this.integ = clamp(this.integ + e, -1, 1);
    const u = this.kp * e + this.ki * this.integ;

    const actions: Actuators = {};

    // High coherence regime: potential herding risk
    if (feat.R > Rhigh) {
      actions.microDelayMs = Math.min(
        this.cfg.maxMicroDelayMs,
        Math.round(Math.random() * this.cfg.maxMicroDelayMs)
      );
      actions.adjustK = -Math.abs(u); // reduce coupling
      actions.dither = Math.random(); // inject randomness
    }
    // Low coherence regime: try to re-entrain
    else if (feat.R < Rlow) {
      actions.adjustK = Math.abs(u); // increase coupling
      // Optionally encourage batching if spectral entropy suggests noise
      if (feat.spectralEntropy > 0.7) {
        actions.batchSize = 2; // simple heuristic; tune per workload
      }
    } else {
      // Within band: small dither only if desired
      actions.dither = 0;
    }

    return actions;
  }

  /**
   * Get configuration
   */
  getConfig(): ControllerConfig {
    return this.cfg;
  }

  /**
   * Update configuration
   */
  updateConfig(partial: Partial<ControllerConfig>): void {
    this.cfg = { ...this.cfg, ...partial };
  }

  /**
   * Reset controller state
   */
  reset(): void {
    this.integ = 0;
  }
}

function clamp(x: number, lo: number, hi: number): number {
  return x < lo ? lo : x > hi ? hi : x;
}


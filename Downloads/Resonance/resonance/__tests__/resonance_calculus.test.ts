// resonance-math/__tests__/resonance_calculus.test.ts

import {
  betaRateLatency,
  betaCoherenceWeighted,
  fitGPD_PWM,
  tailQuantileFromGPD,
  buildWeightMatrix,
  maxCycleMeanKarp,
  aggregateResonance
} from '../resonance-math/resonance_calculus';

describe('Resonance Calculus primitives', () => {
  test('betaRateLatency behaves as expected', () => {
    const p = { R: 10, T: 1 };
    expect(betaRateLatency(0.5, p)).toBe(0);
    expect(betaRateLatency(1, p)).toBe(0);
    expect(betaRateLatency(2, p)).toBeCloseTo(10);
  });

  test('betaCoherenceWeighted reduces effective service under low coherence', () => {
    const p = { R: 100, T: 0.5 };
    const cLow = [
      { t: 0, c: 0.1 },
      { t: 1, c: 0.2 }
    ];
    const cHigh = [
      { t: 0, c: 0.8 },
      { t: 1, c: 0.9 }
    ];
    const t = 2;
    const base = betaRateLatency(t, p);
    const bLow = betaCoherenceWeighted(t, p, cLow, 0.8, 0.5);
    const bHigh = betaCoherenceWeighted(t, p, cHigh, 0.8, 0.5);

    // Low coherence should yield lower (or equal) effective service than high coherence
    expect(bLow).toBeLessThanOrEqual(base);
    expect(bHigh).toBeGreaterThanOrEqual(bLow);
  });

  test('GPD fit + tail quantile roughly behaves (synthetic exponential)', () => {
    const threshold = 200;
    const tailFrac = 0.05;
    // Exponential(mean=50) exceedances
    const exceedances = Array.from({ length: 300 }, () => -50 * Math.log(Math.random()));
    const params = fitGPD_PWM(exceedances, threshold, tailFrac);
    const q99 = tailQuantileFromGPD(0.99, params);
    expect(q99).toBeGreaterThan(threshold);
  });

  test('maxCycleMeanKarp returns expected value for simple cycle', () => {
    // 3-node cycle weights: 1,3,2 => cycle mean = (1+3+2)/3 = 2
    const W = buildWeightMatrix(3, [
      { u: 0, v: 1, w: 1 },
      { u: 1, v: 2, w: 3 },
      { u: 2, v: 0, w: 2 }
    ]);
    const { lambda } = maxCycleMeanKarp(W);
    expect(lambda).toBeCloseTo(2, 1);
  });

  test('aggregateResonance produces score in [0,1]', () => {
    const R = aggregateResonance(
      { coherenceScore: 0.7, tailHealthScore: 0.4, timingScore: 0.9 },
      { wC: 1, wT: 1, wTiming: 1 }
    );
    expect(R).toBeGreaterThanOrEqual(0);
    expect(R).toBeLessThanOrEqual(1);
  });
});


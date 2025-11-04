/**
 * Resonance Bridge
 * Bridges Resonance Calculus with the controller
 */

import {
  betaRateLatency,
  betaCoherenceWeighted,
  RateLatency,
  CoherenceSample,
  fitGPD_PWM,
  tailQuantileFromGPD,
  buildWeightMatrix,
  maxCycleMeanKarp,
  aggregateResonance,
  ResonanceComponents,
} from '../resonance-math/resonance_calculus';

export interface TailSample {
  value: number;
  isExtreme: boolean;
}

export interface GraphEdge {
  u: number;
  v: number;
  w: number; // e.g., coherence-modulated delay
}

export interface ResonanceInputs {
  tHorizon: number;
  rateLatency: RateLatency;
  coherenceSamples: CoherenceSample[];
  tailSamples: TailSample[];
  tailThresholdQuantile: number; // e.g., 0.95
  graphSize: number;
  edges: GraphEdge[];
}

export function computeResonanceFromInputs(
  inputs: ResonanceInputs
): { 
  R: number; 
  lambdaRes: number; 
  coherenceScore: number; 
  tailHealthScore: number; 
  timingScore: number 
} {
  const {
    tHorizon,
    rateLatency,
    coherenceSamples,
    tailSamples,
    tailThresholdQuantile,
    graphSize,
    edges,
  } = inputs;

  // 1) Coherence – compare β_c(t) vs nominal β(t)
  const betaNom = betaRateLatency(tHorizon, rateLatency);
  const betaC = betaCoherenceWeighted(tHorizon, rateLatency, coherenceSamples);
  const coherenceScore = betaNom <= 0 ? 0 : Math.min(1, Math.max(0, betaC / betaNom));

  // 2) Tail – pick threshold at given quantile, then fit GPD on exceedances
  const values = tailSamples.map(s => s.value).sort((a, b) => a - b);
  const n = values.length;
  let tailHealthScore = 0.5; // neutral default

  if (n >= 50) {
    const idxThresh = Math.max(0, Math.min(n - 1, Math.floor(tailThresholdQuantile * n)));
    const threshold = values[idxThresh];
    const exceedances = values.filter(x => x > threshold).map(x => x - threshold);
    const tailFrac = exceedances.length / n;
    if (exceedances.length >= 10 && tailFrac > 0) {
      try {
        const gpd = fitGPD_PWM(exceedances, threshold, tailFrac);
        const q99 = tailQuantileFromGPD(0.99, gpd);
        // Normalize q99 against threshold: lower is better.
        const ratio = q99 <= 0 ? 1 : threshold / q99;
        tailHealthScore = Math.min(1, Math.max(0, ratio));
      } catch (e) {
        // Fallback to neutral if GPD fit fails
        tailHealthScore = 0.5;
      }
    }
  }

  // 3) Timing – max-plus eigenvalue of coherence-modulated delay graph
  let lambdaRes = 0;
  let timingScore = 0.5;
  
  if (graphSize > 0 && edges.length > 0) {
    try {
      const W = buildWeightMatrix(graphSize, edges);
      const { lambda } = maxCycleMeanKarp(W);
      lambdaRes = lambda;
      // Map lambdaRes (cycle time) to timingScore: lower cycle time is better.
      // We use a simple squashing 1 / (1 + lambdaRes / scale).
      const scale = 1.0 || Math.abs(lambdaRes) || 1; // tune as needed
      const timingScoreRaw = lambdaRes <= 0 ? 1 : 1 / (1 + lambdaRes / scale);
      timingScore = Math.min(1, Math.max(0, timingScoreRaw));
    } catch (e) {
      // Fallback to neutral if graph processing fails
      timingScore = 0.5;
    }
  }

  const comp: ResonanceComponents = { coherenceScore, tailHealthScore, timingScore };
  const R = aggregateResonance(comp, { wC: 1, wT: 1, wTiming: 1 });

  return { R, lambdaRes, coherenceScore, tailHealthScore, timingScore };
}


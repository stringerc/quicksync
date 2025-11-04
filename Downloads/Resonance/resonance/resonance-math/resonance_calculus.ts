// resonance-math/resonance_calculus.ts
// Core Resonance Calculus: CWSC, EVT/GPD, Max-Plus, and an aggregate resonance score.

export type RateLatency = { R: number; T: number }; // R >= 0 (rate), T >= 0 (latency)

export type CoherenceSample = { t: number; c: number }; // time in seconds, coherence c in [0,1]

// =========================
// 1) Baseline & Coherence-Weighted Service Curve
// =========================

/**
 * Nominal rate-latency service curve β_{R,T}(t) = R * max(0, t − T).
 * This is a standard network calculus primitive: rate R after latency T.
 */
export function betaRateLatency(t: number, p: RateLatency): number {
  const x = t - p.T;
  return p.R * (x > 0 ? x : 0);
}

/**
 * Compute Δ(u) ≈ ∫_0^u log(1 + λ (c(s) − cBar)) ds via trapezoidal Riemann sum
 * over coherence samples. samples should be sorted by time.
 *
 * Intuition: if c(s) > cBar, the integral is positive (effective service boosted);
 * if c(s) < cBar, it is negative (effective service penalized).
 */
export function coherenceIntegralDelta(
  u: number,
  samples: CoherenceSample[],
  lambda = 1.0,
  cBar = 0.5
): number {
  if (samples.length === 0 || u <= 0) return 0;

  // Ensure sorted
  const sorted = [...samples].sort((a, b) => a.t - b.t);

  let acc = 0;
  let prevT = 0;
  let prevC = sorted[0].c;

  for (let i = 0; i < sorted.length; i++) {
    const { t, c } = sorted[i];
    if (t <= 0) continue;
    const segStart = Math.max(prevT, 0);
    const segEnd = Math.min(t, u);
    if (segEnd > segStart) {
      const dt = segEnd - segStart;
      const cMid = (prevC + c) / 2; // trapezoid rule
      acc += Math.log(1 + lambda * (cMid - cBar)) * dt;
    }
    if (t >= u) break;
    prevT = t;
    prevC = c;
  }

  const last = sorted[sorted.length - 1];
  if (u > last.t) {
    const dt = u - Math.max(last.t, 0);
    acc += Math.log(1 + lambda * (last.c - cBar)) * dt;
  }
  return acc;
}

/**
 * Coherence-Weighted Service Curve (CWSC):
 *
 *   β_c(t) = min_{0 ≤ u ≤ t} [ β(t − u) + Δ(u) ]
 *
 * Discrete approximation:
 *   - We build a set of candidate u "knots" from coherence sample times,
 *     optional extra knots, plus 0 and t.
 *   - Evaluate β and Δ at each u, and take the minimum.
 */
export function betaCoherenceWeighted(
  t: number,
  params: RateLatency,
  samples: CoherenceSample[],
  lambda = 1.0,
  cBar = 0.5,
  extraKnots: number[] = []
): number {
  if (t <= 0) return 0;

  const candidateKnots = new Set<number>();
  candidateKnots.add(0);
  candidateKnots.add(t);

  for (const s of samples) {
    if (s.t >= 0 && s.t <= t) candidateKnots.add(s.t);
  }
  for (const k of extraKnots) {
    if (k >= 0 && k <= t) candidateKnots.add(k);
  }

  const knots = Array.from(candidateKnots).sort((a, b) => a - b);

  let best = Number.POSITIVE_INFINITY;
  for (const u of knots) {
    const base = betaRateLatency(t - u, params);
    const delta = coherenceIntegralDelta(u, samples, lambda, cBar);
    const val = base + delta;
    if (val < best) best = val;
  }
  return best;
}

// =========================
// 2) EVT – GPD fit via PWM, with MoM fallback, and tail quantiles
// =========================

export type GPDParams = {
  xi: number;
  sigma: number;
  threshold: number;
  tailFrac: number; // empirical P(X > threshold)
};

function sortAsc(a: number, b: number) { return a - b; }

/**
 * Hosking PWM (Probability-Weighted Moments) for ordered sample x_(1) ≤ ... ≤ x_(n):
 *
 *   b0 = mean(x)
 *   b1 = (1/n) * Σ_{i=1..n} ((i-1)/(n-1)) * x_(i)
 *
 * Then L-moments:
 *   L1 = b0
 *   L2 = 2*b1 − b0
 */
export function pwmB0B1(sorted: number[]): { b0: number; b1: number } {
  const n = sorted.length;
  if (n === 0) throw new Error('empty sample');

  let sum = 0;
  let wsum = 0;
  for (let i = 0; i < n; i++) {
    const x = sorted[i];
    sum += x;
    const w = n > 1 ? i / (n - 1) : 0; // (i-1)/(n-1) with 0-indexed i
    wsum += w * x;
  }
  return { b0: sum / n, b1: wsum / n };
}

/**
 * Hosking PWM estimator for GPD on exceedances y = X − u > 0:
 *
 *   L1 = b0
 *   L2 = 2*b1 − b0
 *   xi = (2*L2) / (L1 − 2*L2)
 *   sigma = L1 * (1 − xi)
 *
 * If the denominator is non-positive (degenerate) we fall back to a simple
 * method-of-moments approximation.
 */
export function fitGPD_PWM(
  exceedances: number[],
  threshold: number,
  tailFrac: number
): GPDParams {
  if (exceedances.length < 10) {
    throw new Error('Need at least 10 exceedances for stable PWM fit');
  }

  const sorted = [...exceedances].sort(sortAsc);
  const { b0, b1 } = pwmB0B1(sorted);
  const L1 = b0;
  const L2 = 2 * b1 - b0;
  const denom = L1 - 2 * L2;

  if (denom <= 1e-12) {
    // Fallback: crude MoM approximation.
    const mean = L1;
    const m2 = sorted.reduce((acc, x) => acc + (x - mean) ** 2, 0) / Math.max(sorted.length - 1, 1);
    let xi = 0.5 * (1 - (mean * mean) / (m2 || 1e-12));
    // Clamp xi to a reasonable range to avoid degenerate behavior.
    xi = Math.max(-0.5, Math.min(1.5, xi));
    const sigma = Math.max(1e-9, mean * (1 - xi));
    return { xi, sigma, threshold, tailFrac };
  }

  const xi = (2 * L2) / denom;
  const sigma = Math.max(1e-9, L1 * (1 - xi));
  return { xi, sigma, threshold, tailFrac };
}

/**
 * GPD survival function for exceedance y ≥ 0:
 *
 *   S(y) = (1 + xi*y/sigma)^{−1/xi}   if xi ≠ 0
 *        = exp(−y/sigma)             if xi → 0
 */
export function gpdSurvival(y: number, params: GPDParams): number {
  const { xi, sigma } = params;
  if (y < 0) return 1;
  if (Math.abs(xi) < 1e-9) return Math.exp(-y / sigma);
  const z = 1 + (xi * y) / sigma;
  if (z <= 0) return 0; // outside support
  return Math.pow(z, -1 / xi);
}

/**
 * GPD exceedance quantile for exceedance probability p ∈ (0,1):
 *
 *   Q_excess(p) = sigma/xi * ((1 − p)^{−xi} − 1)
 *   If xi → 0, Q_excess(p) = −sigma * ln(1 − p)
 */
export function gpdExceedanceQuantile(p: number, params: GPDParams): number {
  const { xi, sigma } = params;
  if (p <= 0) return 0;
  if (p >= 1) return Infinity;
  if (Math.abs(xi) < 1e-9) return -sigma * Math.log(1 - p);
  return (sigma / xi) * (Math.pow(1 - p, -xi) - 1);
}

/**
 * Tail quantile for the original variable X at high probability q (e.g., q = 0.99).
 *
 * Let u = threshold, τ = P(X > u) (tailFrac).
 * If q ≤ 1 − τ, caller should use an empirical quantile below u; here we return u as a floor.
 * If q > 1 − τ:
 *   p_tail = (q − (1 − τ)) / τ  ∈ (0,1)
 *   Q(q) = u + Q_excess(p_tail)
 */
export function tailQuantileFromGPD(
  q: number,
  params: GPDParams
): number {
  const { threshold: u, tailFrac: tau } = params;
  if (tau <= 0) return Infinity;
  if (q <= 1 - tau) return u;
  const pTail = (q - (1 - tau)) / tau;
  const excess = gpdExceedanceQuantile(pTail, params);
  return u + excess;
}

// =========================
// 3) Max-Plus Eigenvalue: Maximum Cycle Mean (Karp)
// =========================

export type Edge = { u: number; v: number; w: number };

/**
 * Build an n×n weight matrix from an edge list.
 * Missing edges are represented as −Infinity.
 */
export function buildWeightMatrix(n: number, edges: Edge[]): number[][] {
  const W = Array.from({ length: n }, () => Array(n).fill(-Infinity));
  for (const { u, v, w } of edges) {
    if (u < 0 || v < 0 || u >= n || v >= n) {
      throw new Error('Edge index out of range');
    }
    // If multiple edges exist, keep the maximum weight.
    W[u][v] = Math.max(W[u][v], w);
  }
  return W;
}

/**
 * Karp's algorithm for maximum cycle mean on directed graph with weights W[i][j].
 * Returns:
 *   lambda = maximum cycle mean (max-plus eigenvalue)
 *   witness = a node index on an optimal cycle (for debugging/inspection)
 *
 * Complexity: O(n^2) for dense graph, O(n*m) conceptually.
 */
export function maxCycleMeanKarp(W: number[][]): { lambda: number; witness: number } {
  const n = W.length;
  if (n === 0) return { lambda: -Infinity, witness: -1 };

  // dp[k][v]: max weight of a walk of length k ending at v
  const dp: number[][] = Array.from({ length: n + 1 }, () => Array(n).fill(-Infinity));
  for (let v = 0; v < n; v++) dp[0][v] = 0;

  for (let k = 1; k <= n; k++) {
    for (let v = 0; v < n; v++) {
      let best = -Infinity;
      for (let u = 0; u < n; u++) {
        const w = W[u][v];
        if (w === -Infinity) continue;
        if (dp[k - 1][u] === -Infinity) continue;
        const cand = dp[k - 1][u] + w;
        if (cand > best) best = cand;
      }
      dp[k][v] = best;
    }
  }

  let lambda = -Infinity;
  let witness = 0;

  for (let v = 0; v < n; v++) {
    let minAvg = Infinity;
    for (let k = 0; k < n; k++) {
      if (dp[k][v] === -Infinity) continue;
      const avg = (dp[n][v] - dp[k][v]) / (n - k);
      if (avg < minAvg) minAvg = avg;
    }
    if (minAvg > lambda) {
      lambda = minAvg;
      witness = v;
    }
  }

  return { lambda, witness };
}

// =========================
// 4) Aggregate Resonance Score (simple reference implementation)
// =========================

export interface ResonanceComponents {
  // Coherence-related: e.g., normalized CWSC vs nominal
  coherenceScore: number;   // in [0,1]
  // Tail-health: e.g., 1 − normalized tail quantile (higher is better)
  tailHealthScore: number;  // in [0,1]
  // Timing: e.g., 1 / (1 + scaled lambda_res) mapped into [0,1]
  timingScore: number;      // in [0,1]
}

export interface ResonanceWeights {
  wC: number;
  wT: number;
  wTiming: number;
}

/**
 * Combine coherence, tail-health, and timing into a scalar resonance score.
 * Reference form:
 *
 *   R = (wC * C + wT * T + wTiming * M) / (wC + wT + wTiming)
 *
 * where each component is in [0,1]. This matches the "weighted aggregation"
 * pattern in the patent and is easy to extend with learned weights.
 */
export function aggregateResonance(
  comp: ResonanceComponents,
  weights: ResonanceWeights
): number {
  const { coherenceScore, tailHealthScore, timingScore } = comp;
  const { wC, wT, wTiming } = weights;
  const num = wC * coherenceScore + wT * tailHealthScore + wTiming * timingScore;
  const den = Math.max(wC + wT + wTiming, 1e-9);
  const R = num / den;
  // Clamp to [0,1] to be safe
  return Math.min(1, Math.max(0, R));
}


export type RateLatency = {
    R: number;
    T: number;
};
export type CoherenceSample = {
    t: number;
    c: number;
};
/**
 * Nominal rate-latency service curve β_{R,T}(t) = R * max(0, t − T).
 * This is a standard network calculus primitive: rate R after latency T.
 */
export declare function betaRateLatency(t: number, p: RateLatency): number;
/**
 * Compute Δ(u) ≈ ∫_0^u log(1 + λ (c(s) − cBar)) ds via trapezoidal Riemann sum
 * over coherence samples. samples should be sorted by time.
 *
 * Intuition: if c(s) > cBar, the integral is positive (effective service boosted);
 * if c(s) < cBar, it is negative (effective service penalized).
 */
export declare function coherenceIntegralDelta(u: number, samples: CoherenceSample[], lambda?: number, cBar?: number): number;
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
export declare function betaCoherenceWeighted(t: number, params: RateLatency, samples: CoherenceSample[], lambda?: number, cBar?: number, extraKnots?: number[]): number;
export type GPDParams = {
    xi: number;
    sigma: number;
    threshold: number;
    tailFrac: number;
};
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
export declare function pwmB0B1(sorted: number[]): {
    b0: number;
    b1: number;
};
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
export declare function fitGPD_PWM(exceedances: number[], threshold: number, tailFrac: number): GPDParams;
/**
 * GPD survival function for exceedance y ≥ 0:
 *
 *   S(y) = (1 + xi*y/sigma)^{−1/xi}   if xi ≠ 0
 *        = exp(−y/sigma)             if xi → 0
 */
export declare function gpdSurvival(y: number, params: GPDParams): number;
/**
 * GPD exceedance quantile for exceedance probability p ∈ (0,1):
 *
 *   Q_excess(p) = sigma/xi * ((1 − p)^{−xi} − 1)
 *   If xi → 0, Q_excess(p) = −sigma * ln(1 − p)
 */
export declare function gpdExceedanceQuantile(p: number, params: GPDParams): number;
/**
 * Tail quantile for the original variable X at high probability q (e.g., q = 0.99).
 *
 * Let u = threshold, τ = P(X > u) (tailFrac).
 * If q ≤ 1 − τ, caller should use an empirical quantile below u; here we return u as a floor.
 * If q > 1 − τ:
 *   p_tail = (q − (1 − τ)) / τ  ∈ (0,1)
 *   Q(q) = u + Q_excess(p_tail)
 */
export declare function tailQuantileFromGPD(q: number, params: GPDParams): number;
export type Edge = {
    u: number;
    v: number;
    w: number;
};
/**
 * Build an n×n weight matrix from an edge list.
 * Missing edges are represented as −Infinity.
 */
export declare function buildWeightMatrix(n: number, edges: Edge[]): number[][];
/**
 * Karp's algorithm for maximum cycle mean on directed graph with weights W[i][j].
 * Returns:
 *   lambda = maximum cycle mean (max-plus eigenvalue)
 *   witness = a node index on an optimal cycle (for debugging/inspection)
 *
 * Complexity: O(n^2) for dense graph, O(n*m) conceptually.
 */
export declare function maxCycleMeanKarp(W: number[][]): {
    lambda: number;
    witness: number;
};
export interface ResonanceComponents {
    coherenceScore: number;
    tailHealthScore: number;
    timingScore: number;
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
export declare function aggregateResonance(comp: ResonanceComponents, weights: ResonanceWeights): number;
//# sourceMappingURL=resonance_calculus.d.ts.map
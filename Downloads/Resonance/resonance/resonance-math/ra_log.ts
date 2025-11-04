/**
 * RA-Log: Log-Domain Semiring
 * For probabilistic accumulation in predictors
 * 
 * Operations:
 * - ⊗ (multiply): a + b (log-domain addition)
 * - ⊕ (add): log-sum-exp(a, b) or max(a, b) for Viterbi
 */

/**
 * Log-domain multiplication: a + b
 */
export function logMul(a: number, b: number): number {
  return a + b;
}

/**
 * Log-sum-exp (numerically stable)
 * log(exp(a) + exp(b)) = max(a, b) + log(1 + exp(-|a - b|))
 */
export function logAddExp(a: number, b: number): number {
  const mx = Math.max(a, b);
  return mx + Math.log(1 + Math.exp(-Math.abs(a - b)));
}

/**
 * Viterbi-style max (hard max in log domain)
 */
export function logMax(a: number, b: number): number {
  return Math.max(a, b);
}

/**
 * Log-domain zero (additive identity): -Infinity
 */
export const LOG_ZERO = -Infinity;

/**
 * Log-domain one (multiplicative identity): 0
 */
export const LOG_ONE = 0;

/**
 * Sum of log-domain values (numerically stable)
 */
export function logSum(values: number[]): number {
  if (values.length === 0) return LOG_ZERO;
  if (values.length === 1) return values[0];
  
  let result = values[0];
  for (let i = 1; i < values.length; i++) {
    result = logAddExp(result, values[i]);
  }
  
  return result;
}

/**
 * Convert probability to log-domain
 */
export function toLogDomain(p: number): number {
  if (p <= 0) return LOG_ZERO;
  return Math.log(p);
}

/**
 * Convert log-domain value to probability
 */
export function fromLogDomain(logP: number): number {
  if (logP === LOG_ZERO) return 0;
  return Math.exp(logP);
}

/**
 * Softmax in log domain (numerically stable)
 */
export function logSoftmax(logits: number[]): number[] {
  if (logits.length === 0) return [];
  
  // Subtract max for numerical stability
  const maxLogit = Math.max(...logits);
  const shifted = logits.map((x) => x - maxLogit);
  
  // Compute softmax
  return shifted.map((x) => x - Math.log(shifted.reduce((sum, y) => sum + Math.exp(y), 0)));
}

/**
 * Blend probabilities in log domain
 */
export function logBlend(
  logP1: number,
  logP2: number,
  alpha: number
): number {
  const logAlpha = toLogDomain(alpha);
  const logOneMinusAlpha = toLogDomain(1 - alpha);
  
  // exp(logAlpha + logP1) + exp(logOneMinusAlpha + logP2)
  const term1 = logAlpha + logP1;
  const term2 = logOneMinusAlpha + logP2;
  
  return logAddExp(term1, term2);
}


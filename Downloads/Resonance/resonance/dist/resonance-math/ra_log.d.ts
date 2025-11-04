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
export declare function logMul(a: number, b: number): number;
/**
 * Log-sum-exp (numerically stable)
 * log(exp(a) + exp(b)) = max(a, b) + log(1 + exp(-|a - b|))
 */
export declare function logAddExp(a: number, b: number): number;
/**
 * Viterbi-style max (hard max in log domain)
 */
export declare function logMax(a: number, b: number): number;
/**
 * Log-domain zero (additive identity): -Infinity
 */
export declare const LOG_ZERO: number;
/**
 * Log-domain one (multiplicative identity): 0
 */
export declare const LOG_ONE = 0;
/**
 * Sum of log-domain values (numerically stable)
 */
export declare function logSum(values: number[]): number;
/**
 * Convert probability to log-domain
 */
export declare function toLogDomain(p: number): number;
/**
 * Convert log-domain value to probability
 */
export declare function fromLogDomain(logP: number): number;
/**
 * Softmax in log domain (numerically stable)
 */
export declare function logSoftmax(logits: number[]): number[];
/**
 * Blend probabilities in log domain
 */
export declare function logBlend(logP1: number, logP2: number, alpha: number): number;
//# sourceMappingURL=ra_log.d.ts.map
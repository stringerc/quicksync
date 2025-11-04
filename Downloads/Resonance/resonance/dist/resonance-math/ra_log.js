"use strict";
/**
 * RA-Log: Log-Domain Semiring
 * For probabilistic accumulation in predictors
 *
 * Operations:
 * - ⊗ (multiply): a + b (log-domain addition)
 * - ⊕ (add): log-sum-exp(a, b) or max(a, b) for Viterbi
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.LOG_ONE = exports.LOG_ZERO = void 0;
exports.logMul = logMul;
exports.logAddExp = logAddExp;
exports.logMax = logMax;
exports.logSum = logSum;
exports.toLogDomain = toLogDomain;
exports.fromLogDomain = fromLogDomain;
exports.logSoftmax = logSoftmax;
exports.logBlend = logBlend;
/**
 * Log-domain multiplication: a + b
 */
function logMul(a, b) {
    return a + b;
}
/**
 * Log-sum-exp (numerically stable)
 * log(exp(a) + exp(b)) = max(a, b) + log(1 + exp(-|a - b|))
 */
function logAddExp(a, b) {
    const mx = Math.max(a, b);
    return mx + Math.log(1 + Math.exp(-Math.abs(a - b)));
}
/**
 * Viterbi-style max (hard max in log domain)
 */
function logMax(a, b) {
    return Math.max(a, b);
}
/**
 * Log-domain zero (additive identity): -Infinity
 */
exports.LOG_ZERO = -Infinity;
/**
 * Log-domain one (multiplicative identity): 0
 */
exports.LOG_ONE = 0;
/**
 * Sum of log-domain values (numerically stable)
 */
function logSum(values) {
    if (values.length === 0)
        return exports.LOG_ZERO;
    if (values.length === 1)
        return values[0];
    let result = values[0];
    for (let i = 1; i < values.length; i++) {
        result = logAddExp(result, values[i]);
    }
    return result;
}
/**
 * Convert probability to log-domain
 */
function toLogDomain(p) {
    if (p <= 0)
        return exports.LOG_ZERO;
    return Math.log(p);
}
/**
 * Convert log-domain value to probability
 */
function fromLogDomain(logP) {
    if (logP === exports.LOG_ZERO)
        return 0;
    return Math.exp(logP);
}
/**
 * Softmax in log domain (numerically stable)
 */
function logSoftmax(logits) {
    if (logits.length === 0)
        return [];
    // Subtract max for numerical stability
    const maxLogit = Math.max(...logits);
    const shifted = logits.map((x) => x - maxLogit);
    // Compute softmax
    return shifted.map((x) => x - Math.log(shifted.reduce((sum, y) => sum + Math.exp(y), 0)));
}
/**
 * Blend probabilities in log domain
 */
function logBlend(logP1, logP2, alpha) {
    const logAlpha = toLogDomain(alpha);
    const logOneMinusAlpha = toLogDomain(1 - alpha);
    // exp(logAlpha + logP1) + exp(logOneMinusAlpha + logP2)
    const term1 = logAlpha + logP1;
    const term2 = logOneMinusAlpha + logP2;
    return logAddExp(term1, term2);
}
//# sourceMappingURL=ra_log.js.map
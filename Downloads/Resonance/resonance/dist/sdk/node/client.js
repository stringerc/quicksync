"use strict";
/**
 * Resonance Client SDK
 * High-level API for task submission with hedging and retry policies
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.TokenBucket = exports.ResonanceClient = void 0;
class ResonanceClient {
    constructor(core, calculus, tokenBucket) {
        this.core = core;
        this.calculus = calculus;
        this.tokenBucket = tokenBucket;
    }
    /**
     * Submit task with resonance hints
     */
    async submit(fn, hint) {
        if (!this.core) {
            return fn(); // Fallback if no core
        }
        return this.core.decideAndRun(hint, fn);
    }
    /**
     * Submit task with hedging
     */
    async hedge(fn, hint, config) {
        if (!hint.idempotent && config.idempotentOnly) {
            // Non-idempotent, skip hedging
            const result = await this.submit(fn, hint);
            return { result, hedgeFired: false, hedgeDelay: 0, winner: 0 };
        }
        // Fire primary immediately
        const primary = fn();
        // Setup hedge to fire after delay
        const hedgeTimer = new Promise((resolve) => setTimeout(resolve, config.delayMs));
        const primaryFinished = primary.then(() => null).catch(() => null);
        // Race timer vs primary completion
        const first = await Promise.race([hedgeTimer, primaryFinished]);
        if (first === null) {
            // Primary finished before hedge trigger
            const result = await primary;
            return { result, hedgeFired: false, hedgeDelay: 0, winner: 0 };
        }
        // Hedge triggered, race both
        const hedgeReq = fn();
        const results = await Promise.allSettled([primary, hedgeReq]);
        const winner = results.findIndex((r) => r.status === 'fulfilled');
        if (winner === -1)
            throw new Error('Both failed');
        return {
            result: results[winner].value,
            hedgeFired: true,
            hedgeDelay: config.delayMs,
            winner,
        };
    }
    /**
     * Submit task with jittered retry
     */
    async retry(fn, config) {
        let lastError;
        for (let attempt = 0; attempt < config.maxAttempts; attempt++) {
            try {
                // Check token bucket if configured
                if (config.tokenBucket && this.tokenBucket) {
                    if (!this.tokenBucket.take()) {
                        // Rate limited
                        await this.backoff(config.strategy, attempt, config);
                        continue;
                    }
                }
                return await fn();
            }
            catch (error) {
                lastError = error;
                if (attempt < config.maxAttempts - 1) {
                    await this.backoff(config.strategy, attempt, config);
                }
            }
        }
        throw lastError || new Error('Retry exhausted');
    }
    /**
     * Compute backoff delay based on strategy
     */
    async backoff(strategy, attempt, config) {
        const baseDelay = config.baseDelayMs;
        let delayMs = 0;
        switch (strategy) {
            case 'fixed':
                delayMs = baseDelay;
                break;
            case 'exponential':
                delayMs = Math.min(config.maxDelayMs, baseDelay * Math.pow(2, attempt));
                break;
            case 'full_jitter':
                const exponential = baseDelay * Math.pow(2, attempt);
                delayMs = Math.min(config.maxDelayMs, Math.random() * exponential);
                break;
            default:
                delayMs = baseDelay;
        }
        await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    /**
     * Run task immediately (bypass controller)
     */
    now(fn) {
        return fn();
    }
    /**
     * Get current state
     */
    getState() {
        if (typeof globalThis !== 'undefined') {
            return globalThis.__resonance_state;
        }
        return undefined;
    }
    /**
     * Explain decision for task
     */
    explain(taskId) {
        const state = this.getState();
        if (this.calculus) {
            const decision = this.calculus.decide(50); // 50ms defer budget
            return {
                decision: decision.action,
                reason: decision.reason,
                features: {
                    R: state?.R || 0,
                    spectralEntropy: state?.spectralEntropy || 0,
                    K: state?.K || 0,
                    backlog: decision.backlog,
                    boundMs: decision.boundMs,
                },
            };
        }
        return {
            decision: 'execute',
            reason: 'No calculus available',
            features: {
                R: state?.R || 0,
                spectralEntropy: state?.spectralEntropy || 0,
                K: state?.K || 0,
            },
        };
    }
}
exports.ResonanceClient = ResonanceClient;
/**
 * Token Bucket for rate limiting retries
 */
class TokenBucket {
    constructor(config) {
        this.tokens = config.capacity;
        this.capacity = config.capacity;
        this.refillRate = config.refillRate;
        this.lastRefill = Date.now();
    }
    /**
     * Try to take a token
     */
    take() {
        this.refill();
        if (this.tokens >= 1) {
            this.tokens -= 1;
            return true;
        }
        return false;
    }
    /**
     * Refill bucket based on elapsed time
     */
    refill() {
        const now = Date.now();
        const elapsed = (now - this.lastRefill) / 1000; // seconds
        this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillRate);
        this.lastRefill = now;
    }
    /**
     * Get current token count
     */
    getTokens() {
        this.refill();
        return this.tokens;
    }
}
exports.TokenBucket = TokenBucket;
//# sourceMappingURL=client.js.map
/**
 * Resonance Client SDK
 * High-level API for task submission with hedging and retry policies
 */
import type { TaskHint as ResonanceHint, ResonanceState, HedgeConfig, RetryConfig } from '../../resonance-core/types';
export interface ExplainResult {
    decision: 'execute' | 'defer' | 'batch' | 'hedge';
    reason: string;
    features: Record<string, number>;
}
export declare class ResonanceClient {
    private core;
    private calculus;
    private tokenBucket?;
    constructor(core: any, calculus?: any, tokenBucket?: TokenBucket);
    /**
     * Submit task with resonance hints
     */
    submit<T>(fn: () => Promise<T>, hint: ResonanceHint): Promise<T>;
    /**
     * Submit task with hedging
     */
    hedge<T>(fn: () => Promise<T>, hint: ResonanceHint, config: HedgeConfig): Promise<{
        result: T;
        hedgeFired: boolean;
        hedgeDelay: number;
        winner: number;
    }>;
    /**
     * Submit task with jittered retry
     */
    retry<T>(fn: () => Promise<T>, config: RetryConfig): Promise<T>;
    /**
     * Compute backoff delay based on strategy
     */
    private backoff;
    /**
     * Run task immediately (bypass controller)
     */
    now<T>(fn: () => Promise<T>): Promise<T>;
    /**
     * Get current state
     */
    getState(): ResonanceState | undefined;
    /**
     * Explain decision for task
     */
    explain(taskId: string): ExplainResult;
}
/**
 * Token Bucket for rate limiting retries
 */
export declare class TokenBucket {
    private tokens;
    private capacity;
    private refillRate;
    private lastRefill;
    constructor(config: {
        refillRate: number;
        capacity: number;
    });
    /**
     * Try to take a token
     */
    take(): boolean;
    /**
     * Refill bucket based on elapsed time
     */
    private refill;
    /**
     * Get current token count
     */
    getTokens(): number;
}
//# sourceMappingURL=client.d.ts.map
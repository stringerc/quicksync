/**
 * Resonance Client SDK
 * High-level API for task submission with hedging and retry policies
 */

import type { TaskHint as ResonanceHint, ResonanceState, HedgeConfig, RetryConfig } from '../../resonance-core/types';
import type { CalculusDecision } from '../../resonance-core/calculus';

export interface ExplainResult {
  decision: 'execute' | 'defer' | 'batch' | 'hedge';
  reason: string;
  features: Record<string, number>;
}

export class ResonanceClient {
  private core: any; // ResonanceCore via DI
  private calculus: any; // ResonanceCalculus
  private tokenBucket?: TokenBucket;

  constructor(core: any, calculus?: any, tokenBucket?: TokenBucket) {
    this.core = core;
    this.calculus = calculus;
    this.tokenBucket = tokenBucket;
  }

  /**
   * Submit task with resonance hints
   */
  async submit<T>(fn: () => Promise<T>, hint: ResonanceHint): Promise<T> {
    if (!this.core) {
      return fn(); // Fallback if no core
    }

    return this.core.decideAndRun(hint, fn);
  }

  /**
   * Submit task with hedging
   */
  async hedge<T>(
    fn: () => Promise<T>,
    hint: ResonanceHint,
    config: HedgeConfig
  ): Promise<{ result: T; hedgeFired: boolean; hedgeDelay: number; winner: number }> {
    if (!hint.idempotent && config.idempotentOnly) {
      // Non-idempotent, skip hedging
      const result = await this.submit(fn, hint);
      return { result, hedgeFired: false, hedgeDelay: 0, winner: 0 };
    }

    // Fire primary immediately
    const primary = fn();
    
    // Setup hedge to fire after delay
    const hedgeTimer = new Promise<void>((resolve) => setTimeout(resolve, config.delayMs));
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
    
    if (winner === -1) throw new Error('Both failed');
    
    return {
      result: (results[winner] as PromiseFulfilledResult<T>).value,
      hedgeFired: true,
      hedgeDelay: config.delayMs,
      winner,
    };
  }

  /**
   * Submit task with jittered retry
   */
  async retry<T>(
    fn: () => Promise<T>,
    config: RetryConfig
  ): Promise<T> {
    let lastError: Error | undefined;

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
      } catch (error) {
        lastError = error as Error;

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
  private async backoff(
    strategy: RetryConfig['strategy'],
    attempt: number,
    config: RetryConfig
  ): Promise<void> {
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
  now<T>(fn: () => Promise<T>): Promise<T> {
    return fn();
  }

  /**
   * Get current state
   */
  getState(): ResonanceState | undefined {
    if (typeof globalThis !== 'undefined') {
      return (globalThis as any).__resonance_state;
    }
    return undefined;
  }

  /**
   * Explain decision for task
   */
  explain(taskId: string): ExplainResult {
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

/**
 * Token Bucket for rate limiting retries
 */
export class TokenBucket {
  private tokens: number;
  private capacity: number;
  private refillRate: number; // tokens per second
  private lastRefill: number;

  constructor(config: { refillRate: number; capacity: number }) {
    this.tokens = config.capacity;
    this.capacity = config.capacity;
    this.refillRate = config.refillRate;
    this.lastRefill = Date.now();
  }

  /**
   * Try to take a token
   */
  take(): boolean {
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
  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000; // seconds

    this.tokens = Math.min(
      this.capacity,
      this.tokens + elapsed * this.refillRate
    );

    this.lastRefill = now;
  }

  /**
   * Get current token count
   */
  getTokens(): number {
    this.refill();
    return this.tokens;
  }
}


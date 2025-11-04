export type Decision = 'execute' | 'defer' | 'batch';
export type Mode = 'observe' | 'shadow' | 'active' | 'adaptive';

export interface ResonanceState {
  R: number;
  spectralEntropy: number;
  K: number;
  mode: Mode;
}

export interface Features {
  R: number;
  spectralEntropy: number;
  p99Risk: number;
  sigmaTheta: number;
  backlogBound?: number;
}

export interface Actuators {
  microDelayMs?: number;
  batchSize?: number;
  dither?: number;
  adjustK?: number;
}

export interface ControllerConfig {
  R_band: [number, number];
  K_min: number;
  K_max: number;
  maxMicroDelayMs: number;
  defaultBatchLatencyMs: number;
}

export interface TaskHint {
  id: string;
  importance: 'low' | 'normal' | 'high' | 'critical';
  softDeadlineMs?: number;
  canBatch?: boolean;
  maxBatchLatencyMs?: number;
  maxDeferralMs?: number;
  mustRunNow?: boolean;
  phaseAffinity?: 'align' | 'avoid';
  taskClass?: string;
  idempotent?: boolean;
}

export interface HedgeConfig {
  delayMs: number;
  maxInflightPct: number;
  cancelOnFirst: boolean;
  idempotentOnly: boolean;
}

export interface RetryConfig {
  strategy: 'full_jitter' | 'fixed' | 'exponential';
  baseDelayMs: number;
  maxDelayMs: number;
  maxAttempts: number;
  tokenBucket?: TokenBucketConfig;
}

export interface TokenBucketConfig {
  refillRate: number;
  capacity: number;
  localOnly: boolean;
}

export interface HedgeResult<T> {
  result: T;
  hedgeFired: boolean;
  hedgeDelay: number;
  winner: number;
  loserCancelTime?: number;
}


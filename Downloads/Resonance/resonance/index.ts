/**
 * Resonance Runtime
 * Complete package exports
 */

// Core
export * from './resonance-core';
export { ResonanceCalculus } from './resonance-core/calculus';

// Spectral
export * from './spectral';

// Math
export * from './resonance-math';

// SDK
export * from './sdk/node';

// Observability
export { LatencyHistogram } from './observability/histogram';

// Re-export types
export type {
  ResonanceState,
  Features,
  Actuators,
  ControllerConfig,
  TaskHint,
  HedgeConfig,
  RetryConfig,
} from './resonance-core/types';


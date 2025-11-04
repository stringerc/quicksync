/**
 * Actuators
 * Apply controller decisions (delays, batching, coupling adjustments)
 */

import { Actuators as Actuation } from './types';

export type ActuationResult = {
  delayApplied: number;
  ditherApplied?: number;
  kAdjustment?: number;
};

/**
 * Apply actuation to a task
 */
export async function applyActuation<T>(
  act: Actuation,
  run: () => Promise<T>
): Promise<T> {
  // Apply micro-delay if needed
  if (act.microDelayMs && act.microDelayMs > 0) {
    await sleep(act.microDelayMs);
  }

  // Apply dither (small random variance)
  if (act.dither) {
    const ditherMs = act.dither > 0 
      ? Math.random() * Math.abs(act.dither) * 5  // Positive: random delay
      : -Math.random() * Math.abs(act.dither) * 5; // Negative: coherent pulse (immediate)
    
    if (ditherMs > 0) {
      await sleep(ditherMs);
    }
  }

  // Note: batchSize and adjustK are handled at higher levels
  return run();
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Record actuation for observability
 */
export interface ActuationRecord {
  timestamp: number;
  kind: 'microdelay' | 'batch' | 'dither' | 'adjustK' | 'bypass';
  value: number;
  taskClass?: string;
  reason?: string;
}

export class ActuationLogger {
  private records: ActuationRecord[] = [];
  private maxRecords = 1000;

  log(record: ActuationRecord): void {
    this.records.push(record);
    
    // Trim old records
    if (this.records.length > this.maxRecords) {
      this.records = this.records.slice(-this.maxRecords);
    }
  }

  getRecords(): ActuationRecord[] {
    return [...this.records];
  }

  getRecentCount(kind: ActuationRecord['kind'], windowMs = 60000): number {
    const cutoff = Date.now() - windowMs;
    return this.records.filter(
      (r) => r.kind === kind && r.timestamp >= cutoff
    ).length;
  }

  clear(): void {
    this.records = [];
  }
}


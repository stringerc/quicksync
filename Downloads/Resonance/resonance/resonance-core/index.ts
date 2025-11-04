/**
 * Resonance Core
 * Main coordination engine combining all components
 */

import { orderParameter, phaseDispersion } from './kuramoto';
import { BandController } from './controller_pi';
import { adaptK } from './adaptive_coupling';
import { applyActuation } from './actuators';
import { computeResonanceFromInputs, type ResonanceInputs, type TailSample } from './resonance_bridge';
import { LatencyHistogram } from '../observability/histogram';
import type { ControllerConfig, TaskHint, Features, ResonanceState } from './types';
import type { CoherenceSample } from '../resonance-math/resonance_calculus';

export class ResonanceCore {
  state: ResonanceState = {
    R: 0,
    spectralEntropy: 0.5,
    K: 0.3,
    mode: 'observe',
  };

  controller: BandController;
  private phases: number[] = [];
  private lastUpdate = Date.now();
  
  // Resonance Calculus integration
  private coherenceHistory: CoherenceSample[] = [];
  private latencyHistogram: LatencyHistogram;
  private maxHistorySize = 100; // Keep last 100 coherence samples
  private useResonanceCalculus = true; // Enable/disable calculus integration

  constructor(cfg: ControllerConfig) {
    this.controller = new BandController(cfg);
    this.latencyHistogram = new LatencyHistogram();
    this.updateGlobalState();
  }

  /**
   * Update global state with current phases
   * Now uses Resonance Calculus to compute R when enabled
   */
  update(phases: number[], spectralEntropy: number, p99Risk: number): Features {
    this.phases = phases;
    const { R: R_phase } = orderParameter(phases);
    const sigmaTheta = phaseDispersion(phases);

    // Record coherence sample for Resonance Calculus
    const now = Date.now() / 1000; // Convert to seconds
    this.coherenceHistory.push({ t: now, c: R_phase });
    
    // Keep history bounded
    if (this.coherenceHistory.length > this.maxHistorySize) {
      this.coherenceHistory.shift();
    }

    // Compute R using Resonance Calculus if enabled
    let R = R_phase;
    if (this.useResonanceCalculus && this.coherenceHistory.length >= 10) {
      try {
        const resonance = this.computeResonance();
        R = resonance.R;
        
        // Update state with calculus-derived R
        this.state.R = R;
        
        // Store additional metrics for telemetry
        if (typeof globalThis !== 'undefined') {
          (globalThis as any).__resonance_calculus = {
            R,
            coherenceScore: resonance.coherenceScore,
            tailHealthScore: resonance.tailHealthScore,
            timingScore: resonance.timingScore,
            lambdaRes: resonance.lambdaRes,
          };
        }
      } catch (e) {
        // Fallback to phase-based R if calculus fails
        console.warn('Resonance Calculus computation failed, using phase-based R:', e);
        R = R_phase;
      }
    } else {
      // Use phase-based R (fallback or when calculus disabled)
      this.state.R = R_phase;
    }

    this.state.spectralEntropy = spectralEntropy;
    this.state.K = adaptK(
      this.state.K,
      sigmaTheta,
      p99Risk,
      { min: this.controller.getConfig().K_min, max: this.controller.getConfig().K_max }
    );

    this.updateGlobalState();

    return { R, spectralEntropy, p99Risk, sigmaTheta };
  }

  /**
   * Compute resonance using Resonance Calculus
   */
  private computeResonance(): { 
    R: number; 
    coherenceScore: number; 
    tailHealthScore: number; 
    timingScore: number; 
    lambdaRes: number;
  } {
    // Get tail samples from histogram
    const tailSamples = this.getTailSamples();
    
    // Build dependency graph from phases (each phase = node)
    const graphSize = Math.max(this.phases.length, 1);
    const edges = this.buildDependencyGraph();
    
    // Normalize coherence history to recent time window (last 10 seconds)
    const now = Date.now() / 1000;
    const windowStart = now - 10;
    const recentCoherence = this.coherenceHistory
      .filter(s => s.t >= windowStart)
      .map(s => ({ ...s, t: s.t - windowStart })); // Normalize to [0, 10]
    
    // If no recent samples, use all history
    const coherenceSamples = recentCoherence.length > 0 ? recentCoherence : this.coherenceHistory;

    const inputs: ResonanceInputs = {
      tHorizon: 5.0, // 5 second horizon
      rateLatency: { 
        R: 100, // 100 req/s baseline rate
        T: 0.1  // 100ms baseline latency
      },
      coherenceSamples,
      tailSamples,
      tailThresholdQuantile: 0.95,
      graphSize,
      edges,
    };

    return computeResonanceFromInputs(inputs);
  }

  /**
   * Get tail samples from latency histogram
   */
  private getTailSamples(): TailSample[] {
    const samples: TailSample[] = [];
    
    // Get percentiles from histogram
    const percentiles = this.latencyHistogram.getPercentiles();
    const count = this.latencyHistogram.getCount();
    
    if (count === 0) {
      // Return default samples if histogram is empty
      return Array.from({ length: 50 }, (_, i) => ({
        value: 100 + i * 10, // Synthetic values
        isExtreme: false,
      }));
    }

    // Generate samples from histogram buckets
    // This is a simplified approach - in production, use actual histogram data
    const p95 = percentiles.p95 * 1000; // Convert to microseconds
    const p99 = percentiles.p99 * 1000;
    const p99_9 = percentiles.p99_9 * 1000;
    
    // Create samples around key percentiles
    for (let i = 0; i < 20; i++) {
      samples.push({
        value: p95 + (i * 5),
        isExtreme: p95 + (i * 5) > p99,
      });
    }
    
    for (let i = 0; i < 20; i++) {
      samples.push({
        value: p99 + (i * 10),
        isExtreme: true,
      });
    }
    
    for (let i = 0; i < 10; i++) {
      samples.push({
        value: p99_9 + (i * 50),
        isExtreme: true,
      });
    }

    return samples;
  }

  /**
   * Build dependency graph from phases
   * Each phase represents a node, edges represent coherence-modulated delays
   */
  private buildDependencyGraph(): Array<{ u: number; v: number; w: number }> {
    const edges: Array<{ u: number; v: number; w: number }> = [];
    const n = this.phases.length;
    
    if (n === 0) return edges;
    
    // Create a ring topology: each node connects to next
    for (let i = 0; i < n; i++) {
      const next = (i + 1) % n;
      
      // Delay weight based on phase difference and coherence
      const phaseDiff = Math.abs(this.phases[i] - this.phases[next]);
      const coherence = Math.abs(Math.cos(phaseDiff));
      
      // Higher coherence = lower delay (better synchronization)
      const baseDelay = 10; // Base delay in arbitrary units
      const w = baseDelay * (2 - coherence); // Invert coherence for delay
      
      edges.push({ u: i, v: next, w });
    }
    
    // Also add reverse edges for full connectivity
    for (let i = 0; i < n; i++) {
      const prev = (i - 1 + n) % n;
      const phaseDiff = Math.abs(this.phases[i] - this.phases[prev]);
      const coherence = Math.abs(Math.cos(phaseDiff));
      const baseDelay = 10;
      const w = baseDelay * (2 - coherence);
      edges.push({ u: i, v: prev, w });
    }
    
    return edges;
  }

  /**
   * Record latency for tail analysis
   */
  recordLatency(latencyMs: number): void {
    this.latencyHistogram.recordValueMs(latencyMs);
  }

  /**
   * Decide and run task with resonance logic
   * Now uses Resonance Calculus-derived R for controller decisions
   */
  async decideAndRun<T>(hint: TaskHint, run: () => Promise<T>): Promise<T> {
    if (this.state.mode === 'observe') {
      return run(); // No intervention
    }

    // Critical tasks bypass controller
    if (hint.mustRunNow || hint.importance === 'critical') {
      return run();
    }

    // Use Resonance Calculus-derived R for controller decisions
    const features: Features = {
      R: this.state.R, // This is now computed from Resonance Calculus when enabled
      spectralEntropy: this.state.spectralEntropy,
      p99Risk: 0.1,
      sigmaTheta: 1 - this.state.R,
    };

    const act = this.controller.decide(features);

    // Apply actuation if in active mode
    if (this.state.mode === 'active' || this.state.mode === 'adaptive') {
      return applyActuation(act, run);
    }

    // Shadow mode: decide but don't act
    return run();
  }

  /**
   * Get current state
   */
  getState(): ResonanceState {
    return { ...this.state };
  }

  /**
   * Update mode
   */
  setMode(mode: ResonanceState['mode']): void {
    this.state.mode = mode;
    this.updateGlobalState();
  }

  /**
   * Update controller config
   */
  updateConfig(partial: Partial<ControllerConfig>): void {
    this.controller.updateConfig(partial);
  }

  /**
   * Reset core state
   */
  reset(): void {
    this.controller.reset();
    this.phases = [];
    this.lastUpdate = Date.now();
    this.coherenceHistory = [];
    this.latencyHistogram.reset();
  }

  /**
   * Enable/disable Resonance Calculus
   */
  setUseResonanceCalculus(enable: boolean): void {
    this.useResonanceCalculus = enable;
  }

  /**
   * Get latency histogram for external access
   */
  getLatencyHistogram(): LatencyHistogram {
    return this.latencyHistogram;
  }

  /**
   * Update global state for telemetry
   */
  private updateGlobalState(): void {
    // Store in global for metrics collectors
    if (typeof globalThis !== 'undefined') {
      (globalThis as any).__resonance_state = this.state;
    }
  }
}

// Export all components
export * from './types';
export * from './phase_estimator';
export * from './kuramoto';
export * from './pll';
export * from './controller_pi';
export * from './adaptive_coupling';
export * from './actuators';
export * from './calculus';
export * from './resonance_bridge';


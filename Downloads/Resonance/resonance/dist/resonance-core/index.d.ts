/**
 * Resonance Core
 * Main coordination engine combining all components
 */
import { BandController } from './controller_pi';
import { LatencyHistogram } from '../observability/histogram';
import type { ControllerConfig, TaskHint, Features, ResonanceState } from './types';
export declare class ResonanceCore {
    state: ResonanceState;
    controller: BandController;
    private phases;
    private lastUpdate;
    private coherenceHistory;
    private latencyHistogram;
    private maxHistorySize;
    private useResonanceCalculus;
    constructor(cfg: ControllerConfig);
    /**
     * Update global state with current phases
     * Now uses Resonance Calculus to compute R when enabled
     */
    update(phases: number[], spectralEntropy: number, p99Risk: number): Features;
    /**
     * Compute resonance using Resonance Calculus
     */
    private computeResonance;
    /**
     * Get tail samples from latency histogram
     */
    private getTailSamples;
    /**
     * Build dependency graph from phases
     * Each phase represents a node, edges represent coherence-modulated delays
     */
    private buildDependencyGraph;
    /**
     * Record latency for tail analysis
     */
    recordLatency(latencyMs: number): void;
    /**
     * Decide and run task with resonance logic
     * Now uses Resonance Calculus-derived R for controller decisions
     */
    decideAndRun<T>(hint: TaskHint, run: () => Promise<T>): Promise<T>;
    /**
     * Get current state
     */
    getState(): ResonanceState;
    /**
     * Update mode
     */
    setMode(mode: ResonanceState['mode']): void;
    /**
     * Update controller config
     */
    updateConfig(partial: Partial<ControllerConfig>): void;
    /**
     * Reset core state
     */
    reset(): void;
    /**
     * Enable/disable Resonance Calculus
     */
    setUseResonanceCalculus(enable: boolean): void;
    /**
     * Get latency histogram for external access
     */
    getLatencyHistogram(): LatencyHistogram;
    /**
     * Update global state for telemetry
     */
    private updateGlobalState;
}
export * from './types';
export * from './phase_estimator';
export * from './kuramoto';
export * from './pll';
export * from './controller_pi';
export * from './adaptive_coupling';
export * from './actuators';
export * from './calculus';
export * from './resonance_bridge';
//# sourceMappingURL=index.d.ts.map
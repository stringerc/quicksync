/**
 * OpenTelemetry Metrics Exporter for Resonance
 * Exports Resonance metrics to Prometheus via OTEL
 */
import { ResonanceState } from '../resonance-core/types';
export interface OtelExporterConfig {
    port?: number;
    endpoint?: string;
    enableConsole?: boolean;
}
export declare class OtelExporter {
    private meterProvider;
    private histogram;
    private server?;
    private resonanceR;
    private resonanceK;
    private spectralEntropy;
    private latencyP95;
    private latencyP99;
    private latencyP99_9;
    constructor(config?: OtelExporterConfig);
    /**
     * Update metrics from Resonance state
     */
    updateMetrics(state: ResonanceState): void;
    /**
     * Get Prometheus-formatted metrics
     */
    getMetrics(): Promise<string>;
    /**
     * Shutdown the exporter
     */
    shutdown(): Promise<void>;
}
//# sourceMappingURL=otel_exporter.d.ts.map
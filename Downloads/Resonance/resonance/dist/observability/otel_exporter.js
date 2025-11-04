"use strict";
/**
 * OpenTelemetry Metrics Exporter for Resonance
 * Exports Resonance metrics to Prometheus via OTEL
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.OtelExporter = void 0;
const sdk_metrics_1 = require("@opentelemetry/sdk-metrics");
const histogram_1 = require("./histogram");
class OtelExporter {
    constructor(config = {}) {
        // Initialize histogram
        this.histogram = new histogram_1.LatencyHistogram();
        // Setup console exporter for now
        const consoleExporter = new sdk_metrics_1.ConsoleMetricExporter();
        const readers = [new sdk_metrics_1.PeriodicExportingMetricReader({ exporter: consoleExporter })];
        // Create meter provider
        this.meterProvider = new sdk_metrics_1.MeterProvider({ readers });
        // Get meter
        const meter = this.meterProvider.getMeter('resonance', '1.0.0');
        // Register gauges
        this.resonanceR = meter.createObservableGauge('resonance_R', {
            description: 'Kuramoto order parameter R(t) [0-1]',
        });
        this.resonanceK = meter.createObservableGauge('resonance_K', {
            description: 'Adaptive coupling strength',
        });
        this.spectralEntropy = meter.createObservableGauge('resonance_spectral_entropy', {
            description: 'Spectral entropy H_s [0-1]',
        });
        // Histogram-based latency percentiles
        this.latencyP95 = meter.createObservableGauge('resonance_latency_p95_ms', {
            description: 'P95 latency in milliseconds',
        });
        this.latencyP99 = meter.createObservableGauge('resonance_latency_p99_ms', {
            description: 'P99 latency in milliseconds',
        });
        this.latencyP99_9 = meter.createObservableGauge('resonance_latency_p99_9_ms', {
            description: 'P99.9 latency in milliseconds',
        });
        console.log(`Observability initialized (console exporter)`);
    }
    /**
     * Update metrics from Resonance state
     */
    updateMetrics(state) {
        // Update observable gauges
        // Note: This is a simplified approach. In production, you'd use
        // ObservableCallback for real-time updates
        // Histogram update can be added when latency tracking is implemented
    }
    /**
     * Get Prometheus-formatted metrics
     */
    async getMetrics() {
        // This would typically be handled by the PrometheusExporter
        // Return empty string here as a placeholder
        return '';
    }
    /**
     * Shutdown the exporter
     */
    async shutdown() {
        await this.meterProvider.shutdown();
        if (this.server) {
            this.server.close();
        }
    }
}
exports.OtelExporter = OtelExporter;
//# sourceMappingURL=otel_exporter.js.map
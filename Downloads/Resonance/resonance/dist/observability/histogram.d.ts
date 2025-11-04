/**
 * HdrHistogram Wrapper
 * High-precision, low-overhead latency histograms
 *
 * TODO: Integrate with hdr-histogram-js
 * For now: Simple implementation
 */
export declare class LatencyHistogram {
    private buckets;
    private min;
    private max;
    private count;
    private sum;
    /**
     * Record a latency value in microseconds
     */
    recordValue(valueUs: number): void;
    /**
     * Record a latency value in milliseconds
     */
    recordValueMs(valueMs: number): void;
    /**
     * Get value at percentile
     * @param percentile Percentile (0-100)
     * @returns Value in microseconds
     */
    getValueAtPercentile(percentile: number): number;
    /**
     * Get percentiles (p95, p99, p99.9, p99.99) in milliseconds
     */
    getPercentiles(): {
        p95: number;
        p99: number;
        p99_9: number;
        p99_99: number;
        mean: number;
    };
    /**
     * Get count
     */
    getCount(): number;
    /**
     * Reset histogram
     */
    reset(): void;
    /**
     * Get bucket for logarithmic bucketing
     */
    private getBucket;
}
//# sourceMappingURL=histogram.d.ts.map
"use strict";
/**
 * HdrHistogram Wrapper
 * High-precision, low-overhead latency histograms
 *
 * TODO: Integrate with hdr-histogram-js
 * For now: Simple implementation
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.LatencyHistogram = void 0;
class LatencyHistogram {
    constructor() {
        this.buckets = new Map();
        this.min = Infinity;
        this.max = -Infinity;
        this.count = 0;
        this.sum = 0;
    }
    /**
     * Record a latency value in microseconds
     */
    recordValue(valueUs) {
        // Logarithmic bucketing (similar to HdrHistogram)
        const bucket = this.getBucket(valueUs);
        this.buckets.set(bucket, (this.buckets.get(bucket) || 0) + 1);
        this.count++;
        this.sum += valueUs;
        this.min = Math.min(this.min, valueUs);
        this.max = Math.max(this.max, valueUs);
    }
    /**
     * Record a latency value in milliseconds
     */
    recordValueMs(valueMs) {
        this.recordValue(valueMs * 1000);
    }
    /**
     * Get value at percentile
     * @param percentile Percentile (0-100)
     * @returns Value in microseconds
     */
    getValueAtPercentile(percentile) {
        if (this.count === 0)
            return 0;
        if (percentile >= 100)
            return this.max;
        if (percentile <= 0)
            return this.min;
        const target = Math.ceil((percentile / 100) * this.count);
        let cumulative = 0;
        const sortedBuckets = Array.from(this.buckets.entries()).sort((a, b) => a[0] - b[0]);
        for (const [bucket, count] of sortedBuckets) {
            cumulative += count;
            if (cumulative >= target) {
                return bucket;
            }
        }
        return this.max;
    }
    /**
     * Get percentiles (p95, p99, p99.9, p99.99) in milliseconds
     */
    getPercentiles() {
        return {
            p95: this.getValueAtPercentile(95) / 1000,
            p99: this.getValueAtPercentile(99) / 1000,
            p99_9: this.getValueAtPercentile(99.9) / 1000,
            p99_99: this.getValueAtPercentile(99.99) / 1000,
            mean: this.count > 0 ? this.sum / this.count / 1000 : 0,
        };
    }
    /**
     * Get count
     */
    getCount() {
        return this.count;
    }
    /**
     * Reset histogram
     */
    reset() {
        this.buckets.clear();
        this.min = Infinity;
        this.max = -Infinity;
        this.count = 0;
        this.sum = 0;
    }
    /**
     * Get bucket for logarithmic bucketing
     */
    getBucket(valueUs) {
        if (valueUs <= 1000) {
            // Linear bucketing for values <= 1ms (1us precision)
            return Math.round(valueUs);
        }
        else if (valueUs <= 1000000) {
            // Logarithmic bucketing for 1ms-1s (10us precision)
            return Math.round(valueUs / 10) * 10;
        }
        else {
            // Logarithmic bucketing for >1s (1ms precision)
            return Math.round(valueUs / 1000) * 1000;
        }
    }
}
exports.LatencyHistogram = LatencyHistogram;
//# sourceMappingURL=histogram.js.map
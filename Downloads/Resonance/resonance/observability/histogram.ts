/**
 * HdrHistogram Wrapper
 * High-precision, low-overhead latency histograms
 * 
 * TODO: Integrate with hdr-histogram-js
 * For now: Simple implementation
 */

export class LatencyHistogram {
  private buckets: Map<number, number> = new Map();
  private min = Infinity;
  private max = -Infinity;
  private count = 0;
  private sum = 0;

  /**
   * Record a latency value in microseconds
   */
  recordValue(valueUs: number): void {
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
  recordValueMs(valueMs: number): void {
    this.recordValue(valueMs * 1000);
  }

  /**
   * Get value at percentile
   * @param percentile Percentile (0-100)
   * @returns Value in microseconds
   */
  getValueAtPercentile(percentile: number): number {
    if (this.count === 0) return 0;
    if (percentile >= 100) return this.max;
    if (percentile <= 0) return this.min;

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
  getPercentiles(): { p95: number; p99: number; p99_9: number; p99_99: number; mean: number } {
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
  getCount(): number {
    return this.count;
  }

  /**
   * Reset histogram
   */
  reset(): void {
    this.buckets.clear();
    this.min = Infinity;
    this.max = -Infinity;
    this.count = 0;
    this.sum = 0;
  }

  /**
   * Get bucket for logarithmic bucketing
   */
  private getBucket(valueUs: number): number {
    if (valueUs <= 1000) {
      // Linear bucketing for values <= 1ms (1us precision)
      return Math.round(valueUs);
    } else if (valueUs <= 1000000) {
      // Logarithmic bucketing for 1ms-1s (10us precision)
      return Math.round(valueUs / 10) * 10;
    } else {
      // Logarithmic bucketing for >1s (1ms precision)
      return Math.round(valueUs / 1000) * 1000;
    }
  }
}


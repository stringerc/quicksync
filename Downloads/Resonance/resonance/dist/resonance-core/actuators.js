"use strict";
/**
 * Actuators
 * Apply controller decisions (delays, batching, coupling adjustments)
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ActuationLogger = void 0;
exports.applyActuation = applyActuation;
/**
 * Apply actuation to a task
 */
async function applyActuation(act, run) {
    // Apply micro-delay if needed
    if (act.microDelayMs && act.microDelayMs > 0) {
        await sleep(act.microDelayMs);
    }
    // Apply dither (small random variance)
    if (act.dither) {
        const ditherMs = act.dither > 0
            ? Math.random() * Math.abs(act.dither) * 5 // Positive: random delay
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
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
class ActuationLogger {
    constructor() {
        this.records = [];
        this.maxRecords = 1000;
    }
    log(record) {
        this.records.push(record);
        // Trim old records
        if (this.records.length > this.maxRecords) {
            this.records = this.records.slice(-this.maxRecords);
        }
    }
    getRecords() {
        return [...this.records];
    }
    getRecentCount(kind, windowMs = 60000) {
        const cutoff = Date.now() - windowMs;
        return this.records.filter((r) => r.kind === kind && r.timestamp >= cutoff).length;
    }
    clear() {
        this.records = [];
    }
}
exports.ActuationLogger = ActuationLogger;
//# sourceMappingURL=actuators.js.map
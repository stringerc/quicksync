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
export declare function applyActuation<T>(act: Actuation, run: () => Promise<T>): Promise<T>;
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
export declare class ActuationLogger {
    private records;
    private maxRecords;
    log(record: ActuationRecord): void;
    getRecords(): ActuationRecord[];
    getRecentCount(kind: ActuationRecord['kind'], windowMs?: number): number;
    clear(): void;
}
//# sourceMappingURL=actuators.d.ts.map
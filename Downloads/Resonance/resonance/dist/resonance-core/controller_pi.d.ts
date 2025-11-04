/**
 * PI Controller
 * Band control on R(t) with anti-herd and anti-freeze guardrails
 */
import { ControllerConfig, Features, Actuators } from './types';
export declare class BandController {
    private cfg;
    private kp;
    private ki;
    private integ;
    constructor(cfg: ControllerConfig, kp?: number, ki?: number);
    decide(feat: Features): Actuators;
    /**
     * Get configuration
     */
    getConfig(): ControllerConfig;
    /**
     * Update configuration
     */
    updateConfig(partial: Partial<ControllerConfig>): void;
    /**
     * Reset controller state
     */
    reset(): void;
}
//# sourceMappingURL=controller_pi.d.ts.map
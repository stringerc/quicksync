/**
 * Resonance Bridge
 * Bridges Resonance Calculus with the controller
 */
import { RateLatency, CoherenceSample } from '../resonance-math/resonance_calculus';
export interface TailSample {
    value: number;
    isExtreme: boolean;
}
export interface GraphEdge {
    u: number;
    v: number;
    w: number;
}
export interface ResonanceInputs {
    tHorizon: number;
    rateLatency: RateLatency;
    coherenceSamples: CoherenceSample[];
    tailSamples: TailSample[];
    tailThresholdQuantile: number;
    graphSize: number;
    edges: GraphEdge[];
}
export declare function computeResonanceFromInputs(inputs: ResonanceInputs): {
    R: number;
    lambdaRes: number;
    coherenceScore: number;
    tailHealthScore: number;
    timingScore: number;
    gpd?: {
        xi: number;
        sigma: number;
        threshold: number;
    };
    tailQuantiles?: {
        q99: number;
        q99_9: number;
    };
};
//# sourceMappingURL=resonance_bridge.d.ts.map
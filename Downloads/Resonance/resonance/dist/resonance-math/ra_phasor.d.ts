/**
 * RA-Phasor: Complex Phasor Algebra
 * Coherent superposition for phase planning
 */
export interface Phasor {
    a: number;
    phi: number;
}
/**
 * Add two phasors (vector addition in complex plane)
 * Result: coherent superposition
 */
export declare function add(z1: Phasor, z2: Phasor): Phasor;
/**
 * Subtract two phasors
 */
export declare function subtract(z1: Phasor, z2: Phasor): Phasor;
/**
 * Multiply phasor by scalar
 */
export declare function scalarMult(z: Phasor, c: number): Phasor;
/**
 * Conjugate phasor
 */
export declare function conjugate(z: Phasor): Phasor;
/**
 * Magnitude of phasor
 */
export declare function magnitude(z: Phasor): number;
/**
 * Phase of phasor
 */
export declare function phase(z: Phasor): number;
/**
 * Check if phases are aligned (within threshold)
 */
export declare function isAligned(z1: Phasor, z2: Phasor, threshold?: number): boolean;
/**
 * Zero phasor
 */
export declare function zero(): Phasor;
//# sourceMappingURL=ra_phasor.d.ts.map
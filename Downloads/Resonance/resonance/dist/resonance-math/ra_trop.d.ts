/**
 * RA-Trop: Tropical (Max-Plus) Semiring
 * For path costs, scheduling composition, critical-path reasoning
 *
 * Operations:
 * - ⊕ (add): max(a, b)
 * - ⊗ (multiply): a + b
 */
/**
 * Tropical addition (⊕): max
 */
export declare function tropAdd(a: number, b: number): number;
/**
 * Tropical multiplication (⊗): +
 */
export declare function tropMul(a: number, b: number): number;
/**
 * Tropical zero (additive identity): -Infinity
 */
export declare const TROP_ZERO: number;
/**
 * Tropical one (multiplicative identity): 0
 */
export declare const TROP_ONE = 0;
/**
 * Tropical matrix multiplication
 * For computing path costs through graphs
 */
export declare function tropMatrixMul(A: number[][], B: number[][]): number[][];
/**
 * Shortest path using max-plus semiring (Floyd-Warshall-like)
 * For path cost composition
 */
export declare function tropicalShortestPath(distance: number[][]): number[][];
/**
 * Critical path computation
 * Find maximum delay along any path
 */
export declare function criticalPath(graph: Array<[number, number, number]>, // [from, to, cost]
numNodes: number): {
    path: number[];
    cost: number;
};
//# sourceMappingURL=ra_trop.d.ts.map
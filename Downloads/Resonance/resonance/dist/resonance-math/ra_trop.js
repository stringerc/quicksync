"use strict";
/**
 * RA-Trop: Tropical (Max-Plus) Semiring
 * For path costs, scheduling composition, critical-path reasoning
 *
 * Operations:
 * - ⊕ (add): max(a, b)
 * - ⊗ (multiply): a + b
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.TROP_ONE = exports.TROP_ZERO = void 0;
exports.tropAdd = tropAdd;
exports.tropMul = tropMul;
exports.tropMatrixMul = tropMatrixMul;
exports.tropicalShortestPath = tropicalShortestPath;
exports.criticalPath = criticalPath;
/**
 * Tropical addition (⊕): max
 */
function tropAdd(a, b) {
    return Math.max(a, b);
}
/**
 * Tropical multiplication (⊗): +
 */
function tropMul(a, b) {
    return a + b;
}
/**
 * Tropical zero (additive identity): -Infinity
 */
exports.TROP_ZERO = -Infinity;
/**
 * Tropical one (multiplicative identity): 0
 */
exports.TROP_ONE = 0;
/**
 * Tropical matrix multiplication
 * For computing path costs through graphs
 */
function tropMatrixMul(A, B) {
    const n = A.length;
    const m = B[0].length;
    const result = new Array(n).fill(0).map(() => new Array(m).fill(exports.TROP_ZERO));
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < m; j++) {
            for (let k = 0; k < A[0].length; k++) {
                result[i][j] = tropAdd(result[i][j], tropMul(A[i][k], B[k][j]));
            }
        }
    }
    return result;
}
/**
 * Shortest path using max-plus semiring (Floyd-Warshall-like)
 * For path cost composition
 */
function tropicalShortestPath(distance) {
    const n = distance.length;
    const dist = distance.map((row) => [...row]);
    // Initialize with zero diagonal
    for (let i = 0; i < n; i++) {
        if (dist[i][i] === exports.TROP_ZERO || dist[i][i] === undefined) {
            dist[i][i] = exports.TROP_ONE;
        }
    }
    // Floyd-Warshall with tropical operations
    for (let k = 0; k < n; k++) {
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                dist[i][j] = tropAdd(dist[i][j], tropMul(dist[i][k], dist[k][j]));
            }
        }
    }
    return dist;
}
/**
 * Critical path computation
 * Find maximum delay along any path
 */
function criticalPath(graph, // [from, to, cost]
numNodes) {
    const distances = new Array(numNodes).fill(exports.TROP_ZERO);
    const predecessors = new Array(numNodes).fill(-1);
    // Bellman-Ford with tropical algebra
    for (let i = 0; i < numNodes - 1; i++) {
        for (const [u, v, w] of graph) {
            const newDist = tropAdd(distances[v], tropMul(distances[u], w));
            if (newDist > distances[v]) {
                distances[v] = newDist;
                predecessors[v] = u;
            }
        }
    }
    // Find node with maximum distance
    let maxNode = 0;
    let maxCost = exports.TROP_ZERO;
    for (let i = 0; i < numNodes; i++) {
        if (distances[i] > maxCost) {
            maxCost = distances[i];
            maxNode = i;
        }
    }
    // Reconstruct path
    const path = [];
    let current = maxNode;
    while (current !== -1) {
        path.unshift(current);
        current = predecessors[current];
    }
    return { path, cost: maxCost };
}
//# sourceMappingURL=ra_trop.js.map
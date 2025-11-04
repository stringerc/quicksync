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
export function tropAdd(a: number, b: number): number {
  return Math.max(a, b);
}

/**
 * Tropical multiplication (⊗): +
 */
export function tropMul(a: number, b: number): number {
  return a + b;
}

/**
 * Tropical zero (additive identity): -Infinity
 */
export const TROP_ZERO = -Infinity;

/**
 * Tropical one (multiplicative identity): 0
 */
export const TROP_ONE = 0;

/**
 * Tropical matrix multiplication
 * For computing path costs through graphs
 */
export function tropMatrixMul(A: number[][], B: number[][]): number[][] {
  const n = A.length;
  const m = B[0].length;
  const result: number[][] = new Array(n).fill(0).map(() => new Array(m).fill(TROP_ZERO));
  
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
export function tropicalShortestPath(distance: number[][]): number[][] {
  const n = distance.length;
  const dist = distance.map((row) => [...row]);
  
  // Initialize with zero diagonal
  for (let i = 0; i < n; i++) {
    if (dist[i][i] === TROP_ZERO || dist[i][i] === undefined) {
      dist[i][i] = TROP_ONE;
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
export function criticalPath(
  graph: Array<[number, number, number]>, // [from, to, cost]
  numNodes: number
): { path: number[]; cost: number } {
  const distances: number[] = new Array(numNodes).fill(TROP_ZERO);
  const predecessors: number[] = new Array(numNodes).fill(-1);
  
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
  let maxCost = TROP_ZERO;
  
  for (let i = 0; i < numNodes; i++) {
    if (distances[i] > maxCost) {
      maxCost = distances[i];
      maxNode = i;
    }
  }
  
  // Reconstruct path
  const path: number[] = [];
  let current = maxNode;
  
  while (current !== -1) {
    path.unshift(current);
    current = predecessors[current];
  }
  
  return { path, cost: maxCost };
}


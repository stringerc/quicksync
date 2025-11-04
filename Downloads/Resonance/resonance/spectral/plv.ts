/**
 * Pairwise Phase-Locking Value (PLV)
 * Measures synchronization between two oscillators
 */

/**
 * Compute PLV between two phase series
 * 
 * PLV = |mean(e^(j(θᵢ-θⱼ)))| over sliding windows
 * 
 * Interpretation:
 * - PLV ≈ 1: Strongly synchronized
 * - PLV ≈ 0: Independent, uncorrelated
 * 
 * @param phasesI Phase series for oscillator i
 * @param phasesJ Phase series for oscillator j
 * @returns PLV [0,1]
 */
export function plv(phasesI: number[], phasesJ: number[]): number {
  const N = Math.min(phasesI.length, phasesJ.length);
  
  if (N === 0) return 0;
  
  let re = 0;
  let im = 0;
  
  for (let n = 0; n < N; n++) {
    const d = phasesI[n] - phasesJ[n];
    re += Math.cos(d);
    im += Math.sin(d);
  }
  
  const magnitude = Math.hypot(re, im) / N;
  return Math.min(1, Math.max(0, magnitude));
}

/**
 * Compute PLV matrix for multiple oscillators
 * Returns sparse top-N edges for efficiency
 * 
 * @param phases Phase series for each oscillator [series][time]
 * @param topN Number of top edges to return
 * @returns Array of [i, j, PLV] tuples
 */
export function plvMatrix(
  phases: number[][],
  topN = 10
): Array<[number, number, number]> {
  const edges: Array<[number, number, number]> = [];
  
  for (let i = 0; i < phases.length; i++) {
    for (let j = i + 1; j < phases.length; j++) {
      const value = plv(phases[i], phases[j]);
      edges.push([i, j, value]);
    }
  }
  
  // Sort by PLV descending
  edges.sort((a, b) => b[2] - a[2]);
  
  return edges.slice(0, topN);
}

/**
 * Community detection based on PLV threshold
 * Groups oscillators with high mutual PLV
 */
export function detectCommunities(
  phases: number[][],
  threshold = 0.7
): number[][] {
  const n = phases.length;
  const adj: number[][] = new Array(n).fill(0).map(() => []);
  
  // Build adjacency graph
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const p = plv(phases[i], phases[j]);
      if (p >= threshold) {
        adj[i].push(j);
        adj[j].push(i);
      }
    }
  }
  
  // Find connected components
  const visited = new Set<number>();
  const communities: number[][] = [];
  
  for (let i = 0; i < n; i++) {
    if (visited.has(i)) continue;
    
    const community: number[] = [];
    const stack = [i];
    
    while (stack.length > 0) {
      const node = stack.pop()!;
      if (visited.has(node)) continue;
      
      visited.add(node);
      community.push(node);
      
      for (const neighbor of adj[node]) {
        if (!visited.has(neighbor)) {
          stack.push(neighbor);
        }
      }
    }
    
    if (community.length > 1) {
      communities.push(community);
    }
  }
  
  return communities;
}


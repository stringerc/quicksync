/**
 * RA-Phasor: Complex Phasor Algebra
 * Coherent superposition for phase planning
 */

export interface Phasor {
  a: number;  // Amplitude
  phi: number; // Phase (radians)
}

/**
 * Add two phasors (vector addition in complex plane)
 * Result: coherent superposition
 */
export function add(z1: Phasor, z2: Phasor): Phasor {
  const x1 = z1.a * Math.cos(z1.phi);
  const y1 = z1.a * Math.sin(z1.phi);
  const x2 = z2.a * Math.cos(z2.phi);
  const y2 = z2.a * Math.sin(z2.phi);
  
  const X = x1 + x2;
  const Y = y1 + y2;
  
  const a = Math.hypot(X, Y);
  const phi = Math.atan2(Y, X);
  
  return { a, phi };
}

/**
 * Subtract two phasors
 */
export function subtract(z1: Phasor, z2: Phasor): Phasor {
  const z2Neg: Phasor = { a: z2.a, phi: z2.phi + Math.PI };
  return add(z1, z2Neg);
}

/**
 * Multiply phasor by scalar
 */
export function scalarMult(z: Phasor, c: number): Phasor {
  return { a: z.a * c, phi: z.phi };
}

/**
 * Conjugate phasor
 */
export function conjugate(z: Phasor): Phasor {
  return { a: z.a, phi: -z.phi };
}

/**
 * Magnitude of phasor
 */
export function magnitude(z: Phasor): number {
  return z.a;
}

/**
 * Phase of phasor
 */
export function phase(z: Phasor): number {
  return z.phi;
}

/**
 * Check if phases are aligned (within threshold)
 */
export function isAligned(z1: Phasor, z2: Phasor, threshold = 0.1): boolean {
  const phaseDiff = normalizeAngle(z1.phi - z2.phi);
  return Math.abs(phaseDiff) < threshold;
}

/**
 * Normalize angle to [-π, π]
 */
function normalizeAngle(a: number): number {
  while (a > Math.PI) a -= 2 * Math.PI;
  while (a < -Math.PI) a += 2 * Math.PI;
  return a;
}

/**
 * Zero phasor
 */
export function zero(): Phasor {
  return { a: 0, phi: 0 };
}


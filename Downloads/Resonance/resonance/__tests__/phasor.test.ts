import { add, magnitude, phase, scalarMult, isAligned } from '../resonance-math/ra_phasor';

describe('Phasor Algebra', () => {
  test('add: coherent addition', () => {
    const z1 = { a: 1, phi: 0 };
    const z2 = { a: 1, phi: 0 };
    const result = add(z1, z2);
    expect(magnitude(result)).toBeCloseTo(2, 3);
    expect(phase(result)).toBeCloseTo(0, 3);
  });

  test('add: destructive interference', () => {
    const z1 = { a: 1, phi: 0 };
    const z2 = { a: 1, phi: Math.PI };
    const result = add(z1, z2);
    expect(magnitude(result)).toBeCloseTo(0, 3);
  });

  test('scalarMult', () => {
    const z = { a: 5, phi: Math.PI / 4 };
    const result = scalarMult(z, 2);
    expect(magnitude(result)).toBe(10);
    expect(phase(result)).toBeCloseTo(Math.PI / 4, 3);
  });

  test('isAligned', () => {
    const z1 = { a: 1, phi: 0 };
    const z2 = { a: 1, phi: 0.05 };
    expect(isAligned(z1, z2, 0.1)).toBe(true);
    expect(isAligned(z1, z2, 0.01)).toBe(false);
  });
});


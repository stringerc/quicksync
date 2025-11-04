/**
 * Kuramoto Tests
 */

import { orderParameter, phaseDispersion } from '../resonance-core/kuramoto';

describe('Kuramoto', () => {
  test('orderParameter: fully synchronized', () => {
    const phases = [0, 0, 0, 0];
    const { R } = orderParameter(phases);
    expect(R).toBeCloseTo(1.0, 3);
  });

  test('orderParameter: fully desynchronized', () => {
    const phases = [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2];
    const { R } = orderParameter(phases);
    expect(R).toBeCloseTo(0.0, 1);
  });

  test('phaseDispersion: inverse of R', () => {
    const phases = [0, 0.1, 0.2, 0.3];
    const { R } = orderParameter(phases);
    const dispersion = phaseDispersion(phases);
    expect(dispersion).toBeCloseTo(1 - R, 3);
  });
});


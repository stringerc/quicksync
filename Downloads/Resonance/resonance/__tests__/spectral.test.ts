import { spectralEntropy, getEntropyState, isEntropyInBand } from '../spectral/spectral_entropy';
import { plv } from '../spectral/plv';

describe('Spectral', () => {
  test('spectralEntropy: uniform distribution', () => {
    const mag = new Array(10).fill(1.0);
    const ent = spectralEntropy(mag);
    expect(ent).toBeCloseTo(1.0, 3);
  });

  test('spectralEntropy: single peak', () => {
    const mag = [10, 0, 0, 0, 0];
    const ent = spectralEntropy(mag);
    expect(ent).toBeLessThan(0.5);
  });

  test('getEntropyState', () => {
    expect(getEntropyState(0.1)).toBe('too_rigid');
    expect(getEntropyState(0.9)).toBe('too_noisy');
    expect(getEntropyState(0.5)).toBe('healthy');
  });

  test('plv: synchronized', () => {
    const phases1 = [0, 0, 0, 0];
    const phases2 = [0, 0, 0, 0];
    const value = plv(phases1, phases2);
    expect(value).toBeCloseTo(1.0, 3);
  });

  test('plv: constant phase difference', () => {
    const phases1 = [0, 0, 0, 0];
    const phases2 = [Math.PI, Math.PI, Math.PI, Math.PI];
    const value = plv(phases1, phases2);
    // Constant phase difference = perfectly synchronized (but anti-phase)
    expect(value).toBeCloseTo(1.0, 3);
  });

  test('plv: random desynchronized', () => {
    const phases1 = [0, 0.1, 0.2, 0.3];
    const phases2 = [1.5, 2.0, 1.0, 2.5];
    const value = plv(phases1, phases2);
    expect(value).toBeLessThan(1.0); // Not perfectly synchronized
    expect(value).toBeGreaterThan(0.0);
  });
});


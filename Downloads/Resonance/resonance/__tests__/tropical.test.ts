import { tropAdd, tropMul, TROP_ZERO, TROP_ONE, criticalPath } from '../resonance-math/ra_trop';

describe('Tropical Algebra', () => {
  test('tropAdd: max', () => {
    expect(tropAdd(5, 3)).toBe(5);
    expect(tropAdd(3, 5)).toBe(5);
    expect(tropAdd(5, 5)).toBe(5);
  });

  test('tropMul: addition', () => {
    expect(tropMul(5, 3)).toBe(8);
    expect(tropMul(0, 10)).toBe(10);
  });

  test('identities', () => {
    expect(tropAdd(5, TROP_ZERO)).toBe(5);
    expect(tropMul(5, TROP_ONE)).toBe(5);
  });

  test('criticalPath', () => {
    const graph: Array<[number, number, number]> = [
      [0, 1, 10],
      [1, 2, 20],
      [0, 2, 50],
    ];
    const result = criticalPath(graph, 3);
    expect(result.path).toBeDefined();
    expect(result.path.length).toBeGreaterThan(0);
  });
});


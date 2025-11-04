import { ResonanceCalculus, backlogBound, delayBound, maxPlusConvolve } from '../resonance-core/calculus';

describe('Resonance Calculus', () => {
  test('backlogBound: no backlog', () => {
    const arrivals = [10, 10, 10, 10];
    const services = [10, 10, 10, 10];
    const bound = backlogBound(arrivals, services);
    expect(bound).toBe(0);
  });

  test('backlogBound: build up', () => {
    const arrivals = [15, 15, 15, 15];
    const services = [10, 10, 10, 10];
    const bound = backlogBound(arrivals, services);
    expect(bound).toBeGreaterThan(0);
  });

  test('maxPlusConvolve', () => {
    const alpha = [1, 2, 3];
    const beta = [1, 2, 3];
    const result = maxPlusConvolve(alpha, beta);
    expect(result.length).toBe(3);
  });

  test('calculus decide: healthy backlog', () => {
    const calc = new ResonanceCalculus();
    
    // Simulate some arrivals
    for (let i = 0; i < 10; i++) {
      calc.recordArrival();
      calc.recordCompletion();
    }
    
    const decision = calc.decide(100);
    expect(decision.action).toBeDefined();
    expect(decision.boundMs).toBeGreaterThanOrEqual(0);
  });
});


import { describe, expect, it } from 'vitest';
import { calculateRebalancingPlan } from './rebalancing';

describe('calculateRebalancingPlan', () => {
  it('uses a new contribution to fill the largest target gaps first proportionally', () => {
    const plan = calculateRebalancingPlan({
      currentValuesKrw: {
        growth: 8_000_000,
        income: 0,
        defensive: 0,
        cash: 2_000_000,
      },
      targetWeightsPct: {
        growth: 55,
        income: 15,
        defensive: 20,
        cash: 10,
      },
      contributionKrw: 1_000_000,
    });

    expect(plan.currentTotalKrw).toBe(10_000_000);
    expect(plan.projectedTotalKrw).toBe(11_000_000);
    expect(plan.items.find((item) => item.category === 'growth')?.suggestedContributionKrw).toBe(0);
    expect(plan.items.find((item) => item.category === 'income')?.suggestedContributionKrw).toBe(428_571);
    expect(plan.items.find((item) => item.category === 'defensive')?.suggestedContributionKrw).toBe(571_429);
    expect(plan.items.find((item) => item.category === 'cash')?.suggestedContributionKrw).toBe(0);
  });

  it('follows target weights for a new portfolio and preserves the exact total', () => {
    const plan = calculateRebalancingPlan({
      currentValuesKrw: {
        growth: 0,
        income: 0,
        defensive: 0,
        cash: 0,
      },
      targetWeightsPct: {
        growth: 50,
        income: 15,
        defensive: 20,
        cash: 15,
      },
      contributionKrw: 500_001,
    });

    expect(plan.items.map((item) => item.suggestedContributionKrw)).toEqual([
      250_001,
      75_000,
      100_000,
      75_000,
    ]);
    expect(plan.items.reduce(
      (total, item) => total + item.suggestedContributionKrw,
      0,
    )).toBe(500_001);
  });

  it('never emits negative suggestions for an overweight category', () => {
    const plan = calculateRebalancingPlan({
      currentValuesKrw: {
        growth: 9_000_000,
        income: 0,
        defensive: 500_000,
        cash: 500_000,
      },
      targetWeightsPct: {
        growth: 50,
        income: 10,
        defensive: 25,
        cash: 15,
      },
      contributionKrw: 600_000,
    });

    expect(plan.items.every((item) => item.suggestedContributionKrw >= 0)).toBe(true);
    expect(plan.items.find((item) => item.category === 'growth')?.suggestedContributionKrw).toBe(0);
  });
});

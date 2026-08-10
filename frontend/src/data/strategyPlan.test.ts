import { describe, expect, it } from 'vitest';
import type { GoalSnapshot } from './goalSnapshots';
import { resolveStrategyPlan } from './strategyPlan';
import { DEFAULT_USER_PREFERENCES } from './userPreferences';

const activeGoal: GoalSnapshot = {
  id: 'goal-one',
  name: '내 집 마련',
  savedAt: '2026-08-10T00:00:00Z',
  inputs: {
    currentAssetsKrw: 20_000_000,
    targetAmountKrw: 500_000_000,
    monthlyContributionKrw: 700_000,
    investmentYears: 25,
    annualReturnRatePct: 7,
    annualInflationRatePct: 3,
    targetAmountInTodayMoney: true,
    annualContributionGrowthRatePct: 5,
  },
  summary: {
    projectedValue: '410000000',
    achievementRatePct: '82',
    requiredMonthlyContribution: '900000',
    effectiveTargetAmount: '1046888987',
    projectedValueInTodayMoney: '195800000',
  },
};

describe('resolveStrategyPlan', () => {
  it('maps an applied goal to lump-sum strategy inputs', () => {
    const plan = resolveStrategyPlan(DEFAULT_USER_PREFERENCES, activeGoal, 'active_goal');

    expect(plan.source).toBe('active_goal');
    expect(plan.request).toEqual(expect.objectContaining({
      goal: 'lump_sum',
      horizon_years: 25,
      monthly_amount_krw: 700_000,
    }));
  });

  it('preserves the base preferences when the user opts out', () => {
    const plan = resolveStrategyPlan(DEFAULT_USER_PREFERENCES, activeGoal, 'preferences');

    expect(plan.source).toBe('preferences');
    expect(plan.request).toEqual(expect.objectContaining({
      goal: 'retirement',
      horizon_years: 30,
      monthly_amount_krw: 500_000,
    }));
  });

  it('falls back safely when the active goal is below the strategy minimum', () => {
    const plan = resolveStrategyPlan(DEFAULT_USER_PREFERENCES, {
      ...activeGoal,
      inputs: { ...activeGoal.inputs, monthlyContributionKrw: 0 },
    }, 'active_goal');

    expect(plan.source).toBe('preferences');
    expect(plan.activeGoalIssue).toBe('monthly_minimum');
    expect(plan.request.monthly_amount_krw).toBe(500_000);
  });
});

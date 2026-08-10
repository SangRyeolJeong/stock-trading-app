import type { GoalSnapshot, GoalStrategyMode } from './goalSnapshots';
import type { UserPreferences } from './userPreferences';
import type { StrategyRequest } from '../types/api';

export interface ResolvedStrategyPlan {
  request: StrategyRequest;
  source: 'active_goal' | 'preferences';
  activeGoalIssue: 'monthly_minimum' | null;
}

export function resolveStrategyPlan(
  preferences: UserPreferences,
  activeGoal: GoalSnapshot | null,
  mode: GoalStrategyMode,
): ResolvedStrategyPlan {
  const baseRequest: StrategyRequest = {
    goal: preferences.strategyGoal,
    horizon_years: preferences.investmentYears,
    monthly_amount_krw: preferences.monthlyInvestmentKrw,
    risk_profile: preferences.riskProfile,
    liquidity_preference: preferences.liquidityPreference,
    fee_sensitivity: preferences.feeSensitivity,
    income_preference: preferences.incomePreference,
    tax_efficiency_priority: true,
  };
  if (mode !== 'active_goal' || !activeGoal) {
    return { request: baseRequest, source: 'preferences', activeGoalIssue: null };
  }
  if (activeGoal.inputs.monthlyContributionKrw < 10_000) {
    return {
      request: baseRequest,
      source: 'preferences',
      activeGoalIssue: 'monthly_minimum',
    };
  }
  return {
    request: {
      ...baseRequest,
      goal: 'lump_sum',
      horizon_years: activeGoal.inputs.investmentYears,
      monthly_amount_krw: activeGoal.inputs.monthlyContributionKrw,
    },
    source: 'active_goal',
    activeGoalIssue: null,
  };
}

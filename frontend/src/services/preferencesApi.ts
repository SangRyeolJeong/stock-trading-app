import type { UserPreferences } from '../data/userPreferences';
import { apiClient } from './apiClient';

interface UserPreferencesResponse {
  display_name: string;
  annual_salary_krw: number;
  monthly_investment_krw: number;
  investment_years: number;
  annual_return_rate_pct: number;
  withdrawal_age: number;
  strategy_goal: UserPreferences['strategyGoal'];
  risk_profile: UserPreferences['riskProfile'];
  liquidity_preference: boolean;
  fee_sensitivity: boolean;
  income_preference: boolean;
  updated_at: string;
}

function fromApi(response: UserPreferencesResponse): UserPreferences {
  return {
    displayName: response.display_name,
    annualSalaryKrw: response.annual_salary_krw,
    monthlyInvestmentKrw: response.monthly_investment_krw,
    investmentYears: response.investment_years,
    annualReturnRatePct: response.annual_return_rate_pct,
    withdrawalAge: response.withdrawal_age,
    strategyGoal: response.strategy_goal,
    riskProfile: response.risk_profile,
    liquidityPreference: response.liquidity_preference,
    feeSensitivity: response.fee_sensitivity,
    incomePreference: response.income_preference,
  };
}

function toApi(preferences: UserPreferences) {
  return {
    display_name: preferences.displayName,
    annual_salary_krw: preferences.annualSalaryKrw,
    monthly_investment_krw: preferences.monthlyInvestmentKrw,
    investment_years: preferences.investmentYears,
    annual_return_rate_pct: preferences.annualReturnRatePct,
    withdrawal_age: preferences.withdrawalAge,
    strategy_goal: preferences.strategyGoal,
    risk_profile: preferences.riskProfile,
    liquidity_preference: preferences.liquidityPreference,
    fee_sensitivity: preferences.feeSensitivity,
    income_preference: preferences.incomePreference,
  };
}

export const preferencesApi = {
  async get() {
    return fromApi(
      await apiClient<UserPreferencesResponse>('/api/v1/me/preferences'),
    );
  },
  async save(preferences: UserPreferences) {
    return fromApi(
      await apiClient<UserPreferencesResponse>('/api/v1/me/preferences', {
        method: 'PUT',
        body: JSON.stringify(toApi(preferences)),
      }),
    );
  },
};

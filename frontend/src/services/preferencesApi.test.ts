import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_USER_PREFERENCES } from '../data/userPreferences';
import { preferencesApi } from './preferencesApi';

const apiClientMock = vi.hoisted(() => vi.fn());

vi.mock('./apiClient', () => ({
  apiClient: apiClientMock,
}));

const response = {
  display_name: '김모아',
  annual_salary_krw: 45_000_000,
  monthly_investment_krw: 500_000,
  investment_years: 30,
  annual_return_rate_pct: 7,
  withdrawal_age: 60,
  strategy_goal: 'retirement',
  risk_profile: 'growth',
  liquidity_preference: true,
  fee_sensitivity: true,
  income_preference: false,
  updated_at: '2026-07-29T00:00:00Z',
};

describe('preferencesApi', () => {
  beforeEach(() => {
    apiClientMock.mockResolvedValue(response);
  });

  it('maps the server response to frontend preferences', async () => {
    await expect(preferencesApi.get()).resolves.toEqual(
      DEFAULT_USER_PREFERENCES,
    );
    expect(apiClientMock).toHaveBeenCalledWith('/api/v1/me/preferences');
  });

  it('sends the complete preference payload to the current-user endpoint', async () => {
    await preferencesApi.save(DEFAULT_USER_PREFERENCES);

    expect(apiClientMock).toHaveBeenCalledWith('/api/v1/me/preferences', {
      method: 'PUT',
      body: JSON.stringify({
        display_name: '김모아',
        annual_salary_krw: 45_000_000,
        monthly_investment_krw: 500_000,
        investment_years: 30,
        annual_return_rate_pct: 7,
        withdrawal_age: 60,
        strategy_goal: 'retirement',
        risk_profile: 'growth',
        liquidity_preference: true,
        fee_sensitivity: true,
        income_preference: false,
      }),
    });
  });
});

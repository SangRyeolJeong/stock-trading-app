import { beforeEach, describe, expect, it, vi } from 'vitest';
import { goalApi } from './goalApi';

const apiClientMock = vi.hoisted(() => vi.fn());

vi.mock('./apiClient', () => ({
  apiClient: apiClientMock,
}));

describe('goalApi', () => {
  beforeEach(() => {
    apiClientMock.mockResolvedValue({});
  });

  it('sends every deterministic goal assumption to the simulation endpoint', async () => {
    const request = {
      current_assets_krw: 10_000_000,
      target_amount_krw: 300_000_000,
      monthly_contribution_krw: 500_000,
      investment_years: 20,
      annual_return_rate_pct: 7,
    };

    await goalApi.simulate(request);

    expect(apiClientMock).toHaveBeenCalledWith('/api/v1/goals/simulate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  });
});

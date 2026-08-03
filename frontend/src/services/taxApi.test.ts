import { beforeEach, describe, expect, it, vi } from 'vitest';
import { taxApi } from './taxApi';

const apiClientMock = vi.hoisted(() => vi.fn());

vi.mock('./apiClient', () => ({
  apiClient: apiClientMock,
}));

describe('taxApi', () => {
  beforeEach(() => {
    apiClientMock.mockResolvedValue({});
  });

  it('sends pension start assumptions to the deterministic endpoint', async () => {
    const request = {
      annual_salary_krw: 45_000_000,
      current_age: 30,
      withdrawal_age: 60,
      monthly_contribution_krw: 500_000,
      annual_return_rate_pct: 7,
      delay_years: 5,
    };

    await taxApi.comparePensionStart(request);

    expect(apiClientMock).toHaveBeenCalledWith('/api/v1/tax/pension-start', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  });
});

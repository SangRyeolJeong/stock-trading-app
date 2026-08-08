import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createGoalSnapshot,
  saveGoalSnapshot,
  setActiveGoalSnapshot,
} from '../data/goalSnapshots';
import { resetUserPreferences } from '../data/userPreferences';
import { StrategyPage } from './StrategyPage';

const recommendMock = vi.hoisted(() => vi.fn());

vi.mock('../services/strategyApi', () => ({
  strategyApi: { recommend: recommendMock },
}));

const recommendation = {
  engine_version: 'STRATEGY-2026.07',
  strategy_id: 'lump_sum-growth-long',
  title: '목표시점 맞춤 자산배분',
  summary: '목표에 맞춘 전략입니다.',
  score: 91,
  allocation: {},
  allocations: [],
  reason_codes: [],
  reasons: [],
  rationale: [],
  risk_summary: {
    level: 'growth' as const,
    equity_weight_pct: 80,
    defensive_weight_pct: 15,
    liquidity_weight_pct: 5,
    volatility_note: '변동성 안내',
  },
  action_steps: [],
  warnings: [],
  assumptions: [],
  disclaimer: '교육용입니다.',
};

function saveActiveGoal(monthlyContributionKrw = 700_000) {
  const snapshot = createGoalSnapshot({
    currentAssetsKrw: 20_000_000,
    targetAmountKrw: 500_000_000,
    monthlyContributionKrw,
    investmentYears: 25,
    annualReturnRatePct: 7,
    annualInflationRatePct: 3,
    targetAmountInTodayMoney: true,
    annualContributionGrowthRatePct: 5,
  }, {
    projectedValue: '410000000',
    achievementRatePct: '82',
    requiredMonthlyContribution: '900000',
    effectiveTargetAmount: '1046888987',
    projectedValueInTodayMoney: '195800000',
  }, new Date('2026-08-08T00:00:00Z'), '내 집 마련');
  saveGoalSnapshot(snapshot);
  setActiveGoalSnapshot(snapshot.id);
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <StrategyPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('StrategyPage active goal integration', () => {
  beforeEach(() => {
    window.localStorage.clear();
    resetUserPreferences();
    recommendMock.mockReset();
    recommendMock.mockResolvedValue(recommendation);
  });

  it('uses the active goal horizon, monthly amount and lump-sum purpose by default', async () => {
    const user = userEvent.setup();
    saveActiveGoal();
    renderPage();

    await waitFor(() => expect(recommendMock).toHaveBeenCalledWith(expect.objectContaining({
      goal: 'lump_sum',
      horizon_years: 25,
      monthly_amount_krw: 700_000,
    })));
    expect(screen.getByText('목표 계산기 조건 반영')).toBeInTheDocument();
    expect(screen.getByRole('slider')).toBeDisabled();
    expect(screen.getByRole('spinbutton')).toBeDisabled();

    await user.click(screen.getByRole('button', { name: '내 기본 설정 사용' }));
    await waitFor(() => expect(recommendMock).toHaveBeenLastCalledWith(expect.objectContaining({
      goal: 'retirement',
      horizon_years: 30,
      monthly_amount_krw: 500_000,
    })));
    expect(screen.queryByText('목표 계산기 조건 반영')).not.toBeInTheDocument();
    expect(screen.getByRole('slider')).toBeEnabled();
  });

  it('keeps the base strategy when the active goal has no allocatable monthly amount', async () => {
    saveActiveGoal(0);
    renderPage();

    await waitFor(() => expect(recommendMock).toHaveBeenCalledWith(expect.objectContaining({
      goal: 'retirement',
      horizon_years: 30,
      monthly_amount_krw: 500_000,
    })));
    expect(screen.getByRole('button', { name: '목표 수정' })).toBeInTheDocument();
    expect(screen.getByText(/월 1만원 이상 필요/)).toBeInTheDocument();
  });
});

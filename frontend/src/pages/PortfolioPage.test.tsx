import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastContext } from '../app/toast';
import {
  createGoalSnapshot,
  saveGoalSnapshot,
  setActiveGoalSnapshot,
  setGoalStrategyMode,
} from '../data/goalSnapshots';
import { resetUserPreferences } from '../data/userPreferences';
import { PortfolioPage } from './PortfolioPage';

const { getExchangeRateMock, getOrdersMock, getPortfolioSummaryMock, getQuoteMock,
  recommendMock } = vi.hoisted(() => ({
  getExchangeRateMock: vi.fn(),
  getOrdersMock: vi.fn(),
  getPortfolioSummaryMock: vi.fn(),
  getQuoteMock: vi.fn(),
  recommendMock: vi.fn(),
}));

vi.mock('../services/marketApi', () => ({
  marketApi: {
    getExchangeRate: getExchangeRateMock,
    getQuote: getQuoteMock,
  },
}));
vi.mock('../services/paperApi', () => ({
  paperApi: {
    cancelOrder: vi.fn(),
    getOrders: getOrdersMock,
    getPortfolioSummary: getPortfolioSummaryMock,
  },
}));
vi.mock('../services/strategyApi', () => ({
  strategyApi: { recommend: recommendMock },
}));

function saveActiveGoal() {
  const snapshot = createGoalSnapshot({
    currentAssetsKrw: 20_000_000,
    targetAmountKrw: 500_000_000,
    monthlyContributionKrw: 700_000,
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
  }, new Date('2026-08-10T00:00:00Z'), '내 집 마련');
  saveGoalSnapshot(snapshot);
  setActiveGoalSnapshot(snapshot.id);
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <ToastContext.Provider value={{ showToast: vi.fn() }}>
        <MemoryRouter>
          <PortfolioPage />
        </MemoryRouter>
      </ToastContext.Provider>
    </QueryClientProvider>,
  );
}

describe('PortfolioPage active goal rebalancing', () => {
  beforeEach(() => {
    window.localStorage.clear();
    resetUserPreferences();
    vi.clearAllMocks();
    getPortfolioSummaryMock.mockResolvedValue({
      account_id: 'demo',
      currencies: [{
        currency: 'KRW',
        cash: '10000000',
        positions_value: '0',
        total_value: '10000000',
        unrealized_pnl: '0',
        realized_pnl: '0',
      }],
      positions: [],
      as_of: '2026-08-10T00:00:00Z',
    });
    getOrdersMock.mockResolvedValue([]);
    getExchangeRateMock.mockResolvedValue({
      base_currency: 'USD',
      quote_currency: 'KRW',
      rate: '1400',
      source: 'mock',
      delayed: false,
      as_of: '2026-08-10T00:00:00Z',
    });
    getQuoteMock.mockImplementation((symbol: string) => Promise.resolve({
      symbol,
      name: symbol,
      currency: 'USD',
      price: '100',
      change: '0',
      change_rate: '0',
      market_open: true,
      delayed: false,
      as_of: '2026-08-10T00:00:00Z',
    }));
    recommendMock.mockResolvedValue({
      engine_version: 'STRATEGY-2026.07',
      strategy_id: 'lump_sum-growth-long',
      title: '목표시점 맞춤 자산배분',
      summary: '목표에 맞춘 전략입니다.',
      score: 91,
      allocation: {},
      allocations: [
        { asset_class: 'growth', label: '성장', weight_pct: 55, monthly_amount_krw: 0, account_type: 'isa', product_example: 'QQQM', role: '성장' },
        { asset_class: 'income', label: '인컴', weight_pct: 15, monthly_amount_krw: 0, account_type: 'isa', product_example: 'DGRO', role: '인컴' },
        { asset_class: 'defensive', label: '방어', weight_pct: 20, monthly_amount_krw: 0, account_type: 'isa', product_example: 'SGOV', role: '방어' },
        { asset_class: 'cash', label: '현금', weight_pct: 10, monthly_amount_krw: 0, account_type: 'cash', product_example: 'CMA', role: '현금' },
      ],
      reason_codes: [],
      reasons: [],
      rationale: [],
      risk_summary: { level: 'growth', equity_weight_pct: 70, defensive_weight_pct: 20, liquidity_weight_pct: 10, volatility_note: '변동성 안내' },
      action_steps: [],
      warnings: [],
      assumptions: [],
      disclaimer: '교육용입니다.',
    });
  });

  it('uses the active goal amount and horizon for strategy and rebalancing', async () => {
    saveActiveGoal();
    renderPage();

    await waitFor(() => expect(recommendMock).toHaveBeenCalledWith(expect.objectContaining({
      goal: 'lump_sum',
      horizon_years: 25,
      monthly_amount_krw: 700_000,
    })));
    expect(screen.getByText('진행 목표 조건으로 계산 중')).toBeInTheDocument();
    expect(screen.getByText(/25년 · 첫해 월/)).toHaveTextContent('₩700,000');
    expect(await screen.findByText(/다음 ₩700,000/)).toBeInTheDocument();
  });

  it('honors the strategy preference mode shared from the strategy page', async () => {
    saveActiveGoal();
    setGoalStrategyMode('preferences');
    renderPage();

    await waitFor(() => expect(recommendMock).toHaveBeenCalledWith(expect.objectContaining({
      goal: 'retirement',
      horizon_years: 30,
      monthly_amount_krw: 500_000,
    })));
    expect(screen.getByText('내 기본 전략 설정으로 계산 중')).toBeInTheDocument();
    expect(await screen.findByText(/다음 ₩500,000/)).toBeInTheDocument();
  });
});

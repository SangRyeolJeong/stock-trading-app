import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastContext } from '../app/toast';
import {
  createGoalSnapshot,
  saveGoalSnapshot,
  type GoalScenarioInputs,
} from '../data/goalSnapshots';
import type { GoalSimulationResponse } from '../types/api';
import { GoalSimulatorPage } from './GoalSimulatorPage';

const simulateMock = vi.hoisted(() => vi.fn());

vi.mock('../services/goalApi', () => ({
  goalApi: { simulate: simulateMock },
}));

const simulation: GoalSimulationResponse = {
  engine_version: 'GOAL-2026.08.2',
  projected_value: '284669799',
  projected_value_in_today_money: '191579000',
  effective_target_amount_krw: '445784200',
  total_contributed_principal: '130000000',
  investment_gain: '154669799',
  target_gap: '15330201',
  target_surplus: '0',
  target_achievement_rate_pct: '94.9',
  required_monthly_contribution: '531163',
  additional_monthly_contribution: '31163',
  required_monthly_within_supported_limit: true,
  milestones: [{
    year: 20,
    contributed_principal: '130000000',
    annual_contribution: '6000000',
    projected_value: '284669799',
    target_achievement_rate_pct: '94.9',
  }],
  sensitivity: [
    { kind: 'lower', annual_return_rate_pct: '5', projected_value: '220000000', target_achievement_rate_pct: '73.3' },
    { kind: 'base', annual_return_rate_pct: '7', projected_value: '284669799', target_achievement_rate_pct: '94.9' },
    { kind: 'higher', annual_return_rate_pct: '9', projected_value: '370000000', target_achievement_rate_pct: '123.3' },
  ],
  assumptions: [],
  formula: '연말 납입 복리 계산',
  disclaimer: '교육용 계산입니다.',
};

function saveScenario(
  inputs: GoalScenarioInputs,
  summary: {
    projectedValue: string;
    achievementRatePct: string;
    requiredMonthlyContribution: string;
    effectiveTargetAmount: string;
    projectedValueInTodayMoney: string;
  },
  savedAt: string,
  name = '',
) {
  saveGoalSnapshot(createGoalSnapshot(inputs, summary, new Date(savedAt), name));
}

function renderPage(showToast = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <ToastContext.Provider value={{ showToast }}>
        <MemoryRouter>
          <GoalSimulatorPage />
        </MemoryRouter>
      </ToastContext.Provider>
    </QueryClientProvider>,
  );
  return { showToast };
}

describe('GoalSimulatorPage saved scenario comparison', () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.history.replaceState(null, '', '/goal-simulator');
    simulateMock.mockResolvedValue(simulation);
    saveScenario({
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
    }, '2026-08-02T00:00:00Z', '장기 목표');
    saveScenario({
      currentAssetsKrw: 10_000_000,
      targetAmountKrw: 300_000_000,
      monthlyContributionKrw: 500_000,
      investmentYears: 20,
      annualReturnRatePct: 5,
      annualInflationRatePct: 2,
      targetAmountInTodayMoney: false,
      annualContributionGrowthRatePct: 0,
    }, {
      projectedValue: '250000000',
      achievementRatePct: '83.3',
      requiredMonthlyContribution: '620000',
      effectiveTargetAmount: '300000000',
      projectedValueInTodayMoney: '168200000',
    }, '2026-08-03T00:00:00Z', '기본 목표');
  });

  it('renders two selected snapshots side by side and clears the comparison', async () => {
    const user = userEvent.setup();
    renderPage();

    const compareButtons = screen.getAllByRole('button', { name: '비교' });
    await user.click(compareButtons[0]);
    await user.click(compareButtons[1]);

    const comparison = screen.getByText('저장 시나리오 비교').closest('.goal-comparison');
    expect(comparison).not.toBeNull();
    const table = within(comparison as HTMLElement).getByRole('table');
    expect(within(table).getByText('기본 목표')).toBeInTheDocument();
    expect(within(table).getByText('장기 목표')).toBeInTheDocument();
    expect(within(table).getByText('2.50억원')).toBeInTheDocument();
    expect(within(table).getByText('4.10억원')).toBeInTheDocument();
    expect(within(table).getByText('83.3%')).toBeInTheDocument();
    expect(within(table).getByText('82%')).toBeInTheDocument();
    expect(within(table).getByText('현재 구매력')).toBeInTheDocument();
    expect(within(table).getByText('만기 명목')).toBeInTheDocument();

    await user.click(within(comparison as HTMLElement).getByRole('button', { name: '선택 해제' }));
    expect(screen.queryByText('저장 시나리오 비교')).not.toBeInTheDocument();
  });

  it('removes a deleted snapshot from the active comparison', async () => {
    const user = userEvent.setup();
    renderPage();

    const compareButtons = screen.getAllByRole('button', { name: '비교' });
    await user.click(compareButtons[0]);
    await user.click(compareButtons[1]);
    expect(screen.getByText('저장 시나리오 비교')).toBeInTheDocument();

    const deleteButtons = screen.getAllByRole('button', { name: /목표 시나리오 삭제/ });
    await user.click(deleteButtons[0]);

    expect(screen.queryByText('저장 시나리오 비교')).not.toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: '불러오기' })).toHaveLength(1);
    expect(screen.getByRole('button', { name: '선택됨' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('restores every planning assumption from a saved scenario', async () => {
    const user = userEvent.setup();
    renderPage();

    const savedScenario = screen.getByRole(
      'button',
      { name: '장기 목표 이름 수정' },
    ).closest('article');
    expect(savedScenario).not.toBeNull();
    await user.click(within(savedScenario as HTMLElement).getByRole('button', { name: '불러오기' }));

    expect(screen.getByRole('button', { name: '현재 구매력' })).toHaveClass('active');
    expect(screen.getByRole('spinbutton', { name: '연 물가상승률' })).toHaveValue(3);
    expect(screen.getByRole('spinbutton', { name: '연 투자금 증액률' })).toHaveValue(5);
    expect(screen.getByRole('slider')).toHaveValue('25');
  });

  it('saves a new scenario with a name and renames an existing scenario', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(
      await screen.findByRole('textbox', { name: '저장할 시나리오 이름' }),
      '내 집 마련',
    );
    await user.click(screen.getByRole('button', { name: '결과 저장' }));
    expect(screen.getByText('내 집 마련')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '기본 목표 이름 수정' }));
    const nameInput = screen.getByRole('textbox', { name: '시나리오 이름' });
    await user.clear(nameInput);
    await user.type(nameInput, '은퇴 준비');
    await user.click(screen.getByRole('button', { name: '저장' }));

    expect(screen.getByText('은퇴 준비')).toBeInTheDocument();
    expect(screen.queryByText('기본 목표')).not.toBeInTheDocument();
    expect(JSON.parse(window.localStorage.getItem('moa-goal-snapshots-v1') ?? '[]')).toEqual(
      expect.arrayContaining([expect.objectContaining({ name: '은퇴 준비' })]),
    );
  });

  it('sends inflation, target basis and contribution growth assumptions to the engine', async () => {
    const user = userEvent.setup();
    renderPage();

    await screen.findByText('GOAL-2026.08.2');
    await user.click(screen.getByRole('button', { name: '현재 구매력' }));
    const inflationInput = screen.getByRole('spinbutton', { name: '연 물가상승률' });
    const growthInput = screen.getByRole('spinbutton', { name: '연 투자금 증액률' });
    await user.clear(inflationInput);
    await user.type(inflationInput, '3');
    await user.clear(growthInput);
    await user.type(growthInput, '5');

    await waitFor(() => expect(simulateMock).toHaveBeenLastCalledWith(expect.objectContaining({
      annual_inflation_rate_pct: 3,
      target_amount_in_today_money: true,
      annual_contribution_growth_rate_pct: 5,
    })));
  });
});

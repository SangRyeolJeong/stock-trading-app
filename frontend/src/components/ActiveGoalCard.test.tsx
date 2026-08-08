import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';
import {
  createGoalSnapshot,
  saveGoalSnapshot,
  setActiveGoalSnapshot,
} from '../data/goalSnapshots';
import { ActiveGoalCard } from './ActiveGoalCard';

function renderCard() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<ActiveGoalCard />} />
        <Route path="/goal-simulator" element={<main>목표 계산기 이동 완료</main>} />
        <Route path="/strategy" element={<main>전략 이동 완료</main>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ActiveGoalCard', () => {
  beforeEach(() => window.localStorage.clear());

  it('guides the user to create a goal when none is active', async () => {
    const user = userEvent.setup();
    renderCard();

    expect(screen.getByText('아직 대표 목표가 없어요.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /목표 계획 만들기/ }));
    expect(screen.getByText('목표 계산기 이동 완료')).toBeInTheDocument();
  });

  it('shows the active plan and carries it into the strategy route', async () => {
    const user = userEvent.setup();
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
    }, new Date('2026-08-08T00:00:00Z'), '내 집 마련');
    saveGoalSnapshot(snapshot);
    setActiveGoalSnapshot(snapshot.id);
    renderCard();

    expect(screen.getByText('내 집 마련')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '82');
    await user.click(screen.getByRole('button', { name: /이 목표로 전략 보기/ }));
    expect(screen.getByText('전략 이동 완료')).toBeInTheDocument();
  });
});

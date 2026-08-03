import { render, screen, waitFor } from '@testing-library/react';
import { Outlet } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { TAX_PLANNER_PATH } from './paths';

vi.mock('../components/layout/AppLayout', () => ({
  AppLayout: () => <Outlet />,
}));
vi.mock('../pages/TaxPlannerPage', () => ({
  TaxPlannerPage: () => <main>절세 플래너 테스트 화면</main>,
}));
vi.mock('../pages/GoalSimulatorPage', () => ({
  GoalSimulatorPage: () => <main>목표 계산기 테스트 화면</main>,
}));

describe('AppRouter', () => {
  it('redirects the legacy tax path to the tax planner', async () => {
    window.history.replaceState(null, '', '/tax');
    const { AppRouter } = await import('./router');

    render(<AppRouter />);

    expect(await screen.findByText('절세 플래너 테스트 화면')).toBeInTheDocument();
    await waitFor(() => expect(window.location.pathname).toBe(TAX_PLANNER_PATH));

    window.history.pushState(null, '', '/goal-simulator');
    window.dispatchEvent(new PopStateEvent('popstate'));
    expect(await screen.findByText('목표 계산기 테스트 화면')).toBeInTheDocument();
  });
});

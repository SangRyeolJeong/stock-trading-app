import { lazy, Suspense, type ReactElement } from 'react';
import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { HomePage } from '../pages/HomePage';
import { GoalSimulatorPage } from '../pages/GoalSimulatorPage';
import { PortfolioPage } from '../pages/PortfolioPage';
import { SettingsPage } from '../pages/SettingsPage';
import { StrategyPage } from '../pages/StrategyPage';
import { TaxPlannerPage } from '../pages/TaxPlannerPage';
import { LEGACY_TAX_PATH, TAX_PLANNER_PATH } from './paths';

const LearnPage = lazy(async () => ({
  default: (await import('../pages/LearnPage')).LearnPage,
}));
const MarketPage = lazy(async () => ({
  default: (await import('../pages/MarketPage')).MarketPage,
}));
const LessonDetailPage = lazy(async () => ({
  default: (await import('../pages/LessonDetailPage')).LessonDetailPage,
}));

function lazyRoute(element: ReactElement) {
  return (
    <Suspense fallback={<main className="page route-loading">콘텐츠를 불러오고 있어요…</main>}>
      {element}
    </Suspense>
  );
}

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/market', element: lazyRoute(<MarketPage />) },
      { path: '/market/:symbol', element: lazyRoute(<MarketPage />) },
      { path: TAX_PLANNER_PATH, element: <TaxPlannerPage /> },
      { path: LEGACY_TAX_PATH, element: <Navigate to={TAX_PLANNER_PATH} replace /> },
      { path: '/goal-simulator', element: <GoalSimulatorPage /> },
      { path: '/strategy', element: <StrategyPage /> },
      { path: '/portfolio', element: <PortfolioPage /> },
      { path: '/settings', element: <SettingsPage /> },
      { path: '/learn', element: lazyRoute(<LearnPage />) },
      { path: '/learn/:slug', element: lazyRoute(<LessonDetailPage />) },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}

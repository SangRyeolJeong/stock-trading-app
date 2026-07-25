import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { HomePage } from '../pages/HomePage';
import { LearnPage } from '../pages/LearnPage';
import { MarketPage } from '../pages/MarketPage';
import { PortfolioPage } from '../pages/PortfolioPage';
import { StrategyPage } from '../pages/StrategyPage';
import { TaxPlannerPage } from '../pages/TaxPlannerPage';

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/market/:symbol', element: <MarketPage /> },
      { path: '/tax-planner', element: <TaxPlannerPage /> },
      { path: '/strategy', element: <StrategyPage /> },
      { path: '/portfolio', element: <PortfolioPage /> },
      { path: '/learn', element: <LearnPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}

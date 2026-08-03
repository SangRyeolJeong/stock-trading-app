import { useMemo, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { ToastContext } from '../../app/toast';
import { Icon } from '../common/Icon';
import { Header } from './Header';
import { Logo } from './Logo';
import { Sidebar } from './Sidebar';

const pageTitles: Record<string, string> = {
  '/': '홈',
  '/tax-planner': '절세 플래너',
  '/goal-simulator': '목표 계산기',
  '/strategy': 'AI 투자전략',
  '/portfolio': '내 포트폴리오',
  '/learn': '투자 지식',
  '/settings': '내 설정',
};

export function AppLayout() {
  const [toast, setToast] = useState('');
  const location = useLocation();
  const title = location.pathname.startsWith('/market/')
    ? '주식'
    : location.pathname.startsWith('/learn/')
      ? '투자 지식'
      : pageTitles[location.pathname] ?? 'MOA';

  const contextValue = useMemo(() => ({
    showToast: (message: string) => {
      setToast(message);
      window.setTimeout(() => setToast(''), 2_800);
    },
  }), []);

  return (
    <ToastContext.Provider value={contextValue}>
      <div className="app-shell">
        <Sidebar />
        <div className="workspace">
          <Header />
          <div className="mobile-title"><Logo /><span>{title}</span></div>
          <Outlet />
        </div>
        {toast && <div className="toast"><span><Icon name="check" size={15} /></span>{toast}</div>}
      </div>
    </ToastContext.Provider>
  );
}

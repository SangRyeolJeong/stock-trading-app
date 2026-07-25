import { NavLink } from 'react-router-dom';
import { Icon, type IconName } from '../common/Icon';
import { Logo } from './Logo';

const navigation = [
  { path: '/', label: '홈', icon: 'home' as IconName, end: true },
  { path: '/market/QQQM', label: '주식', icon: 'chart' as IconName },
  { path: '/tax-planner', label: '절세 플래너', icon: 'wallet' as IconName, badge: '핵심' },
  { path: '/strategy', label: 'AI 투자전략', icon: 'sparkles' as IconName },
  { path: '/portfolio', label: '내 포트폴리오', icon: 'pie' as IconName },
  { path: '/learn', label: '투자 지식', icon: 'book' as IconName },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <NavLink to="/" aria-label="MOA 홈"><Logo /></NavLink>
      <nav className="main-nav" aria-label="주 메뉴">
        {navigation.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon name={item.icon} size={19} />
            <span>{item.label}</span>
            {item.badge && <em>{item.badge}</em>}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-guide">
        <span className="guide-icon"><Icon name="sparkles" size={18} /></span>
        <strong>이번 달 절세 체크</strong>
        <p>연금저축 세액공제 한도까지<br /><b>184만원</b> 남았어요</p>
        <NavLink to="/tax-planner">채우러 가기 <Icon name="chevron" size={14} /></NavLink>
      </div>
      <div className="profile">
        <span className="avatar">김</span>
        <div><strong>김모아</strong><span>안전한 모의투자</span></div>
        <button aria-label="프로필 더보기"><Icon name="more" size={18} /></button>
      </div>
    </aside>
  );
}

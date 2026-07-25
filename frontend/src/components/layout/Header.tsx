import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../common/Icon';
import { useToast } from '../../app/toast';

export function Header() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { showToast } = useToast();

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const normalized = query.trim().toUpperCase();
    if (!normalized) return;
    navigate(`/market/${encodeURIComponent(normalized)}`);
    showToast(`“${query.trim()}” 검색 결과를 불러왔어요.`);
  };

  return (
    <header className="topbar">
      <form className="search" onSubmit={handleSubmit}>
        <Icon name="search" size={19} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="종목, ETF, 투자 지식을 검색해보세요" aria-label="통합 검색" />
        <kbd>⌘ K</kbd>
      </form>
      <div className="top-actions">
        <span className="market-status"><i /> 미국장 운영 중 <b>02:14:32</b></span>
        <button className="icon-button notification" onClick={() => showToast('새로운 절세 알림이 2개 있어요.')} aria-label="알림"><Icon name="bell" size={20} /><i /></button>
        <button className="mode-chip">모의투자 <Icon name="chevron" size={13} /></button>
      </div>
    </header>
  );
}

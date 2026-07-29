import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/authContext';
import { useToast } from '../../app/toast';
import { marketApi } from '../../services/marketApi';
import { formatUpdatedAt } from '../../utils/format';
import type { IconName } from '../common/Icon';
import { Icon } from '../common/Icon';

const APP_SHORTCUTS: Array<{
  path: string;
  title: string;
  description: string;
  icon: IconName;
  keywords: string;
}> = [
  {
    path: '/tax-planner',
    title: '절세 플래너',
    description: 'ISA·연금저축·IRP 세후 결과 비교',
    icon: 'shield',
    keywords: '절세 세금 tax isa 연금저축 irp',
  },
  {
    path: '/strategy',
    title: '투자전략 추천',
    description: '목표와 위험성향에 맞는 자산배분',
    icon: 'sparkles',
    keywords: '전략 추천 자산배분 포트폴리오 strategy',
  },
  {
    path: '/portfolio',
    title: '모의투자 포트폴리오',
    description: '보유 종목과 주문 원장 확인',
    icon: 'pie',
    keywords: '포트폴리오 보유 종목 주문 원장 portfolio',
  },
  {
    path: '/learn',
    title: '투자 지식',
    description: 'ETF·절세 계좌·연금 학습 콘텐츠',
    icon: 'book',
    keywords: '투자 지식 공부 학습 etf 연금 learn',
  },
  {
    path: '/settings',
    title: '내 투자 설정',
    description: '이름과 공통 투자 계획 기본값 관리',
    icon: 'target',
    keywords: '설정 프로필 이름 투자금 기간 성향 settings profile',
  },
];

interface SearchItem {
  key: string;
  title: string;
  description: string;
  meta: string;
  path: string;
  icon: IconName;
  kind: 'shortcut' | 'instrument';
}

export function Header() {
  const [query, setQuery] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const searchRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { isSupabase, signOut, userEmail } = useAuth();
  const { showToast } = useToast();

  const normalizedQuery = query.trim();
  useEffect(() => {
    const timer = window.setTimeout(() => setSearchTerm(normalizedQuery), 200);
    return () => window.clearTimeout(timer);
  }, [normalizedQuery]);

  const instrumentsQuery = useQuery({
    queryKey: ['header-instruments', searchTerm],
    queryFn: () => marketApi.searchInstruments(searchTerm, 'all', 8),
    enabled: searchTerm.length > 0,
    staleTime: 24 * 60 * 60_000,
  });
  const marketStatusQuery = useQuery({
    queryKey: ['quote', 'QQQM'],
    queryFn: () => marketApi.getQuote('QQQM'),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const results = useMemo<SearchItem[]>(() => {
    if (!normalizedQuery) return [];
    const lowerQuery = normalizedQuery.toLocaleLowerCase('ko-KR');
    const shortcuts: SearchItem[] = APP_SHORTCUTS
      .filter((item) => `${item.title} ${item.description} ${item.keywords}`.toLocaleLowerCase('ko-KR').includes(lowerQuery))
      .map((item) => ({
        key: `shortcut-${item.path}`,
        title: item.title,
        description: item.description,
        meta: 'MOA 기능',
        path: item.path,
        icon: item.icon,
        kind: 'shortcut',
      }));
    const instruments: SearchItem[] = normalizedQuery === searchTerm
      ? (instrumentsQuery.data?.items ?? []).map((instrument) => ({
          key: `instrument-${instrument.exchange_code}-${instrument.symbol}`,
          title: instrument.symbol,
          description: instrument.name,
          meta: `${instrument.market} · ${instrument.asset_type.toUpperCase()}`,
          path: `/market/${encodeURIComponent(instrument.symbol)}`,
          icon: 'chart',
          kind: 'instrument',
        }))
      : [];
    return [...shortcuts, ...instruments];
  }, [instrumentsQuery.data?.items, normalizedQuery, searchTerm]);

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (!searchRef.current?.contains(event.target as Node)) setIsOpen(false);
    };
    const handleShortcut = (event: globalThis.KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLocaleLowerCase() === 'k') {
        event.preventDefault();
        setIsOpen(true);
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };
    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleShortcut);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleShortcut);
    };
  }, []);

  const selectResult = (result: SearchItem) => {
    navigate(result.path);
    setQuery('');
    setSearchTerm('');
    setIsOpen(false);
    inputRef.current?.blur();
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!normalizedQuery) return;
    const selected = results[activeIndex] ?? results[0];
    if (selected) {
      selectResult(selected);
      return;
    }
    if (/^[A-Z0-9.]{1,12}$/i.test(normalizedQuery)) {
      selectResult({
        key: 'direct-symbol',
        title: normalizedQuery.toUpperCase(),
        description: '',
        meta: '',
        path: `/market/${encodeURIComponent(normalizedQuery.toUpperCase())}`,
        icon: 'chart',
        kind: 'instrument',
      });
      return;
    }
    showToast('검색 결과가 없습니다. 종목명이나 티커를 다시 확인해 주세요.');
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
      return;
    }
    if (!isOpen || results.length === 0) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((current) => (current + 1) % results.length);
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((current) => (current - 1 + results.length) % results.length);
    }
  };

  const isDebouncing = Boolean(normalizedQuery) && normalizedQuery !== searchTerm;
  const showPanel = isOpen && Boolean(normalizedQuery);

  return (
    <header className="topbar">
      <form className={`search ${showPanel ? 'open' : ''}`} onSubmit={handleSubmit} ref={searchRef} role="search">
        <Icon name="search" size={19} />
        <input
          ref={inputRef}
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setActiveIndex(0);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="종목, ETF, MOA 기능을 검색해보세요"
          aria-label="통합 검색"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showPanel}
          aria-controls="global-search-results"
          aria-activedescendant={showPanel && results[activeIndex] ? `global-search-${activeIndex}` : undefined}
        />
        <kbd>⌘ K</kbd>
        {showPanel && (
          <div className="global-search-panel" id="global-search-results" role="listbox">
            {results.map((result, index) => (
              <button
                type="button"
                id={`global-search-${index}`}
                role="option"
                aria-selected={activeIndex === index}
                className={`global-search-result ${activeIndex === index ? 'active' : ''}`}
                key={result.key}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => selectResult(result)}
              >
                <span className={`global-search-icon ${result.kind}`}><Icon name={result.icon} size={16} /></span>
                <span className="global-search-copy"><strong>{result.title}</strong><small>{result.description}</small></span>
                <span className="global-search-meta">{result.meta}</span>
              </button>
            ))}
            {(isDebouncing || instrumentsQuery.isLoading) && (
              <div className="global-search-state">검색 결과를 찾고 있어요…</div>
            )}
            {!isDebouncing && instrumentsQuery.isError && (
              <div className="global-search-state error">
                <span>종목 검색 서버에 연결하지 못했습니다.</span>
                <button type="button" onClick={() => instrumentsQuery.refetch()}>다시 시도</button>
              </div>
            )}
            {!isDebouncing && !instrumentsQuery.isLoading && !instrumentsQuery.isError && results.length === 0 && (
              <div className="global-search-state">일치하는 종목이나 기능이 없습니다.</div>
            )}
            <div className="global-search-footer">
              <span><kbd>↑</kbd><kbd>↓</kbd> 이동</span>
              <span><kbd>Enter</kbd> 선택</span>
              <span><kbd>Esc</kbd> 닫기</span>
            </div>
          </div>
        )}
      </form>
      <div className="top-actions">
        <span className={`market-status ${marketStatusQuery.isError ? 'unavailable' : marketStatusQuery.data?.market_open ? 'open' : 'closed'}`}>
          <i />
          {marketStatusQuery.isLoading
            ? '미국장 확인 중'
            : marketStatusQuery.isError
              ? '미국장 상태 확인 불가'
              : marketStatusQuery.data?.market_open ? '미국장 운영 중' : '미국장 마감'}
          <b>{formatUpdatedAt(marketStatusQuery.data?.as_of)}</b>
        </span>
        <button className="icon-button notification" onClick={() => showToast('현재 새로운 알림이 없습니다.')} aria-label="알림"><Icon name="bell" size={20} /></button>
        <button className="mode-chip" onClick={() => navigate('/portfolio')}>모의투자 <Icon name="chevron" size={13} /></button>
        {isSupabase && (
          <button
            className="auth-chip"
            title={userEmail ?? '로그인 사용자'}
            onClick={() => {
              void signOut().catch(() => showToast('로그아웃하지 못했습니다. 다시 시도해 주세요.'));
            }}
          >
            로그아웃
          </button>
        )}
      </div>
    </header>
  );
}

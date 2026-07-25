import { useMemo, useState } from 'react';
import ChartSection from './components/ChartSection';

type IconName =
  | 'home'
  | 'chart'
  | 'wallet'
  | 'sparkles'
  | 'pie'
  | 'book'
  | 'search'
  | 'bell'
  | 'chevron'
  | 'arrowUp'
  | 'arrowDown'
  | 'shield'
  | 'check'
  | 'clock'
  | 'plus'
  | 'more'
  | 'info'
  | 'target'
  | 'refresh';

const iconPaths: Record<IconName, JSX.Element> = {
  home: <><path d="M3 11.2 12 4l9 7.2"/><path d="M5.5 10v9h13v-9"/><path d="M9.5 19v-5h5v5"/></>,
  chart: <><path d="M4 19V9"/><path d="M10 19V5"/><path d="M16 19v-7"/><path d="M22 19H2"/></>,
  wallet: <><rect x="3" y="5" width="18" height="15" rx="3"/><path d="M16 12h5"/><path d="M3 9h15V5"/></>,
  sparkles: <><path d="m12 3 1.2 3.8L17 8l-3.8 1.2L12 13l-1.2-3.8L7 8l3.8-1.2L12 3Z"/><path d="m5 14 .8 2.2L8 17l-2.2.8L5 20l-.8-2.2L2 17l2.2-.8L5 14Z"/><path d="m19 13 .7 2.3 2.3.7-2.3.7L19 19l-.7-2.3L16 16l2.3-.7L19 13Z"/></>,
  pie: <><path d="M11 3a9 9 0 1 0 9 9h-9V3Z"/><path d="M14 3.5V9h5.5A7.5 7.5 0 0 0 14 3.5Z"/></>,
  book: <><path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H11v17H7.5A3.5 3.5 0 0 0 4 22V5.5Z"/><path d="M20 5.5A3.5 3.5 0 0 0 16.5 2H13v17h3.5A3.5 3.5 0 0 1 20 22V5.5Z"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"/><path d="M10 21h4"/></>,
  chevron: <path d="m9 18 6-6-6-6"/>,
  arrowUp: <><path d="m5 14 7-7 7 7"/><path d="M12 7v11"/></>,
  arrowDown: <><path d="m5 10 7 7 7-7"/><path d="M12 17V6"/></>,
  shield: <><path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10Z"/><path d="m9 12 2 2 4-5"/></>,
  check: <path d="m5 12 4 4L19 6"/>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  plus: <><path d="M12 5v14"/><path d="M5 12h14"/></>,
  more: <><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>,
  info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7h.01"/></>,
  target: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></>,
  refresh: <><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M6.1 9A7 7 0 0 1 18 6l2 2"/><path d="M17.9 15A7 7 0 0 1 6 18l-2-2"/></>,
};

function Icon({ name, size = 20, className = '' }: { name: IconName; size?: number; className?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {iconPaths[name]}
    </svg>
  );
}

const navigation = [
  { id: 'home', label: '홈', icon: 'home' as IconName },
  { id: 'market', label: '주식', icon: 'chart' as IconName },
  { id: 'tax', label: '절세 플래너', icon: 'wallet' as IconName, badge: '핵심' },
  { id: 'strategy', label: 'AI 투자전략', icon: 'sparkles' as IconName },
  { id: 'portfolio', label: '내 포트폴리오', icon: 'pie' as IconName },
  { id: 'learn', label: '투자 지식', icon: 'book' as IconName },
];

const watchlist = [
  { symbol: 'QQQM', name: 'Invesco NASDAQ 100 ETF', price: '$231.72', change: '+1.28%', positive: true, color: '#3867ff' },
  { symbol: '005930', name: '삼성전자', price: '82,400원', change: '+0.61%', positive: true, color: '#2478ff' },
  { symbol: '360750', name: 'TIGER 미국S&P500', price: '22,165원', change: '-0.34%', positive: false, color: '#e95768' },
  { symbol: 'AAPL', name: 'Apple', price: '$219.31', change: '+0.92%', positive: true, color: '#202531' },
];

const holdings = [
  { symbol: 'QQQM', name: 'Invesco NASDAQ 100 ETF', quantity: '38주', value: '12,438,120원', profit: '+1,184,300원', rate: '+10.52%', positive: true, weight: 42, color: '#5578ff' },
  { symbol: '360750', name: 'TIGER 미국S&P500', quantity: '214주', value: '4,743,310원', profit: '+318,540원', rate: '+7.20%', positive: true, weight: 26, color: '#6cd2b8' },
  { symbol: '005930', name: '삼성전자', quantity: '42주', value: '3,460,800원', profit: '-92,400원', rate: '-2.60%', positive: false, weight: 19, color: '#ffb15c' },
  { symbol: 'CASH', name: '예수금 · 달러', quantity: '$1,482', value: '2,044,520원', profit: '대기 자금', rate: '13.0%', positive: true, weight: 13, color: '#3d4758' },
];

function Logo() {
  return (
    <button className="logo" aria-label="MOA 홈">
      <span className="logo-mark"><span /><span /><span /></span>
      <span>moa</span>
    </button>
  );
}

function Sidebar({ active, onChange }: { active: string; onChange: (id: string) => void }) {
  return (
    <aside className="sidebar">
      <Logo />
      <nav className="main-nav" aria-label="주 메뉴">
        {navigation.map((item) => (
          <button key={item.id} className={`nav-item ${active === item.id ? 'active' : ''}`} onClick={() => onChange(item.id)}>
            <Icon name={item.icon} size={19} />
            <span>{item.label}</span>
            {item.badge && <em>{item.badge}</em>}
          </button>
        ))}
      </nav>
      <div className="sidebar-guide">
        <span className="guide-icon"><Icon name="sparkles" size={18} /></span>
        <strong>이번 달 절세 체크</strong>
        <p>연금저축 세액공제 한도까지<br /><b>184만원</b> 남았어요</p>
        <button onClick={() => onChange('tax')}>채우러 가기 <Icon name="chevron" size={14} /></button>
      </div>
      <div className="profile">
        <span className="avatar">김</span>
        <div><strong>김모아</strong><span>안전한 모의투자</span></div>
        <button aria-label="더보기"><Icon name="more" size={18} /></button>
      </div>
    </aside>
  );
}

function Topbar({ onSearch, onNotify }: { onSearch: (value: string) => void; onNotify: () => void }) {
  const [query, setQuery] = useState('');
  return (
    <header className="topbar">
      <form className="search" onSubmit={(e) => { e.preventDefault(); onSearch(query); }}>
        <Icon name="search" size={19} />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="종목, ETF, 투자 지식을 검색해보세요" aria-label="통합 검색" />
        <kbd>⌘ K</kbd>
      </form>
      <div className="top-actions">
        <span className="market-status"><i /> 미국장 운영 중 <b>02:14:32</b></span>
        <button className="icon-button notification" onClick={onNotify} aria-label="알림"><Icon name="bell" size={20} /><i /></button>
        <button className="mode-chip">모의투자 <Icon name="chevron" size={13} /></button>
      </div>
    </header>
  );
}

function MiniLineChart() {
  return (
    <svg className="mini-chart" viewBox="0 0 560 170" preserveAspectRatio="none" role="img" aria-label="최근 1개월 자산 추이">
      <defs>
        <linearGradient id="miniFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4c79ff" stopOpacity=".3" />
          <stop offset="100%" stopColor="#4c79ff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path className="grid-line" d="M0 32H560M0 86H560M0 140H560" />
      <path className="area" d="M0 138 C24 133 32 119 58 124 S94 113 118 116 S150 105 174 109 S210 89 232 94 S265 74 288 80 S321 64 347 72 S378 51 404 58 S444 43 466 47 S500 25 525 34 S548 23 560 19 V170H0Z" />
      <path className="line" d="M0 138 C24 133 32 119 58 124 S94 113 118 116 S150 105 174 109 S210 89 232 94 S265 74 288 80 S321 64 347 72 S378 51 404 58 S444 43 466 47 S500 25 525 34 S548 23 560 19" />
      <circle cx="560" cy="19" r="4" />
    </svg>
  );
}

function HomeScreen({ onNavigate }: { onNavigate: (id: string) => void }) {
  const [range, setRange] = useState('1개월');
  return (
    <main className="page home-page">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">7월 25일 토요일</p>
          <h1>좋은 저녁이에요, 김모아님</h1>
          <p>오늘도 세금은 줄이고, 투자는 길게 이어가 볼까요?</p>
        </div>
        <button className="primary-button" onClick={() => onNavigate('strategy')}><Icon name="sparkles" size={17} /> AI에게 전략 물어보기</button>
      </section>

      <section className="dashboard-grid">
        <article className="card asset-card">
          <div className="card-heading">
            <div><span className="label">총 자산</span><button className="small-link">KRW <Icon name="chevron" size={12} /></button></div>
            <button className="more-button"><Icon name="more" size={19} /></button>
          </div>
          <div className="asset-value"><strong>32,686,750</strong><span>원</span></div>
          <div className="asset-change"><span><Icon name="arrowUp" size={13} /> 2,184,320원</span><b>+7.16%</b><em>투자 원금 대비</em></div>
          <div className="range-tabs">
            {['1주', '1개월', '3개월', '1년', '전체'].map((item) => <button key={item} onClick={() => setRange(item)} className={range === item ? 'active' : ''}>{item}</button>)}
          </div>
          <MiniLineChart />
          <div className="chart-labels"><span>6월 25일</span><span>7월 25일</span></div>
        </article>

        <article className="card tax-score-card">
          <div className="card-heading">
            <div><span className="label">나의 절세 점수</span><p>놓치고 있는 혜택을 확인해보세요</p></div>
            <button className="more-button" onClick={() => onNavigate('tax')}><Icon name="chevron" size={18} /></button>
          </div>
          <div className="score-wrap">
            <div className="score-ring"><div><strong>72</strong><span>/ 100점</span></div></div>
            <div className="score-copy"><span className="pill positive">상위 31%</span><strong>잘하고 있어요!</strong><p>연금저축을 더 활용하면<br />최대 304,000원 절약 가능해요.</p></div>
          </div>
          <button className="soft-button" onClick={() => onNavigate('tax')}>내 절세 리포트 보기 <Icon name="chevron" size={15} /></button>
        </article>

        <article className="card watch-card">
          <div className="card-heading">
            <div><span className="label">관심 종목</span><p>실시간 시세</p></div>
            <button className="add-button"><Icon name="plus" size={15} /> 추가</button>
          </div>
          <div className="watch-list">
            {watchlist.map((stock) => (
              <button key={stock.symbol} className="watch-row" onClick={() => onNavigate('market')}>
                <span className="stock-logo" style={{ background: stock.color }}>{stock.symbol === '005930' ? 'S' : stock.symbol.slice(0, 1)}</span>
                <span className="stock-name"><strong>{stock.symbol}</strong><small>{stock.name}</small></span>
                <span className="stock-price"><strong>{stock.price}</strong><small className={stock.positive ? 'up' : 'down'}>{stock.change}</small></span>
              </button>
            ))}
          </div>
          <button className="text-button" onClick={() => onNavigate('market')}>관심 종목 전체보기 <Icon name="chevron" size={14} /></button>
        </article>

        <article className="card insight-card">
          <div className="insight-top">
            <span className="ai-badge"><Icon name="sparkles" size={15} /> MOA AI 인사이트</span>
            <span className="new-badge">NEW</span>
          </div>
          <h2>나스닥100, 어떤 계좌와<br />ETF가 가장 유리할까요?</h2>
          <p>30년 장기투자와 월 50만원 적립을 기준으로<br />세후 수익을 비교했어요.</p>
          <div className="compare-preview">
            <div><span>추천 조합</span><strong>연금저축 + TIGER 미국나스닥100</strong></div>
            <div><span>예상 절세</span><strong>약 4,820만원</strong></div>
          </div>
          <button onClick={() => onNavigate('strategy')}>분석 결과 자세히 보기 <Icon name="chevron" size={15} /></button>
          <span className="decor-orb orb-one" /><span className="decor-orb orb-two" />
        </article>

        <article className="card allocation-card">
          <div className="card-heading">
            <div><span className="label">포트폴리오 구성</span><p>전체 투자자산 기준</p></div>
            <button className="more-button" onClick={() => onNavigate('portfolio')}><Icon name="chevron" size={18} /></button>
          </div>
          <div className="allocation-content">
            <div className="donut"><div><strong>4</strong><span>종목</span></div></div>
            <div className="legend">
              {holdings.map((item) => <div key={item.symbol}><i style={{ background: item.color }} /><span>{item.symbol === 'CASH' ? '현금' : item.symbol}</span><b>{item.weight}%</b></div>)}
            </div>
          </div>
          <div className="rebalance-tip"><Icon name="info" size={16} /><span><strong>리밸런싱 알림</strong> QQQM 비중이 목표보다 7% 높아요.</span></div>
        </article>
      </section>
    </main>
  );
}

function TradePanel({ onOrder }: { onOrder: (message: string) => void }) {
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState('지정가');
  const [quantity, setQuantity] = useState(1);
  const price = 231.72;
  return (
    <aside className="trade-panel card">
      <div className="trade-tabs">
        <button className={side === 'buy' ? 'active buy' : ''} onClick={() => setSide('buy')}>구매</button>
        <button className={side === 'sell' ? 'active sell' : ''} onClick={() => setSide('sell')}>판매</button>
      </div>
      <div className="available"><span>주문 가능 금액</span><strong>$4,128.60</strong></div>
      <label>주문 방식</label>
      <div className="segmented">{['지정가', '시장가'].map((item) => <button key={item} className={orderType === item ? 'active' : ''} onClick={() => setOrderType(item)}>{item}</button>)}</div>
      <label>주문 가격</label>
      <div className="price-input"><button>−</button><div><strong>${price.toFixed(2)}</strong><span>약 320,100원</span></div><button>＋</button></div>
      <label>수량</label>
      <div className="quantity-input"><button onClick={() => setQuantity(Math.max(1, quantity - 1))}>−</button><strong>{quantity}주</strong><button onClick={() => setQuantity(quantity + 1)}>＋</button></div>
      <div className="quick-amounts">{['10%', '25%', '50%', '최대'].map((item) => <button key={item}>{item}</button>)}</div>
      <div className="order-summary"><div><span>예상 주문 금액</span><strong>${(price * quantity).toFixed(2)}</strong></div><div><span>예상 수수료</span><strong>$0.00</strong></div></div>
      <button className={`order-button ${side}`} onClick={() => onOrder(`QQQM ${quantity}주 ${side === 'buy' ? '구매' : '판매'} 주문을 접수했어요.`)}>
        {quantity}주 {side === 'buy' ? '구매하기' : '판매하기'}
      </button>
      <p className="paper-note"><Icon name="shield" size={14} /> 모의투자 주문으로 실제 돈은 사용되지 않아요</p>
    </aside>
  );
}

function MarketScreen({ onToast }: { onToast: (message: string) => void }) {
  const [period, setPeriod] = useState('1일');
  const [activeTab, setActiveTab] = useState('차트');
  const orderRows = [
    { price: '232.18', volume: '1,203', type: 'ask' }, { price: '232.04', volume: '842', type: 'ask' }, { price: '231.88', volume: '2,105', type: 'ask' },
    { price: '231.72', volume: '현재가', type: 'current' }, { price: '231.68', volume: '986', type: 'bid' }, { price: '231.51', volume: '1,547', type: 'bid' }, { price: '231.34', volume: '758', type: 'bid' },
  ];
  return (
    <main className="page market-page">
      <div className="market-layout">
        <aside className="stock-browser card">
          <div className="browser-title"><h2>관심 종목</h2><button><Icon name="plus" size={16} /></button></div>
          <div className="browser-search"><Icon name="search" size={16} /><input placeholder="종목 검색" /></div>
          <div className="browser-tabs"><button className="active">관심</button><button>국내</button><button>해외</button><button>ETF</button></div>
          <div className="browser-list">
            {watchlist.concat([{ symbol: 'NVDA', name: 'NVIDIA', price: '$174.92', change: '+2.41%', positive: true, color: '#74b72e' }]).map((stock, index) => (
              <button key={stock.symbol} className={index === 0 ? 'selected' : ''}>
                <span className="stock-logo" style={{ background: stock.color }}>{stock.symbol.slice(0, 1)}</span>
                <span className="stock-name"><strong>{stock.symbol}</strong><small>{stock.name}</small></span>
                <span className="stock-price"><strong>{stock.price}</strong><small className={stock.positive ? 'up' : 'down'}>{stock.change}</small></span>
              </button>
            ))}
          </div>
        </aside>

        <section className="stock-detail card">
          <div className="stock-header">
            <div className="stock-identity"><span className="stock-logo large">Q</span><div><span>Invesco NASDAQ 100 ETF · NASDAQ</span><h1>QQQM <button>☆</button></h1></div></div>
            <div className="live-price"><strong>$231.72</strong><span className="up">+$2.94 (+1.28%)</span><small>실시간 · USD/KRW 1,381.50</small></div>
          </div>
          <div className="detail-tabs">{['차트', '호가', '기업정보', '토론'].map((tab) => <button key={tab} onClick={() => setActiveTab(tab)} className={activeTab === tab ? 'active' : ''}>{tab}</button>)}</div>
          {activeTab === '차트' ? (
            <>
              <div className="chart-toolbar">
                <div>{['1일', '1주', '1개월', '3개월', '1년', '5년'].map((item) => <button key={item} className={period === item ? 'active' : ''} onClick={() => setPeriod(item)}>{item}</button>)}</div>
                <div><button>캔들</button><button>지표</button><button><Icon name="refresh" size={14} /></button></div>
              </div>
              <div className="main-chart"><ChartSection symbol="QQQM" /></div>
              <div className="market-metrics">
                <div><span>오늘 고가</span><strong>$233.08</strong></div><div><span>오늘 저가</span><strong>$228.41</strong></div><div><span>거래량</span><strong>1.42M</strong></div><div><span>시가총액</span><strong>$40.2B</strong></div>
              </div>
              <div className="account-hint">
                <span><Icon name="sparkles" size={18} /></span>
                <div><strong>30년 장기 적립이라면 QQQ보다 QQQM이 유리할 수 있어요</strong><p>동일 지수 추종, 더 낮은 총보수(0.15%)로 적립식 투자에 적합해요.</p></div>
                <button onClick={() => onToast('AI 비교 리포트를 준비했어요.')}>비교하기 <Icon name="chevron" size={14} /></button>
              </div>
            </>
          ) : activeTab === '호가' ? (
            <div className="orderbook-view">
              <div className="orderbook-head"><span>잔량</span><span>가격(USD)</span><span>변동률</span></div>
              {orderRows.map((row, i) => <div key={i} className={row.type}><span>{row.volume}</span><strong>{row.price}</strong><span>{row.type === 'ask' ? '+1.4%' : row.type === 'bid' ? '+1.1%' : '+1.28%'}</span></div>)}
            </div>
          ) : (
            <div className="empty-state"><span><Icon name={activeTab === '기업정보' ? 'chart' : 'book'} size={28} /></span><h3>{activeTab} 화면</h3><p>한투 API 및 데이터 소스 연결 후 실시간 정보가 표시됩니다.</p></div>
          )}
        </section>
        <TradePanel onOrder={onToast} />
      </div>
    </main>
  );
}

const accounts = [
  { id: 'direct', name: '해외주식 직투', tag: '유동성', tax: '연 250만원 공제 후 22%', limit: '제한 없음', product: 'QQQM', note: '달러 자산을 직접 보유하고 언제든 매매하기 좋아요.', score: 76 },
  { id: 'isa', name: '중개형 ISA', tag: '절세', tax: '200만원 비과세 + 9.9%', limit: '연 2,000만원', product: '국내상장 해외 ETF', note: '3년 이상 투자하고 목돈을 운용할 때 효율적이에요.', score: 88 },
  { id: 'pension', name: '연금저축펀드', tag: '장기투자', tax: '최대 16.5% 세액공제', limit: '세액공제 연 600만원', product: 'TIGER 미국나스닥100', note: '55세 이후 사용할 장기 자금이라면 우선순위가 높아요.', score: 96 },
  { id: 'irp', name: 'IRP', tag: '노후', tax: '연금저축 합산 900만원', limit: '연 1,800만원', product: 'ETF + 안전자산 30%', note: '추가 세액공제에 좋지만 중도인출 제약을 확인하세요.', score: 84 },
];

function TaxScreen() {
  const [income, setIncome] = useState('5,500만원 이하');
  const [selected, setSelected] = useState('pension');
  const account = accounts.find((item) => item.id === selected)!;
  return (
    <main className="page content-page">
      <section className="page-title">
        <span className="title-icon blue"><Icon name="wallet" size={23} /></span>
        <div><p className="eyebrow">TAX PLANNER</p><h1>내게 맞는 절세 계좌 찾기</h1><p>같은 투자도 어떤 계좌를 쓰느냐에 따라 세후 수익이 달라져요.</p></div>
      </section>
      <section className="tax-grid">
        <article className="card planner-form">
          <div className="step-title"><span>1</span><div><strong>투자 조건을 알려주세요</strong><p>샘플 조건으로 바로 비교해볼 수 있어요.</p></div></div>
          <label>연간 총급여</label>
          <div className="option-grid two">{['5,500만원 이하', '5,500만원 초과'].map((item) => <button className={income === item ? 'active' : ''} key={item} onClick={() => setIncome(item)}>{item}<Icon name="check" size={15} /></button>)}</div>
          <label>투자 목적</label>
          <div className="option-grid three"><button className="active">노후 준비</button><button>목돈 마련</button><button>자유로운 운용</button></div>
          <label>예상 투자 기간</label>
          <div className="slider-label"><strong>30년</strong><span>장기투자</span></div>
          <input className="range-input" type="range" min="1" max="40" defaultValue="30" />
          <div className="range-ends"><span>1년</span><span>40년</span></div>
          <label>월 투자금</label>
          <div className="money-input"><span>₩</span><strong>500,000</strong><em>원</em></div>
          <div className="form-note"><Icon name="shield" size={17} /><p>입력한 정보는 계좌 추천에만 사용되며 저장되지 않아요.</p></div>
        </article>

        <article className="card tax-result">
          <div className="result-heading"><span className="ai-badge"><Icon name="sparkles" size={15} /> 맞춤 분석 완료</span><p>현재 조건에서 가장 유리한 조합이에요</p></div>
          <div className="winner">
            <div><span className="winner-rank">BEST</span><h2>연금저축펀드</h2><p>+ 국내상장 나스닥100 ETF</p></div>
            <div className="save-number"><span>30년 예상 절세 효과</span><strong>약 4,820만원</strong><small>직투 대비, 가정 수익률 연 7%</small></div>
          </div>
          <div className="result-bars">
            <div><span>직투 계좌</span><i><b style={{ width: '54%' }} /></i><strong>세후 4.21억</strong></div>
            <div><span>중개형 ISA</span><i><b style={{ width: '70%' }} /></i><strong>세후 4.48억</strong></div>
            <div className="best"><span>연금저축</span><i><b style={{ width: '91%' }} /></i><strong>세후 4.69억</strong></div>
            <div><span>IRP</span><i><b style={{ width: '82%' }} /></i><strong>세후 4.57억</strong></div>
          </div>
          <p className="disclaimer"><Icon name="info" size={14} /> 단순 가정에 따른 예시이며 실제 수익률, 환율, 세법 개정에 따라 달라질 수 있어요.</p>
        </article>
      </section>
      <section className="account-section">
        <div className="section-heading"><div><h2>계좌별로 꼼꼼히 비교했어요</h2><p>카드를 눌러 장점과 유의사항을 확인하세요.</p></div><span>샘플 계산 · 실행 전 최신 기준 재확인</span></div>
        <div className="account-cards">
          {accounts.map((item) => (
            <button key={item.id} onClick={() => setSelected(item.id)} className={`account-card ${selected === item.id ? 'active' : ''}`}>
              <div><span className="account-tag">{item.tag}</span>{selected === item.id && <span className="selected-check"><Icon name="check" size={14} /></span>}</div>
              <h3>{item.name}</h3><p>{item.note}</p>
              <div className="account-score"><i><b style={{ width: `${item.score}%` }} /></i><strong>{item.score}점</strong></div>
            </button>
          ))}
        </div>
        <article className="account-detail card">
          <div><span className="stock-logo account-logo"><Icon name="wallet" size={20} /></span><div><span>선택한 계좌</span><h3>{account.name}</h3></div></div>
          <dl><div><dt>과세 방식</dt><dd>{account.tax}</dd></div><div><dt>납입 한도</dt><dd>{account.limit}</dd></div><div><dt>추천 상품</dt><dd>{account.product}</dd></div></dl>
          <button>계좌 활용법 자세히 보기 <Icon name="chevron" size={14} /></button>
        </article>
      </section>
    </main>
  );
}

function StrategyScreen() {
  const [goal, setGoal] = useState('30년 장기투자');
  const [risk, setRisk] = useState('성장형');
  return (
    <main className="page content-page strategy-page">
      <section className="strategy-hero">
        <div><span className="ai-badge light"><Icon name="sparkles" size={15} /> MOA AI STRATEGIST</span><h1>좋은 상품보다<br /><em>나에게 맞는 방식</em>을 찾으세요.</h1><p>투자 기간, 목적, 계좌까지 함께 보고 실행 가능한 전략을 제안해요.</p></div>
        <div className="hero-orbit"><span className="center-orb"><Icon name="sparkles" size={30} /></span><span className="orbit-item one">ISA</span><span className="orbit-item two">QQQM</span><span className="orbit-item three">IRP</span><span className="orbit-item four">연금</span></div>
      </section>
      <section className="strategy-layout">
        <article className="card strategy-form">
          <div className="step-title"><span>1</span><div><strong>어떤 투자를 계획하고 있나요?</strong><p>선택에 따라 전략이 실시간으로 바뀌어요.</p></div></div>
          <label>목표</label>
          <div className="choice-stack">{['30년 장기투자', '10년 목돈 마련', '배당 현금흐름'].map((item) => <button key={item} className={goal === item ? 'active' : ''} onClick={() => setGoal(item)}><span><Icon name={item === '30년 장기투자' ? 'clock' : item === '10년 목돈 마련' ? 'target' : 'wallet'} size={19} />{item}</span>{goal === item && <Icon name="check" size={17} />}</button>)}</div>
          <label>투자 성향</label>
          <div className="segmented wide">{['안정형', '균형형', '성장형'].map((item) => <button key={item} className={risk === item ? 'active' : ''} onClick={() => setRisk(item)}>{item}</button>)}</div>
          <label>선호하는 조건</label>
          <div className="check-list"><label><input type="checkbox" defaultChecked /><span><Icon name="check" size={13} /></span>언제든 매도할 수 있는 유동성</label><label><input type="checkbox" defaultChecked /><span><Icon name="check" size={13} /></span>낮은 운용보수</label><label><input type="checkbox" /><span><Icon name="check" size={13} /></span>매달 배당금 수령</label></div>
        </article>
        <article className="card recommendation">
          <div className="recommend-top"><div><span className="ai-badge"><Icon name="sparkles" size={15} /> AI 추천 전략</span><h2>{goal} · {risk}</h2></div><span className="fit-score"><b>94</b>점<small>적합도</small></span></div>
          <div className="strategy-name"><span className="strategy-icon">Q</span><div><span>핵심 성장 자산</span><h3>달러 직투 + QQQM 적립식</h3><p>매월 50만원 · 매월 15일 자동 매수</p></div></div>
          <div className="why-box">
            <h4>왜 이 전략인가요?</h4>
            <div><span>01</span><p><strong>QQQ와 같은 나스닥100을 추종해요</strong><small>장기 성과의 핵심은 유지하면서 총보수는 연 0.15%로 더 낮아요.</small></p></div>
            <div><span>02</span><p><strong>달러 유동성을 확보할 수 있어요</strong><small>해외 직투 계좌에서 달러를 직접 보유하고 자유롭게 매매할 수 있어요.</small></p></div>
            <div><span>03</span><p><strong>연금 계좌와 함께 쓰면 더 효율적이에요</strong><small>노후 자금은 연금저축의 국내상장 ETF로 나눠 세액공제를 챙기세요.</small></p></div>
          </div>
          <div className="allocation-plan"><div><span>QQQM 직투</span><strong>60%</strong></div><div><span>연금저축 나스닥100</span><strong>30%</strong></div><div><span>달러 현금</span><strong>10%</strong></div></div>
          <button className="primary-button full">이 전략으로 모의투자 시작하기 <Icon name="chevron" size={15} /></button>
          <p className="disclaimer"><Icon name="info" size={14} /> AI 분석은 투자 권유가 아니며, 최종 판단과 책임은 투자자에게 있어요.</p>
        </article>
      </section>
    </main>
  );
}

function PortfolioScreen() {
  return (
    <main className="page content-page">
      <section className="page-title compact">
        <div><p className="eyebrow">MY PORTFOLIO</p><h1>내 포트폴리오</h1><p>계좌를 합쳐 전체 자산과 위험도를 한눈에 확인하세요.</p></div>
        <button className="primary-button"><Icon name="plus" size={16} /> 계좌 연결</button>
      </section>
      <section className="portfolio-summary">
        <article className="card portfolio-total"><span>평가 금액</span><h2>22,686,750원</h2><p><b>+1,410,040원</b> (+6.63%)</p><div className="long-bar">{holdings.map((h) => <i key={h.symbol} style={{ width: `${h.weight}%`, background: h.color }} />)}</div><div className="portfolio-legend">{holdings.map((h) => <span key={h.symbol}><i style={{ background: h.color }} />{h.symbol} {h.weight}%</span>)}</div></article>
        <article className="card metric-card"><span>예상 연 보수</span><h3>0.18%</h3><p>약 40,800원</p><small className="positive-text">동일 전략 평균보다 0.12% 낮아요</small></article>
        <article className="card metric-card"><span>위험도</span><h3>성장형</h3><p>변동성 18.4%</p><small>미국 기술주 비중이 높아요</small></article>
      </section>
      <article className="card holdings-card">
        <div className="card-heading"><div><span className="label">보유 자산</span><p>실시간 평가 기준</p></div><button className="add-button">수익률순 <Icon name="chevron" size={13} /></button></div>
        <div className="holdings-head"><span>자산</span><span>보유</span><span>평가 금액</span><span>평가 손익</span><span>비중</span><span /></div>
        {holdings.map((item) => <div className="holding-row" key={item.symbol}><span className="holding-name"><i style={{ background: item.color }}>{item.symbol.slice(0, 1)}</i><span><strong>{item.symbol}</strong><small>{item.name}</small></span></span><span>{item.quantity}</span><strong>{item.value}</strong><span className={item.positive ? 'up' : 'down'}><strong>{item.profit}</strong><small>{item.rate}</small></span><span><i className="weight-bar"><b style={{ width: `${item.weight * 2}%`, background: item.color }} /></i>{item.weight}%</span><button><Icon name="more" size={18} /></button></div>)}
      </article>
    </main>
  );
}

const lessons = [
  { category: 'ETF 비교', title: 'QQQ와 QQQM, 무엇이 다를까요?', desc: '같은 지수를 추종해도 보수와 거래량이 달라요.', time: '6분', color: 'blue' },
  { category: '절세 계좌', title: 'ISA 만기 자금, 연금으로 옮기면?', desc: '추가 세액공제를 받는 연계 전략을 알아봐요.', time: '8분', color: 'green' },
  { category: '연금', title: '연금저축과 IRP의 결정적 차이', desc: '인출 조건과 투자 가능 자산을 비교해요.', time: '7분', color: 'purple' },
  { category: '자격증', title: '투자자산운용사 핵심 개념 노트', desc: '포트폴리오 이론부터 세제까지 정리했어요.', time: '12분', color: 'orange' },
  { category: '해외주식', title: '달러를 직접 보유한다는 것', desc: '환전, 유동성, 양도소득세를 쉽게 설명해요.', time: '9분', color: 'navy' },
  { category: '투자 습관', title: '장기 적립식 투자의 체크리스트', desc: '수익률보다 오래 지키는 규칙을 만들어요.', time: '5분', color: 'mint' },
];

function LearnScreen() {
  const [filter, setFilter] = useState('전체');
  return (
    <main className="page content-page">
      <section className="learn-hero">
        <div><p className="eyebrow">MOA LEARN</p><h1>어려운 투자를<br />내 것이 되는 지식으로.</h1><p>절세부터 자격증 핵심 개념까지, 검증된 콘텐츠만 모았어요.</p></div>
        <div className="today-lesson"><span>오늘의 5분 공부</span><strong>복리 효과는 언제부터<br />눈에 보일까요?</strong><button>이어보기 <Icon name="chevron" size={14} /></button></div>
      </section>
      <div className="filter-tabs">{['전체', 'ETF 비교', '절세 계좌', '연금', '해외주식', '투자자산운용사'].map((item) => <button key={item} onClick={() => setFilter(item)} className={filter === item ? 'active' : ''}>{item}</button>)}</div>
      <section className="lesson-grid">
        {lessons.filter((lesson) => filter === '전체' || lesson.category === filter || (filter === '투자자산운용사' && lesson.category === '자격증')).map((lesson) => <article className="card lesson-card" key={lesson.title}><div className={`lesson-visual ${lesson.color}`}><Icon name={lesson.category.includes('계좌') || lesson.category === '연금' ? 'wallet' : lesson.category === '자격증' ? 'book' : 'chart'} size={30} /><span>{lesson.category}</span></div><div className="lesson-copy"><span>{lesson.category}</span><h3>{lesson.title}</h3><p>{lesson.desc}</p><small><Icon name="clock" size={13} /> {lesson.time} 읽기</small></div></article>)}
      </section>
    </main>
  );
}

function App() {
  const [active, setActive] = useState('home');
  const [toast, setToast] = useState('');
  const title = useMemo(() => navigation.find((item) => item.id === active)?.label ?? '홈', [active]);

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 2800);
  };

  const handleSearch = (query: string) => {
    if (!query.trim()) return;
    setActive('market');
    showToast(`“${query}” 검색 결과를 불러왔어요.`);
  };

  return (
    <div className="app-shell">
      <Sidebar active={active} onChange={setActive} />
      <div className="workspace">
        <Topbar onSearch={handleSearch} onNotify={() => showToast('새로운 절세 알림이 2개 있어요.')} />
        <div className="mobile-title"><Logo /><span>{title}</span></div>
        {active === 'home' && <HomeScreen onNavigate={setActive} />}
        {active === 'market' && <MarketScreen onToast={showToast} />}
        {active === 'tax' && <TaxScreen />}
        {active === 'strategy' && <StrategyScreen />}
        {active === 'portfolio' && <PortfolioScreen />}
        {active === 'learn' && <LearnScreen />}
      </div>
      {toast && <div className="toast"><span><Icon name="check" size={15} /></span>{toast}</div>}
    </div>
  );
}

export default App;

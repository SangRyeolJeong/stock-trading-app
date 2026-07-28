import { useQueries, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { useUserPreferences } from '../data/userPreferences';
import { marketApi } from '../services/marketApi';
import { paperApi } from '../services/paperApi';
import { taxApi } from '../services/taxApi';
import type { PortfolioSummary } from '../types/api';
import { formatChangeRate, formatQuotePrice } from '../utils/format';

const DEFAULT_FAVORITES = ['QQQM', '005930', 'AAPL', 'NVDA', '360750'];
const ALLOCATION_COLORS = ['#5578ff', '#6cd2b8', '#ffb15c', '#9a7cff', '#4f98d8'];

function loadFavorites() {
  try {
    const stored = window.localStorage.getItem('moa-market-favorites');
    const parsed = stored ? JSON.parse(stored) as unknown : null;
    return Array.isArray(parsed) && parsed.every((item) => typeof item === 'string')
      ? parsed
      : DEFAULT_FAVORITES;
  } catch {
    return DEFAULT_FAVORITES;
  }
}

function getTodayLabel() {
  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(new Date());
}

function getGreeting() {
  const hourPart = new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    hour: 'numeric',
    hourCycle: 'h23',
  }).formatToParts(new Date()).find((part) => part.type === 'hour');
  const hour = Number(hourPart?.value ?? 12);
  if (hour < 12) return '좋은 아침이에요';
  if (hour < 18) return '좋은 오후예요';
  return '좋은 저녁이에요';
}

function formatKrw(value: number) {
  return `${Math.round(value).toLocaleString('ko-KR')}원`;
}

function toKrw(value: string | number, currency: 'KRW' | 'USD', usdKrwRate: number) {
  return Number(value) * (currency === 'USD' ? usdKrwRate : 1);
}

function getPortfolioMetrics(portfolio: PortfolioSummary | undefined, usdKrwRate: number) {
  const summaries = portfolio?.currencies ?? [];
  const total = summaries.reduce(
    (sum, item) => sum + toKrw(item.total_value, item.currency, usdKrwRate),
    0,
  );
  const cash = summaries.reduce(
    (sum, item) => sum + toKrw(item.cash, item.currency, usdKrwRate),
    0,
  );
  const unrealizedPnl = summaries.reduce(
    (sum, item) => sum + toKrw(item.unrealized_pnl, item.currency, usdKrwRate),
    0,
  );
  const realizedPnl = summaries.reduce(
    (sum, item) => sum + toKrw(item.realized_pnl, item.currency, usdKrwRate),
    0,
  );
  const pnl = unrealizedPnl + realizedPnl;
  const principal = total - pnl;

  return {
    total,
    cash,
    invested: Math.max(total - cash, 0),
    pnl,
    returnRate: principal > 0 ? (pnl / principal) * 100 : 0,
  };
}

export function HomePage() {
  const navigate = useNavigate();
  const preferences = useUserPreferences();
  const favorites = loadFavorites();
  const visibleFavorites = favorites.slice(0, 4);
  const portfolioQuery = useQuery({
    queryKey: ['paper-portfolio', 'demo-account'],
    queryFn: () => paperApi.getPortfolioSummary('demo-account'),
    staleTime: 15_000,
  });
  const exchangeRateQuery = useQuery({
    queryKey: ['exchange-rate', 'USD', 'KRW'],
    queryFn: () => marketApi.getExchangeRate('USD', 'KRW'),
    staleTime: 60_000,
  });
  const quoteQueries = useQueries({
    queries: visibleFavorites.map((symbol) => ({
      queryKey: ['quote', symbol],
      queryFn: () => marketApi.getQuote(symbol),
      staleTime: 15_000,
    })),
  });
  const taxQuery = useQuery({
    queryKey: [
      'tax-simulation',
      preferences.annualSalaryKrw,
      preferences.monthlyInvestmentKrw,
      preferences.investmentYears,
      preferences.annualReturnRatePct,
      preferences.withdrawalAge,
    ],
    queryFn: () => taxApi.simulate({
      annual_salary_krw: preferences.annualSalaryKrw,
      monthly_contribution_krw: preferences.monthlyInvestmentKrw,
      investment_years: preferences.investmentYears,
      annual_return_rate_pct: preferences.annualReturnRatePct,
      withdrawal_age: preferences.withdrawalAge,
    }),
    staleTime: 5 * 60_000,
  });

  const portfolio = portfolioQuery.data;
  const usdKrwRate = Number(exchangeRateQuery.data?.rate ?? 0);
  const hasUsdAssets = portfolio?.currencies.some(
    (item) => item.currency === 'USD' && Number(item.total_value) !== 0,
  ) ?? false;
  const portfolioReady = Boolean(portfolio) && (!hasUsdAssets || usdKrwRate > 0);
  const metrics = getPortfolioMetrics(portfolio, usdKrwRate);
  const investedWeight = metrics.total > 0 ? (metrics.invested / metrics.total) * 100 : 0;
  const cashWeight = Math.max(100 - investedWeight, 0);
  const taxWinner = taxQuery.data?.results.find(
    (result) => result.account_type === taxQuery.data?.best_account_type,
  );
  const taxSaving = Number(taxWinner?.tax_savings_vs_direct ?? 0);
  const taxSavingText = !taxWinner
    ? '계산 중'
    : taxSaving >= 100_000_000
      ? `${(taxSaving / 100_000_000).toFixed(2)}억원`
      : `${Math.round(taxSaving / 10_000).toLocaleString('ko-KR')}만원`;

  const rawAllocations = [
    ...(portfolio?.positions ?? []).map((position) => ({
      symbol: position.symbol,
      value: toKrw(position.market_value ?? 0, position.currency, usdKrwRate),
    })),
    { symbol: '현금', value: metrics.cash },
  ]
    .filter((item) => item.value > 0)
    .sort((left, right) => right.value - left.value);
  const allocations = rawAllocations.length <= 5
    ? rawAllocations
    : [
        ...rawAllocations.slice(0, 4),
        {
          symbol: '기타',
          value: rawAllocations.slice(4).reduce((sum, item) => sum + item.value, 0),
        },
      ];
  const allocationItems = allocations.map((item, index) => ({
    ...item,
    color: ALLOCATION_COLORS[index % ALLOCATION_COLORS.length],
    weight: metrics.total > 0 ? (item.value / metrics.total) * 100 : 0,
  }));
  let gradientOffset = 0;
  const donutGradient = allocationItems.length
    ? `conic-gradient(${allocationItems.map((item) => {
        const start = gradientOffset;
        gradientOffset += item.weight;
        return `${item.color} ${start}% ${gradientOffset}%`;
      }).join(', ')})`
    : '#252d39';
  const largestAllocation = allocationItems[0];
  const allocationTip = !portfolio?.positions.length
    ? '종목을 매수하면 자산별 비중을 자동으로 계산해요.'
    : largestAllocation && largestAllocation.weight >= 50
      ? `${largestAllocation.symbol} 비중이 ${largestAllocation.weight.toFixed(1)}%예요. 집중 위험을 확인해 보세요.`
      : largestAllocation
        ? `가장 큰 비중은 ${largestAllocation.symbol} ${largestAllocation.weight.toFixed(1)}%예요.`
        : '포트폴리오 비중을 계산하고 있어요.';

  const portfolioError = portfolioQuery.isError || exchangeRateQuery.isError;
  const watchlistLoading = quoteQueries.some((query) => query.isLoading);
  const watchlistError = quoteQueries.length > 0 && quoteQueries.every((query) => query.isError);

  return (
    <PageContainer className="home-page">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">{getTodayLabel()}</p>
          <h1>{getGreeting()}, {preferences.displayName}님</h1>
          <p>오늘도 세금은 줄이고, 투자는 길게 이어가 볼까요?</p>
        </div>
        <button className="primary-button" onClick={() => navigate('/strategy')}><Icon name="sparkles" size={17} /> 전략 추천 받기</button>
      </section>

      <section className="dashboard-grid">
        <article className="card asset-card">
          <div className="card-heading">
            <div><span className="label">모의투자 총 자산</span><span className="small-link">KRW 환산</span></div>
            <button className="more-button" onClick={() => navigate('/portfolio')} aria-label="포트폴리오 보기"><Icon name="chevron" size={19} /></button>
          </div>
          <div className="asset-value">
            <strong>{portfolioReady ? Math.round(metrics.total).toLocaleString('ko-KR') : '—'}</strong>
            <span>원</span>
          </div>
          <div className={`asset-change ${metrics.pnl >= 0 ? 'positive' : 'negative'}`}>
            <span><Icon name={metrics.pnl >= 0 ? 'arrowUp' : 'arrowDown'} size={13} /> {portfolioReady ? formatKrw(Math.abs(metrics.pnl)) : '계산 중'}</span>
            <b>{portfolioReady ? `${metrics.returnRate >= 0 ? '+' : ''}${metrics.returnRate.toFixed(2)}%` : '—'}</b>
            <em>평가·실현손익 합계</em>
          </div>
          {portfolioError && (
            <div className="data-status error">
              <span>원장 또는 환율을 불러오지 못했습니다.</span>
              <button onClick={() => { portfolioQuery.refetch(); exchangeRateQuery.refetch(); }}>다시 시도</button>
            </div>
          )}
          <div className="asset-composition">
            <div className="composition-heading">
              <span>현재 자산 구성</span>
              <small>{exchangeRateQuery.data ? `USD/KRW ${usdKrwRate.toLocaleString('ko-KR')}` : '환율 확인 중'}</small>
            </div>
            <div className="composition-bar" aria-label={`투자자산 ${investedWeight.toFixed(1)}%, 현금 ${cashWeight.toFixed(1)}%`}>
              <i style={{ width: `${investedWeight}%` }} />
              <b style={{ width: `${cashWeight}%` }} />
            </div>
            <div className="composition-legend">
              <div><span><i className="invested-dot" />투자자산</span><strong>{portfolioReady ? formatKrw(metrics.invested) : '—'}</strong><small>{investedWeight.toFixed(1)}%</small></div>
              <div><span><i className="cash-dot" />현금</span><strong>{portfolioReady ? formatKrw(metrics.cash) : '—'}</strong><small>{cashWeight.toFixed(1)}%</small></div>
            </div>
          </div>
        </article>

        <article className="card tax-score-card">
          <div className="card-heading">
            <div>
              <span className="label">절세 시뮬레이션</span>
              <p>월 {Math.round(preferences.monthlyInvestmentKrw / 10_000).toLocaleString('ko-KR')}만원 · {preferences.investmentYears}년 설정</p>
            </div>
            <button className="more-button" onClick={() => navigate('/tax-planner')}><Icon name="chevron" size={18} /></button>
          </div>
          {taxQuery.isError && (
            <div className="data-status error">
              <span>절세 계산을 불러오지 못했습니다.</span>
              <button onClick={() => taxQuery.refetch()}>다시 시도</button>
            </div>
          )}
          <div className="score-wrap">
            <div className="score-ring" style={{ background: `conic-gradient(#557eff 0 ${taxWinner?.score ?? 0}%, #252d39 ${taxWinner?.score ?? 0}% 100%)` }}><div><strong>{taxWinner?.score ?? '—'}</strong><span>/ 100점</span></div></div>
            <div className="score-copy"><span className="pill positive">{taxQuery.data?.rules.version ?? '계산 중'}</span><strong>{taxWinner?.name ?? '분석 중'}</strong><p>동일 조건의 해외직투보다<br />약 {taxSavingText} 유리한 추정치예요.</p></div>
          </div>
          <button className="soft-button" onClick={() => navigate('/tax-planner')}>내 조건으로 다시 계산 <Icon name="chevron" size={15} /></button>
        </article>

        <article className="card watch-card">
          <div className="card-heading">
            <div><span className="label">관심 종목</span><p>{watchlistLoading ? '시세 갱신 중' : '최근 시세'}</p></div>
            <button className="add-button" onClick={() => navigate('/market')}><Icon name="plus" size={15} /> 편집</button>
          </div>
          <div className="watch-list">
            {quoteQueries.map((query, index) => {
              const symbol = visibleFavorites[index];
              const quote = query.data;
              return (
                <button key={symbol} className="watch-row" onClick={() => navigate(`/market/${symbol}`)}>
                  <span className={`stock-logo ${symbol.match(/^\d{6}$/) ? 'kr' : 'us'}`}>{symbol === '005930' ? 'S' : symbol.slice(0, 1)}</span>
                  <span className="stock-name"><strong>{symbol}</strong><small>{quote?.name ?? (query.isError ? '시세를 불러오지 못함' : '불러오는 중')}</small></span>
                  <span className="stock-price"><strong>{quote ? formatQuotePrice(quote.price, quote.currency) : '—'}</strong><small className={quote && Number(quote.change_rate) >= 0 ? 'up' : 'down'}>{quote ? formatChangeRate(quote.change_rate) : '—'}</small></span>
                </button>
              );
            })}
            {visibleFavorites.length === 0 && <div className="dashboard-empty">관심 종목을 추가해 보세요.</div>}
            {watchlistError && <div className="dashboard-inline-error">시세 서버 연결을 확인해 주세요.</div>}
          </div>
          <button className="text-button" onClick={() => navigate(`/market/${visibleFavorites[0] ?? 'QQQM'}`)}>관심 종목 전체보기 <Icon name="chevron" size={14} /></button>
        </article>

        <article className="card insight-card">
          <div className="insight-top">
            <span className="ai-badge"><Icon name="sparkles" size={15} /> 규칙 기반 인사이트</span>
            <span className="new-badge">2026</span>
          </div>
          <h2>장기투자, 어떤 계좌와<br />상품이 가장 유리할까요?</h2>
          <p>30년 장기투자와 월 50만원 적립을 기준으로<br />세후 수익을 비교했어요.</p>
          <div className="compare-preview">
            <div><span>추천 조합</span><strong>{taxWinner ? `${taxWinner.name} + ${taxWinner.recommended_product}` : '계산 중'}</strong></div>
            <div><span>예상 절세</span><strong>약 {taxSavingText}</strong></div>
          </div>
          <button onClick={() => navigate('/tax-planner')}>계산 근거 자세히 보기 <Icon name="chevron" size={15} /></button>
          <span className="decor-orb orb-one" /><span className="decor-orb orb-two" />
        </article>

        <article className="card allocation-card">
          <div className="card-heading">
            <div><span className="label">포트폴리오 구성</span><p>원장 평가액 · 원화 환산</p></div>
            <button className="more-button" onClick={() => navigate('/portfolio')}><Icon name="chevron" size={18} /></button>
          </div>
          <div className="allocation-content">
            <div className="donut" style={{ background: donutGradient }}><div><strong>{portfolio?.positions.length ?? '—'}</strong><span>보유 종목</span></div></div>
            <div className="legend">
              {allocationItems.map((item) => <div key={item.symbol}><i style={{ background: item.color }} /><span>{item.symbol}</span><b>{item.weight.toFixed(1)}%</b></div>)}
              {portfolioReady && allocationItems.length === 0 && <span className="dashboard-empty">표시할 자산이 없습니다.</span>}
            </div>
          </div>
          <div className="rebalance-tip"><Icon name="info" size={16} /><span><strong>비중 점검</strong> {allocationTip}</span></div>
        </article>
      </section>
    </PageContainer>
  );
}

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from '../app/toast';
import ChartSection from '../components/ChartSection';
import CompanyOverview from '../components/CompanyOverview';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import OrderBook from '../components/OrderBook';
import { useQuote } from '../hooks/useQuote';
import { useQuoteStream } from '../hooks/useQuoteStream';
import { marketApi, type MarketFilter } from '../services/marketApi';
import { paperApi } from '../services/paperApi';
import type { Instrument } from '../types/api';
import { formatChangeRate, formatQuotePrice, formatUpdatedAt } from '../utils/format';

const DEFAULT_FAVORITES = ['QQQM', '005930', 'AAPL', 'NVDA', '360750'];
const BROWSER_TABS = [
  { key: 'favorites', label: '관심' },
  { key: 'domestic', label: '국내' },
  { key: 'overseas', label: '해외' },
  { key: 'etf', label: 'ETF' },
] as const;
const PERIODS = [
  { label: '1주', days: 5 },
  { label: '1개월', days: 22 },
  { label: '3개월', days: 66 },
  { label: '6개월', days: 126 },
  { label: '1년', days: 252 },
] as const;

type BrowserTab = (typeof BROWSER_TABS)[number]['key'];

function formatCash(value: number, currency: 'KRW' | 'USD') {
  return new Intl.NumberFormat(currency === 'KRW' ? 'ko-KR' : 'en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: currency === 'KRW' ? 0 : 2,
  }).format(value);
}

function formatVolume(value: string | undefined) {
  const number = Number(value ?? 0);
  return new Intl.NumberFormat('ko-KR', {
    notation: number >= 100_000 ? 'compact' : 'standard',
    maximumFractionDigits: 1,
  }).format(number);
}

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

function TradePanel({
  symbol,
  price,
  currency,
}: {
  symbol: string;
  price: number;
  currency: 'KRW' | 'USD';
}) {
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [quantity, setQuantity] = useState(1);
  const [customLimitPrice, setCustomLimitPrice] = useState<number | null>(null);
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const accountsQuery = useQuery({
    queryKey: ['paper-accounts'],
    queryFn: paperApi.getAccounts,
  });
  const positionsQuery = useQuery({
    queryKey: ['paper-positions', 'demo-account'],
    queryFn: paperApi.getPositions,
  });
  const exchangeRateQuery = useQuery({
    queryKey: ['exchange-rate', 'USD', 'KRW'],
    queryFn: () => marketApi.getExchangeRate('USD', 'KRW'),
    enabled: currency === 'USD',
    staleTime: 60_000,
  });
  const usdKrwRate = Number(exchangeRateQuery.data?.rate ?? 0);
  const cashBalance = accountsQuery.data?.[0]?.cash_balances.find(
    (balance) => balance.currency === currency,
  );
  const availableCash = Number(cashBalance?.amount ?? 0);
  const position = positionsQuery.data?.find((item) => item.symbol === symbol);
  const availableQuantity = Math.floor(Number(position?.quantity ?? 0));
  const limitPrice = customLimitPrice ?? price;
  const executionPrice = orderType === 'limit' ? limitPrice : price;
  const estimatedGross = executionPrice * quantity;
  const estimatedFee = estimatedGross * 0.001;
  const orderError = executionPrice <= 0
    ? '유효한 주문 가격이 필요합니다.'
    : side === 'buy' && estimatedGross + estimatedFee > availableCash
      ? '주문 가능 금액을 초과했습니다.'
      : side === 'sell' && quantity > availableQuantity
        ? '보유 수량을 초과했습니다.'
        : '';
  const orderMutation = useMutation({
    mutationFn: paperApi.createOrder,
    onSuccess: (order) => {
      showToast(order.status === 'filled'
        ? `${order.symbol} ${order.quantity}주가 ${order.filled_price}에 모의 체결됐어요.`
        : `${order.symbol} ${order.quantity}주 지정가 주문을 접수했어요.`);
      void queryClient.invalidateQueries({ queryKey: ['paper-accounts'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-positions'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-portfolio'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-orders'] });
      setQuantity(1);
    },
    onError: (error: Error) => showToast(error.message),
  });

  const selectOrderType = (nextType: 'market' | 'limit') => {
    setOrderType(nextType);
    if (nextType === 'limit' && price > 0) setCustomLimitPrice(price);
  };

  const selectSide = (nextSide: 'buy' | 'sell') => {
    setSide(nextSide);
    setQuantity(1);
  };

  const adjustLimitPrice = (direction: -1 | 1) => {
    if (orderType !== 'limit') return;
    const step = currency === 'KRW' ? 1 : 0.01;
    const nextPrice = Math.max(step, limitPrice + step * direction);
    setCustomLimitPrice(currency === 'KRW' ? Math.round(nextPrice) : Number(nextPrice.toFixed(2)));
  };

  const setOrderRatio = (ratio: number) => {
    if (side === 'sell') {
      setQuantity(Math.max(1, Math.floor(availableQuantity * ratio)));
      return;
    }
    if (executionPrice <= 0) return;
    setQuantity(Math.max(1, Math.floor((availableCash * ratio) / (executionPrice * 1.001))));
  };

  const submitOrder = () => {
    if (orderError) {
      showToast(orderError);
      return;
    }
    orderMutation.mutate({
      symbol,
      side,
      order_type: orderType,
      quantity,
      limit_price: orderType === 'limit'
        ? currency === 'KRW' ? String(Math.round(limitPrice)) : limitPrice.toFixed(2)
        : undefined,
      idempotency_key: crypto.randomUUID(),
    });
  };

  return (
    <aside className="trade-panel card">
      <div className="trade-tabs">
        <button className={side === 'buy' ? 'active buy' : ''} onClick={() => selectSide('buy')}>구매</button>
        <button className={side === 'sell' ? 'active sell' : ''} onClick={() => selectSide('sell')}>판매</button>
      </div>
      <div className="available">
        <span>{side === 'buy' ? '주문 가능 금액' : '보유 수량'}</span>
        <strong>
          {side === 'buy'
            ? cashBalance ? formatCash(availableCash, currency) : '불러오는 중'
            : positionsQuery.isLoading ? '불러오는 중' : `${availableQuantity.toLocaleString('ko-KR')}주`}
        </strong>
      </div>
      <label>주문 방식</label>
      <div className="segmented">
        <button className={orderType === 'market' ? 'active' : ''} onClick={() => selectOrderType('market')}>시장가</button>
        <button className={orderType === 'limit' ? 'active' : ''} onClick={() => selectOrderType('limit')}>지정가</button>
      </div>
      <label>주문 가격</label>
      <div className="price-input">
        <button aria-label="가격 내리기" onClick={() => adjustLimitPrice(-1)} disabled={orderType === 'market'}>−</button>
        <div>
          <strong>{executionPrice > 0 ? formatCash(executionPrice, currency) : '시세 대기 중'}</strong>
          <span>
            {currency === 'USD' && usdKrwRate && executionPrice > 0
              ? `약 ${formatCash(executionPrice * usdKrwRate, 'KRW')}`
              : orderType === 'market' ? '현재 시세 기준' : '모의 지정가'}
          </span>
        </div>
        <button aria-label="가격 올리기" onClick={() => adjustLimitPrice(1)} disabled={orderType === 'market'}>＋</button>
      </div>
      <label>수량</label>
      <div className="quantity-input"><button onClick={() => setQuantity(Math.max(1, quantity - 1))}>−</button><strong>{quantity}주</strong><button onClick={() => setQuantity(quantity + 1)}>＋</button></div>
      <div className="quick-amounts">
        {[0.1, 0.25, 0.5, 1].map((ratio) => (
          <button key={ratio} onClick={() => setOrderRatio(ratio)} disabled={side === 'sell' && availableQuantity < 1}>
            {ratio === 1 ? '최대' : `${ratio * 100}%`}
          </button>
        ))}
      </div>
      {orderType === 'limit' && <p className="limit-order-note">현재 시세가 지정가 조건을 충족하면 시세로 체결되고, 그 전까지 주문 원장에 대기합니다.</p>}
      {orderError && !accountsQuery.isLoading && !positionsQuery.isLoading && <p className="order-validation">{orderError}</p>}
      <div className="order-summary"><div><span>예상 주문 금액</span><strong>{formatCash(estimatedGross, currency)}</strong></div><div><span>예상 수수료</span><strong>{formatCash(estimatedFee, currency)}</strong></div></div>
      <button className={`order-button ${side}`} onClick={submitOrder} disabled={orderMutation.isPending || Boolean(orderError) || accountsQuery.isLoading || positionsQuery.isLoading}>
        {orderMutation.isPending ? '주문 접수 중…' : `${quantity}주 ${side === 'buy' ? '구매하기' : '판매하기'}`}
      </button>
      <p className="paper-note"><Icon name="shield" size={14} /> 모의투자 주문으로 실제 돈은 사용되지 않아요</p>
    </aside>
  );
}

function InstrumentRow({
  instrument,
  selected,
  favorite,
  onSelect,
  onToggleFavorite,
}: {
  instrument: Instrument;
  selected: boolean;
  favorite: boolean;
  onSelect: () => void;
  onToggleFavorite: () => void;
}) {
  return (
    <div className={`instrument-row ${selected ? 'selected' : ''}`}>
      <button className="instrument-main" onClick={onSelect}>
        <span className={`stock-logo ${instrument.country === 'KR' ? 'kr' : 'us'}`}>{instrument.symbol.slice(0, 1)}</span>
        <span className="stock-name"><strong>{instrument.symbol}</strong><small>{instrument.name}</small></span>
        <span className="instrument-market"><strong>{instrument.market}</strong><small>{instrument.asset_type.toUpperCase()}</small></span>
      </button>
      <button className={`favorite-button ${favorite ? 'active' : ''}`} onClick={onToggleFavorite} aria-label={`${instrument.symbol} 관심종목 ${favorite ? '해제' : '추가'}`}>
        {favorite ? '★' : '☆'}
      </button>
    </div>
  );
}

export function MarketPage() {
  const [periodDays, setPeriodDays] = useState(66);
  const [activeTab, setActiveTab] = useState('차트');
  const [browserTab, setBrowserTab] = useState<BrowserTab>('favorites');
  const [searchInput, setSearchInput] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [favorites, setFavorites] = useState<string[]>(loadFavorites);
  const { symbol: routeSymbol = 'QQQM' } = useParams();
  const symbol = routeSymbol.toUpperCase();
  const navigate = useNavigate();

  useEffect(() => {
    const timer = window.setTimeout(() => setSearchTerm(searchInput.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    window.localStorage.setItem('moa-market-favorites', JSON.stringify(favorites));
  }, [favorites]);

  const marketFilter: MarketFilter = browserTab === 'favorites' ? 'all' : browserTab;
  const instrumentsQuery = useQuery({
    queryKey: ['instruments', searchTerm, marketFilter],
    queryFn: () => marketApi.searchInstruments(searchTerm, marketFilter, searchTerm ? 50 : 100),
    staleTime: 24 * 60 * 60 * 1000,
  });
  const quoteQuery = useQuote(symbol);
  const { tick, status: streamStatus } = useQuoteStream(symbol);
  const candlesQuery = useQuery({
    queryKey: ['candles', symbol],
    queryFn: () => marketApi.getCandles(symbol, 252),
    enabled: Boolean(symbol),
    staleTime: 5 * 60 * 1000,
  });
  const orderBookQuery = useQuery({
    queryKey: ['orderbook', symbol],
    queryFn: () => marketApi.getOrderBook(symbol),
    enabled: Boolean(symbol) && activeTab === '호가',
    staleTime: 5_000,
    refetchInterval: activeTab === '호가' ? 5_000 : false,
  });
  const overviewQuery = useQuery({
    queryKey: ['security-overview', symbol],
    queryFn: () => marketApi.getSecurityOverview(symbol),
    enabled: Boolean(symbol) && activeTab === '기업정보',
    staleTime: 60_000,
  });

  const allInstruments = instrumentsQuery.data?.items ?? [];
  const displayedInstruments = browserTab === 'favorites' && !searchTerm
    ? allInstruments.filter((item) => favorites.includes(item.symbol))
    : allInstruments;
  const selectedInstrument = allInstruments.find((item) => item.symbol === symbol);
  const quote = quoteQuery.data;
  const currentPrice = tick?.price ?? Number(quote?.price ?? 0);
  const currency = quote?.currency ?? selectedInstrument?.currency ?? (symbol.match(/^\d{6}$/) ? 'KRW' : 'USD');
  const candles = candlesQuery.data?.candles;
  const visibleCandles = useMemo(() => (candles ?? []).slice(-periodDays), [candles, periodDays]);
  const latestCandle = candles?.[candles.length - 1];
  const previousCandle = candles?.[candles.length - 2];
  const exchangeName = selectedInstrument?.market ?? (currency === 'KRW' ? 'KRX' : '미국');
  const dataSourceLabel = instrumentsQuery.data?.source === 'kis-master'
    ? 'KIS 종목 마스터'
    : instrumentsQuery.data?.source === 'kis-master-cache'
      ? 'KIS 종목 마스터 캐시'
      : '기본 종목 목록';

  const toggleFavorite = (target: string) => {
    setFavorites((current) => current.includes(target)
      ? current.filter((item) => item !== target)
      : [...current, target]);
  };

  return (
    <PageContainer className="market-page">
      <div className="market-layout">
        <aside className="stock-browser card">
          <div className="browser-title"><div><h2>종목 탐색</h2><small>{dataSourceLabel}</small></div><span>{instrumentsQuery.data?.total ?? 0}</span></div>
          <div className="browser-search"><Icon name="search" size={16} /><input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="종목명·티커 검색" /></div>
          <div className="browser-tabs">
            {BROWSER_TABS.map((tab) => <button key={tab.key} className={browserTab === tab.key ? 'active' : ''} onClick={() => setBrowserTab(tab.key)}>{tab.label}</button>)}
          </div>
          <div className="browser-list">
            {instrumentsQuery.isLoading && <div className="browser-state">종목 목록을 준비하고 있어요…</div>}
            {instrumentsQuery.isError && <div className="browser-state error">종목 목록을 불러오지 못했습니다.<button onClick={() => instrumentsQuery.refetch()}>다시 시도</button></div>}
            {!instrumentsQuery.isLoading && displayedInstruments.length === 0 && <div className="browser-state">검색 결과가 없습니다.</div>}
            {displayedInstruments.map((instrument) => (
              <InstrumentRow
                key={`${instrument.exchange_code}-${instrument.symbol}`}
                instrument={instrument}
                selected={instrument.symbol === symbol}
                favorite={favorites.includes(instrument.symbol)}
                onSelect={() => navigate(`/market/${instrument.symbol}`)}
                onToggleFavorite={() => toggleFavorite(instrument.symbol)}
              />
            ))}
          </div>
        </aside>

        <section className="stock-detail card">
          <div className="stock-header">
            <div className="stock-identity">
              <span className="stock-logo large">{symbol.slice(0, 1)}</span>
              <div><span>{quote?.name ?? selectedInstrument?.name ?? symbol} · {exchangeName}</span><h1>{symbol} <button className={favorites.includes(symbol) ? 'favorite-active' : ''} onClick={() => toggleFavorite(symbol)}>{favorites.includes(symbol) ? '★' : '☆'}</button></h1></div>
            </div>
            <div className="live-price">
              <strong>{quoteQuery.isLoading ? '불러오는 중' : currentPrice > 0 ? formatQuotePrice(currentPrice, currency) : '—'}</strong>
              <span className={Number(quote?.change_rate ?? 0) >= 0 ? 'up' : 'down'}>{quote ? formatChangeRate(quote.change_rate) : '—'}</span>
              <small>{streamStatus === 'connected' ? '시세 연결' : streamStatus === 'reconnecting' ? '재연결 중' : '연결 중'} · {quote?.market_open ? '장중' : '장 마감'} · {formatUpdatedAt(tick?.as_of ?? quote?.as_of)}</small>
            </div>
          </div>
          {quoteQuery.isError && <div className="data-status error"><span>현재 시세를 불러오지 못했습니다.</span><button onClick={() => quoteQuery.refetch()}>다시 시도</button></div>}
          <div className="detail-tabs">{['차트', '호가', '기업정보'].map((tab) => <button key={tab} onClick={() => setActiveTab(tab)} className={activeTab === tab ? 'active' : ''}>{tab}</button>)}</div>
          {activeTab === '차트' ? (
            <>
              <div className="chart-toolbar">
                <div>{PERIODS.map((item) => <button key={item.label} className={periodDays === item.days ? 'active' : ''} onClick={() => setPeriodDays(item.days)}>{item.label}</button>)}</div>
                <div><span className="chart-source">{candlesQuery.data?.source === 'kis' ? 'KIS 일봉' : '데모 일봉'}</span><button onClick={() => candlesQuery.refetch()} aria-label="차트 새로고침"><Icon name="refresh" size={14} /></button></div>
              </div>
              <div className="main-chart">
                {candlesQuery.isLoading && <div className="chart-state">실제 일봉을 불러오는 중…</div>}
                {candlesQuery.isError && <div className="chart-state error">차트 데이터를 불러오지 못했습니다.<button onClick={() => candlesQuery.refetch()}>다시 시도</button></div>}
                {visibleCandles.length > 0 && <ChartSection symbol={symbol} currency={currency} candles={visibleCandles} />}
              </div>
              <div className="market-metrics">
                <div><span>최근 시가</span><strong>{latestCandle ? formatQuotePrice(latestCandle.open, currency) : '—'}</strong></div>
                <div><span>최근 고가 / 저가</span><strong>{latestCandle ? `${formatQuotePrice(latestCandle.high, currency)} / ${formatQuotePrice(latestCandle.low, currency)}` : '—'}</strong></div>
                <div><span>최근 거래량</span><strong>{formatVolume(latestCandle?.volume)}</strong></div>
                <div><span>전일 종가</span><strong>{previousCandle ? formatQuotePrice(previousCandle.close, currency) : '—'}</strong></div>
              </div>
              <div className="market-data-note"><Icon name="shield" size={15} /><span>시세와 일봉은 한국투자증권 Open API 기준입니다. 현재 실시간 스트림은 REST 캐시 갱신 방식이며 실제 주문은 전송하지 않습니다.</span></div>
            </>
          ) : activeTab === '호가' ? (
            <OrderBook
              data={orderBookQuery.data}
              currentPrice={currentPrice}
              isLoading={orderBookQuery.isLoading}
              isError={orderBookQuery.isError}
              onRetry={() => { void orderBookQuery.refetch(); }}
            />
          ) : (
            <CompanyOverview
              data={overviewQuery.data}
              currentPrice={currentPrice}
              isLoading={overviewQuery.isLoading}
              isError={overviewQuery.isError}
              onRetry={() => { void overviewQuery.refetch(); }}
            />
          )}
        </section>
        <TradePanel key={symbol} symbol={symbol} price={currentPrice} currency={currency} />
      </div>
    </PageContainer>
  );
}

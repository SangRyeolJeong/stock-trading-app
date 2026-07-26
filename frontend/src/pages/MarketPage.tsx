import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from '../app/toast';
import ChartSection from '../components/ChartSection';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { watchlist } from '../data/mock/market';
import { useQuote } from '../hooks/useQuote';
import { useQuoteStream } from '../hooks/useQuoteStream';
import { marketApi } from '../services/marketApi';
import { paperApi } from '../services/paperApi';
import { formatChangeRate, formatQuotePrice, formatUpdatedAt } from '../utils/format';

function formatCash(value: number, currency: 'KRW' | 'USD') {
  return new Intl.NumberFormat(currency === 'KRW' ? 'ko-KR' : 'en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: currency === 'KRW' ? 0 : 2,
  }).format(value);
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
  const [orderType, setOrderType] = useState('지정가');
  const [quantity, setQuantity] = useState(1);
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const accountsQuery = useQuery({
    queryKey: ['paper-accounts'],
    queryFn: paperApi.getAccounts,
  });
  const exchangeRateQuery = useQuery({
    queryKey: ['exchange-rate', 'USD', 'KRW'],
    queryFn: () => marketApi.getExchangeRate('USD', 'KRW'),
    enabled: currency === 'USD',
  });
  const usdKrwRate = Number(exchangeRateQuery.data?.rate ?? 0);
  const cashBalance = accountsQuery.data?.[0]?.cash_balances.find(
    (balance) => balance.currency === currency,
  );
  const orderMutation = useMutation({
    mutationFn: paperApi.createOrder,
    onSuccess: (order) => {
      showToast(`${order.symbol} ${order.quantity}주가 ${order.filled_price}에 모의 체결됐어요.`);
      void queryClient.invalidateQueries({ queryKey: ['paper-accounts'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-portfolio'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-orders'] });
    },
    onError: (error: Error) => showToast(error.message),
  });

  const submitOrder = () => {
    orderMutation.mutate({
      symbol,
      side,
      order_type: orderType === '지정가' ? 'limit' : 'market',
      quantity,
      limit_price: orderType === '지정가' ? price.toFixed(2) : undefined,
      account_id: 'demo-account',
      idempotency_key: crypto.randomUUID(),
    });
  };

  return (
    <aside className="trade-panel card">
      <div className="trade-tabs">
        <button className={side === 'buy' ? 'active buy' : ''} onClick={() => setSide('buy')}>구매</button>
        <button className={side === 'sell' ? 'active sell' : ''} onClick={() => setSide('sell')}>판매</button>
      </div>
      <div className="available">
        <span>주문 가능 금액</span>
        <strong>{cashBalance ? formatCash(Number(cashBalance.amount), currency) : '불러오는 중'}</strong>
      </div>
      <label>주문 방식</label>
      <div className="segmented">{['지정가', '시장가'].map((item) => <button key={item} className={orderType === item ? 'active' : ''} onClick={() => setOrderType(item)}>{item}</button>)}</div>
      <label>주문 가격</label>
      <div className="price-input"><button>−</button><div><strong>{formatCash(price, currency)}</strong><span>{currency === 'USD' && usdKrwRate ? `약 ${formatCash(price * usdKrwRate, 'KRW')}` : '현재 시세 기준'}</span></div><button>＋</button></div>
      <label>수량</label>
      <div className="quantity-input"><button onClick={() => setQuantity(Math.max(1, quantity - 1))}>−</button><strong>{quantity}주</strong><button onClick={() => setQuantity(quantity + 1)}>＋</button></div>
      <div className="quick-amounts">{['10%', '25%', '50%', '최대'].map((item) => <button key={item}>{item}</button>)}</div>
      <div className="order-summary"><div><span>예상 주문 금액</span><strong>{formatCash(price * quantity, currency)}</strong></div><div><span>예상 수수료</span><strong>{formatCash(price * quantity * 0.001, currency)}</strong></div></div>
      <button className={`order-button ${side}`} onClick={submitOrder} disabled={orderMutation.isPending}>
        {orderMutation.isPending ? '주문 접수 중…' : `${quantity}주 ${side === 'buy' ? '구매하기' : '판매하기'}`}
      </button>
      <p className="paper-note"><Icon name="shield" size={14} /> 모의투자 주문으로 실제 돈은 사용되지 않아요</p>
    </aside>
  );
}

export function MarketPage() {
  const [period, setPeriod] = useState('1일');
  const [activeTab, setActiveTab] = useState('차트');
  const { symbol: routeSymbol = 'QQQM' } = useParams();
  const symbol = routeSymbol.toUpperCase();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const selectedStock = watchlist.find((stock) => stock.symbol === symbol) ?? watchlist[0];
  const quoteQuery = useQuote(symbol);
  const { tick, status: streamStatus } = useQuoteStream(symbol);
  const quote = quoteQuery.data;
  const currentPrice = tick?.price ?? Number(quote?.price ?? selectedStock.price.replace(/[$,원]/g, ''));
  const currency = quote?.currency ?? (selectedStock.price.includes('$') ? 'USD' : 'KRW');
  const displayPrice = formatQuotePrice(currentPrice, currency);
  const displayChange = quote ? formatChangeRate(quote.change_rate) : selectedStock.change;
  const orderRows = [
    { price: '232.18', volume: '1,203', type: 'ask' }, { price: '232.04', volume: '842', type: 'ask' }, { price: '231.88', volume: '2,105', type: 'ask' },
    { price: '231.72', volume: '현재가', type: 'current' }, { price: '231.68', volume: '986', type: 'bid' }, { price: '231.51', volume: '1,547', type: 'bid' }, { price: '231.34', volume: '758', type: 'bid' },
  ];

  return (
    <PageContainer className="market-page">
      <div className="market-layout">
        <aside className="stock-browser card">
          <div className="browser-title"><h2>관심 종목</h2><button><Icon name="plus" size={16} /></button></div>
          <div className="browser-search"><Icon name="search" size={16} /><input placeholder="종목 검색" /></div>
          <div className="browser-tabs"><button className="active">관심</button><button>국내</button><button>해외</button><button>ETF</button></div>
          <div className="browser-list">
            {watchlist.concat([{ symbol: 'NVDA', name: 'NVIDIA', price: '$174.92', change: '+2.41%', positive: true, color: '#74b72e' }]).map((stock) => (
              <button key={stock.symbol} className={stock.symbol === symbol ? 'selected' : ''} onClick={() => navigate(`/market/${stock.symbol}`)}>
                <span className="stock-logo" style={{ background: stock.color }}>{stock.symbol.slice(0, 1)}</span>
                <span className="stock-name"><strong>{stock.symbol}</strong><small>{stock.name}</small></span>
                <span className="stock-price"><strong>{stock.price}</strong><small className={stock.positive ? 'up' : 'down'}>{stock.change}</small></span>
              </button>
            ))}
          </div>
        </aside>

        <section className="stock-detail card">
          <div className="stock-header">
            <div className="stock-identity"><span className="stock-logo large">{symbol.slice(0, 1)}</span><div><span>{quote?.name ?? selectedStock.name} · NASDAQ</span><h1>{symbol} <button>☆</button></h1></div></div>
            <div className="live-price">
              <strong>{quoteQuery.isLoading ? '불러오는 중' : displayPrice}</strong>
              <span className={Number(quote?.change_rate ?? 1) >= 0 ? 'up' : 'down'}>{displayChange}</span>
              <small>{streamStatus === 'connected' ? '실시간 연결' : streamStatus === 'reconnecting' ? '재연결 중' : '연결 중'} · {formatUpdatedAt(tick?.as_of ?? quote?.as_of)}</small>
            </div>
          </div>
          {quoteQuery.isError && <div className="data-status error"><span>시세 서버에 연결하지 못해 샘플 가격을 표시하고 있어요.</span><button onClick={() => quoteQuery.refetch()}>다시 시도</button></div>}
          <div className="detail-tabs">{['차트', '호가', '기업정보', '토론'].map((tab) => <button key={tab} onClick={() => setActiveTab(tab)} className={activeTab === tab ? 'active' : ''}>{tab}</button>)}</div>
          {activeTab === '차트' ? (
            <>
              <div className="chart-toolbar">
                <div>{['1일', '1주', '1개월', '3개월', '1년', '5년'].map((item) => <button key={item} className={period === item ? 'active' : ''} onClick={() => setPeriod(item)}>{item}</button>)}</div>
                <div><button>캔들</button><button>지표</button><button><Icon name="refresh" size={14} /></button></div>
              </div>
              <div className="main-chart"><ChartSection symbol={symbol} /></div>
              <div className="market-metrics">
                <div><span>오늘 고가</span><strong>$233.08</strong></div><div><span>오늘 저가</span><strong>$228.41</strong></div><div><span>거래량</span><strong>1.42M</strong></div><div><span>시가총액</span><strong>$40.2B</strong></div>
              </div>
              <div className="account-hint">
                <span><Icon name="sparkles" size={18} /></span>
                <div><strong>30년 장기 적립이라면 QQQ보다 QQQM이 유리할 수 있어요</strong><p>동일 지수 추종, 더 낮은 총보수(0.15%)로 적립식 투자에 적합해요.</p></div>
                <button onClick={() => showToast('AI 비교 리포트를 준비했어요.')}>비교하기 <Icon name="chevron" size={14} /></button>
              </div>
            </>
          ) : activeTab === '호가' ? (
            <div className="orderbook-view">
              <div className="orderbook-head"><span>잔량</span><span>가격(USD)</span><span>변동률</span></div>
              {orderRows.map((row, index) => <div key={index} className={row.type}><span>{row.volume}</span><strong>{row.price}</strong><span>{row.type === 'ask' ? '+1.4%' : row.type === 'bid' ? '+1.1%' : '+1.28%'}</span></div>)}
            </div>
          ) : (
            <div className="empty-state"><span><Icon name={activeTab === '기업정보' ? 'chart' : 'book'} size={28} /></span><h3>{activeTab} 화면</h3><p>한투 API 및 데이터 소스 연결 후 실시간 정보가 표시됩니다.</p></div>
          )}
        </section>
        <TradePanel symbol={symbol} price={currentPrice} currency={currency} />
      </div>
    </PageContainer>
  );
}

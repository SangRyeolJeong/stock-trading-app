import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../app/toast';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { marketApi } from '../services/marketApi';
import { paperApi } from '../services/paperApi';
import type { PaperPosition } from '../types/api';

const colors = ['#5578ff', '#6cd2b8', '#ffb15c', '#9a7cff', '#4f98d8'];

function formatMoney(value: string | number, currency: 'KRW' | 'USD') {
  return new Intl.NumberFormat(currency === 'KRW' ? 'ko-KR' : 'en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: currency === 'KRW' ? 0 : 2,
  }).format(Number(value));
}

function formatQuantity(value: string) {
  return `${new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 8 }).format(Number(value))}주`;
}

function HoldingRow({
  position,
  index,
  total,
  onOpen,
}: {
  position: PaperPosition;
  index: number;
  total: number;
  onOpen: () => void;
}) {
  const value = Number(position.market_value ?? 0);
  const weight = total > 0 ? (value / total) * 100 : 0;
  const profit = Number(position.unrealized_pnl ?? 0);
  const color = colors[index % colors.length];

  return (
    <div className="holding-row">
      <span className="holding-name">
        <i style={{ background: color }}>{position.symbol.slice(0, 1)}</i>
        <span><strong>{position.symbol}</strong><small>{position.name} · {position.currency}</small></span>
      </span>
      <span>{formatQuantity(position.quantity)}</span>
      <strong>{formatMoney(value, position.currency)}</strong>
      <span className={profit >= 0 ? 'up' : 'down'}>
        <strong>{formatMoney(profit, position.currency)}</strong>
        <small>{Number(position.return_rate ?? 0).toFixed(2)}%</small>
      </span>
      <span><i className="weight-bar"><b style={{ width: `${Math.min(weight * 2, 100)}%`, background: color }} /></i>{weight.toFixed(1)}%</span>
      <button onClick={onOpen} aria-label={`${position.symbol} 시장 화면 열기`}><Icon name="chevron" size={18} /></button>
    </div>
  );
}

export function PortfolioPage() {
  const [orderFilter, setOrderFilter] = useState<'all' | 'buy' | 'sell'>('all');
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const portfolioQuery = useQuery({
    queryKey: ['paper-portfolio', 'demo-account'],
    queryFn: paperApi.getPortfolioSummary,
  });
  const ordersQuery = useQuery({
    queryKey: ['paper-orders', 'demo-account'],
    queryFn: paperApi.getOrders,
    refetchInterval: 10_000,
  });
  const exchangeRateQuery = useQuery({
    queryKey: ['exchange-rate', 'USD', 'KRW'],
    queryFn: () => marketApi.getExchangeRate('USD', 'KRW'),
    staleTime: 60_000,
  });
  const portfolio = portfolioQuery.data;
  const positions = portfolio?.positions ?? [];
  const usdKrwRate = Number(exchangeRateQuery.data?.rate ?? 0);
  const toKrw = (value: string, currency: 'KRW' | 'USD') => (
    Number(value) * (currency === 'USD' ? usdKrwRate : 1)
  );
  const combined = (portfolio?.currencies ?? []).reduce(
    (result, summary) => ({
      total: result.total + toKrw(summary.total_value, summary.currency),
      cash: result.cash + toKrw(summary.cash, summary.currency),
      positions: result.positions + toKrw(summary.positions_value, summary.currency),
      unrealized: result.unrealized + toKrw(summary.unrealized_pnl, summary.currency),
      realized: result.realized + toKrw(summary.realized_pnl, summary.currency),
    }),
    { total: 0, cash: 0, positions: 0, unrealized: 0, realized: 0 },
  );
  const conversionReady = Boolean(portfolio) && usdKrwRate > 0;
  const filteredOrders = (ordersQuery.data ?? []).filter(
    (order) => orderFilter === 'all' || order.side === orderFilter,
  );
  const totals = Object.fromEntries(
    (portfolio?.currencies ?? []).map((summary) => [summary.currency, Number(summary.positions_value)]),
  );
  const cancelMutation = useMutation({
    mutationFn: (orderId: string) => paperApi.cancelOrder(orderId),
    onSuccess: (order) => {
      showToast(`${order.symbol} 지정가 주문을 취소했습니다.`);
      void queryClient.invalidateQueries({ queryKey: ['paper-orders'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-accounts'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-positions'] });
      void queryClient.invalidateQueries({ queryKey: ['paper-portfolio'] });
    },
    onError: (error: Error) => showToast(error.message),
  });
  const statusLabels = {
    accepted: '대기',
    filled: '체결',
    rejected: '거절',
    cancelled: '취소',
  };

  return (
    <PageContainer className="content-page">
      <section className="page-title compact">
        <div><p className="eyebrow">PAPER PORTFOLIO</p><h1>모의투자 포트폴리오</h1><p>체결 원장에 반영된 잔액, 보유 종목과 손익입니다.</p></div>
        <button className="primary-button" onClick={() => {
          void portfolioQuery.refetch();
          void ordersQuery.refetch();
          void exchangeRateQuery.refetch();
        }}><Icon name="refresh" size={16} /> 새로고침</button>
      </section>

      {portfolioQuery.isError && <div className="data-status error"><span>포트폴리오를 불러오지 못했습니다.</span><button onClick={() => portfolioQuery.refetch()}>다시 시도</button></div>}

      <section className="portfolio-summary">
        <article className="card portfolio-total combined-total">
          <span>KRW 환산 총 자산</span>
          <h2>{conversionReady ? formatMoney(combined.total, 'KRW') : '환율 확인 중'}</h2>
          <p><b>{conversionReady ? formatMoney(combined.unrealized + combined.realized, 'KRW') : '—'}</b> 평가·실현손익 합계</p>
          <div className="balance-breakdown">
            <span>현금 <strong>{conversionReady ? formatMoney(combined.cash, 'KRW') : '—'}</strong></span>
            <span>주식 <strong>{conversionReady ? formatMoney(combined.positions, 'KRW') : '—'}</strong></span>
          </div>
          <small>USD/KRW {usdKrwRate > 0 ? usdKrwRate.toLocaleString('ko-KR') : '—'} 적용</small>
        </article>
        {(portfolio?.currencies ?? []).map((summary) => (
          <article className="card portfolio-total" key={summary.currency}>
            <span>{summary.currency} 총 자산</span>
            <h2>{formatMoney(summary.total_value, summary.currency)}</h2>
            <p><b>{formatMoney(summary.unrealized_pnl, summary.currency)}</b> 평가손익 · {formatMoney(summary.realized_pnl, summary.currency)} 실현손익</p>
            <div className="balance-breakdown">
              <span>현금 <strong>{formatMoney(summary.cash, summary.currency)}</strong></span>
              <span>주식 <strong>{formatMoney(summary.positions_value, summary.currency)}</strong></span>
            </div>
          </article>
        ))}
        {!portfolio && <article className="card portfolio-loading">원장을 불러오는 중입니다…</article>}
      </section>

      <article className="card holdings-card">
        <div className="card-heading"><div><span className="label">보유 자산</span><p>현재 시세 평가 기준</p></div><span className="ledger-count">{positions.length}종목</span></div>
        <div className="holdings-head"><span>자산</span><span>보유</span><span>평가 금액</span><span>평가 손익</span><span>통화 내 비중</span><span /></div>
        {positions.map((position, index) => (
          <HoldingRow
            key={position.id}
            position={position}
            index={index}
            total={totals[position.currency] ?? 0}
            onOpen={() => navigate(`/market/${position.symbol}`)}
          />
        ))}
        {portfolio && positions.length === 0 && <div className="ledger-empty">아직 체결된 보유 종목이 없습니다.</div>}
      </article>

      <article className="card holdings-card order-history-card">
        <div className="card-heading">
          <div><span className="label">주문 내역</span><p>대기 지정가를 10초마다 시세와 대조</p></div>
          <div className="order-filters">
            {[
              { value: 'all', label: '전체' },
              { value: 'buy', label: '매수' },
              { value: 'sell', label: '매도' },
            ].map((item) => (
              <button key={item.value} className={orderFilter === item.value ? 'active' : ''} onClick={() => setOrderFilter(item.value as 'all' | 'buy' | 'sell')}>{item.label}</button>
            ))}
            <span className="ledger-count">{filteredOrders.length}건</span>
          </div>
        </div>
        {ordersQuery.isError && <div className="data-status error"><span>주문 내역을 불러오지 못했습니다.</span><button onClick={() => ordersQuery.refetch()}>다시 시도</button></div>}
        <div className="order-history-head"><span>일시</span><span>종목</span><span>구분</span><span>수량</span><span>상태</span><span>가격</span><span>수수료</span><span>실현손익</span><span /></div>
        {filteredOrders.map((order) => (
          <div className="order-history-row" key={order.id}>
            <span>{new Date(order.created_at).toLocaleString('ko-KR')}</span>
            <strong>{order.symbol}</strong>
            <span className={order.side === 'buy' ? 'up' : 'down'}>{order.side === 'buy' ? '매수' : '매도'}</span>
            <span>{formatQuantity(order.quantity)}</span>
            <span className={`order-status ${order.status}`}>{statusLabels[order.status]}</span>
            <span>
              {order.filled_price
                ? formatMoney(order.filled_price, order.currency)
                : order.limit_price ? `지정 ${formatMoney(order.limit_price, order.currency)}` : '—'}
            </span>
            <span>{order.fee ? formatMoney(order.fee, order.currency) : '—'}</span>
            <span>{order.realized_pnl ? formatMoney(order.realized_pnl, order.currency) : '—'}</span>
            <button
              className="cancel-order-button"
              disabled={order.status !== 'accepted' || cancelMutation.isPending}
              onClick={() => cancelMutation.mutate(order.id)}
            >
              {order.status === 'accepted' ? '취소' : '—'}
            </button>
          </div>
        ))}
        {ordersQuery.data && filteredOrders.length === 0 && <div className="ledger-empty">조건에 맞는 주문 내역이 없습니다.</div>}
      </article>
    </PageContainer>
  );
}

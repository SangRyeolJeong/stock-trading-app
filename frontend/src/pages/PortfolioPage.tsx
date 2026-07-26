import { useQuery } from '@tanstack/react-query';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
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
}: {
  position: PaperPosition;
  index: number;
  total: number;
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
      <button><Icon name="more" size={18} /></button>
    </div>
  );
}

export function PortfolioPage() {
  const portfolioQuery = useQuery({
    queryKey: ['paper-portfolio', 'demo-account'],
    queryFn: () => paperApi.getPortfolioSummary('demo-account'),
  });
  const ordersQuery = useQuery({
    queryKey: ['paper-orders', 'demo-account'],
    queryFn: () => paperApi.getOrders('demo-account'),
  });
  const portfolio = portfolioQuery.data;
  const positions = portfolio?.positions ?? [];
  const totals = Object.fromEntries(
    (portfolio?.currencies ?? []).map((summary) => [summary.currency, Number(summary.positions_value)]),
  );

  return (
    <PageContainer className="content-page">
      <section className="page-title compact">
        <div><p className="eyebrow">PAPER PORTFOLIO</p><h1>모의투자 포트폴리오</h1><p>체결 원장에 반영된 잔액, 보유 종목과 손익입니다.</p></div>
        <button className="primary-button" onClick={() => portfolioQuery.refetch()}><Icon name="refresh" size={16} /> 새로고침</button>
      </section>

      {portfolioQuery.isError && <div className="data-status error"><span>포트폴리오를 불러오지 못했습니다.</span><button onClick={() => portfolioQuery.refetch()}>다시 시도</button></div>}

      <section className="portfolio-summary">
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
        <div className="card-heading"><div><span className="label">보유 자산</span><p>데모 시세 평가 기준</p></div><span className="ledger-count">{positions.length}종목</span></div>
        <div className="holdings-head"><span>자산</span><span>보유</span><span>평가 금액</span><span>평가 손익</span><span>통화 내 비중</span><span /></div>
        {positions.map((position, index) => (
          <HoldingRow
            key={position.id}
            position={position}
            index={index}
            total={totals[position.currency] ?? 0}
          />
        ))}
        {portfolio && positions.length === 0 && <div className="ledger-empty">아직 체결된 보유 종목이 없습니다.</div>}
      </article>

      <article className="card holdings-card order-history-card">
        <div className="card-heading"><div><span className="label">주문 내역</span><p>최근 시장가·지정가 즉시 체결</p></div><span className="ledger-count">{ordersQuery.data?.length ?? 0}건</span></div>
        <div className="order-history-head"><span>일시</span><span>종목</span><span>구분</span><span>수량</span><span>체결가</span><span>수수료</span><span>실현손익</span></div>
        {(ordersQuery.data ?? []).map((order) => (
          <div className="order-history-row" key={order.id}>
            <span>{new Date(order.created_at).toLocaleString('ko-KR')}</span>
            <strong>{order.symbol}</strong>
            <span className={order.side === 'buy' ? 'up' : 'down'}>{order.side === 'buy' ? '매수' : '매도'}</span>
            <span>{formatQuantity(order.quantity)}</span>
            <span>{formatMoney(order.filled_price, order.currency)}</span>
            <span>{formatMoney(order.fee, order.currency)}</span>
            <span>{formatMoney(order.realized_pnl, order.currency)}</span>
          </div>
        ))}
        {ordersQuery.data?.length === 0 && <div className="ledger-empty">주문 내역이 없습니다.</div>}
      </article>
    </PageContainer>
  );
}

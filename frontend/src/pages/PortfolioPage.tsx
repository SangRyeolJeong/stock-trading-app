import { useState } from 'react';
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../app/toast';
import { TAX_PLANNER_PATH } from '../app/paths';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import {
  categoryForPosition,
  REBALANCING_PRODUCTS,
} from '../data/rebalancingProducts';
import { useUserPreferences } from '../data/userPreferences';
import { marketApi } from '../services/marketApi';
import { paperApi } from '../services/paperApi';
import { strategyApi } from '../services/strategyApi';
import type { PaperPosition } from '../types/api';
import { calculateWholeShareOrderDraft } from '../utils/orderDraft';
import { calculateRebalancingPlan } from '../utils/rebalancing';

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
  const preferences = useUserPreferences();
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
  const strategyQuery = useQuery({
    queryKey: ['strategy', 'portfolio-rebalancing', preferences],
    queryFn: () => strategyApi.recommend({
      goal: preferences.strategyGoal,
      horizon_years: preferences.investmentYears,
      monthly_amount_krw: preferences.monthlyInvestmentKrw,
      risk_profile: preferences.riskProfile,
      liquidity_preference: preferences.liquidityPreference,
      fee_sensitivity: preferences.feeSensitivity,
      income_preference: preferences.incomePreference,
      tax_efficiency_priority: true,
    }),
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
  const cashWeight = combined.total > 0 ? combined.cash / combined.total * 100 : 0;
  const positionWeights = positions.map((position) => ({
    symbol: position.symbol,
    valueKrw: toKrw(String(position.market_value ?? 0), position.currency),
  }));
  const largestPosition = positionWeights.reduce<{
    symbol: string;
    valueKrw: number;
  } | null>(
    (largest, item) => !largest || item.valueKrw > largest.valueKrw ? item : largest,
    null,
  );
  const largestPositionWeight = largestPosition && combined.positions > 0
    ? largestPosition.valueKrw / combined.positions * 100
    : 0;
  const investedValuesByCategory = positions.reduce(
    (values, position) => {
      const category = categoryForPosition(position.symbol);
      values[category] += toKrw(String(position.market_value ?? 0), position.currency);
      return values;
    },
    { growth: 0, income: 0, defensive: 0 },
  );
  const targetWeights = Object.fromEntries(
    (strategyQuery.data?.allocations ?? []).map((allocation) => [
      allocation.asset_class,
      allocation.weight_pct,
    ]),
  );
  const rebalancingPlan = conversionReady && strategyQuery.data
    ? calculateRebalancingPlan({
        currentValuesKrw: {
          growth: investedValuesByCategory.growth,
          income: investedValuesByCategory.income,
          defensive: investedValuesByCategory.defensive,
          cash: combined.cash,
        },
        targetWeightsPct: {
          growth: targetWeights.growth ?? 0,
          income: targetWeights.income ?? 0,
          defensive: targetWeights.defensive ?? 0,
          cash: targetWeights.cash ?? 0,
        },
        contributionKrw: preferences.monthlyInvestmentKrw,
      })
    : null;
  const rebalancingLabels = {
    growth: '성장주식 자산',
    income: '배당·인컴 자산',
    defensive: '채권·방어 자산',
    cash: '현금성 자산',
  };
  const rebalancingByCategory = Object.fromEntries(
    (rebalancingPlan?.items ?? []).map((item) => [item.category, item]),
  );
  const executionQuoteQueries = useQueries({
    queries: REBALANCING_PRODUCTS.map((product) => ({
      queryKey: ['quote', product.symbol, 'rebalancing-draft'],
      queryFn: () => marketApi.getQuote(product.symbol),
      enabled: Number(
        rebalancingByCategory[product.category]?.suggestedContributionKrw ?? 0,
      ) > 0,
      staleTime: 30_000,
    })),
  });
  const executionDrafts = REBALANCING_PRODUCTS.map((product, index) => {
    const rebalancing = rebalancingByCategory[product.category];
    const quoteQuery = executionQuoteQueries[index];
    const orderDraft = rebalancing && quoteQuery.data && usdKrwRate > 0
      ? calculateWholeShareOrderDraft({
          allocationKrw: rebalancing.suggestedContributionKrw,
          priceUsd: Number(quoteQuery.data.price),
          usdKrwRate,
        })
      : null;
    return { product, rebalancing, quoteQuery, orderDraft };
  });
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

      <section className="portfolio-guidance">
        <article className="card portfolio-diagnosis">
          <div className="card-heading">
            <div><span className="label">실제 원장 기반 진단</span><p>USD 자산은 현재 환율로 KRW 환산</p></div>
            <span className="ledger-count">{conversionReady ? '계산 완료' : '계산 중'}</span>
          </div>
          <div className="diagnosis-metrics">
            <span><small>현금 완충 비중</small><strong>{conversionReady ? `${cashWeight.toFixed(1)}%` : '—'}</strong></span>
            <span><small>최대 종목</small><strong>{largestPosition?.symbol ?? '—'}</strong></span>
            <span><small>최대 종목 비중</small><strong>{conversionReady ? `${largestPositionWeight.toFixed(1)}%` : '—'}</strong></span>
          </div>
          <p className={largestPositionWeight >= 40 ? 'diagnosis-warning' : ''}>
            {positions.length === 0
              ? '시장 화면에서 첫 모의 주문을 체결하면 실제 보유 비중 진단이 시작됩니다.'
              : largestPositionWeight >= 40
                ? `${largestPosition?.symbol} 비중이 투자자산의 40% 이상입니다. 새 주문 전 분산 여부를 점검하세요.`
                : cashWeight < 5
                  ? '현금 비중이 5% 미만입니다. 추가 매수와 예상 지출에 쓸 유동성을 확인하세요.'
                  : '현재 원장을 기준으로 단일 종목 40% 미만, 현금 5% 이상을 유지하고 있습니다.'}
          </p>
        </article>
        <article className="card portfolio-next-actions">
          <div className="card-heading"><div><span className="label">계산기로 이어가기</span><p>보유 현황을 확인한 다음 세후 계좌와 목표 비중을 비교하세요.</p></div></div>
          <button onClick={() => navigate(TAX_PLANNER_PATH)}>
            <span className="title-icon blue"><Icon name="wallet" size={18} /></span>
            <p><strong>세후 계좌 비교</strong><small>같은 월 투자금으로 일반·ISA·연금·IRP 비교</small></p>
            <Icon name="chevron" size={16} />
          </button>
          <button onClick={() => navigate('/strategy')}>
            <span className="title-icon purple"><Icon name="sparkles" size={18} /></span>
            <p><strong>맞춤 목표 비중</strong><small>기간·성향·목표에 맞는 다음 월 배분 확인</small></p>
            <Icon name="chevron" size={16} />
          </button>
        </article>
      </section>

      <article className="card rebalancing-card">
        <div className="card-heading">
          <div>
            <span className="label">다음 월 투자금 리밸런싱</span>
            <p>현재 보유 비중과 {strategyQuery.data?.title ?? '맞춤 전략'} 목표 비중의 부족분을 계산</p>
          </div>
          <button className="ledger-count action" onClick={() => navigate('/strategy')}>
            전략 설정 <Icon name="chevron" size={12} />
          </button>
        </div>
        {strategyQuery.isError ? (
          <div className="data-status error">
            <span>목표 비중을 불러오지 못했습니다.</span>
            <button onClick={() => strategyQuery.refetch()}>다시 시도</button>
          </div>
        ) : rebalancingPlan ? (
          <>
            <div className="rebalancing-head">
              <span>자산군</span><span>현재 / 목표</span><span>비중 차이</span><span>다음 {formatMoney(rebalancingPlan.contributionKrw, 'KRW')}</span>
            </div>
            {rebalancingPlan.items.map((item) => (
              <div className="rebalancing-row" key={item.category}>
                <strong>{rebalancingLabels[item.category]}</strong>
                <span className="weight-comparison">
                  <i><b style={{ width: `${Math.min(item.currentWeightPct, 100)}%` }} /></i>
                  {item.currentWeightPct.toFixed(1)}% / {item.targetWeightPct}%
                </span>
                <span className={item.driftPctPoint > 0 ? 'up' : item.driftPctPoint < 0 ? 'down' : ''}>
                  {item.driftPctPoint > 0 ? '+' : ''}{item.driftPctPoint.toFixed(1)}%p
                </span>
                <strong>{formatMoney(item.suggestedContributionKrw, 'KRW')}</strong>
              </div>
            ))}
            <p className="rebalancing-note">
              <Icon name="info" size={13} />
              DGRO는 배당·인컴, SGOV는 채권·방어 자산으로 구분하고 그 밖의 현재 지원 종목은
              성장주식으로 계산합니다. 매도 없이 새 투자금만 부족한 자산군에 배분하는 예시입니다.
            </p>
            {executionDrafts.map(({
              product,
              rebalancing,
              quoteQuery,
              orderDraft,
            }) => rebalancing && rebalancing.suggestedContributionKrw > 0 && (
              <section className="execution-draft" key={product.category}>
                <div>
                  <span className="stock-logo">{product.logo}</span>
                  <p>
                    <small>{product.role} · 확정 추천 아님</small>
                    <strong>{product.symbol} 정수 수량 모의주문 초안</strong>
                    <a href={product.officialSourceUrl} target="_blank" rel="noreferrer">
                      {product.name} 공식 정보
                    </a>
                  </p>
                </div>
                {quoteQuery.isError ? (
                  <button onClick={() => void quoteQuery.refetch()}>시세 다시 불러오기</button>
                ) : orderDraft ? (
                  <>
                    <dl>
                      <div><dt>배분 제안</dt><dd>{formatMoney(rebalancing.suggestedContributionKrw, 'KRW')}</dd></div>
                      <div><dt>현재가 환산</dt><dd>{formatMoney(orderDraft.unitPriceKrw, 'KRW')}</dd></div>
                      <div><dt>주문 초안</dt><dd>{orderDraft.quantity}주</dd></div>
                      <div><dt>수수료 포함 후 잔액</dt><dd>{formatMoney(orderDraft.remainingKrw, 'KRW')}</dd></div>
                    </dl>
                    <button
                      className="primary-button"
                      disabled={orderDraft.quantity < 1}
                      onClick={() => navigate(
                        `/market/${product.symbol}?tab=etf&draftQuantity=${orderDraft.quantity}`,
                      )}
                    >
                      {orderDraft.quantity > 0
                        ? `${orderDraft.quantity}주 주문창으로`
                        : '1주 금액까지 모으기'}
                      <Icon name="chevron" size={14} />
                    </button>
                  </>
                ) : (
                  <span className="execution-loading">
                    {product.symbol} 현재가와 환율로 수량을 계산하는 중…
                  </span>
                )}
                <small className="execution-caution">
                  환산 수량은 참고용입니다. 모의주문은 자동 환전하지 않으므로 주문창에서 USD 잔액을 별도로 확인합니다.
                </small>
              </section>
            ))}
          </>
        ) : <div className="ledger-empty compact">현재 원장과 맞춤 목표 비중을 연결하는 중입니다…</div>}
      </article>

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

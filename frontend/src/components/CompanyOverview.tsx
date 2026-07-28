import type { SecurityOverview } from '../types/api';
import { formatQuotePrice, formatUpdatedAt } from '../utils/format';
import { Icon } from './common/Icon';

interface CompanyOverviewProps {
  data: SecurityOverview | undefined;
  currentPrice: number;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}

function formatVolume(value: string | null) {
  if (!value) return '—';
  return Number(value).toLocaleString('ko-KR', {
    notation: Number(value) >= 100_000 ? 'compact' : 'standard',
    maximumFractionDigits: 1,
  });
}

function formatRatio(value: string | null) {
  return value ? `${Number(value).toLocaleString('ko-KR', { maximumFractionDigits: 2 })}배` : '—';
}

function formatMetricPrice(value: string | null, currency: 'KRW' | 'USD') {
  return value ? formatQuotePrice(value, currency) : '—';
}

export default function CompanyOverview({
  data,
  currentPrice,
  isLoading,
  isError,
  onRetry,
}: CompanyOverviewProps) {
  if (isLoading) return <div className="company-state">기업정보를 불러오는 중…</div>;
  if (isError) {
    return (
      <div className="company-state error">
        <span>기업정보를 불러오지 못했습니다.</span>
        <button onClick={onRetry}>다시 시도</button>
      </div>
    );
  }
  if (!data) return <div className="company-state">표시할 기업정보가 없습니다.</div>;

  const weekHigh = Number(data.week_52_high ?? 0);
  const weekLow = Number(data.week_52_low ?? 0);
  const range = weekHigh - weekLow;
  const rangePosition = range > 0
    ? Math.max(0, Math.min(((currentPrice - weekLow) / range) * 100, 100))
    : 0;
  const valuationUnavailable = !data.per && !data.pbr && !data.eps && !data.bps;

  return (
    <div className="company-overview">
      <div className="company-overview-head">
        <div>
          <span className="company-type">{data.asset_type.toUpperCase()}</span>
          <h2>{data.name}</h2>
          <p>{data.symbol} · {data.market} · {data.currency}</p>
        </div>
        <span className="company-source"><Icon name="shield" size={14} />{data.source === 'kis' ? 'KIS 현재가 지표' : '데모 지표'}</span>
      </div>

      <section className="week-range">
        <div><span>52주 범위</span><small>{formatUpdatedAt(data.as_of)} 기준</small></div>
        <div className="week-range-bar"><i style={{ left: `${rangePosition}%` }} /></div>
        <div>
          <span><small>최저</small>{formatMetricPrice(data.week_52_low, data.currency)}</span>
          <strong><small>현재</small>{formatQuotePrice(currentPrice, data.currency)}</strong>
          <span><small>최고</small>{formatMetricPrice(data.week_52_high, data.currency)}</span>
        </div>
      </section>

      <section className="company-metric-grid">
        <div><span>시가</span><strong>{formatMetricPrice(data.open, data.currency)}</strong></div>
        <div><span>고가</span><strong>{formatMetricPrice(data.high, data.currency)}</strong></div>
        <div><span>저가</span><strong>{formatMetricPrice(data.low, data.currency)}</strong></div>
        <div><span>누적 거래량</span><strong>{formatVolume(data.volume)}</strong></div>
        <div><span>PER</span><strong>{formatRatio(data.per)}</strong><small>주가 / 주당순이익</small></div>
        <div><span>PBR</span><strong>{formatRatio(data.pbr)}</strong><small>주가 / 주당순자산</small></div>
        <div><span>EPS</span><strong>{formatMetricPrice(data.eps, data.currency)}</strong><small>주당순이익</small></div>
        <div><span>BPS</span><strong>{formatMetricPrice(data.bps, data.currency)}</strong><small>주당순자산</small></div>
      </section>

      <div className="company-overview-note">
        <Icon name="info" size={15} />
        <span>
          {valuationUnavailable
            ? 'ETF·ETN 등 일부 상품은 PER, PBR, EPS, BPS가 제공되지 않을 수 있습니다.'
            : 'PER·PBR 같은 단일 지표만으로 투자 가치를 판단할 수 없습니다. 업종과 이익 변동성을 함께 확인하세요.'}
        </span>
      </div>
    </div>
  );
}

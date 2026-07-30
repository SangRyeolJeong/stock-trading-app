import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Icon } from './common/Icon';
import { marketApi } from '../services/marketApi';
import type { EtfProfile } from '../types/api';

function formatPercent(value: string) {
  return `${Number(value).toLocaleString('ko-KR', { maximumFractionDigits: 2 })}%`;
}

function formatWon(value: string) {
  return `${Math.round(Number(value)).toLocaleString('ko-KR')}원`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(`${value}T00:00:00`));
}

function ProfileCard({
  profile,
  lowerExpense,
  onOpen,
}: {
  profile: EtfProfile;
  lowerExpense: boolean;
  onOpen: () => void;
}) {
  return (
    <article className={`etf-profile-card ${lowerExpense ? 'lower-expense' : ''}`}>
      <div className="etf-profile-title">
        <div>
          <span>{profile.issuer}</span>
          <h3>{profile.symbol}</h3>
        </div>
        {lowerExpense && <em>낮은 보수</em>}
      </div>
      <p>{profile.name}</p>
      <div className="etf-listing-tags">
        <span>{profile.listing_country === 'KR' ? '한국 상장' : '미국 상장'}</span>
        <span>{profile.trading_currency} 거래</span>
      </div>
      <dl>
        <div><dt>기초지수</dt><dd>{profile.underlying_index}</dd></div>
        <div><dt>총보수</dt><dd>{formatPercent(profile.expense_ratio_pct)}</dd></div>
        <div><dt>전체 종목</dt><dd>{profile.holdings_count.toLocaleString('ko-KR')}개</dd></div>
        <div><dt>설정일</dt><dd>{formatDate(profile.inception_date)}</dd></div>
      </dl>
      <button onClick={onOpen}>{profile.symbol} 종목·주문 보기 <Icon name="chevron" size={13} /></button>
    </article>
  );
}

export function EtfComparisonPanel({ symbol }: { symbol: string }) {
  const navigate = useNavigate();
  const [requestedRight, setRequestedRight] = useState('');
  const catalogQuery = useQuery({
    queryKey: ['etf-catalog'],
    queryFn: marketApi.getEtfs,
    staleTime: 24 * 60 * 60 * 1000,
  });
  const profiles = catalogQuery.data?.items ?? [];
  const currentProfile = profiles.find((profile) => profile.symbol === symbol);
  const alternatives = profiles.filter((profile) => profile.symbol !== symbol);
  const preferredAlternative = alternatives.find(
    (profile) => profile.underlying_index === currentProfile?.underlying_index,
  ) ?? alternatives[0];
  const selectedAlternative = alternatives.find(
    (profile) => profile.symbol === requestedRight,
  ) ?? preferredAlternative;
  const rightSymbol = selectedAlternative?.symbol ?? '';
  const comparisonQuery = useQuery({
    queryKey: ['etf-comparison', symbol, rightSymbol],
    queryFn: () => marketApi.compareEtfs(symbol, rightSymbol),
    enabled: Boolean(currentProfile && rightSymbol),
    staleTime: 24 * 60 * 60 * 1000,
  });

  if (catalogQuery.isLoading) {
    return <div className="etf-compare-state">공식 ETF 비교 자료를 불러오고 있어요…</div>;
  }
  if (catalogQuery.isError || !currentProfile) {
    return (
      <div className="etf-compare-state error">
        ETF 비교 자료를 불러오지 못했습니다.
        <button onClick={() => catalogQuery.refetch()}>다시 시도</button>
      </div>
    );
  }

  const comparison = comparisonQuery.data;
  return (
    <div className="etf-compare">
      <header className="etf-compare-head">
        <div>
          <span>{catalogQuery.data?.data_version}</span>
          <h2>ETF 구성·비용 비교</h2>
          <p>운용사 공식 스냅샷으로 보수와 상위 구성종목의 실제 겹침을 계산합니다.</p>
        </div>
        <label>
          <span>{symbol}와 비교할 ETF</span>
          <select value={rightSymbol} onChange={(event) => setRequestedRight(event.target.value)}>
            {alternatives.map((profile) => (
              <option key={profile.symbol} value={profile.symbol}>
                {profile.symbol} · {profile.underlying_index}
              </option>
            ))}
          </select>
        </label>
      </header>

      {comparisonQuery.isLoading && (
        <div className="etf-compare-state">중복도와 비용 차이를 계산하고 있어요…</div>
      )}
      {comparisonQuery.isError && (
        <div className="etf-compare-state error">
          비교 계산을 불러오지 못했습니다.
          <button onClick={() => comparisonQuery.refetch()}>다시 시도</button>
        </div>
      )}
      {comparison && (
        <>
          <section className="etf-compare-summary">
            <div
              className="etf-overlap-ring"
              style={{
                background: `conic-gradient(#6689ff 0 ${comparison.top_holdings_overlap_pct}%, #28313d ${comparison.top_holdings_overlap_pct}% 100%)`,
              }}
            >
              <div>
                <strong>{formatPercent(comparison.top_holdings_overlap_pct)}</strong>
                <span>상위 종목 중복도</span>
              </div>
            </div>
            <div className="etf-summary-copy">
              <span className={comparison.same_underlying_index ? 'same-index' : ''}>
                {comparison.same_underlying_index ? '같은 기초지수' : '서로 다른 기초지수'}
              </span>
              <strong>공통 상위 종목 {comparison.common_top_holdings_count}개</strong>
              <p>{comparison.interpretation}</p>
            </div>
            <div className="etf-fee-gap">
              <span>{formatWon(comparison.comparison_principal_krw)} 투자 시</span>
              <strong>연 {formatWon(comparison.annual_fee_difference_krw)}</strong>
              <small>
                {comparison.lower_expense_symbol
                  ? `${comparison.lower_expense_symbol}의 총보수가 더 낮아요.`
                  : '두 ETF의 총보수가 같아요.'}
              </small>
            </div>
          </section>

          <section className="etf-profile-grid">
            <ProfileCard
              profile={comparison.left}
              lowerExpense={comparison.lower_expense_symbol === comparison.left.symbol}
              onOpen={() => navigate(`/market/${comparison.left.symbol}?tab=etf`)}
            />
            <ProfileCard
              profile={comparison.right}
              lowerExpense={comparison.lower_expense_symbol === comparison.right.symbol}
              onOpen={() => navigate(`/market/${comparison.right.symbol}?tab=etf`)}
            />
          </section>

          <section className="etf-common-holdings">
            <div className="etf-section-heading">
              <div>
                <h3>겹치는 상위 구성종목</h3>
                <p>
                  {comparison.left.symbol} {formatPercent(comparison.left.top_holdings_coverage_pct)}
                  {' · '}
                  {comparison.right.symbol} {formatPercent(comparison.right.top_holdings_coverage_pct)}
                  {' '}표시 범위 기준
                </p>
              </div>
              <span>구성 기준일 {formatDate(comparison.left.holdings_as_of)} · {formatDate(comparison.right.holdings_as_of)}</span>
            </div>
            <div className="etf-holding-head">
              <span>종목</span><span>{comparison.left.symbol}</span><span>{comparison.right.symbol}</span><span>공통 비중</span>
            </div>
            {comparison.common_top_holdings.map((holding) => (
              <div className="etf-holding-row" key={holding.symbol}>
                <span><strong>{holding.symbol}</strong><small>{holding.name}</small></span>
                <b>{formatPercent(holding.left_weight_pct)}</b>
                <b>{formatPercent(holding.right_weight_pct)}</b>
                <div>
                  <i style={{ width: `${Math.min(Number(holding.shared_weight_pct) * 10, 100)}%` }} />
                  <small>{formatPercent(holding.shared_weight_pct)}</small>
                </div>
              </div>
            ))}
          </section>

          <section className="etf-compare-evidence">
            <div>
              <Icon name="info" size={15} />
              <p><strong>계산식</strong>{comparison.formula}</p>
            </div>
            <div className="etf-source-links">
              {[comparison.left, comparison.right].flatMap((profile) => [
                {
                  key: `${profile.symbol}-facts`,
                  label: `${profile.symbol} 상품 정보`,
                  url: profile.source_url,
                },
                ...(profile.holdings_source_url === profile.source_url ? [] : [{
                  key: `${profile.symbol}-holdings`,
                  label: `${profile.symbol} 구성종목`,
                  url: profile.holdings_source_url,
                }]),
              ]).map((source) => (
                <a href={source.url} target="_blank" rel="noreferrer" key={source.key}>
                  {source.label} <Icon name="chevron" size={12} />
                </a>
              ))}
              <button onClick={() => navigate('/learn/qqq-vs-qqqm')}>
                ETF 비교 학습 <Icon name="book" size={12} />
              </button>
            </div>
            <small>{comparison.disclaimer}</small>
            {comparison.left.listing_country !== comparison.right.listing_country && (
              <small className="cross-listing-note">
                상장국이 다른 비교입니다. 국내상장 해외 ETF와 미국상장 ETF의 과세·환전·
                거래시간 구조는 동일하지 않습니다.
              </small>
            )}
          </section>
        </>
      )}
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { updateUserPreferences, useUserPreferences } from '../data/userPreferences';
import { strategyApi } from '../services/strategyApi';
import type { StrategyRequest } from '../types/api';

const goalOptions = [
  { label: '장기 은퇴 준비', value: 'retirement', icon: 'clock' },
  { label: '목돈 마련', value: 'lump_sum', icon: 'target' },
  { label: '배당 현금흐름', value: 'cashflow', icon: 'wallet' },
] as const;

const riskOptions = [
  { label: '안정형', value: 'conservative' },
  { label: '균형형', value: 'balanced' },
  { label: '성장형', value: 'growth' },
] as const;

const accountLabels = {
  direct: '일반계좌',
  isa: 'ISA',
  pension: '연금저축',
  irp: 'IRP',
  cash: '현금',
};

const formatWon = (value: number) => `${new Intl.NumberFormat('ko-KR').format(value)}원`;

export function StrategyPage() {
  const navigate = useNavigate();
  const preferences = useUserPreferences();
  const goal = preferences.strategyGoal;
  const risk = preferences.riskProfile;
  const liquidityPreference = preferences.liquidityPreference;
  const feeSensitivity = preferences.feeSensitivity;
  const incomePreference = preferences.incomePreference;
  const selectedGoal = goalOptions.find((option) => option.value === goal) ?? goalOptions[0];
  const selectedRisk = riskOptions.find((option) => option.value === risk) ?? riskOptions[2];
  const request: StrategyRequest = {
    goal,
    horizon_years: preferences.investmentYears,
    monthly_amount_krw: preferences.monthlyInvestmentKrw,
    risk_profile: risk,
    liquidity_preference: liquidityPreference,
    fee_sensitivity: feeSensitivity,
    income_preference: incomePreference,
    tax_efficiency_priority: true,
  };
  const strategyQuery = useQuery({
    queryKey: ['strategy', request],
    queryFn: () => strategyApi.recommend(request),
  });
  const recommendation = strategyQuery.data;

  return (
    <PageContainer className="content-page strategy-page">
      <section className="strategy-hero">
        <div>
          <span className="ai-badge light">
            <Icon name="sparkles" size={15} /> MOA RULE STRATEGIST
          </span>
          <h1>
            좋은 상품보다
            <br />
            <em>나에게 맞는 방식</em>을 찾으세요.
          </h1>
          <p>투자 기간, 목적, 계좌까지 함께 보고 실행 가능한 전략을 제안해요.</p>
        </div>
        <div className="hero-orbit">
          <span className="center-orb"><Icon name="sparkles" size={30} /></span>
          <span className="orbit-item one">ISA</span>
          <span className="orbit-item two">ETF</span>
          <span className="orbit-item three">IRP</span>
          <span className="orbit-item four">연금</span>
        </div>
      </section>

      <section className="strategy-layout">
        <article className="card strategy-form">
          <div className="step-title">
            <span>1</span>
            <div>
              <strong>어떤 투자를 계획하고 있나요?</strong>
              <p>선택에 따라 규칙 엔진이 전략을 다시 계산해요.</p>
            </div>
          </div>
          <label>목표</label>
          <div className="choice-stack">
            {goalOptions.map((option) => (
              <button
                key={option.value}
                className={goal === option.value ? 'active' : ''}
                onClick={() => updateUserPreferences({ strategyGoal: option.value })}
              >
                <span>
                  <Icon name={option.icon} size={19} />
                  {option.label}
                </span>
                {goal === option.value && <Icon name="check" size={17} />}
              </button>
            ))}
          </div>
          <label>투자 성향</label>
          <div className="segmented wide">
            {riskOptions.map((option) => (
              <button
                key={option.value}
                className={risk === option.value ? 'active' : ''}
                onClick={() => updateUserPreferences({ riskProfile: option.value })}
              >
                {option.label}
              </button>
            ))}
          </div>
          <label>예상 투자 기간</label>
          <div className="slider-label">
            <strong>{preferences.investmentYears}년</strong>
            <span>{preferences.investmentYears >= 10 ? '장기투자' : '중기투자'}</span>
          </div>
          <input
            className="range-input"
            type="range"
            min="3"
            max="40"
            value={preferences.investmentYears}
            onChange={(event) => updateUserPreferences({
              investmentYears: Number(event.target.value),
            })}
          />
          <div className="range-ends"><span>3년</span><span>40년</span></div>
          <label>월 투자금</label>
          <div className="money-input">
            <span>₩</span>
            <input
              type="number"
              min="10000"
              step="10000"
              value={preferences.monthlyInvestmentKrw}
              onChange={(event) => updateUserPreferences({
                monthlyInvestmentKrw: Number(event.target.value),
              })}
            />
            <em>원</em>
          </div>
          <label>선호하는 조건</label>
          <div className="check-list">
            <label>
              <input
                type="checkbox"
                checked={liquidityPreference}
                onChange={(event) => updateUserPreferences({
                  liquidityPreference: event.target.checked,
                })}
              />
              <span><Icon name="check" size={13} /></span>
              언제든 사용할 수 있는 유동성
            </label>
            <label>
              <input
                type="checkbox"
                checked={feeSensitivity}
                onChange={(event) => updateUserPreferences({
                  feeSensitivity: event.target.checked,
                })}
              />
              <span><Icon name="check" size={13} /></span>
              낮은 운용보수
            </label>
            <label>
              <input
                type="checkbox"
                checked={incomePreference}
                onChange={(event) => updateUserPreferences({
                  incomePreference: event.target.checked,
                })}
              />
              <span><Icon name="check" size={13} /></span>
              배당·분배금 비중 확대
            </label>
          </div>
        </article>

        <article className="card recommendation">
          <div className="recommend-top">
            <div>
              <span className="ai-badge">
                <Icon name="sparkles" size={15} /> 구조화된 규칙 기반 추천
              </span>
              <h2>{selectedGoal.label} · {preferences.investmentYears}년 · {selectedRisk.label}</h2>
            </div>
            {recommendation && (
              <span className="fit-score">
                <b>{recommendation.score}</b>점
                <small>적합도</small>
              </span>
            )}
          </div>

          {strategyQuery.isPending && (
            <div className="strategy-status">입력 조건에 맞춰 전략을 계산하고 있어요.</div>
          )}
          {strategyQuery.isError && (
            <div className="data-status error">
              <span>전략 서버에 연결하지 못했습니다.</span>
              <button onClick={() => strategyQuery.refetch()}>다시 시도</button>
            </div>
          )}

          {recommendation && (
            <>
              <div className="strategy-name">
                <span className="strategy-icon">M</span>
                <div>
                  <span>{recommendation.engine_version}</span>
                  <h3>{recommendation.title}</h3>
                  <p>{recommendation.summary}</p>
                </div>
              </div>

              <div className="risk-overview">
                <span><small>주식성</small><strong>{recommendation.risk_summary.equity_weight_pct}%</strong></span>
                <span><small>방어자산</small><strong>{recommendation.risk_summary.defensive_weight_pct}%</strong></span>
                <span><small>유동성</small><strong>{recommendation.risk_summary.liquidity_weight_pct}%</strong></span>
              </div>

              <div className="allocation-plan structured">
                {recommendation.allocations.map((allocation) => (
                  <div key={allocation.asset_class}>
                    <span>{allocation.label}</span>
                    <strong>{allocation.weight_pct}%</strong>
                    <small>{formatWon(allocation.monthly_amount_krw)} · {accountLabels[allocation.account_type]}</small>
                    <em>{allocation.product_example}</em>
                  </div>
                ))}
              </div>

              <div className="why-box">
                <h4>왜 이 전략인가요?</h4>
                {recommendation.rationale.map((reason, index) => (
                  <div key={reason.code}>
                    <span>{String(index + 1).padStart(2, '0')}</span>
                    <p>
                      <strong>{reason.title}</strong>
                      <small>{reason.description}</small>
                      <code>{reason.code}</code>
                    </p>
                  </div>
                ))}
              </div>

              <div className="strategy-actions">
                <h4>실행 순서</h4>
                {recommendation.action_steps.map((step) => (
                  <div key={step.order}>
                    <b>{step.order}</b>
                    <p><strong>{step.title}</strong><span>{step.description}</span></p>
                  </div>
                ))}
              </div>

              {recommendation.warnings.length > 0 && (
                <div className="strategy-warnings">
                  {recommendation.warnings.map((warning) => (
                    <p key={warning}><Icon name="info" size={13} /> {warning}</p>
                  ))}
                </div>
              )}

              <button className="primary-button full" onClick={() => navigate('/market')}>
                이 전략으로 모의투자 시작하기 <Icon name="chevron" size={15} />
              </button>
              <p className="disclaimer"><Icon name="info" size={14} /> {recommendation.disclaimer}</p>
            </>
          )}
        </article>
      </section>
    </PageContainer>
  );
}

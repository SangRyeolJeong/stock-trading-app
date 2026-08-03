import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { updateUserPreferences, useUserPreferences } from '../data/userPreferences';
import { taxApi } from '../services/taxApi';
import type { TaxAccountType } from '../types/api';

const incomeOptions = [
  { label: '5,000만원 이하', value: 45_000_000 },
  { label: '5,000~5,500만원', value: 52_000_000 },
  { label: '5,500만원 초과', value: 70_000_000 },
];

function formatWon(value: string | number) {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatCompactWon(value: string | number) {
  const amount = Number(value);
  if (Math.abs(amount) >= 100_000_000) return `${(amount / 100_000_000).toFixed(2)}억원`;
  if (Math.abs(amount) >= 10_000) return `${Math.round(amount / 10_000).toLocaleString('ko-KR')}만원`;
  return formatWon(amount);
}

export function TaxPlannerPage() {
  const preferences = useUserPreferences();
  const [selected, setSelected] = useState<TaxAccountType>('pension');
  const [currentAge, setCurrentAge] = useState(30);
  const annualSalary = preferences.annualSalaryKrw;
  const years = preferences.investmentYears;
  const monthlyContribution = preferences.monthlyInvestmentKrw;
  const returnRate = preferences.annualReturnRatePct;
  const withdrawalAge = preferences.withdrawalAge;
  const delayYears = 5;
  const maxCurrentAge = Math.max(18, withdrawalAge - delayYears - 1);
  const calculationCurrentAge = Math.min(currentAge, maxCurrentAge);
  const simulationQuery = useQuery({
    queryKey: [
      'tax-simulation',
      annualSalary,
      monthlyContribution,
      years,
      returnRate,
      withdrawalAge,
    ],
    queryFn: () => taxApi.simulate({
      annual_salary_krw: annualSalary,
      monthly_contribution_krw: monthlyContribution,
      investment_years: years,
      annual_return_rate_pct: returnRate,
      withdrawal_age: withdrawalAge,
    }),
    enabled: monthlyContribution > 0,
  });

  const simulation = simulationQuery.data;
  const pensionStartQuery = useQuery({
    queryKey: [
      'pension-start-comparison',
      annualSalary,
      calculationCurrentAge,
      withdrawalAge,
      monthlyContribution,
      returnRate,
      delayYears,
    ],
    queryFn: () => taxApi.comparePensionStart({
      annual_salary_krw: annualSalary,
      current_age: calculationCurrentAge,
      withdrawal_age: withdrawalAge,
      monthly_contribution_krw: monthlyContribution,
      annual_return_rate_pct: returnRate,
      delay_years: delayYears,
    }),
    enabled: monthlyContribution > 0,
  });
  const pensionStart = pensionStartQuery.data;
  const results = simulation?.results ?? [];
  const winner = results.find((item) => item.account_type === simulation?.best_account_type);
  const account = results.find((item) => item.account_type === selected) ?? winner;
  const maxAfterTax = Math.max(...results.map((item) => Number(item.after_tax_value)), 1);

  return (
    <PageContainer className="content-page">
      <section className="page-title">
        <span className="title-icon blue"><Icon name="wallet" size={23} /></span>
        <div><p className="eyebrow">TAX PLANNER</p><h1>내게 맞는 절세 계좌 찾기</h1><p>공식 세제 규칙과 동일한 투자 가정으로 세후 결과를 비교합니다.</p></div>
      </section>
      <section className="tax-grid">
        <article className="card planner-form">
          <div className="step-title"><span>1</span><div><strong>투자 조건을 알려주세요</strong><p>입력값은 내 설정에 자동 저장됩니다.</p></div></div>
          <label>연간 총급여</label>
          <div className="option-grid three">{incomeOptions.map((item) => <button className={annualSalary === item.value ? 'active' : ''} key={item.value} onClick={() => updateUserPreferences({ annualSalaryKrw: item.value })}>{item.label}<Icon name="check" size={15} /></button>)}</div>
          <label>예상 투자 기간</label>
          <div className="slider-label"><strong>{years}년</strong><span>{years >= 10 ? '장기투자' : '중기투자'}</span></div>
          <input className="range-input" type="range" min="3" max="40" value={years} onChange={(event) => updateUserPreferences({ investmentYears: Number(event.target.value) })} />
          <div className="range-ends"><span>3년</span><span>40년</span></div>
          <label>월 투자금</label>
          <div className="money-input"><span>₩</span><input type="number" min="10000" step="10000" value={monthlyContribution} onChange={(event) => updateUserPreferences({ monthlyInvestmentKrw: Number(event.target.value) })} /><em>원</em></div>
          <label>연 예상 수익률</label>
          <div className="option-grid three">{[4, 7, 10].map((rate) => <button className={returnRate === rate ? 'active' : ''} key={rate} onClick={() => updateUserPreferences({ annualReturnRatePct: rate })}>{rate}%<Icon name="check" size={15} /></button>)}</div>
          <label>연금 수령 시작 나이</label>
          <div className="option-grid three">{[60, 70, 80].map((age) => <button className={withdrawalAge === age ? 'active' : ''} key={age} onClick={() => updateUserPreferences({ withdrawalAge: age })}>{age}세<Icon name="check" size={15} /></button>)}</div>
          <div className="form-note"><Icon name="shield" size={17} /><p>수수료·환율 변동 없이 매년 말 납입하고 마지막 해에 처분하는 비교입니다.</p></div>
        </article>

        <article className="card tax-result">
          <div className="result-heading"><span className="ai-badge"><Icon name="chart" size={15} /> 규칙 기반 분석</span><p>{simulation ? `${simulation.rules.version} 기준` : '계산 중'}</p></div>
          {simulationQuery.isError && <div className="data-status error"><span>절세 계산을 불러오지 못했습니다.</span><button onClick={() => simulationQuery.refetch()}>다시 시도</button></div>}
          {winner ? (
            <>
              <div className="winner">
                <div><span className="winner-rank">BEST</span><h2>{winner.name}</h2><p>+ {winner.recommended_product}</p></div>
                <div className="save-number"><span>{years}년 예상 절세 효과</span><strong>{formatCompactWon(winner.tax_savings_vs_direct)}</strong><small>해외직투 대비 · 연 {returnRate}% 가정</small></div>
              </div>
              <div className="result-bars">
                {results.map((item) => (
                  <div className={item.account_type === winner.account_type ? 'best' : ''} key={item.account_type}>
                    <span>{item.name}</span>
                    <i><b style={{ width: `${Math.max(8, Number(item.after_tax_value) / maxAfterTax * 100)}%` }} /></i>
                    <strong>세후 {formatCompactWon(item.after_tax_value)}</strong>
                  </div>
                ))}
              </div>
              <div className="tax-breakdown">
                <span>납입 세액공제 <strong>{formatCompactWon(winner.contribution_tax_credit)}</strong></span>
                <span>예상 운용·인출세금 <strong>{formatCompactWon(Number(winner.investment_tax) + Number(winner.withdrawal_tax))}</strong></span>
              </div>
              <p className="disclaimer"><Icon name="info" size={14} /> {simulation?.disclaimer}</p>
            </>
          ) : <div className="tax-loading">공식 규칙으로 계산하고 있습니다…</div>}
        </article>
      </section>

      <section className="card pension-start-calculator">
        <div className="section-heading">
          <div><span className="label">복리 시간 계산기</span><h2>연금저축, 5년 먼저 시작하면?</h2><p>같은 월 납입액으로 지금 시작할 때와 5년 뒤 시작할 때를 비교합니다.</p></div>
          <span>{pensionStart?.rules.version ?? '공식 규칙 계산 중'}</span>
        </div>
        <div className="pension-start-grid">
          <div className="pension-age-control">
            <label>현재 나이</label>
            <div className="slider-label"><strong>{calculationCurrentAge}세</strong><span>{withdrawalAge}세 수령까지 {withdrawalAge - calculationCurrentAge}년</span></div>
            <input className="range-input" type="range" min="18" max={maxCurrentAge} value={calculationCurrentAge} onChange={(event) => setCurrentAge(Number(event.target.value))} />
            <div className="range-ends"><span>18세</span><span>최대 {maxCurrentAge}세</span></div>
            <div className="pension-input-summary">
              <span><small>월 납입액</small><strong>{formatCompactWon(monthlyContribution)}</strong></span>
              <span><small>예상 수익률</small><strong>연 {returnRate}%</strong></span>
              <span><small>세액공제 구간</small><strong>{annualSalary <= 55_000_000 ? '16.5%' : '13.2%'}</strong></span>
            </div>
            <p className="form-note"><Icon name="info" size={16} /> 연 1,800만원 납입한도와 연금저축 세액공제 연 600만원 한도를 적용합니다.</p>
          </div>

          <div className="pension-start-results">
            {pensionStartQuery.isError && <div className="data-status error"><span>연금 시작 시점 계산을 불러오지 못했습니다.</span><button onClick={() => pensionStartQuery.refetch()}>다시 시도</button></div>}
            {pensionStart ? (
              <>
                <div className="pension-scenario-grid">
                  {[pensionStart.start_now, pensionStart.delayed_start].map((scenario, index) => (
                    <article className={index === 0 ? 'recommended' : ''} key={scenario.start_age}>
                      <span>{index === 0 ? '지금 시작' : `${delayYears}년 뒤 시작`}</span>
                      <h3>{scenario.start_age}세부터 {scenario.contribution_years}년</h3>
                      <small className="scenario-total-label">예상 가치 · 세액공제 포함</small>
                      <strong>{formatCompactWon(scenario.projected_value_with_tax_credit)}</strong>
                      <dl>
                        <div><dt>납입 원금</dt><dd>{formatCompactWon(scenario.total_principal)}</dd></div>
                        <div><dt>예상 운용자산</dt><dd>{formatCompactWon(scenario.projected_balance)}</dd></div>
                        <div><dt>누적 세액공제</dt><dd>{formatCompactWon(scenario.contribution_tax_credit)}</dd></div>
                      </dl>
                    </article>
                  ))}
                </div>
                <div className="pension-waiting-cost">
                  <div><span>5년을 기다릴 때 줄어드는 예상 가치</span><strong>{formatCompactWon(pensionStart.projected_value_gap)}</strong></div>
                  <div><span>{pensionStart.delayed_start.start_age}세에 시작해 따라잡으려면</span><strong>월 {formatCompactWon(pensionStart.delayed_required_monthly_contribution)}</strong><small>{pensionStart.delayed_required_within_pension_limit ? '연금계좌 일반 납입한도 안' : '연 1,800만원 납입한도 초과'}</small></div>
                </div>
                <p className="disclaimer"><Icon name="info" size={14} /> {pensionStart.disclaimer}</p>
              </>
            ) : <div className="tax-loading">시작 시점에 따른 복리 차이를 계산하고 있습니다…</div>}
          </div>
        </div>
      </section>

      <section className="account-section">
        <div className="section-heading"><div><h2>계좌별 계산 결과</h2><p>카드를 눌러 적용 세율과 한도, 유의사항을 확인하세요.</p></div><span>{simulation?.rules.effective_date ?? '—'} 시행 기준</span></div>
        <div className="account-cards">
          {results.map((item) => (
            <button key={item.account_type} onClick={() => setSelected(item.account_type)} className={`account-card ${selected === item.account_type ? 'active' : ''}`}>
              <div><span className="account-tag">{item.tag}</span>{selected === item.account_type && <span className="selected-check"><Icon name="check" size={14} /></span>}</div>
              <h3>{item.name}</h3><p>{item.tax_description}</p>
              <div className="account-score"><i><b style={{ width: `${item.score}%` }} /></i><strong>{item.score}점</strong></div>
            </button>
          ))}
        </div>
        {account && (
          <article className="account-detail card">
            <div><span className="stock-logo account-logo"><Icon name="wallet" size={20} /></span><div><span>선택한 계좌</span><h3>{account.name}</h3></div></div>
            <dl><div><dt>과세 방식</dt><dd>{account.tax_description}</dd></div><div><dt>납입 한도</dt><dd>{account.contribution_limit_description}</dd></div><div><dt>추천 상품</dt><dd>{account.recommended_product}</dd></div></dl>
            <a href={simulation?.rules.sources[0]?.url} target="_blank" rel="noreferrer">공식 근거 확인 <Icon name="chevron" size={14} /></a>
          </article>
        )}
        {account && (
          <article className="card tax-notes">
            <div><strong>장점</strong>{account.benefits.map((item) => <span key={item}>✓ {item}</span>)}</div>
            <div><strong>유의사항</strong>{account.cautions.map((item) => <span key={item}>· {item}</span>)}</div>
          </article>
        )}
      </section>
    </PageContainer>
  );
}

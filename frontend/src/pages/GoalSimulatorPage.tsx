import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { updateUserPreferences, useUserPreferences } from '../data/userPreferences';
import {
  buildGoalShareUrl,
  createGoalSnapshot,
  deleteGoalSnapshot,
  loadGoalSnapshots,
  parseGoalShareParams,
  saveGoalSnapshot,
  type GoalScenarioInputs,
  type GoalSnapshot,
} from '../data/goalSnapshots';
import { useToast } from '../app/toast';
import { goalApi } from '../services/goalApi';

const targetOptions = [100_000_000, 300_000_000, 500_000_000, 1_000_000_000];
const sensitivityLabels = {
  lower: '입력보다 2%p 낮음',
  base: '입력 수익률',
  higher: '입력보다 2%p 높음',
};

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

function formatSavedAt(value: string) {
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

export function GoalSimulatorPage() {
  const preferences = useUserPreferences();
  const { showToast } = useToast();
  const sharedInputs = useMemo(
    () => parseGoalShareParams(window.location.hash),
    [],
  );
  const [currentAssets, setCurrentAssets] = useState(
    sharedInputs?.currentAssetsKrw ?? 10_000_000,
  );
  const [targetAmount, setTargetAmount] = useState(
    sharedInputs?.targetAmountKrw ?? 300_000_000,
  );
  const [monthlyContribution, setMonthlyContribution] = useState(
    sharedInputs?.monthlyContributionKrw ?? preferences.monthlyInvestmentKrw,
  );
  const [investmentYears, setInvestmentYears] = useState(
    sharedInputs?.investmentYears ?? preferences.investmentYears,
  );
  const [returnRate, setReturnRate] = useState(
    sharedInputs?.annualReturnRatePct ?? preferences.annualReturnRatePct,
  );
  const [snapshots, setSnapshots] = useState(loadGoalSnapshots);
  const simulationQuery = useQuery({
    queryKey: [
      'goal-simulation',
      currentAssets,
      targetAmount,
      monthlyContribution,
      investmentYears,
      returnRate,
    ],
    queryFn: () => goalApi.simulate({
      current_assets_krw: currentAssets,
      target_amount_krw: targetAmount,
      monthly_contribution_krw: monthlyContribution,
      investment_years: investmentYears,
      annual_return_rate_pct: returnRate,
    }),
    enabled: targetAmount > 0 && monthlyContribution >= 0,
  });
  const simulation = simulationQuery.data;
  const visibleMilestones = useMemo(() => {
    if (!simulation) return [];
    const interval = investmentYears <= 10 ? 1 : 5;
    return simulation.milestones.filter((item) => (
      item.year === 1
      || item.year === investmentYears
      || item.year % interval === 0
    ));
  }, [investmentYears, simulation]);
  const chartMaximum = Math.max(
    targetAmount,
    Number(simulation?.projected_value ?? 0),
    1,
  );
  const achievementRate = Number(simulation?.target_achievement_rate_pct ?? 0);
  const scenarioInputs: GoalScenarioInputs = {
    currentAssetsKrw: currentAssets,
    targetAmountKrw: targetAmount,
    monthlyContributionKrw: monthlyContribution,
    investmentYears,
    annualReturnRatePct: returnRate,
  };

  const updateMonthlyContribution = (value: number) => {
    setMonthlyContribution(value);
    updateUserPreferences({ monthlyInvestmentKrw: value });
  };

  const updateInvestmentYears = (value: number) => {
    setInvestmentYears(value);
    updateUserPreferences({ investmentYears: value });
  };

  const updateReturnRate = (value: number) => {
    setReturnRate(value);
    updateUserPreferences({ annualReturnRatePct: value });
  };

  const saveCurrentResult = () => {
    if (!simulation) return;
    try {
      const snapshot = createGoalSnapshot(scenarioInputs, {
        projectedValue: simulation.projected_value,
        achievementRatePct: simulation.target_achievement_rate_pct,
        requiredMonthlyContribution: simulation.required_monthly_contribution,
      });
      setSnapshots(saveGoalSnapshot(snapshot));
      showToast('목표 계산 결과를 이 브라우저에 저장했습니다.');
    } catch {
      showToast('결과를 저장하지 못했습니다. 브라우저 저장소 설정을 확인해주세요.');
    }
  };

  const copyShareLink = async () => {
    try {
      await navigator.clipboard.writeText(buildGoalShareUrl(scenarioInputs));
      showToast('같은 조건을 재현하는 공유 링크를 복사했습니다.');
    } catch {
      showToast('링크를 복사하지 못했습니다. 브라우저 권한을 확인해주세요.');
    }
  };

  const loadSnapshot = (snapshot: GoalSnapshot) => {
    setCurrentAssets(snapshot.inputs.currentAssetsKrw);
    setTargetAmount(snapshot.inputs.targetAmountKrw);
    updateMonthlyContribution(snapshot.inputs.monthlyContributionKrw);
    updateInvestmentYears(snapshot.inputs.investmentYears);
    updateReturnRate(snapshot.inputs.annualReturnRatePct);
    showToast('저장한 목표 조건을 불러왔습니다.');
  };

  const removeSnapshot = (snapshotId: string) => {
    try {
      setSnapshots(deleteGoalSnapshot(snapshotId));
      showToast('저장한 목표 시나리오를 삭제했습니다.');
    } catch {
      showToast('저장 결과를 삭제하지 못했습니다.');
    }
  };

  return (
    <PageContainer className="content-page goal-page">
      <section className="page-title">
        <span className="title-icon blue"><Icon name="target" size={23} /></span>
        <div><p className="eyebrow">GOAL SIMULATOR</p><h1>목표 금액까지 가는 길 계산하기</h1><p>현재 자산과 투자 계획을 입력하면 필요한 월 투자금과 연도별 경로를 계산합니다.</p></div>
      </section>

      <section className="goal-layout">
        <article className="card goal-form">
          <div className="step-title"><span>1</span><div><strong>목표와 투자 조건</strong><p>월 투자금·기간·수익률은 내 설정과 함께 사용합니다.</p></div></div>
          <label>목표 금액</label>
          <div className="goal-target-options">
            {targetOptions.map((amount) => (
              <button key={amount} className={targetAmount === amount ? 'active' : ''} onClick={() => setTargetAmount(amount)}>
                {formatCompactWon(amount)}
              </button>
            ))}
          </div>
          <div className="money-input"><span>₩</span><input aria-label="목표 금액" type="number" min="1" step="1000000" value={targetAmount} onChange={(event) => setTargetAmount(Math.max(1, Number(event.target.value)))} /><em>원</em></div>
          <label>현재 투자 가능 자산</label>
          <div className="money-input"><span>₩</span><input aria-label="현재 투자 가능 자산" type="number" min="0" step="1000000" value={currentAssets} onChange={(event) => setCurrentAssets(Math.max(0, Number(event.target.value)))} /><em>원</em></div>
          <label>월 투자금</label>
          <div className="money-input"><span>₩</span><input aria-label="월 투자금" type="number" min="0" step="10000" value={monthlyContribution} onChange={(event) => updateMonthlyContribution(Math.max(0, Number(event.target.value)))} /><em>원</em></div>
          <label>투자 기간</label>
          <div className="slider-label"><strong>{investmentYears}년</strong><span>{investmentYears >= 20 ? '장기 목표' : '중기 목표'}</span></div>
          <input className="range-input" type="range" min="1" max="50" value={investmentYears} onChange={(event) => updateInvestmentYears(Number(event.target.value))} />
          <div className="range-ends"><span>1년</span><span>50년</span></div>
          <label>연 예상 수익률</label>
          <div className="option-grid three">{[4, 7, 10].map((rate) => <button className={returnRate === rate ? 'active' : ''} key={rate} onClick={() => updateReturnRate(rate)}>{rate}%<Icon name="check" size={15} /></button>)}</div>
          <div className="form-note"><Icon name="shield" size={17} /><p>입력 수익률이 매년 반복된다는 단순 복리 가정이며 실제 결과를 보장하지 않습니다.</p></div>
        </article>

        <article className="card goal-result">
          <div className="result-heading"><span className="ai-badge"><Icon name="chart" size={15} /> 규칙 기반 계산</span><p>{simulation?.engine_version ?? '계산 중'}</p></div>
          {simulationQuery.isError && <div className="data-status error"><span>목표 계산 결과를 불러오지 못했습니다.</span><button onClick={() => simulationQuery.refetch()}>다시 시도</button></div>}
          {simulation ? (
            <>
              <div className="goal-result-hero">
                <span>{investmentYears}년 뒤 예상 자산</span>
                <strong>{formatCompactWon(simulation.projected_value)}</strong>
                <p>목표 {formatCompactWon(targetAmount)}의 <b>{achievementRate.toLocaleString('ko-KR')}%</b></p>
                <i><b style={{ width: `${Math.min(achievementRate, 100)}%` }} /></i>
              </div>
              <div className="goal-metrics">
                <span><small>총 투입 원금</small><strong>{formatCompactWon(simulation.total_contributed_principal)}</strong></span>
                <span><small>예상 운용수익</small><strong>{formatCompactWon(simulation.investment_gain)}</strong></span>
                <span><small>{Number(simulation.target_gap) > 0 ? '목표 부족액' : '목표 초과액'}</small><strong>{formatCompactWon(Number(simulation.target_gap) > 0 ? simulation.target_gap : simulation.target_surplus)}</strong></span>
              </div>
              <div className="goal-required">
                <div><span>현재 조건에서 목표를 맞추려면</span><strong>월 {formatCompactWon(simulation.required_monthly_contribution)}</strong></div>
                <p>{!simulation.required_monthly_within_supported_limit ? '필요 월 투자금이 계산기 지원 상한인 1억원을 넘습니다. 목표 금액이나 기간을 조정해보세요.' : Number(simulation.additional_monthly_contribution) > 0 ? `현재보다 월 ${formatCompactWon(simulation.additional_monthly_contribution)} 추가가 필요합니다.` : '현재 월 투자 계획으로 목표 금액 이상을 기대하는 계산입니다.'}</p>
              </div>
              <div className="goal-result-actions">
                <button onClick={saveCurrentResult}><Icon name="bookmark" size={15} /> 결과 저장</button>
                <button onClick={copyShareLink}><Icon name="link" size={15} /> 공유 링크 복사</button>
              </div>
              <small className="goal-share-note">공유 링크에는 현재 자산·목표·납입 조건이 포함됩니다. 신뢰할 수 있는 사람에게만 보내세요.</small>
              <p className="disclaimer"><Icon name="info" size={14} /> {simulation.disclaimer}</p>
            </>
          ) : <div className="tax-loading">목표까지 필요한 투자 경로를 계산하고 있습니다…</div>}
        </article>
      </section>

      {simulation && (
        <section className="goal-detail-grid">
          <article className="card goal-milestones">
            <div className="section-heading"><div><h2>연도별 예상 성장 경로</h2><p>연말 납입을 반영한 결정론적 계산입니다.</p></div><span>{simulation.formula}</span></div>
            <div className="goal-path-chart">
              {visibleMilestones.map((milestone) => (
                <div key={milestone.year}>
                  <span>{milestone.year}년</span>
                  <i><b style={{ width: `${Math.min(100, Math.max(2, Number(milestone.projected_value) / chartMaximum * 100))}%` }} /></i>
                  <strong>{formatCompactWon(milestone.projected_value)}</strong>
                </div>
              ))}
            </div>
          </article>

          <article className="card goal-sensitivity">
            <div className="section-heading"><div><h2>수익률 민감도</h2><p>±2%p 차이가 장기 결과에 미치는 영향을 비교합니다.</p></div></div>
            <div className="goal-sensitivity-cards">
              {simulation.sensitivity.map((scenario) => (
                <div className={scenario.kind === 'base' ? 'active' : ''} key={scenario.kind}>
                  <span>{sensitivityLabels[scenario.kind]}</span>
                  <strong>연 {scenario.annual_return_rate_pct}%</strong>
                  <b>{formatCompactWon(scenario.projected_value)}</b>
                  <small>목표의 {scenario.target_achievement_rate_pct}%</small>
                </div>
              ))}
            </div>
            <div className="goal-actions">
              <Link to="/strategy">목표에 맞는 자산배분 보기 <Icon name="chevron" size={14} /></Link>
              <Link to="/portfolio">내 모의 포트폴리오 점검 <Icon name="chevron" size={14} /></Link>
            </div>
          </article>
        </section>
      )}

      <section className="card goal-saved-results">
        <div className="section-heading"><div><h2>저장한 목표 시나리오</h2><p>이 브라우저에만 보관되며 최대 10개까지 저장합니다.</p></div><span>{snapshots.length}개 저장됨</span></div>
        {snapshots.length > 0 ? (
          <div className="goal-snapshot-list">
            {snapshots.map((snapshot) => (
              <article key={snapshot.id}>
                <div><span>{formatSavedAt(snapshot.savedAt)}</span><strong>목표 {formatCompactWon(snapshot.inputs.targetAmountKrw)}</strong><small>월 {formatCompactWon(snapshot.inputs.monthlyContributionKrw)} · {snapshot.inputs.investmentYears}년 · 연 {snapshot.inputs.annualReturnRatePct}%</small></div>
                <p><span>예상 {formatCompactWon(snapshot.summary.projectedValue)}</span><strong>{snapshot.summary.achievementRatePct}% 달성</strong></p>
                <button onClick={() => loadSnapshot(snapshot)}>불러오기</button>
                <button className="delete" aria-label={`${formatSavedAt(snapshot.savedAt)} 목표 시나리오 삭제`} onClick={() => removeSnapshot(snapshot.id)}><Icon name="trash" size={14} /></button>
              </article>
            ))}
          </div>
        ) : <div className="goal-snapshot-empty"><Icon name="bookmark" size={20} /><span>비교해두고 싶은 계산 결과를 저장해보세요.</span></div>}
      </section>
    </PageContainer>
  );
}

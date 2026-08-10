import { useNavigate } from 'react-router-dom';
import { setGoalStrategyMode, useActiveGoalSnapshot } from '../data/goalSnapshots';
import { Icon } from './common/Icon';

function formatCompactWon(value: string | number) {
  const amount = Number(value);
  if (Math.abs(amount) >= 100_000_000) return `${(amount / 100_000_000).toFixed(2)}억원`;
  if (Math.abs(amount) >= 10_000) {
    return `${Math.round(amount / 10_000).toLocaleString('ko-KR')}만원`;
  }
  return `${Math.round(amount).toLocaleString('ko-KR')}원`;
}

export function ActiveGoalCard() {
  const navigate = useNavigate();
  const activeGoal = useActiveGoalSnapshot();

  if (!activeGoal) {
    return (
      <article className="card active-goal-card empty">
        <div className="card-heading">
          <div><span className="label">진행 중인 목표</span></div>
          <Icon name="target" size={19} />
        </div>
        <div className="active-goal-empty">
          <span><Icon name="bookmark" size={22} /></span>
          <strong>아직 대표 목표가 없어요.</strong>
          <p>목표를 계산하고 저장하면 홈과 투자전략에서 같은 계획을 이어갈 수 있어요.</p>
        </div>
        <button className="soft-button" onClick={() => navigate('/goal-simulator')}>
          목표 계획 만들기 <Icon name="chevron" size={14} />
        </button>
      </article>
    );
  }

  const achievementRate = Number(activeGoal.summary.achievementRatePct);
  const progressWidth = Math.min(Math.max(achievementRate, 0), 100);

  return (
    <article className="card active-goal-card">
      <div className="card-heading">
        <div><span className="label">진행 중인 목표</span><span className="pill positive">계획 연결됨</span></div>
        <button
          className="more-button"
          onClick={() => navigate('/goal-simulator')}
          aria-label="진행 중인 목표 관리"
        >
          <Icon name="chevron" size={18} />
        </button>
      </div>
      <div className="active-goal-title">
        <span><Icon name="target" size={17} /></span>
        <div>
          <strong>{activeGoal.name}</strong>
          <small>{activeGoal.inputs.investmentYears}년 뒤 {formatCompactWon(activeGoal.summary.effectiveTargetAmount)}</small>
        </div>
      </div>
      <div className="active-goal-projection">
        <div><span>예상 자산</span><strong>{formatCompactWon(activeGoal.summary.projectedValue)}</strong></div>
        <div><span>계획 달성 예상</span><strong>{activeGoal.summary.achievementRatePct}%</strong></div>
      </div>
      <div
        className="active-goal-progress"
        role="progressbar"
        aria-label={`${activeGoal.name} 계획 달성 예상`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progressWidth)}
      >
        <i style={{ width: `${progressWidth}%` }} />
      </div>
      <p className="active-goal-plan">
        첫해 월 {formatCompactWon(activeGoal.inputs.monthlyContributionKrw)}
        {activeGoal.inputs.annualContributionGrowthRatePct > 0
          ? ` · 매년 ${activeGoal.inputs.annualContributionGrowthRatePct}% 증액`
          : ' · 정액 투자'}
      </p>
      <button className="primary-button full" onClick={() => {
        setGoalStrategyMode('active_goal');
        navigate('/strategy');
      }}>
        이 목표로 전략 보기 <Icon name="chevron" size={14} />
      </button>
    </article>
  );
}

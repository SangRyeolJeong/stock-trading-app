import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { strategyApi } from '../services/strategyApi';
import type { StrategyRequest } from '../types/api';

export function StrategyPage() {
  const [goal, setGoal] = useState('30년 장기투자');
  const [risk, setRisk] = useState('성장형');
  const request: StrategyRequest = {
    goal: goal === '30년 장기투자' ? 'retirement' : goal === '10년 목돈 마련' ? 'lump_sum' : 'cashflow',
    horizon_years: goal === '30년 장기투자' ? 30 : 10,
    monthly_amount_krw: 500_000,
    risk_profile: risk === '성장형' ? 'growth' : risk === '균형형' ? 'balanced' : 'conservative',
  };
  const strategyQuery = useQuery({
    queryKey: ['strategy', request],
    queryFn: () => strategyApi.recommend(request),
  });
  const recommendation = strategyQuery.data;

  return (
    <PageContainer className="content-page strategy-page">
      <section className="strategy-hero">
        <div><span className="ai-badge light"><Icon name="sparkles" size={15} /> MOA AI STRATEGIST</span><h1>좋은 상품보다<br /><em>나에게 맞는 방식</em>을 찾으세요.</h1><p>투자 기간, 목적, 계좌까지 함께 보고 실행 가능한 전략을 제안해요.</p></div>
        <div className="hero-orbit"><span className="center-orb"><Icon name="sparkles" size={30} /></span><span className="orbit-item one">ISA</span><span className="orbit-item two">QQQM</span><span className="orbit-item three">IRP</span><span className="orbit-item four">연금</span></div>
      </section>
      <section className="strategy-layout">
        <article className="card strategy-form">
          <div className="step-title"><span>1</span><div><strong>어떤 투자를 계획하고 있나요?</strong><p>선택에 따라 전략이 실시간으로 바뀌어요.</p></div></div>
          <label>목표</label>
          <div className="choice-stack">{['30년 장기투자', '10년 목돈 마련', '배당 현금흐름'].map((item) => <button key={item} className={goal === item ? 'active' : ''} onClick={() => setGoal(item)}><span><Icon name={item === '30년 장기투자' ? 'clock' : item === '10년 목돈 마련' ? 'target' : 'wallet'} size={19} />{item}</span>{goal === item && <Icon name="check" size={17} />}</button>)}</div>
          <label>투자 성향</label>
          <div className="segmented wide">{['안정형', '균형형', '성장형'].map((item) => <button key={item} className={risk === item ? 'active' : ''} onClick={() => setRisk(item)}>{item}</button>)}</div>
          <label>선호하는 조건</label>
          <div className="check-list"><label><input type="checkbox" defaultChecked /><span><Icon name="check" size={13} /></span>언제든 매도할 수 있는 유동성</label><label><input type="checkbox" defaultChecked /><span><Icon name="check" size={13} /></span>낮은 운용보수</label><label><input type="checkbox" /><span><Icon name="check" size={13} /></span>매달 배당금 수령</label></div>
        </article>
        <article className="card recommendation">
          <div className="recommend-top"><div><span className="ai-badge"><Icon name="sparkles" size={15} /> 규칙 기반 추천 전략</span><h2>{goal} · {risk}</h2></div><span className="fit-score"><b>{recommendation?.score ?? 94}</b>점<small>적합도</small></span></div>
          {strategyQuery.isError && <div className="data-status error"><span>전략 서버에 연결하지 못해 샘플 전략을 표시하고 있어요.</span><button onClick={() => strategyQuery.refetch()}>다시 시도</button></div>}
          <div className="strategy-name"><span className="strategy-icon">Q</span><div><span>핵심 성장 자산</span><h3>달러 직투 + QQQM 적립식</h3><p>매월 50만원 · 매월 15일 자동 매수</p></div></div>
          <div className="why-box">
            <h4>왜 이 전략인가요?</h4>
            {(recommendation?.reasons ?? [
              '투자 기간이 길어 비용 차이가 누적될 수 있습니다.',
              '연금 목적 자금과 자유롭게 쓸 자금을 계좌별로 분리합니다.',
              '세액공제 계산은 규칙 엔진으로 검증하고 AI는 설명만 담당합니다.',
            ]).map((reason, index) => <div key={reason}><span>{String(index + 1).padStart(2, '0')}</span><p><strong>{reason}</strong><small>{recommendation?.reason_codes[index] ?? 'SAMPLE_REASON'}</small></p></div>)}
          </div>
          <div className="allocation-plan">
            {Object.entries(recommendation?.allocation ?? { '해외주식 직투': 50, '연금저축 국내상장 ETF': 40, '현금성 자산': 10 }).map(([label, weight]) => <div key={label}><span>{label}</span><strong>{weight}%</strong></div>)}
          </div>
          <button className="primary-button full">이 전략으로 모의투자 시작하기 <Icon name="chevron" size={15} /></button>
          <p className="disclaimer"><Icon name="info" size={14} /> AI 분석은 투자 권유가 아니며, 최종 판단과 책임은 투자자에게 있어요.</p>
        </article>
      </section>
    </PageContainer>
  );
}

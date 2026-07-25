import { useState } from 'react';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';

export function StrategyPage() {
  const [goal, setGoal] = useState('30년 장기투자');
  const [risk, setRisk] = useState('성장형');

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
          <div className="recommend-top"><div><span className="ai-badge"><Icon name="sparkles" size={15} /> AI 추천 전략</span><h2>{goal} · {risk}</h2></div><span className="fit-score"><b>94</b>점<small>적합도</small></span></div>
          <div className="strategy-name"><span className="strategy-icon">Q</span><div><span>핵심 성장 자산</span><h3>달러 직투 + QQQM 적립식</h3><p>매월 50만원 · 매월 15일 자동 매수</p></div></div>
          <div className="why-box">
            <h4>왜 이 전략인가요?</h4>
            <div><span>01</span><p><strong>QQQ와 같은 나스닥100을 추종해요</strong><small>장기 성과의 핵심은 유지하면서 총보수는 연 0.15%로 더 낮아요.</small></p></div>
            <div><span>02</span><p><strong>달러 유동성을 확보할 수 있어요</strong><small>해외 직투 계좌에서 달러를 직접 보유하고 자유롭게 매매할 수 있어요.</small></p></div>
            <div><span>03</span><p><strong>연금 계좌와 함께 쓰면 더 효율적이에요</strong><small>노후 자금은 연금저축의 국내상장 ETF로 나눠 세액공제를 챙기세요.</small></p></div>
          </div>
          <div className="allocation-plan"><div><span>QQQM 직투</span><strong>60%</strong></div><div><span>연금저축 나스닥100</span><strong>30%</strong></div><div><span>달러 현금</span><strong>10%</strong></div></div>
          <button className="primary-button full">이 전략으로 모의투자 시작하기 <Icon name="chevron" size={15} /></button>
          <p className="disclaimer"><Icon name="info" size={14} /> AI 분석은 투자 권유가 아니며, 최종 판단과 책임은 투자자에게 있어요.</p>
        </article>
      </section>
    </PageContainer>
  );
}

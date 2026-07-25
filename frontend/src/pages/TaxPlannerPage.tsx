import { useState } from 'react';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { accounts } from '../data/mock/tax';

export function TaxPlannerPage() {
  const [income, setIncome] = useState('5,500만원 이하');
  const [selected, setSelected] = useState('pension');
  const account = accounts.find((item) => item.id === selected) ?? accounts[0];

  return (
    <PageContainer className="content-page">
      <section className="page-title">
        <span className="title-icon blue"><Icon name="wallet" size={23} /></span>
        <div><p className="eyebrow">TAX PLANNER</p><h1>내게 맞는 절세 계좌 찾기</h1><p>같은 투자도 어떤 계좌를 쓰느냐에 따라 세후 수익이 달라져요.</p></div>
      </section>
      <section className="tax-grid">
        <article className="card planner-form">
          <div className="step-title"><span>1</span><div><strong>투자 조건을 알려주세요</strong><p>샘플 조건으로 바로 비교해볼 수 있어요.</p></div></div>
          <label>연간 총급여</label>
          <div className="option-grid two">{['5,500만원 이하', '5,500만원 초과'].map((item) => <button className={income === item ? 'active' : ''} key={item} onClick={() => setIncome(item)}>{item}<Icon name="check" size={15} /></button>)}</div>
          <label>투자 목적</label>
          <div className="option-grid three"><button className="active">노후 준비</button><button>목돈 마련</button><button>자유로운 운용</button></div>
          <label>예상 투자 기간</label>
          <div className="slider-label"><strong>30년</strong><span>장기투자</span></div>
          <input className="range-input" type="range" min="1" max="40" defaultValue="30" />
          <div className="range-ends"><span>1년</span><span>40년</span></div>
          <label>월 투자금</label>
          <div className="money-input"><span>₩</span><strong>500,000</strong><em>원</em></div>
          <div className="form-note"><Icon name="shield" size={17} /><p>입력한 정보는 계좌 추천에만 사용되며 저장되지 않아요.</p></div>
        </article>

        <article className="card tax-result">
          <div className="result-heading"><span className="ai-badge"><Icon name="sparkles" size={15} /> 맞춤 분석 완료</span><p>현재 조건에서 가장 유리한 조합이에요</p></div>
          <div className="winner">
            <div><span className="winner-rank">BEST</span><h2>연금저축펀드</h2><p>+ 국내상장 나스닥100 ETF</p></div>
            <div className="save-number"><span>30년 예상 절세 효과</span><strong>약 4,820만원</strong><small>직투 대비, 가정 수익률 연 7%</small></div>
          </div>
          <div className="result-bars">
            <div><span>직투 계좌</span><i><b style={{ width: '54%' }} /></i><strong>세후 4.21억</strong></div>
            <div><span>중개형 ISA</span><i><b style={{ width: '70%' }} /></i><strong>세후 4.48억</strong></div>
            <div className="best"><span>연금저축</span><i><b style={{ width: '91%' }} /></i><strong>세후 4.69억</strong></div>
            <div><span>IRP</span><i><b style={{ width: '82%' }} /></i><strong>세후 4.57억</strong></div>
          </div>
          <p className="disclaimer"><Icon name="info" size={14} /> 단순 가정에 따른 예시이며 실제 수익률, 환율, 세법 개정에 따라 달라질 수 있어요.</p>
        </article>
      </section>
      <section className="account-section">
        <div className="section-heading"><div><h2>계좌별로 꼼꼼히 비교했어요</h2><p>카드를 눌러 장점과 유의사항을 확인하세요.</p></div><span>샘플 계산 · 실행 전 최신 기준 재확인</span></div>
        <div className="account-cards">
          {accounts.map((item) => (
            <button key={item.id} onClick={() => setSelected(item.id)} className={`account-card ${selected === item.id ? 'active' : ''}`}>
              <div><span className="account-tag">{item.tag}</span>{selected === item.id && <span className="selected-check"><Icon name="check" size={14} /></span>}</div>
              <h3>{item.name}</h3><p>{item.note}</p>
              <div className="account-score"><i><b style={{ width: `${item.score}%` }} /></i><strong>{item.score}점</strong></div>
            </button>
          ))}
        </div>
        <article className="account-detail card">
          <div><span className="stock-logo account-logo"><Icon name="wallet" size={20} /></span><div><span>선택한 계좌</span><h3>{account.name}</h3></div></div>
          <dl><div><dt>과세 방식</dt><dd>{account.tax}</dd></div><div><dt>납입 한도</dt><dd>{account.limit}</dd></div><div><dt>추천 상품</dt><dd>{account.product}</dd></div></dl>
          <button>계좌 활용법 자세히 보기 <Icon name="chevron" size={14} /></button>
        </article>
      </section>
    </PageContainer>
  );
}

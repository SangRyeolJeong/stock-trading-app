import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { holdings, watchlist } from '../data/mock/market';

function MiniLineChart() {
  return (
    <svg className="mini-chart" viewBox="0 0 560 170" preserveAspectRatio="none" role="img" aria-label="최근 1개월 자산 추이">
      <defs>
        <linearGradient id="miniFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4c79ff" stopOpacity=".3" />
          <stop offset="100%" stopColor="#4c79ff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path className="grid-line" d="M0 32H560M0 86H560M0 140H560" />
      <path className="area" d="M0 138 C24 133 32 119 58 124 S94 113 118 116 S150 105 174 109 S210 89 232 94 S265 74 288 80 S321 64 347 72 S378 51 404 58 S444 43 466 47 S500 25 525 34 S548 23 560 19 V170H0Z" />
      <path className="line" d="M0 138 C24 133 32 119 58 124 S94 113 118 116 S150 105 174 109 S210 89 232 94 S265 74 288 80 S321 64 347 72 S378 51 404 58 S444 43 466 47 S500 25 525 34 S548 23 560 19" />
      <circle cx="560" cy="19" r="4" />
    </svg>
  );
}

export function HomePage() {
  const [range, setRange] = useState('1개월');
  const navigate = useNavigate();

  return (
    <PageContainer className="home-page">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">7월 25일 토요일</p>
          <h1>좋은 저녁이에요, 김모아님</h1>
          <p>오늘도 세금은 줄이고, 투자는 길게 이어가 볼까요?</p>
        </div>
        <button className="primary-button" onClick={() => navigate('/strategy')}><Icon name="sparkles" size={17} /> AI에게 전략 물어보기</button>
      </section>

      <section className="dashboard-grid">
        <article className="card asset-card">
          <div className="card-heading">
            <div><span className="label">총 자산</span><button className="small-link">KRW <Icon name="chevron" size={12} /></button></div>
            <button className="more-button"><Icon name="more" size={19} /></button>
          </div>
          <div className="asset-value"><strong>32,686,750</strong><span>원</span></div>
          <div className="asset-change"><span><Icon name="arrowUp" size={13} /> 2,184,320원</span><b>+7.16%</b><em>투자 원금 대비</em></div>
          <div className="range-tabs">
            {['1주', '1개월', '3개월', '1년', '전체'].map((item) => <button key={item} onClick={() => setRange(item)} className={range === item ? 'active' : ''}>{item}</button>)}
          </div>
          <MiniLineChart />
          <div className="chart-labels"><span>6월 25일</span><span>7월 25일</span></div>
        </article>

        <article className="card tax-score-card">
          <div className="card-heading">
            <div><span className="label">나의 절세 점수</span><p>놓치고 있는 혜택을 확인해보세요</p></div>
            <button className="more-button" onClick={() => navigate('/tax-planner')}><Icon name="chevron" size={18} /></button>
          </div>
          <div className="score-wrap">
            <div className="score-ring"><div><strong>72</strong><span>/ 100점</span></div></div>
            <div className="score-copy"><span className="pill positive">상위 31%</span><strong>잘하고 있어요!</strong><p>연금저축을 더 활용하면<br />최대 304,000원 절약 가능해요.</p></div>
          </div>
          <button className="soft-button" onClick={() => navigate('/tax-planner')}>내 절세 리포트 보기 <Icon name="chevron" size={15} /></button>
        </article>

        <article className="card watch-card">
          <div className="card-heading">
            <div><span className="label">관심 종목</span><p>실시간 시세</p></div>
            <button className="add-button"><Icon name="plus" size={15} /> 추가</button>
          </div>
          <div className="watch-list">
            {watchlist.map((stock) => (
              <button key={stock.symbol} className="watch-row" onClick={() => navigate(`/market/${stock.symbol}`)}>
                <span className="stock-logo" style={{ background: stock.color }}>{stock.symbol === '005930' ? 'S' : stock.symbol.slice(0, 1)}</span>
                <span className="stock-name"><strong>{stock.symbol}</strong><small>{stock.name}</small></span>
                <span className="stock-price"><strong>{stock.price}</strong><small className={stock.positive ? 'up' : 'down'}>{stock.change}</small></span>
              </button>
            ))}
          </div>
          <button className="text-button" onClick={() => navigate('/market/QQQM')}>관심 종목 전체보기 <Icon name="chevron" size={14} /></button>
        </article>

        <article className="card insight-card">
          <div className="insight-top">
            <span className="ai-badge"><Icon name="sparkles" size={15} /> MOA AI 인사이트</span>
            <span className="new-badge">NEW</span>
          </div>
          <h2>나스닥100, 어떤 계좌와<br />ETF가 가장 유리할까요?</h2>
          <p>30년 장기투자와 월 50만원 적립을 기준으로<br />세후 수익을 비교했어요.</p>
          <div className="compare-preview">
            <div><span>추천 조합</span><strong>연금저축 + TIGER 미국나스닥100</strong></div>
            <div><span>예상 절세</span><strong>약 4,820만원</strong></div>
          </div>
          <button onClick={() => navigate('/strategy')}>분석 결과 자세히 보기 <Icon name="chevron" size={15} /></button>
          <span className="decor-orb orb-one" /><span className="decor-orb orb-two" />
        </article>

        <article className="card allocation-card">
          <div className="card-heading">
            <div><span className="label">포트폴리오 구성</span><p>전체 투자자산 기준</p></div>
            <button className="more-button" onClick={() => navigate('/portfolio')}><Icon name="chevron" size={18} /></button>
          </div>
          <div className="allocation-content">
            <div className="donut"><div><strong>4</strong><span>종목</span></div></div>
            <div className="legend">
              {holdings.map((item) => <div key={item.symbol}><i style={{ background: item.color }} /><span>{item.symbol === 'CASH' ? '현금' : item.symbol}</span><b>{item.weight}%</b></div>)}
            </div>
          </div>
          <div className="rebalance-tip"><Icon name="info" size={16} /><span><strong>리밸런싱 알림</strong> QQQM 비중이 목표보다 7% 높아요.</span></div>
        </article>
      </section>
    </PageContainer>
  );
}

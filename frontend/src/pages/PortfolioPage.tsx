import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { holdings } from '../data/mock/market';

export function PortfolioPage() {
  return (
    <PageContainer className="content-page">
      <section className="page-title compact">
        <div><p className="eyebrow">MY PORTFOLIO</p><h1>내 포트폴리오</h1><p>계좌를 합쳐 전체 자산과 위험도를 한눈에 확인하세요.</p></div>
        <button className="primary-button"><Icon name="plus" size={16} /> 계좌 연결</button>
      </section>
      <section className="portfolio-summary">
        <article className="card portfolio-total"><span>평가 금액</span><h2>22,686,750원</h2><p><b>+1,410,040원</b> (+6.63%)</p><div className="long-bar">{holdings.map((holding) => <i key={holding.symbol} style={{ width: `${holding.weight}%`, background: holding.color }} />)}</div><div className="portfolio-legend">{holdings.map((holding) => <span key={holding.symbol}><i style={{ background: holding.color }} />{holding.symbol} {holding.weight}%</span>)}</div></article>
        <article className="card metric-card"><span>예상 연 보수</span><h3>0.18%</h3><p>약 40,800원</p><small className="positive-text">동일 전략 평균보다 0.12% 낮아요</small></article>
        <article className="card metric-card"><span>위험도</span><h3>성장형</h3><p>변동성 18.4%</p><small>미국 기술주 비중이 높아요</small></article>
      </section>
      <article className="card holdings-card">
        <div className="card-heading"><div><span className="label">보유 자산</span><p>실시간 평가 기준</p></div><button className="add-button">수익률순 <Icon name="chevron" size={13} /></button></div>
        <div className="holdings-head"><span>자산</span><span>보유</span><span>평가 금액</span><span>평가 손익</span><span>비중</span><span /></div>
        {holdings.map((item) => <div className="holding-row" key={item.symbol}><span className="holding-name"><i style={{ background: item.color }}>{item.symbol.slice(0, 1)}</i><span><strong>{item.symbol}</strong><small>{item.name}</small></span></span><span>{item.quantity}</span><strong>{item.value}</strong><span className={item.positive ? 'up' : 'down'}><strong>{item.profit}</strong><small>{item.rate}</small></span><span><i className="weight-bar"><b style={{ width: `${item.weight * 2}%`, background: item.color }} /></i>{item.weight}%</span><button><Icon name="more" size={18} /></button></div>)}
      </article>
    </PageContainer>
  );
}

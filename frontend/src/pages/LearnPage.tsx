import { useState } from 'react';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { lessons } from '../data/mock/learn';

export function LearnPage() {
  const [filter, setFilter] = useState('전체');
  const filteredLessons = lessons.filter((lesson) =>
    filter === '전체'
    || lesson.category === filter
    || (filter === '투자자산운용사' && lesson.category === '자격증')
  );

  return (
    <PageContainer className="content-page">
      <section className="learn-hero">
        <div><p className="eyebrow">MOA LEARN</p><h1>어려운 투자를<br />내 것이 되는 지식으로.</h1><p>절세부터 자격증 핵심 개념까지, 검증된 콘텐츠만 모았어요.</p></div>
        <div className="today-lesson"><span>오늘의 5분 공부</span><strong>복리 효과는 언제부터<br />눈에 보일까요?</strong><button>이어보기 <Icon name="chevron" size={14} /></button></div>
      </section>
      <div className="filter-tabs">{['전체', 'ETF 비교', '절세 계좌', '연금', '해외주식', '투자자산운용사'].map((item) => <button key={item} onClick={() => setFilter(item)} className={filter === item ? 'active' : ''}>{item}</button>)}</div>
      <section className="lesson-grid">
        {filteredLessons.map((lesson) => <article className="card lesson-card" key={lesson.title}><div className={`lesson-visual ${lesson.color}`}><Icon name={lesson.icon} size={30} /><span>{lesson.category}</span></div><div className="lesson-copy"><span>{lesson.category}</span><h3>{lesson.title}</h3><p>{lesson.desc}</p><small><Icon name="clock" size={13} /> {lesson.time} 읽기</small></div></article>)}
      </section>
    </PageContainer>
  );
}

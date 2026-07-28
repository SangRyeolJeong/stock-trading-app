import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import { lessons, loadLessonProgress } from '../data/learn';

const FILTERS = [
  { label: '전체', value: '전체' },
  { label: 'ETF 비교', value: 'ETF 비교' },
  { label: '절세 계좌', value: '절세 계좌' },
  { label: '연금', value: '연금' },
  { label: '해외주식', value: '해외주식' },
  { label: '투자 습관', value: '투자 습관' },
  { label: '투자자산운용사', value: '자격증' },
];

export function LearnPage() {
  const [filter, setFilter] = useState('전체');
  const [progress] = useState(loadLessonProgress);
  const navigate = useNavigate();
  const filteredLessons = lessons.filter((lesson) => filter === '전체' || lesson.category === filter);
  const completedCount = lessons.filter((lesson) => progress[lesson.slug]?.completed).length;
  const recentlyOpened = [...lessons]
    .filter((lesson) => progress[lesson.slug]?.lastOpenedAt && !progress[lesson.slug]?.completed)
    .sort((left, right) => (
      progress[right.slug].lastOpenedAt.localeCompare(progress[left.slug].lastOpenedAt)
    ))[0];
  const todayLesson = recentlyOpened ?? lessons.find((lesson) => lesson.slug === 'compound-interest') ?? lessons[0];
  const progressRate = lessons.length ? (completedCount / lessons.length) * 100 : 0;

  return (
    <PageContainer className="content-page">
      <section className="learn-hero">
        <div>
          <p className="eyebrow">MOA LEARN</p>
          <h1>어려운 투자를<br />내 것이 되는 지식으로.</h1>
          <p>공식 근거가 연결된 콘텐츠를 읽고 학습 진도를 기록해 보세요.</p>
          <div className="learn-progress">
            <span><i style={{ width: `${progressRate}%` }} /></span>
            <small>{completedCount}/{lessons.length}개 학습 완료</small>
          </div>
        </div>
        <div className="today-lesson">
          <span>{recentlyOpened ? '이어서 학습하기' : '오늘의 5분 공부'}</span>
          <strong>{todayLesson.title}</strong>
          <small>{todayLesson.category} · {todayLesson.minutes}분</small>
          <button onClick={() => navigate(`/learn/${todayLesson.slug}`)}>
            {recentlyOpened ? '이어보기' : '시작하기'} <Icon name="chevron" size={14} />
          </button>
        </div>
      </section>
      <div className="filter-tabs" role="tablist" aria-label="학습 카테고리">
        {FILTERS.map((item) => (
          <button
            key={item.value}
            role="tab"
            aria-selected={filter === item.value}
            onClick={() => setFilter(item.value)}
            className={filter === item.value ? 'active' : ''}
          >
            {item.label}
          </button>
        ))}
      </div>
      <section className="lesson-grid">
        {filteredLessons.map((lesson) => {
          const completed = progress[lesson.slug]?.completed;
          const started = Boolean(progress[lesson.slug]?.lastOpenedAt);
          return (
            <button
              type="button"
              className="card lesson-card"
              key={lesson.slug}
              onClick={() => navigate(`/learn/${lesson.slug}`)}
            >
              <div className={`lesson-visual ${lesson.color}`}>
                <Icon name={lesson.icon} size={30} />
                <span>{lesson.category}</span>
                {completed && <i className="lesson-completed"><Icon name="check" size={12} /> 완료</i>}
              </div>
              <div className="lesson-copy">
                <span>{started && !completed ? '학습 중' : lesson.category}</span>
                <h3>{lesson.title}</h3>
                <p>{lesson.desc}</p>
                <small><Icon name="clock" size={13} /> {lesson.minutes}분 읽기 · 공식 근거 {lesson.sources.length}개</small>
              </div>
            </button>
          );
        })}
      </section>
      {filteredLessons.length === 0 && <div className="card lesson-empty">이 카테고리의 콘텐츠를 준비하고 있어요.</div>}
    </PageContainer>
  );
}

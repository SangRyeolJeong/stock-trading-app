import { useEffect, useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { useToast } from '../app/toast';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import {
  findLesson,
  lessons,
  loadLessonProgress,
  saveLessonProgress,
} from '../data/learn';

export function LessonDetailPage() {
  const { slug } = useParams();
  const lesson = findLesson(slug);
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [completed, setCompleted] = useState(
    () => Boolean(slug && loadLessonProgress()[slug]?.completed),
  );

  useEffect(() => {
    if (!lesson) return;
    const progress = loadLessonProgress();
    setCompleted(Boolean(progress[lesson.slug]?.completed));
    saveLessonProgress({
      ...progress,
      [lesson.slug]: {
        completed: progress[lesson.slug]?.completed ?? false,
        lastOpenedAt: new Date().toISOString(),
      },
    });
  }, [lesson]);

  if (!lesson) return <Navigate to="/learn" replace />;

  const lessonIndex = lessons.findIndex((item) => item.slug === lesson.slug);
  const previousLesson = lessons[lessonIndex - 1];
  const nextLesson = lessons[lessonIndex + 1];

  const toggleCompleted = () => {
    const nextCompleted = !completed;
    const progress = loadLessonProgress();
    saveLessonProgress({
      ...progress,
      [lesson.slug]: {
        completed: nextCompleted,
        lastOpenedAt: new Date().toISOString(),
      },
    });
    setCompleted(nextCompleted);
    showToast(nextCompleted ? '학습 완료로 기록했어요.' : '학습 완료 표시를 취소했어요.');
  };

  return (
    <PageContainer className="lesson-detail-page">
      <button className="lesson-back" onClick={() => navigate('/learn')}>
        <Icon name="chevron" size={15} /> 투자 지식으로 돌아가기
      </button>
      <article className="lesson-article">
        <header className={`lesson-article-hero ${lesson.color}`}>
          <div className="lesson-article-meta">
            <span>{lesson.category}</span>
            <span><Icon name="clock" size={13} /> {lesson.minutes}분</span>
            <span>업데이트 {lesson.updatedAt}</span>
          </div>
          <h1>{lesson.title}</h1>
          <p>{lesson.summary}</p>
        </header>

        <div className="lesson-article-layout">
          <div className="lesson-article-body">
            <section className="lesson-takeaways">
              <span>먼저 기억할 3가지</span>
              <ul>
                {lesson.takeaways.map((takeaway) => <li key={takeaway}><Icon name="check" size={14} />{takeaway}</li>)}
              </ul>
            </section>
            {lesson.sections.map((section) => (
              <section className="lesson-section" key={section.heading}>
                <h2>{section.heading}</h2>
                {section.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
                {section.bullets && (
                  <ul>{section.bullets.map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>
                )}
              </section>
            ))}
            <aside className="lesson-disclaimer">
              <Icon name="info" size={17} />
              <p>교육용 일반 정보이며 개인별 투자·세무 자문이 아닙니다. 상품 조건과 세법은 바뀔 수 있으므로 실행 전 최신 공식 자료를 확인하세요.</p>
            </aside>
          </div>

          <aside className="lesson-evidence">
            <div className="card">
              <span className="evidence-label"><Icon name="shield" size={14} /> 공식 근거</span>
              {lesson.sources.map((source) => (
                <a href={source.url} target="_blank" rel="noreferrer" key={source.url}>
                  <span><strong>{source.title}</strong><small>{source.authority}</small></span>
                  <Icon name="chevron" size={14} />
                </a>
              ))}
              <small className="evidence-note">마지막 콘텐츠 검토: {lesson.updatedAt}</small>
            </div>
            {lesson.relatedSymbol && (
              <button className="card related-market" onClick={() => navigate(`/market/${lesson.relatedSymbol}`)}>
                <span>관련 종목 살펴보기</span>
                <strong>{lesson.relatedSymbol}</strong>
                <Icon name="chevron" size={15} />
              </button>
            )}
            <button className={`lesson-complete-button ${completed ? 'completed' : ''}`} onClick={toggleCompleted}>
              <Icon name={completed ? 'check' : 'book'} size={16} />
              {completed ? '학습 완료됨' : '학습 완료로 표시'}
            </button>
          </aside>
        </div>
      </article>

      <nav className="lesson-navigation" aria-label="이전 및 다음 학습">
        {previousLesson
          ? <button onClick={() => navigate(`/learn/${previousLesson.slug}`)}><small>이전 학습</small><strong>{previousLesson.title}</strong></button>
          : <span />}
        {nextLesson
          ? <button className="next" onClick={() => navigate(`/learn/${nextLesson.slug}`)}><small>다음 학습</small><strong>{nextLesson.title}</strong></button>
          : <button className="next" onClick={() => navigate('/learn')}><small>학습 완료</small><strong>전체 목록으로 돌아가기</strong></button>}
      </nav>
    </PageContainer>
  );
}

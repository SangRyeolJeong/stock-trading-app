import { useState, type FormEvent } from 'react';
import { useToast } from '../app/toast';
import { Icon } from '../components/common/Icon';
import { PageContainer } from '../components/layout/PageContainer';
import {
  DEFAULT_USER_PREFERENCES,
  resetUserPreferences,
  saveUserPreferences,
  useUserPreferences,
  type UserPreferences,
} from '../data/userPreferences';

const riskOptions: Array<{ label: string; value: UserPreferences['riskProfile'] }> = [
  { label: '안정형', value: 'conservative' },
  { label: '균형형', value: 'balanced' },
  { label: '성장형', value: 'growth' },
];

export function SettingsPage() {
  const preferences = useUserPreferences();
  return (
    <SettingsForm
      key={JSON.stringify(preferences)}
      preferences={preferences}
    />
  );
}

function SettingsForm({ preferences }: { preferences: UserPreferences }) {
  const [draft, setDraft] = useState(preferences);
  const { showToast } = useToast();

  const setNumber = (
    key: keyof Pick<
      UserPreferences,
      | 'annualSalaryKrw'
      | 'monthlyInvestmentKrw'
      | 'investmentYears'
      | 'annualReturnRatePct'
      | 'withdrawalAge'
    >,
    value: string,
  ) => {
    setDraft((current) => ({ ...current, [key]: Number(value) }));
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    saveUserPreferences(draft);
    showToast('사용자 설정을 저장했습니다.');
  };

  const handleReset = () => {
    resetUserPreferences();
    setDraft(DEFAULT_USER_PREFERENCES);
    showToast('기본 설정으로 되돌렸습니다.');
  };

  return (
    <PageContainer className="content-page settings-page">
      <section className="page-title">
        <span className="title-icon blue"><Icon name="target" size={23} /></span>
        <div>
          <p className="eyebrow">MY SETTINGS</p>
          <h1>내 투자 기본 설정</h1>
          <p>여기서 저장한 값은 홈, 절세 플래너, 전략 추천에 함께 적용됩니다.</p>
        </div>
      </section>

      <form className="settings-layout" onSubmit={handleSubmit}>
        <article className="card settings-card">
          <div className="settings-heading">
            <span>프로필</span>
            <small>이 기기에만 저장</small>
          </div>
          <label htmlFor="display-name">표시 이름</label>
          <div className="settings-input">
            <input
              id="display-name"
              value={draft.displayName}
              maxLength={20}
              onChange={(event) => setDraft((current) => ({
                ...current,
                displayName: event.target.value,
              }))}
              required
            />
          </div>

          <div className="settings-heading divided">
            <span>투자 계획</span>
            <small>절세·전략 계산 공통값</small>
          </div>
          <div className="settings-fields">
            <label>
              연간 총급여
              <span className="settings-input">
                <input
                  type="number"
                  min="0"
                  max="1000000000"
                  step="1000000"
                  value={draft.annualSalaryKrw}
                  onChange={(event) => setNumber('annualSalaryKrw', event.target.value)}
                />
                <em>원</em>
              </span>
            </label>
            <label>
              월 투자금
              <span className="settings-input">
                <input
                  type="number"
                  min="10000"
                  max="100000000"
                  step="10000"
                  value={draft.monthlyInvestmentKrw}
                  onChange={(event) => setNumber('monthlyInvestmentKrw', event.target.value)}
                />
                <em>원</em>
              </span>
            </label>
            <label>
              예상 투자 기간
              <span className="settings-input">
                <input
                  type="number"
                  min="3"
                  max="40"
                  value={draft.investmentYears}
                  onChange={(event) => setNumber('investmentYears', event.target.value)}
                />
                <em>년</em>
              </span>
            </label>
            <label>
              연 예상 수익률
              <span className="settings-input">
                <input
                  type="number"
                  min="0"
                  max="30"
                  step="0.1"
                  value={draft.annualReturnRatePct}
                  onChange={(event) => setNumber('annualReturnRatePct', event.target.value)}
                />
                <em>%</em>
              </span>
            </label>
            <label>
              연금 수령 시작 나이
              <span className="settings-input">
                <input
                  type="number"
                  min="55"
                  max="100"
                  value={draft.withdrawalAge}
                  onChange={(event) => setNumber('withdrawalAge', event.target.value)}
                />
                <em>세</em>
              </span>
            </label>
          </div>
        </article>

        <aside className="card settings-card settings-preference">
          <div className="settings-heading">
            <span>투자 성향</span>
            <small>추천 엔진 입력값</small>
          </div>
          <div className="option-grid three">
            {riskOptions.map((option) => (
              <button
                type="button"
                className={draft.riskProfile === option.value ? 'active' : ''}
                key={option.value}
                onClick={() => setDraft((current) => ({
                  ...current,
                  riskProfile: option.value,
                }))}
              >
                {option.label}<Icon name="check" size={15} />
              </button>
            ))}
          </div>
          <div className="settings-summary">
            <span>공통 월 투자금<strong>{draft.monthlyInvestmentKrw.toLocaleString('ko-KR')}원</strong></span>
            <span>기본 투자 기간<strong>{draft.investmentYears}년</strong></span>
            <span>예상 수익률<strong>연 {draft.annualReturnRatePct}%</strong></span>
          </div>
          <div className="form-note">
            <Icon name="shield" size={17} />
            <p>설정은 현재 브라우저에만 저장되며 서버로 전송되지 않습니다. 계산 요청에는 필요한 숫자만 사용됩니다.</p>
          </div>
          <div className="settings-actions">
            <button type="button" className="settings-reset" onClick={handleReset}>기본값 복원</button>
            <button type="submit" className="primary-button">설정 저장 <Icon name="check" size={15} /></button>
          </div>
        </aside>
      </form>
    </PageContainer>
  );
}

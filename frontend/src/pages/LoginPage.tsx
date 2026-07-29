import { useState, type FormEvent } from 'react';
import { Logo } from '../components/layout/Logo';
import { getSupabaseClient } from '../services/authClient';

type AuthAction = 'sign-in' | 'sign-up';

export function LoginPage() {
  const [action, setAction] = useState<AuthAction>('sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const supabase = await getSupabaseClient();
    if (!supabase) return;
    setIsSubmitting(true);
    setMessage('');

    try {
      const result = action === 'sign-in'
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({
            email,
            password,
            options: { emailRedirectTo: window.location.origin },
          });
      if (result.error) {
        setMessage(action === 'sign-in'
          ? '이메일 또는 비밀번호를 확인해 주세요.'
          : result.error.message);
        return;
      }
      if (action === 'sign-up' && !result.data.session) {
        setMessage('확인 메일을 보냈습니다. 이메일 인증 후 로그인해 주세요.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectAction = (nextAction: AuthAction) => {
    setAction(nextAction);
    setMessage('');
  };

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <Logo />
        <div className="auth-heading">
          <p className="eyebrow">SECURE INVESTING WORKSPACE</p>
          <h1>{action === 'sign-in' ? 'MOA에 로그인' : 'MOA 계정 만들기'}</h1>
          <p>모의투자 원장과 포트폴리오는 로그인한 사용자별로 안전하게 분리됩니다.</p>
        </div>
        <div className="auth-tabs">
          <button
            type="button"
            className={action === 'sign-in' ? 'active' : ''}
            onClick={() => selectAction('sign-in')}
          >
            로그인
          </button>
          <button
            type="button"
            className={action === 'sign-up' ? 'active' : ''}
            onClick={() => selectAction('sign-up')}
          >
            회원가입
          </button>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            이메일
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            비밀번호
            <input
              type="password"
              autoComplete={action === 'sign-in' ? 'current-password' : 'new-password'}
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {message && <p className="auth-message">{message}</p>}
          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting
              ? '처리 중…'
              : action === 'sign-in' ? '로그인' : '계정 만들기'}
          </button>
        </form>
        <p className="auth-note">
          비밀번호는 MOA 서버가 저장하지 않으며 Supabase Auth에서 관리합니다.
        </p>
      </section>
    </main>
  );
}

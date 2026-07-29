import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LoginPage } from './LoginPage';

const getSupabaseClientMock = vi.hoisted(() => vi.fn());

vi.mock('../services/authClient', () => ({
  getSupabaseClient: getSupabaseClientMock,
}));

describe('LoginPage', () => {
  const signInWithPassword = vi.fn();
  const signUp = vi.fn();

  beforeEach(() => {
    getSupabaseClientMock.mockResolvedValue({
      auth: {
        signInWithPassword,
        signUp,
      },
    });
  });

  it('submits an email and password to Supabase sign-in', async () => {
    signInWithPassword.mockResolvedValue({
      data: { session: { access_token: 'token' } },
      error: null,
    });
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText('이메일'), 'investor@example.com');
    await user.type(screen.getByLabelText('비밀번호'), 'password123');
    const loginButtons = screen.getAllByRole('button', { name: '로그인' });
    await user.click(loginButtons[loginButtons.length - 1]);

    await waitFor(() => {
      expect(signInWithPassword).toHaveBeenCalledWith({
        email: 'investor@example.com',
        password: 'password123',
      });
    });
  });

  it('shows a safe message when sign-in fails', async () => {
    signInWithPassword.mockResolvedValue({
      data: { session: null },
      error: { message: 'provider details must not be shown' },
    });
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText('이메일'), 'investor@example.com');
    await user.type(screen.getByLabelText('비밀번호'), 'wrong-password');
    const loginButtons = screen.getAllByRole('button', { name: '로그인' });
    await user.click(loginButtons[loginButtons.length - 1]);

    expect(
      await screen.findByText('이메일 또는 비밀번호를 확인해 주세요.'),
    ).toBeInTheDocument();
    expect(screen.queryByText('provider details must not be shown')).not.toBeInTheDocument();
  });

  it('explains email confirmation after sign-up without a session', async () => {
    signUp.mockResolvedValue({
      data: { session: null },
      error: null,
    });
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.click(screen.getByRole('button', { name: '회원가입' }));
    await user.type(screen.getByLabelText('이메일'), 'new@example.com');
    await user.type(screen.getByLabelText('비밀번호'), 'password123');
    await user.click(screen.getByRole('button', { name: '계정 만들기' }));

    await waitFor(() => {
      expect(signUp).toHaveBeenCalledWith({
        email: 'new@example.com',
        password: 'password123',
        options: { emailRedirectTo: window.location.origin },
      });
    });
    expect(
      await screen.findByText('확인 메일을 보냈습니다. 이메일 인증 후 로그인해 주세요.'),
    ).toBeInTheDocument();
  });
});

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DEFAULT_USER_PREFERENCES,
  resetUserPreferences,
  saveUserPreferences,
  setUserPreferencesScope,
} from '../data/userPreferences';
import { ApiError } from '../services/apiClient';
import { PreferencesSync } from './preferencesSync';

const useAuthMock = vi.hoisted(() => vi.fn());
const getPreferencesMock = vi.hoisted(() => vi.fn());
const savePreferencesMock = vi.hoisted(() => vi.fn());

vi.mock('./authContext', () => ({
  useAuth: useAuthMock,
}));

vi.mock('../services/preferencesApi', () => ({
  preferencesApi: {
    get: getPreferencesMock,
    save: savePreferencesMock,
  },
}));

const serverPreferences = {
  ...DEFAULT_USER_PREFERENCES,
  displayName: '서버 사용자',
  riskProfile: 'balanced' as const,
};

function LocalPreferenceEditor() {
  return (
    <button
      type="button"
      onClick={() => saveUserPreferences({
        ...serverPreferences,
        displayName: '변경 사용자',
      })}
    >
      설정 변경
    </button>
  );
}

describe('PreferencesSync', () => {
  beforeEach(() => {
    setUserPreferencesScope(null);
    resetUserPreferences();
    window.localStorage.clear();
    useAuthMock.mockReturnValue({
      isSupabase: true,
      session: { user: { id: 'user-a' } },
    });
    getPreferencesMock.mockResolvedValue(serverPreferences);
    savePreferencesMock.mockImplementation(async (preferences) => preferences);
  });

  it('hydrates the user-scoped local cache from the server', async () => {
    render(
      <PreferencesSync>
        <div>동기화 완료 화면</div>
      </PreferencesSync>,
    );

    expect(screen.getByText('투자 설정을 동기화하고 있어요…')).toBeInTheDocument();
    expect(await screen.findByText('동기화 완료 화면')).toBeInTheDocument();
    expect(getPreferencesMock).toHaveBeenCalledOnce();
    expect(JSON.parse(
      window.localStorage.getItem('moa-user-preferences-v1:user-a') ?? '{}',
    )).toMatchObject({
      displayName: '서버 사용자',
      riskProfile: 'balanced',
    });
  });

  it('creates server preferences from a new user scoped default', async () => {
    getPreferencesMock.mockRejectedValue(
      new ApiError('저장된 사용자 설정이 없습니다.', 404),
    );

    render(
      <PreferencesSync>
        <div>최초 설정 완료</div>
      </PreferencesSync>,
    );

    expect(await screen.findByText('최초 설정 완료')).toBeInTheDocument();
    expect(savePreferencesMock).toHaveBeenCalledWith(DEFAULT_USER_PREFERENCES);
  });

  it('does not overwrite server state after an unclassified fetch failure', async () => {
    getPreferencesMock.mockRejectedValue(
      new ApiError('서버에 연결할 수 없습니다.', 0),
    );

    render(
      <PreferencesSync>
        <div>오프라인 로컬 화면</div>
      </PreferencesSync>,
    );

    expect(await screen.findByText('오프라인 로컬 화면')).toBeInTheDocument();
    await new Promise((resolve) => window.setTimeout(resolve, 700));
    expect(savePreferencesMock).not.toHaveBeenCalled();
  });

  it('debounces local changes before saving them to the server', async () => {
    const user = userEvent.setup();
    render(
      <PreferencesSync>
        <LocalPreferenceEditor />
      </PreferencesSync>,
    );

    await user.click(await screen.findByRole('button', { name: '설정 변경' }));

    await waitFor(() => {
      expect(savePreferencesMock).toHaveBeenLastCalledWith({
        ...serverPreferences,
        displayName: '변경 사용자',
      });
    });
  });
});

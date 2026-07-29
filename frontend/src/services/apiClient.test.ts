import { beforeEach, describe, expect, it, vi } from 'vitest';
import { API_BASE_URL, ApiError, apiClient } from './apiClient';

const getAccessTokenMock = vi.hoisted(() => vi.fn());

vi.mock('./authClient', () => ({
  getAccessToken: getAccessTokenMock,
}));

describe('apiClient', () => {
  beforeEach(() => {
    getAccessTokenMock.mockResolvedValue(null);
  });

  it('adds the current access token to API requests', async () => {
    getAccessTokenMock.mockResolvedValue('test-access-token');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiClient<{ ok: boolean }>('/paper/portfolio')).resolves.toEqual({
      ok: true,
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}/paper/portfolio`);
    expect(new Headers(options.headers).get('Authorization')).toBe(
      'Bearer test-access-token',
    );
  });

  it('does not overwrite an explicitly supplied authorization header', async () => {
    getAccessTokenMock.mockResolvedValue('session-token');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await apiClient('/health', {
      headers: { Authorization: 'Bearer explicit-token' },
    });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(options.headers).get('Authorization')).toBe(
      'Bearer explicit-token',
    );
  });

  it('exposes the backend error detail and status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: '주문 가능 수량을 초과했습니다.' }), {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    const request = apiClient('/paper/orders', { method: 'POST' });

    await expect(request).rejects.toEqual(
      new ApiError('주문 가능 수량을 초과했습니다.', 409),
    );
  });

  it('converts network failures to a safe client error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('socket failed')));

    await expect(apiClient('/market/quote/005930')).rejects.toEqual(
      new ApiError('서버에 연결할 수 없습니다.', 0),
    );
  });
});

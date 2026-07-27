import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../services/apiClient';
import type { QuoteTick } from '../types/api';

type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

export function useQuoteStream(symbol: string) {
  const [tick, setTick] = useState<QuoteTick | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>('connecting');

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retryTimer: number | undefined;
    let retryCount = 0;
    let disposed = false;
    setTick(null);

    const connect = () => {
      if (disposed) return;
      setStatus(retryCount === 0 ? 'connecting' : 'reconnecting');
      const socketBase = API_BASE_URL.replace(/^http/, 'ws');
      socket = new WebSocket(`${socketBase}/api/v1/markets/ws/quotes/${encodeURIComponent(symbol)}`);

      socket.onopen = () => {
        retryCount = 0;
        setStatus('connected');
      };
      socket.onmessage = (event) => {
        setTick(JSON.parse(event.data) as QuoteTick);
      };
      socket.onclose = () => {
        if (disposed) return;
        setStatus('reconnecting');
        retryCount += 1;
        retryTimer = window.setTimeout(connect, Math.min(10_000, 1_000 * 2 ** retryCount));
      };
      socket.onerror = () => socket?.close();
    };

    connect();
    return () => {
      disposed = true;
      window.clearTimeout(retryTimer);
      socket?.close();
      setStatus('disconnected');
    };
  }, [symbol]);

  return { tick, status };
}

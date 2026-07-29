import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../services/apiClient';
import type { QuoteTick } from '../types/api';

type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

export function useQuoteStream(symbol: string) {
  const [latestTick, setLatestTick] = useState<{
    symbol: string;
    tick: QuoteTick;
  } | null>(null);
  const [connection, setConnection] = useState<{
    symbol: string;
    status: ConnectionStatus;
  }>({ symbol, status: 'connecting' });

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retryTimer: number | undefined;
    let retryCount = 0;
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      const socketBase = API_BASE_URL.replace(/^http/, 'ws');
      socket = new WebSocket(`${socketBase}/api/v1/markets/ws/quotes/${encodeURIComponent(symbol)}`);

      socket.onopen = () => {
        retryCount = 0;
        setConnection({ symbol, status: 'connected' });
      };
      socket.onmessage = (event) => {
        setLatestTick({
          symbol,
          tick: JSON.parse(event.data) as QuoteTick,
        });
      };
      socket.onclose = () => {
        if (disposed) return;
        setConnection({ symbol, status: 'reconnecting' });
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
    };
  }, [symbol]);

  return {
    tick: latestTick?.symbol === symbol ? latestTick.tick : null,
    status: connection.symbol === symbol ? connection.status : 'connecting',
  };
}

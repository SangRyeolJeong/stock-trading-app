import type { OrderBook as OrderBookData, OrderBookLevel } from '../types/api';
import { formatQuotePrice, formatUpdatedAt } from '../utils/format';
import { Icon } from './common/Icon';

interface OrderBookProps {
  data: OrderBookData | undefined;
  currentPrice: number;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}

function formatQuantity(value: string) {
  return Number(value).toLocaleString('ko-KR', { maximumFractionDigits: 4 });
}

function OrderLevel({
  level,
  type,
  maxQuantity,
  currency,
}: {
  level: OrderBookLevel;
  type: 'ask' | 'bid';
  maxQuantity: number;
  currency: 'KRW' | 'USD';
}) {
  const depth = maxQuantity > 0 ? Math.min((Number(level.quantity) / maxQuantity) * 100, 100) : 0;
  return (
    <div className={`orderbook-level ${type}`}>
      <span className="orderbook-depth"><i style={{ width: `${depth}%` }} /></span>
      <strong>{formatQuotePrice(level.price, currency)}</strong>
      <span>{formatQuantity(level.quantity)}</span>
    </div>
  );
}

export default function OrderBook({
  data,
  currentPrice,
  isLoading,
  isError,
  onRetry,
}: OrderBookProps) {
  if (isLoading) return <div className="orderbook-state">호가를 불러오는 중…</div>;
  if (isError) {
    return (
      <div className="orderbook-state error">
        <span>호가 데이터를 불러오지 못했습니다.</span>
        <button onClick={onRetry}>다시 시도</button>
      </div>
    );
  }
  if (!data || (!data.asks.length && !data.bids.length)) {
    return <div className="orderbook-state">표시할 호가가 없습니다.</div>;
  }

  const maxQuantity = Math.max(
    ...data.asks.map((level) => Number(level.quantity)),
    ...data.bids.map((level) => Number(level.quantity)),
    0,
  );

  return (
    <div className="orderbook-view">
      <div className="orderbook-summary">
        <span>매도 잔량 <strong>{formatQuantity(data.total_ask_quantity)}</strong></span>
        <small>{data.source === 'kis' ? 'KIS REST 호가' : '데모 호가'} · {formatUpdatedAt(data.as_of)}</small>
        <span>매수 잔량 <strong>{formatQuantity(data.total_bid_quantity)}</strong></span>
      </div>
      <div className="orderbook-head"><span>잔량 비중</span><span>가격</span><span>수량</span></div>
      {[...data.asks].reverse().map((level) => (
        <OrderLevel
          key={`ask-${level.price}`}
          level={level}
          type="ask"
          maxQuantity={maxQuantity}
          currency={data.currency}
        />
      ))}
      <div className="orderbook-current">
        <span><Icon name="refresh" size={13} /> 현재가</span>
        <strong>{formatQuotePrice(currentPrice, data.currency)}</strong>
        <small>{data.delayed ? '지연·데모 데이터' : '조회 시점 스냅샷'}</small>
      </div>
      {data.bids.map((level) => (
        <OrderLevel
          key={`bid-${level.price}`}
          level={level}
          type="bid"
          maxQuantity={maxQuantity}
          currency={data.currency}
        />
      ))}
    </div>
  );
}

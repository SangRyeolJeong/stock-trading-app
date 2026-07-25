export function formatQuotePrice(price: string | number, currency: 'KRW' | 'USD') {
  const value = Number(price);
  return currency === 'USD'
    ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : `${Math.round(value).toLocaleString('ko-KR')}원`;
}

export function formatChangeRate(rate: string | number) {
  const value = Number(rate);
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

export function formatUpdatedAt(value?: string) {
  if (!value) return '업데이트 대기 중';
  return new Intl.DateTimeFormat('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value));
}

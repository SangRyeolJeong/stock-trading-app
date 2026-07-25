export interface AccountComparison {
  id: string;
  name: string;
  tag: string;
  tax: string;
  limit: string;
  product: string;
  note: string;
  score: number;
}

export const accounts: AccountComparison[] = [
  { id: 'direct', name: '해외주식 직투', tag: '유동성', tax: '연 250만원 공제 후 22%', limit: '제한 없음', product: 'QQQM', note: '달러 자산을 직접 보유하고 언제든 매매하기 좋아요.', score: 76 },
  { id: 'isa', name: '중개형 ISA', tag: '절세', tax: '200만원 비과세 + 9.9%', limit: '연 2,000만원', product: '국내상장 해외 ETF', note: '3년 이상 투자하고 목돈을 운용할 때 효율적이에요.', score: 88 },
  { id: 'pension', name: '연금저축펀드', tag: '장기투자', tax: '최대 16.5% 세액공제', limit: '세액공제 연 600만원', product: 'TIGER 미국나스닥100', note: '55세 이후 사용할 장기 자금이라면 우선순위가 높아요.', score: 96 },
  { id: 'irp', name: 'IRP', tag: '노후', tax: '연금저축 합산 900만원', limit: '연 1,800만원', product: 'ETF + 안전자산 30%', note: '추가 세액공제에 좋지만 중도인출 제약을 확인하세요.', score: 84 },
];

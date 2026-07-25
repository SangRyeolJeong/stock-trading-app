import type { IconName } from '../../components/common/Icon';

export interface Lesson {
  category: string;
  title: string;
  desc: string;
  time: string;
  color: string;
  icon: IconName;
}

export const lessons: Lesson[] = [
  { category: 'ETF 비교', title: 'QQQ와 QQQM, 무엇이 다를까요?', desc: '같은 지수를 추종해도 보수와 거래량이 달라요.', time: '6분', color: 'blue', icon: 'chart' },
  { category: '절세 계좌', title: 'ISA 만기 자금, 연금으로 옮기면?', desc: '추가 세액공제를 받는 연계 전략을 알아봐요.', time: '8분', color: 'green', icon: 'wallet' },
  { category: '연금', title: '연금저축과 IRP의 결정적 차이', desc: '인출 조건과 투자 가능 자산을 비교해요.', time: '7분', color: 'purple', icon: 'wallet' },
  { category: '자격증', title: '투자자산운용사 핵심 개념 노트', desc: '포트폴리오 이론부터 세제까지 정리했어요.', time: '12분', color: 'orange', icon: 'book' },
  { category: '해외주식', title: '달러를 직접 보유한다는 것', desc: '환전, 유동성, 양도소득세를 쉽게 설명해요.', time: '9분', color: 'navy', icon: 'chart' },
  { category: '투자 습관', title: '장기 적립식 투자의 체크리스트', desc: '수익률보다 오래 지키는 규칙을 만들어요.', time: '5분', color: 'mint', icon: 'chart' },
];

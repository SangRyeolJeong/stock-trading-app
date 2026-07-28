import type { IconName } from '../components/common/Icon';

export interface LessonSource {
  title: string;
  authority: string;
  url: string;
}

export interface LessonSection {
  heading: string;
  paragraphs: string[];
  bullets?: string[];
}

export interface Lesson {
  slug: string;
  category: string;
  title: string;
  desc: string;
  minutes: number;
  color: string;
  icon: IconName;
  updatedAt: string;
  summary: string;
  takeaways: string[];
  sections: LessonSection[];
  sources: LessonSource[];
  relatedSymbol?: string;
}

export const lessons: Lesson[] = [
  {
    slug: 'compound-interest',
    category: '투자 습관',
    title: '복리 효과는 언제부터 눈에 보일까요?',
    desc: '원금뿐 아니라 누적 수익에도 다시 수익이 붙는 구조를 이해해요.',
    minutes: 5,
    color: 'mint',
    icon: 'chart',
    updatedAt: '2026-07-28',
    summary: '복리는 단기 수익률을 높이는 기술이 아니라, 수익이 다시 투자되는 시간을 충분히 확보하는 구조입니다.',
    takeaways: [
      '복리는 원금과 이미 쌓인 수익에 함께 수익이 붙는 구조예요.',
      '수익률이 같다면 투자 기간이 길수록 후반부 증가 폭이 커져요.',
      '높은 기대수익률보다 꾸준한 납입과 중도 이탈 방지가 먼저예요.',
    ],
    sections: [
      {
        heading: '시간이 수익의 일부가 되는 이유',
        paragraphs: [
          '단리에서는 최초 원금에만 수익이 붙지만, 복리에서는 이전 기간에 발생한 수익도 다음 기간의 계산 기반에 포함됩니다. 그래서 초기에는 차이가 작아 보여도 시간이 길어질수록 격차가 커집니다.',
          '다만 실제 투자는 매년 같은 수익률을 보장하지 않습니다. 복리 계산은 미래를 확정하는 예측이 아니라 기간과 수익률의 관계를 이해하기 위한 시뮬레이션으로 봐야 합니다.',
        ],
      },
      {
        heading: '복리를 지키는 실전 규칙',
        paragraphs: [
          '장기 계획에서는 가장 높은 수익률을 맞히는 것보다 투자 중단을 피할 수 있는 납입액과 자산배분을 정하는 편이 중요합니다.',
        ],
        bullets: [
          '생활비와 비상자금을 투자금과 분리하기',
          '감당 가능한 금액을 자동이체로 정기 납입하기',
          '배당과 분배금의 재투자 여부를 미리 정하기',
          '수수료와 세금처럼 반복해서 빠지는 비용 확인하기',
        ],
      },
    ],
    sources: [
      {
        title: 'What is compound interest?',
        authority: '미국 SEC Investor.gov',
        url: 'https://www.investor.gov/additional-resources/information/youth/teachers-classroom-resources/what-compound-interest',
      },
      {
        title: 'Compound Interest Calculator',
        authority: '미국 SEC Investor.gov',
        url: 'https://www.investor.gov/financial-tools-calculators/calculators/compound-interest-calculator',
      },
    ],
  },
  {
    slug: 'qqq-vs-qqqm',
    category: 'ETF 비교',
    title: 'QQQ와 QQQM, 무엇이 다를까요?',
    desc: '같은 지수를 추종해도 보수와 거래 특성이 달라요.',
    minutes: 6,
    color: 'blue',
    icon: 'chart',
    updatedAt: '2026-07-28',
    summary: '두 ETF 모두 Nasdaq-100 지수를 추종하지만, 장기 보유 비용과 거래 편의 중 무엇을 중시하는지에 따라 선택이 달라질 수 있습니다.',
    takeaways: [
      '두 상품의 기초지수는 Nasdaq-100으로 같아요.',
      '2026년 7월 공식 자료 기준 총보수는 QQQ 0.18%, QQQM 0.15%예요.',
      '실제 매수 전에는 보수 외에도 호가 스프레드와 거래량을 확인해야 해요.',
    ],
    sections: [
      {
        heading: '같은 지수, 다른 상품 구조',
        paragraphs: [
          'QQQ와 QQQM은 모두 Nasdaq 시장에 상장된 대형 비금융 기업 100개로 구성된 Nasdaq-100 지수에 노출됩니다. 지수 방향은 같지만 펀드의 설정 시점, 규모, 거래 특성, 비용은 서로 다릅니다.',
          'Invesco의 2026년 7월 상품 자료에는 QQQ 총보수 0.18%, QQQM 총보수 0.15%로 표시됩니다. 보수는 변경될 수 있으므로 주문 직전 운용사 문서를 다시 확인해야 합니다.',
        ],
      },
      {
        heading: '장기 적립과 잦은 거래의 체크포인트',
        paragraphs: [
          '보유 기간이 길수록 반복되는 보수 차이를 살펴볼 가치가 있습니다. 반면 매매가 잦다면 특정 시점의 호가 스프레드와 체결 가능성이 총보수 차이보다 크게 작용할 수 있습니다.',
        ],
        bullets: [
          '장기 적립: 총보수와 추적 오차를 우선 확인',
          '잦은 거래: 거래량, 호가 잔량, 스프레드도 확인',
          '세금: 거주 국가와 계좌 유형에 따른 과세 방식 확인',
          '분산: Nasdaq-100 집중도가 전체 포트폴리오에서 과하지 않은지 확인',
        ],
      },
    ],
    sources: [
      {
        title: 'QQQ Innovation Suite',
        authority: 'Invesco',
        url: 'https://www.invesco.com/us/en/solutions/innovation-suite.html',
      },
      {
        title: 'QQQM: Innovation for the long term',
        authority: 'Invesco',
        url: 'https://www.invesco.com/us/en/insights/qqqm-innovation-long-term.html',
      },
    ],
    relatedSymbol: 'QQQM',
  },
  {
    slug: 'isa-to-pension',
    category: '절세 계좌',
    title: 'ISA 만기 자금, 연금으로 옮기면?',
    desc: '계좌를 잇는 전략의 조건과 유동성 변화를 살펴봐요.',
    minutes: 8,
    color: 'green',
    icon: 'wallet',
    updatedAt: '2026-07-28',
    summary: 'ISA 만기 자금을 연금계좌로 옮기는 선택은 추가 세제 혜택 가능성과 장기간의 인출 제약을 함께 비교해야 합니다.',
    takeaways: [
      'ISA는 일정 유지기간과 납입 조건을 충족해야 세제 혜택을 적용받아요.',
      '만기 자금의 연금계좌 이전은 세제 혜택과 유동성 제약을 함께 만들어요.',
      '이전 전에는 최신 법령과 개인별 공제 여력을 확인해야 해요.',
    ],
    sections: [
      {
        heading: 'ISA에서 먼저 확인할 것',
        paragraphs: [
          'ISA는 계좌 안에서 여러 금융상품을 운용하면서 손익을 통산하고 일정 요건 아래 세제 혜택을 적용받는 구조입니다. 기획재정부 안내는 의무 계약기간을 3년 이상으로 설명하고, 미사용 납입한도의 이월을 허용한다고 안내합니다.',
          '중개형 ISA에서는 국내상장주식과 국내상장 ETF 등을 거래할 수 있지만 해외상장주식을 직접 담을 수는 없습니다. 상품의 상장 국가와 계좌 편입 가능 여부를 구분해야 합니다.',
        ],
      },
      {
        heading: '연금으로 옮기기 전 질문',
        paragraphs: [
          '연금계좌 이전은 노후자금의 세제 효율을 높이는 데 도움이 될 수 있지만, 필요한 시점에 자유롭게 쓰기 어려워질 수 있습니다. 이전 금액과 시기, 세액공제 한도는 당시 규정과 개인의 다른 연금 납입액에 따라 달라집니다.',
        ],
        bullets: [
          '가까운 시일 안에 사용할 자금인지',
          '이미 연금저축이나 IRP 세액공제 한도를 사용했는지',
          '연금 수령 전 중도 인출 가능성과 세금 불이익을 이해했는지',
          '이전 신청 기한과 금융회사 처리 절차를 확인했는지',
        ],
      },
    ],
    sources: [
      {
        title: '개인종합자산관리계좌(ISA) 전면 개편',
        authority: '기획재정부',
        url: 'https://whatsnew.moef.go.kr/mec/ots/dif/view.do?comBaseCd=DIFGODEPRT&difGovDepart1=DIFGODR001&difSer=c514effc-c831-4eb1-94c7-6eab084dcac8&temp=2021&temp2=HALF001',
      },
      {
        title: '연금계좌 세액공제 안내',
        authority: '국세청',
        url: 'https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=2238',
      },
    ],
  },
  {
    slug: 'pension-vs-irp',
    category: '연금',
    title: '연금저축과 IRP의 결정적 차이',
    desc: '인출 조건과 투자 가능 자산을 중심으로 비교해요.',
    minutes: 7,
    color: 'purple',
    icon: 'wallet',
    updatedAt: '2026-07-28',
    summary: '연금저축과 IRP는 모두 노후 준비에 쓰이지만, 세액공제 범위와 중도 인출, 위험자산 편입 제약이 다릅니다.',
    takeaways: [
      '세액공제만 보지 말고 자금을 묶어둘 수 있는 기간을 먼저 정해요.',
      'IRP는 법정 사유 외 중도 인출이 제한적이고 위험자산 비중에도 제약이 있어요.',
      '두 계좌를 함께 쓸 때는 합산 한도와 기존 납입액을 확인해야 해요.',
    ],
    sections: [
      {
        heading: '공통점과 차이점',
        paragraphs: [
          '두 계좌 모두 납입 단계의 세액공제와 운용 중 과세이연을 활용할 수 있는 장기 계좌입니다. 정상적인 연금 수령 요건을 충족하지 못하고 자금을 꺼내면 세제상 불이익이 생길 수 있습니다.',
          '연금저축은 상품 선택과 인출 측면에서 상대적으로 유연한 편이고, IRP는 퇴직금 수령 기능과 더 넓은 세액공제 범위를 제공하는 대신 중도 인출과 위험자산 편입에 더 강한 제약이 있습니다.',
        ],
      },
      {
        heading: '계좌 순서를 정하는 방법',
        paragraphs: [
          '정답은 세액공제 금액 하나로 결정되지 않습니다. 비상자금, 은퇴까지 남은 기간, 다른 연금 납입액, 원하는 투자상품을 함께 놓고 판단해야 합니다.',
        ],
        bullets: [
          '중도에 쓸 가능성이 있는 돈은 먼저 분리',
          '각 계좌에서 매수 가능한 ETF와 예금 상품 확인',
          '연말정산에서 실제로 받을 수 있는 공제 범위 확인',
          '연금 수령 시점의 예상 소득과 수령 계획 점검',
        ],
      },
    ],
    sources: [
      {
        title: '연금계좌 세액공제 안내',
        authority: '국세청',
        url: 'https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=2238',
      },
      {
        title: '연금계좌 과세대상과 연금수령 세율',
        authority: '국세청 국세법령정보시스템',
        url: 'https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=200000000000010709',
      },
    ],
  },
  {
    slug: 'investment-manager-notes',
    category: '자격증',
    title: '투자자산운용사 핵심 개념 노트',
    desc: '포트폴리오 이론을 실제 투자 판단과 연결해요.',
    minutes: 12,
    color: 'orange',
    icon: 'book',
    updatedAt: '2026-07-28',
    summary: '암기한 공식을 문제 상황에 적용하려면 기대수익, 위험, 상관관계가 포트폴리오 전체에 미치는 영향을 함께 이해해야 합니다.',
    takeaways: [
      '개별 자산의 위험과 포트폴리오 위험은 같지 않아요.',
      '상관관계가 낮은 자산의 조합은 분산 효과를 만들 수 있어요.',
      '시험 일정과 세부 출제 기준은 금융투자협회 공지를 기준으로 확인해요.',
    ],
    sections: [
      {
        heading: '위험과 수익을 한 문장으로 설명하기',
        paragraphs: [
          '기대수익률은 가능한 결과의 확률가중 평균이고, 분산과 표준편차는 결과가 평균에서 얼마나 퍼질 수 있는지 보여주는 지표입니다. 숫자를 계산한 뒤에는 그 값이 투자자의 목표와 손실 감내 범위에 맞는지 해석해야 합니다.',
          '여러 자산을 묶으면 각 자산의 변동성뿐 아니라 자산끼리 함께 움직이는 정도가 전체 위험을 좌우합니다. 이것이 상관계수와 공분산을 배우는 이유입니다.',
        ],
      },
      {
        heading: '문제 풀이 체크리스트',
        paragraphs: [
          '공식을 바로 대입하기 전에 문제에서 요구하는 값, 기간 단위, 수익률 표기 방식부터 표시하면 계산 실수를 줄일 수 있습니다.',
        ],
        bullets: [
          '연 수익률과 월 수익률의 단위가 섞였는지 확인',
          '표준편차와 분산을 구분',
          '명목수익률과 실질수익률을 구분',
          '분산투자가 모든 시장 하락을 막아주는 것은 아님을 기억',
        ],
      },
    ],
    sources: [
      {
        title: '투자자산운용사 시험 안내',
        authority: '금융투자협회 자격시험센터',
        url: 'https://license.kofia.or.kr/',
      },
      {
        title: 'Asset Allocation and Diversification',
        authority: '미국 SEC Investor.gov',
        url: 'https://www.investor.gov/introduction-investing/getting-started/asset-allocation',
      },
    ],
  },
  {
    slug: 'holding-us-dollars',
    category: '해외주식',
    title: '달러를 직접 보유한다는 것',
    desc: '환전, 유동성, 세금이 수익에 미치는 영향을 살펴봐요.',
    minutes: 9,
    color: 'navy',
    icon: 'chart',
    updatedAt: '2026-07-28',
    summary: '해외주식 수익은 주가 변화뿐 아니라 환율, 환전 비용, 세금과 매매 비용이 함께 결정합니다.',
    takeaways: [
      '원화 기준 수익률은 달러 자산 가격과 USD/KRW 환율의 영향을 함께 받아요.',
      '환전 스프레드와 매매수수료는 반복될수록 누적돼요.',
      '국외주식 양도손익은 국내 과세 규정에 맞춰 기록하고 신고해야 해요.',
    ],
    sections: [
      {
        heading: '주가는 올랐는데 원화 수익은 다를 수 있어요',
        paragraphs: [
          '달러 표시 주식이 올라도 같은 기간 원화가 강해지면 원화 환산 수익은 줄어들 수 있습니다. 반대로 주가가 약해도 달러 강세가 일부 손실을 상쇄할 수 있습니다.',
          '따라서 해외주식 성과를 볼 때는 달러 기준 수익과 원화 환산 수익을 분리해 확인하는 편이 좋습니다.',
        ],
      },
      {
        heading: '매매 전에 기록할 네 가지',
        paragraphs: [
          '세금 계산과 성과 측정을 위해 체결일, 체결금액, 적용 환율, 수수료를 함께 보관해야 합니다. 국외주식 과세 규정과 신고 방식은 거래연도와 개인 상황에 따라 달라질 수 있어 최신 국세청 안내를 확인해야 합니다.',
        ],
        bullets: [
          '매수·매도 체결일과 수량',
          '거래 통화 기준 체결가격',
          '환전 시점과 적용 환율',
          '증권사 수수료와 현지 제비용',
        ],
      },
    ],
    sources: [
      {
        title: '국내·국외주식 양도소득세 안내',
        authority: '국세청',
        url: 'https://s.nts.go.kr/jongno/na/ntt/selectNttInfo.do?mi=2201&nttSn=1350890',
      },
      {
        title: '소득세법 제104조',
        authority: '국가법령정보센터',
        url: 'https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1021859939',
      },
    ],
    relatedSymbol: 'AAPL',
  },
  {
    slug: 'long-term-checklist',
    category: '투자 습관',
    title: '장기 적립식 투자의 체크리스트',
    desc: '수익률보다 오래 지킬 수 있는 투자 규칙을 만들어요.',
    minutes: 5,
    color: 'mint',
    icon: 'check',
    updatedAt: '2026-07-28',
    summary: '정기 적립은 매수 시점을 분산하고 감정적인 결정을 줄일 수 있지만, 수익을 보장하거나 모든 손실을 막아주지는 않습니다.',
    takeaways: [
      '정기 적립은 시장 예측보다 실행 규칙에 초점을 맞춰요.',
      '현금을 나눠 투자하면 변동 위험은 줄 수 있지만 기회비용이 생길 수 있어요.',
      'ETF를 여러 개 보유해도 기초자산이 겹치면 충분히 분산되지 않을 수 있어요.',
    ],
    sections: [
      {
        heading: '적립식 투자가 해결하는 문제',
        paragraphs: [
          '같은 금액을 정기적으로 투자하면 가격이 낮을 때 더 많은 수량을, 높을 때 더 적은 수량을 사게 됩니다. 무엇보다 일정에 따라 실행하기 때문에 공포와 낙관에 따른 충동 매매를 줄이는 데 도움이 될 수 있습니다.',
          '이미 가진 목돈을 오랜 기간 현금으로 남겨 나눠 투자하면 상승장에서 일부 수익 기회를 놓칠 수 있습니다. 정기 적립은 위험과 기대수익 사이의 선택이지 항상 더 높은 수익을 주는 공식이 아닙니다.',
        ],
      },
      {
        heading: '월 1회 확인할 항목',
        paragraphs: [
          '매일 가격을 확인하는 대신 납입 실행 여부와 포트폴리오의 구조적 변화에 집중합니다.',
        ],
        bullets: [
          '자동이체와 주문이 계획대로 실행됐는지',
          '비상자금을 건드리지 않았는지',
          '특정 국가·섹터·종목의 비중이 과도해지지 않았는지',
          '상품 보수와 계좌 수수료가 바뀌지 않았는지',
        ],
      },
    ],
    sources: [
      {
        title: 'The Benefits and Limitations of Dollar-Cost Averaging',
        authority: 'FINRA',
        url: 'https://syndication.finra.org/content/benefits-and-limitations-dollar-cost-averaging',
      },
      {
        title: 'Asset Allocation and Diversification',
        authority: '미국 SEC Investor.gov',
        url: 'https://www.investor.gov/introduction-investing/getting-started/asset-allocation',
      },
    ],
  },
];

export function findLesson(slug: string | undefined) {
  return lessons.find((lesson) => lesson.slug === slug);
}

export interface LessonProgressEntry {
  completed: boolean;
  lastOpenedAt: string;
}

export type LessonProgress = Record<string, LessonProgressEntry>;

const PROGRESS_STORAGE_KEY = 'moa-learn-progress';

export function loadLessonProgress(): LessonProgress {
  try {
    const stored = window.localStorage.getItem(PROGRESS_STORAGE_KEY);
    const parsed = stored ? JSON.parse(stored) as unknown : null;
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? parsed as LessonProgress
      : {};
  } catch {
    return {};
  }
}

export function saveLessonProgress(progress: LessonProgress) {
  window.localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(progress));
}

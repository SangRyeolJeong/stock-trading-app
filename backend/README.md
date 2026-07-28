# MOA API

FastAPI 기반의 MOA 백엔드입니다. 비동기 시세 스트림, 모의 주문, 포트폴리오,
절세 계산 및 전략 추천을 제공하는 것을 목표로 합니다.

현재는 한투 API 키 없이도 프론트엔드 개발과 테스트가 가능하도록
`MockMarketDataProvider`가 기본값입니다. 주문은 PostgreSQL 원장에 영속화되며,
단일 데모 사용자의 원화·달러 초기 잔액이 첫 조회 또는 주문 시 생성됩니다.

`MARKET_DATA_PROVIDER=kis`로 변경하면 한국투자증권 REST API에서 국내·해외
현재가와 USD/KRW 환율을 조회합니다. 앱 키가 없을 때 서버가 실수로 KIS 모드로
실행되지 않도록 시작 단계에서 설정 오류를 발생시킵니다.

## 로컬 실행

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
pytest
uvicorn app.main:app --reload --port 8000
```

현재 작업 환경처럼 WSL의 `python3-venv`가 없는 경우 Windows PowerShell에서
Python 3.12 가상환경을 사용할 수 있습니다.

```powershell
cd D:\programming\backend
py -3.12 -m venv .venv-win
.\.venv-win\Scripts\python -m pip install -r requirements-dev.txt
.\.venv-win\Scripts\python -m alembic upgrade head
.\.venv-win\Scripts\python -m pytest
.\.venv-win\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

실행 후 확인:

- API 상태: `http://localhost:8000/health`
- API 문서: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

## 현재 구조

```text
app/
├── api/              # HTTP/WebSocket 라우터
├── core/             # 환경설정과 공통 예외
├── db/               # 비동기 SQLAlchemy 엔진과 세션
├── integrations/kis/ # 한국투자증권 경계
├── models/           # 모의 계좌, 주문, 체결, 원장과 포지션
├── schemas/          # 요청·응답 모델
└── services/         # 시장, 모의투자, 전략 서비스
```

## 모의투자 API

- `GET /api/v1/paper/accounts`
- `GET /api/v1/paper/orders`
- `GET /api/v1/paper/positions`
- `GET /api/v1/portfolios/summary`
- `POST /api/v1/paper/orders`
- `DELETE /api/v1/paper/orders/{order_id}`

시장가 주문은 현재 시세로 즉시 체결합니다. 지정가는 매수 시 현재가 이하,
매도 시 현재가 이상이라는 가격 제한을 지키며, 조건이 충족되지 않으면 대기합니다.
주문 목록 조회 시 최신 시세와 대기 주문을 다시 대조하고 조건이 충족되면 현재
시세로 체결합니다. 대기 주문은 취소할 수 있고, 현금과 보유 수량은 다른 대기
주문에 예약된 금액·수량까지 반영해 검증합니다. 수수료율은 `PAPER_FEE_RATE`로
설정하며, 체결 시 주문·현금 원장·포지션·스냅샷을 하나의 DB 트랜잭션으로
처리합니다.

## 시장 데이터 API

- `GET /api/v1/markets/quotes/{symbol}`
- `GET /api/v1/markets/instruments`
- `GET /api/v1/markets/candles/{symbol}`
- `GET /api/v1/markets/orderbooks/{symbol}`
- `GET /api/v1/markets/overview/{symbol}`
- `GET /api/v1/markets/exchange-rates/{base_currency}/{quote_currency}`
- `WS /api/v1/markets/ws/quotes/{symbol}`

KIS 모드의 국내 현재가는 `FHKST01010100`, 해외 현재가는
`HHDFS00000300`을 사용합니다. USD/KRW는 해외 현재가 상세
`HHDFS76200200` 응답의 당일 환율을 사용합니다. 현재 지원 통화는 KRW와
USD이며, 해외 종목의 기본 거래소는 `KIS_DEFAULT_OVERSEAS_EXCHANGE`로
설정합니다. REST 기반 WebSocket 브리지는 호출 제한을 고려해 5초마다
갱신합니다.

종목 검색은 KIS가 배포하는 국내·미국 종목 마스터를 로컬 캐시하며, 마스터
다운로드가 실패하면 기본 종목 목록으로 폴백합니다. 일봉은 국내
`FHKST03010100`, 해외 `HHDFS76240000`을 사용합니다. 호가는 국내
`FHKST01010200`의 10단계 호가와 해외 `HHDFS76200100`의 최우선 1호가를
공통 응답으로 정규화합니다. 호가 REST 응답은 실시간 스트림이 아닌 조회 시점
스냅샷입니다. 기업정보는 같은 현재가 응답에서 시가·고가·저가·거래량,
52주 범위와 PER·PBR·EPS·BPS를 국내외 공통 필드로 제공합니다.

## 절세 계산 API

- `POST /api/v1/tax/simulate`

동일한 총급여, 월 투자금, 기간, 수익률과 연금 수령 나이로 해외직투,
중개형 ISA, 연금저축펀드와 IRP를 비교합니다. 세제 숫자는
`app/tax/rules.py`의 `KR-2026.07` 규칙으로 버전 관리하며 API 응답에 공식
근거와 가정을 포함합니다.

현재 계산은 매년 말 납입, 마지막 해 일괄 처분, 수수료·환율 제외 모델입니다.
ISA는 누적 납입 1억원까지만 혜택을 적용하고 초과 금액은 해외직투로 계산합니다.
연금 세액공제 환급액은 재투자하지 않으며 정상적인 연금 수령을 가정합니다.

## 전략 추천 API

- `POST /api/v1/strategies/recommend`

목표, 투자기간, 월 투자금, 위험성향과 유동성·비용·배당 선호를 입력받아
`STRATEGY-2026.07` 규칙으로 자산군·계좌별 비중을 계산합니다. 응답에는
월 납입액, 적합도, 추천 근거 코드, 위험 요약, 실행 순서, 경고와 계산 가정이
포함됩니다.

추천 결과는 같은 입력에 항상 같은 결과를 반환하며 총 자산 비중은 100%,
자산별 월 납입액 합계는 입력 월 투자금과 일치합니다. 위험성향별 주식성 자산
상한과 유동성 선호 시 최소 현금 비중도 엔진에서 검증합니다.

## 설계 원칙

- 금융·세금 계산은 버전이 기록되는 규칙 엔진에서 결정적으로 수행합니다.
- AI는 근거 검색과 설명을 담당하고 계산 결과를 임의로 만들지 않습니다.
- 실제 시세, 모의 주문, 실전 증권 주문은 서로 다른 모듈로 분리합니다.
- 주문 요청은 `idempotency_key`를 필수로 받으며, 영속 원장 단계에서 유일 제약으로 중복 처리를 막습니다.
- 금액과 수량은 `float`가 아니라 `Decimal`/PostgreSQL `NUMERIC`을 사용합니다.
- 한투 API 키는 서버 환경변수에만 보관합니다.
